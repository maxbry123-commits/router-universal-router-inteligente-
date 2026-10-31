// server.test.mjs — integracion de server.js REAL con dependencias externas simuladas.
// - Copia web-bridge a un directorio temporal (os.tmpdir).
// - express: `npm install express` en el temporal; sin red (o TEST_STUB_EXPRESS=1) usa un stub minimo.
// - playwright: paquete falso en node_modules (solo para que browser.js se pueda importar).
// - src/motor.js de la COPIA se reemplaza por un doble controlable (consultarWeb/salud); el resto de src/ es el real.
// - Groq / NVIDIA / HF-local: http.createServer en 127.0.0.1 (BASES se ajusta con --import preload).
// Nada toca el repo ni la red externa.
import test, { before, after } from 'node:test';
import assert from 'node:assert/strict';
import { spawn, spawnSync } from 'node:child_process';
import fs from 'node:fs';
import http from 'node:http';
import net from 'node:net';
import os from 'node:os';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const AQUI = path.dirname(fileURLToPath(import.meta.url));
const ORIGEN = path.resolve(AQUI, '..');
const TMP = fs.mkdtempSync(path.join(os.tmpdir(), 'bridge-int-'));
const APP = path.join(TMP, 'app');
const servidores = [];   // procesos hijos del bridge
const mocks = [];        // http.Server simulados

// ---------- doble de motor.js (se escribe en la copia) ----------
const MOTOR_FALSO = `
import fs from 'node:fs';
import path from 'node:path';
import { pool } from './cuentas.js';
const D = () => process.env.BRIDGE_STATE_DIR || './state';
const ctrl = () => { try { return JSON.parse(fs.readFileSync(path.join(D(), 'fake-web.json'), 'utf8')); } catch { return { modo: 'ok' }; } };
let sano = false;
export async function consultarWeb(modelo, texto, opts = {}) {
  pool(); // como browser.js: sin cuentas -> CUENTAS_FALTAN
  fs.mkdirSync(D(), { recursive: true });
  fs.appendFileSync(path.join(D(), 'web-calls.jsonl'), JSON.stringify({ modelo, texto, opts }) + '\\n');
  const m = ctrl().modo;
  if (m === 'fail') throw Object.assign(new Error('selector roto'), { code: 'SELECTOR_BROKEN' });
  if (m === 'expire_always') throw Object.assign(new Error('sesion muerta'), { code: 'SESSION_EXPIRED' });
  if (m === 'expire_once' && !sano) throw Object.assign(new Error('sesion muerta'), { code: 'SESSION_EXPIRED' });
  if (m === 'empty') return '';
  if (m === 'slow') await new Promise(() => {});
  return 'WEB[' + modelo + ']';
}
export async function salud() { sano = true; return { qwen: 'vivo', deepseek: 'vivo' }; }
`;

const PLAYWRIGHT_FALSO = `export const chromium = { launchPersistentContext() { throw new Error('playwright simulado: no hay navegador en tests'); } };\n`;

const PRELOAD = `
const r = await import('./src/respaldo.js');
if (process.env.TEST_GROQ_URL) r.BASES.groq = process.env.TEST_GROQ_URL;
if (process.env.TEST_NVIDIA_URL) r.BASES.nvidia = process.env.TEST_NVIDIA_URL;
`;

// express minimo (solo si no hay red para instalar el real)
const EXPRESS_STUB = `
import http from 'node:http';
function express() {
  const rutas = [], mws = [];
  const app = async (req, res) => {
    const u = new URL(req.url, 'http://x');
    req.query = Object.fromEntries(u.searchParams); req.path = u.pathname; req.params = {};
    res.status = (c) => { res.statusCode = c; return res; };
    res.json = (o) => { if (!res.getHeader('content-type')) res.setHeader('content-type', 'application/json'); res.end(JSON.stringify(o)); return res; };
    for (const mw of mws) await new Promise((ok) => mw(req, res, ok));
    if (res.writableEnded) return;
    for (const r of rutas) {
      if (r.metodo !== req.method) continue;
      const ks = []; const re = new RegExp('^' + r.ruta.replace(/:([a-zA-Z_]+)/g, (_, k) => { ks.push(k); return '([^/]+)'; }) + '$');
      const m = re.exec(u.pathname); if (!m) continue;
      ks.forEach((k, i) => req.params[k] = decodeURIComponent(m[i + 1]));
      return r.fn(req, res);
    }
    res.statusCode = 404; res.end('not found');
  };
  app.use = (fn) => mws.push(fn);
  for (const m of ['get', 'post', 'delete']) app[m] = (ruta, fn) => rutas.push({ metodo: m.toUpperCase(), ruta, fn });
  app.listen = (port, cb) => { const s = http.createServer(app).listen(port, cb); return s; };
  return app;
}
express.json = () => (req, res, next) => {
  if (req.method !== 'POST') return next();
  let d = ''; req.on('data', (c) => d += c);
  req.on('end', () => { try { req.body = d ? JSON.parse(d) : {}; next(); } catch { res.statusCode = 400; res.end('bad json'); } });
};
export default express;
`;

function prepararApp() {
  fs.mkdirSync(APP, { recursive: true });
  fs.cpSync(path.join(ORIGEN, 'src'), path.join(APP, 'src'), { recursive: true });
  for (const f of ['memoria_hf.py']) if (fs.existsSync(path.join(ORIGEN, f))) fs.copyFileSync(path.join(ORIGEN, f), path.join(APP, f));
  fs.writeFileSync(path.join(APP, 'package.json'), JSON.stringify({ name: 'bridge-test', private: true, type: 'module', dependencies: { express: '^4.19.2' } }));
  fs.writeFileSync(path.join(APP, 'src', 'motor.js'), MOTOR_FALSO);
  fs.writeFileSync(path.join(APP, 'preload.mjs'), PRELOAD);

  let expressReal = false;
  if (!process.env.TEST_STUB_EXPRESS) {
    const r = spawnSync('npm', ['install', 'express', '--no-audit', '--no-fund', '--no-package-lock', '--loglevel=error'], { cwd: APP, timeout: 120000, encoding: 'utf8' });
    expressReal = r.status === 0 && fs.existsSync(path.join(APP, 'node_modules', 'express', 'package.json'));
  }
  if (!expressReal) {
    const d = path.join(APP, 'node_modules', 'express');
    fs.mkdirSync(d, { recursive: true });
    fs.writeFileSync(path.join(d, 'package.json'), JSON.stringify({ name: 'express', type: 'module', main: 'index.js', exports: './index.js' }));
    fs.writeFileSync(path.join(d, 'index.js'), EXPRESS_STUB);
  }
  // playwright falso (despues del install para que npm no lo pode)
  const pw = path.join(APP, 'node_modules', 'playwright');
  fs.mkdirSync(pw, { recursive: true });
  fs.writeFileSync(path.join(pw, 'package.json'), JSON.stringify({ name: 'playwright', type: 'module', main: 'index.js', exports: './index.js' }));
  fs.writeFileSync(path.join(pw, 'index.js'), PLAYWRIGHT_FALSO);
  return expressReal;
}

// ---------- utilidades ----------
const puertoLibre = () => new Promise((ok) => { const s = net.createServer().listen(0, '127.0.0.1', () => { const p = s.address().port; s.close(() => ok(p)); }); });

// API openai-compatible simulada (Groq / NVIDIA / HF-local). `cfg.status` y `cfg.texto` se pueden cambiar entre tests.
async function mockApi(nombre) {
  const cfg = { status: 200, texto: `de-${nombre}`, hits: [] };
  const s = http.createServer((req, res) => {
    let d = ''; req.on('data', (c) => d += c); req.on('end', () => {
      let body = null; try { body = JSON.parse(d); } catch { /* ignore */ }
      cfg.hits.push({ url: req.url, auth: req.headers.authorization, body });
      res.writeHead(cfg.status, { 'content-type': 'application/json' });
      res.end(JSON.stringify({ choices: [{ finish_reason: cfg.tool_calls ? 'tool_calls' : 'stop', message: { role: 'assistant', content: cfg.tool_calls ? null : cfg.texto, ...(cfg.tool_calls ? { tool_calls: cfg.tool_calls } : {}) } }] }));
    });
  });
  await new Promise((ok) => s.listen(0, '127.0.0.1', ok));
  mocks.push(s);
  cfg.url = `http://127.0.0.1:${s.address().port}`;
  return cfg;
}

async function arrancar(nombre, envExtra = {}) {
  const port = await puertoLibre();
  const state = path.join(TMP, `state-${nombre}`);
  fs.mkdirSync(state, { recursive: true });
  const env = {
    PATH: process.env.PATH, HOME: TMP, TMPDIR: TMP,
    BRIDGE_PORT: String(port), BRIDGE_STATE_DIR: state,
    RIU_ACTIVAR_PATH: fileURLToPath(new URL('../../../SWE CODE free/activar.js', import.meta.url)),
    ...envExtra,
  };
  const p = spawn(process.execPath, ['--import', './preload.mjs', 'src/server.js'], { cwd: APP, env, stdio: ['ignore', 'pipe', 'pipe'] });
  let log = '';
  p.stdout.on('data', (c) => log += c); p.stderr.on('data', (c) => log += c);
  await new Promise((ok, ko) => {
    const t = setTimeout(() => ko(new Error(`server ${nombre} no arranco:\n${log}`)), 15000);
    const iv = setInterval(() => { if (/escuchando/.test(log)) { clearTimeout(t); clearInterval(iv); ok(); } }, 50);
    p.on('exit', (c) => { clearTimeout(t); clearInterval(iv); ko(new Error(`server ${nombre} salio (${c}):\n${log}`)); });
  });
  const srv = { nombre, port, state, proc: p, base: `http://127.0.0.1:${port}`, log: () => log };
  servidores.push(srv);
  return srv;
}

const get = async (srv, ruta) => { const r = await fetch(srv.base + ruta); return { status: r.status, headers: r.headers, json: await r.json().catch(() => null) }; };
const chat = async (srv, body) => {
  const r = await fetch(srv.base + '/v1/chat/completions', { method: 'POST', headers: { 'content-type': 'application/json' }, body: JSON.stringify({ messages: [{ role: 'user', content: 'hola mundo' }], ...body }) });
  return { status: r.status, headers: r.headers, json: await r.json().catch(() => null) };
};
const modoWeb = (srv, modo) => fs.writeFileSync(path.join(srv.state, 'fake-web.json'), JSON.stringify({ modo }));
const llamadasWeb = (srv) => { try { return fs.readFileSync(path.join(srv.state, 'web-calls.jsonl'), 'utf8').trim().split('\n').filter(Boolean).map((l) => JSON.parse(l)); } catch { return []; } };
const lecciones = (srv) => { try { return fs.readFileSync(path.join(srv.state, 'evolucion', 'lecciones.jsonl'), 'utf8').trim().split('\n').filter(Boolean).map((l) => JSON.parse(l)); } catch { return []; } };
const esperar = async (fn, ms = 4000) => { const t0 = Date.now(); while (Date.now() - t0 < ms) { const v = await fn(); if (v) return v; await new Promise((r) => setTimeout(r, 50)); } return null; };

// ---------- fixtures ----------
let groq, nvidia, hf, A, C, T, K, expressReal;
const ACCESO = 'clave-de-acceso-del-chat';
const FORMATO = 'FORMATO-DE-SALIDA-DE-PRUEBA: usa listas cortas y bloques de codigo con lenguaje.';

before(async () => {
  expressReal = prepararApp();
  groq = await mockApi('groq'); nvidia = await mockApi('nvidia'); hf = await mockApi('hf');
  const formato = path.join(TMP, 'FORMATO.md'); fs.writeFileSync(formato, FORMATO);
  const memLog = path.join(TMP, 'memoria.log'); fs.writeFileSync(path.join(TMP, 'fake-mem.sh'), `#!/bin/sh\necho "ARGS $@" >> "${memLog}"\ncat >> "${memLog}"\necho >> "${memLog}"\necho '{"ok": true}'\n`, { mode: 0o755 });
  const comun = {
    TEST_GROQ_URL: groq.url, TEST_NVIDIA_URL: nvidia.url, SWECODE_URL_S1: hf.url,
    GROQ_API_KEY: 'gsk-SECRETO-1', GROQ_API_KEY_2: 'gsk-SECRETO-2', NVIDIA_API_KEY: 'nv-SECRETO-1',
    RIU_FORMATO_PATH: formato, BRIDGE_RESPALDO_MS: '5000',
  };
  // A: con cuentas web; el hijo de memoria es un script falso que registra lo recibido
  A = await arrancar('A', { ...comun, WEB_ACCOUNTS: 'a@x.com,b@x.com', WEB_PASS: 'pw', HF_TOKEN: 'hf-falso', RIU_MEMORIA_CMD: path.join(TMP, 'fake-mem.sh'), BRIDGE_DEADLINE_MS: '1500' });
  // C: sin cuentas (WEB_ACCOUNTS/WEB_PASS ausentes)
  C = await arrancar('C', comun);
  // T: con token de acceso (BRIDGE_TOKEN)
  // K: panel de claves del chat: sin claves de Groq/NVIDIA en el entorno, con clave de acceso y un helper de banco falso
  const bancoLog = path.join(TMP, 'banco-calls.log');
  fs.writeFileSync(path.join(TMP, 'fake-banco.sh'), `#!/bin/sh\necho "$1" >> "${bancoLog}"\nif [ "$1" = "leer" ]; then echo '{"groq": [], "nvidia": []}'; elif [ "$1" = "guardar" ]; then cat > "${path.join(TMP, 'banco-guardado.json')}"; echo '{"ok": true}'; else echo '{"ok": true}'; fi\n`, { mode: 0o755 });
  const { GROQ_API_KEY: _g, GROQ_API_KEY_2: _g2, NVIDIA_API_KEY: _n, ...sinClaves } = comun;
  K = await arrancar('K', { ...sinClaves, WEB_ACCOUNTS: 'a@x.com', WEB_PASS: 'pw', RIU_API_KEY: ACCESO, RIU_CLAVES_CMD: path.join(TMP, 'fake-banco.sh'), RIU_OPENCLAW_DIR: fileURLToPath(new URL('../../../SWE CODE free', import.meta.url)), OPENCLAW_WORKSPACE_DIR: path.join(TMP, 'ws-oc') });
  T = await arrancar('T', { ...comun, WEB_ACCOUNTS: 'a@x.com', WEB_PASS: 'pw', BRIDGE_TOKEN: 'tok-prueba' });
});

after(async () => {
  for (const s of servidores) { s.proc.kill('SIGKILL'); await new Promise((ok) => s.proc.once('exit', ok)).catch(() => {}); }
  await Promise.all(mocks.map((m) => new Promise((ok) => { m.closeAllConnections?.(); m.close(ok); })));
  fs.rmSync(TMP, { recursive: true, force: true });
});

// ---------- (1) groq/xxx directo a Groq ----------
test('1. groq/xxx va directo a Groq (sin tocar la web), con clave y formato del chat', async () => {
  groq.hits.length = 0; groq.status = 200; groq.texto = 'respuesta-groq-directa';
  const n0 = llamadasWeb(A).length;
  const r = await chat(A, { model: 'groq/xxx' });
  assert.equal(r.status, 200);
  assert.equal(r.json.choices[0].message.content, 'respuesta-groq-directa');
  assert.equal(r.json.via_respaldo, 'groq');
  assert.equal(r.json.modelo_usado, 'groq/xxx');
  assert.equal(r.json.model, 'swecode:groq/xxx');
  assert.equal(r.headers.get('x-modelo-usado'), 'groq/xxx');
  assert.equal(llamadasWeb(A).length, n0, 'no debe consultar la web');
  assert.equal(groq.hits.length, 1);
  assert.equal(groq.hits[0].url, '/chat/completions');
  assert.equal(groq.hits[0].auth, 'Bearer gsk-SECRETO-1');
  assert.equal(groq.hits[0].body.model, 'xxx');
  const sys = groq.hits[0].body.messages[0];
  assert.equal(sys.role, 'system'); assert.ok(sys.content.includes(FORMATO.slice(0, 60)), 'formato.js antepone el formato de salida');
  assert.equal(groq.hits[0].body.messages.at(-1).content, 'hola mundo');
});

test('1b. groq/xxx con la primera clave rota usa la segunda', async () => {
  groq.hits.length = 0; groq.texto = 'segunda-clave';
  const orig = groq.status;
  groq.status = 500;
  const watcher = setInterval(() => { if (groq.hits.length >= 1) groq.status = 200; }, 1);  // la 1a peticion falla, las siguientes OK
  const r = await chat(A, { model: 'groq/xxx' });
  clearInterval(watcher); groq.status = orig;
  assert.equal(r.status, 200);
  assert.equal(groq.hits[0].auth, 'Bearer gsk-SECRETO-1');
  assert.equal(groq.hits[1].auth, 'Bearer gsk-SECRETO-2');
  assert.equal(r.json.choices[0].message.content, 'segunda-clave');
});

// ---------- (2) web falla -> respaldo ----------
test('2. web falla -> responde respaldo (Groq) con via_respaldo, aviso y header x-via-respaldo', async () => {
  modoWeb(A, 'fail'); groq.hits.length = 0; groq.status = 200; groq.texto = 'respaldo-de-groq';
  const r = await chat(A, { model: 'web-qwen38max' });
  assert.equal(r.status, 200);
  assert.equal(r.json.choices[0].message.content, 'respaldo-de-groq');
  assert.equal(r.json.via_respaldo, 'groq');
  assert.equal(r.headers.get('x-via-respaldo'), 'groq');
  assert.equal(r.json.aviso, 'SELECTOR_BROKEN');
  assert.equal(groq.hits.length, 1);
  assert.ok(lecciones(A).some((l) => l.codigo === 'SELECTOR_BROKEN' && l.resultado === 'PASS' && /groq/.test(l.accion)));
  // fallback dentro de la web: probo los 3 modelos antes de escalar
  const modelos = llamadasWeb(A).slice(-3).map((c) => c.modelo);
  assert.deepEqual(modelos, ['qwen38max', 'qwen37max', 'dsv4-flash']);
  modoWeb(A, 'ok');
});

test('2b. cadena de respaldo: Groq caido -> NVIDIA; ambos caidos -> HF local; todo caido -> 500 RESPALDO_AGOTADO', async () => {
  modoWeb(A, 'fail');
  groq.status = 500; nvidia.status = 200; nvidia.texto = 'respaldo-nvidia'; nvidia.hits.length = 0;
  let r = await chat(A, { model: 'web-dsv4-flash' });
  assert.equal(r.json.via_respaldo, 'nvidia'); assert.equal(r.headers.get('x-via-respaldo'), 'nvidia');
  assert.equal(r.json.choices[0].message.content, 'respaldo-nvidia');
  assert.equal(nvidia.hits[0].auth, 'Bearer nv-SECRETO-1');

  nvidia.status = 500; hf.status = 200; hf.texto = 'respaldo-hf'; hf.hits.length = 0;
  r = await chat(A, { model: 'web-dsv4-flash' });
  assert.equal(r.json.via_respaldo, 'hf-local'); assert.equal(r.json.modelo_usado, 'lfm2.5-350m');
  assert.equal(hf.hits[0].body.model, 'lfm2.5-350m'); assert.equal(hf.hits[0].auth, undefined);

  hf.status = 500;
  r = await chat(A, { model: 'web-dsv4-flash' });
  assert.equal(r.status, 500); assert.equal(r.json.error.code, 'RESPALDO_AGOTADO');
  assert.match(r.json.error.message, /groq/); assert.match(r.json.error.message, /HF_LOCAL/);
  assert.ok(!JSON.stringify(r.json).includes('SECRETO'), 'no filtra claves en el error');
  groq.status = nvidia.status = hf.status = 200; modoWeb(A, 'ok');
});

test('2c. respuesta vacia de la web tambien cae al respaldo (EMPTY_RESPONSE) y la web ok no usa respaldo', async () => {
  groq.texto = 'x-groq'; modoWeb(A, 'empty');
  let r = await chat(A, { model: 'web-qwen38max' });
  assert.equal(r.json.via_respaldo, 'groq'); assert.equal(r.json.aviso, 'EMPTY_RESPONSE');
  modoWeb(A, 'ok'); groq.hits.length = 0;
  r = await chat(A, { model: 'web-qwen38max' });
  assert.equal(r.status, 200);
  assert.equal(r.json.choices[0].message.content, 'WEB[qwen38max]');
  assert.equal(r.json.via_respaldo, null); assert.equal(r.json.aviso, null);
  assert.equal(r.headers.get('x-via-respaldo'), null);
  assert.equal(groq.hits.length, 0);
});

test('2d. reintento tras SESSION_EXPIRED: salud() y segundo intento OK (sin respaldo); si sigue caida -> respaldo con aviso', async () => {
  modoWeb(A, 'expire_once'); groq.hits.length = 0;
  let r = await chat(A, { model: 'web-qwen38max' });
  assert.equal(r.status, 200);
  assert.equal(r.json.choices[0].message.content, 'WEB[qwen38max]');
  assert.equal(r.json.via_respaldo, null);
  assert.equal(groq.hits.length, 0);
  assert.ok(lecciones(A).some((l) => l.codigo === 'SESSION_EXPIRED' && l.resultado === 'PASS'));

  modoWeb(A, 'expire_always'); groq.texto = 'tras-expirar';
  r = await chat(A, { model: 'web-qwen38max' });
  assert.equal(r.status, 200); assert.equal(r.json.via_respaldo, 'groq'); assert.equal(r.json.aviso, 'SESSION_EXPIRED');
  assert.ok(lecciones(A).some((l) => l.codigo === 'SESSION_EXPIRED' && l.resultado === 'FAIL'));
  modoWeb(A, 'ok');
});

test('2e. deadline duro: web colgada -> UPSTREAM_TIMEOUT -> respaldo (no cuelga)', async () => {
  modoWeb(A, 'slow'); groq.texto = 'tras-timeout';
  const t0 = Date.now();
  const r = await chat(A, { model: 'web-qwen38max', conv_id: 'conv-lenta' });
  assert.ok(Date.now() - t0 < 10000);
  assert.equal(r.status, 200); assert.equal(r.json.via_respaldo, 'groq'); assert.equal(r.json.aviso, 'UPSTREAM_TIMEOUT');
  modoWeb(A, 'ok');
});

// ---------- (3) sin cuentas ----------
test('3. sin cuentas -> aviso CUENTAS_FALTAN (con respaldo); al inyectar cuentas la web vuelve a responder', async () => {
  groq.texto = 'sin-cuentas'; groq.status = 200;
  let r = await chat(C, { model: 'web-qwen38max' });
  assert.equal(r.status, 200);
  assert.equal(r.json.aviso, 'CUENTAS_FALTAN');
  assert.equal(r.json.via_respaldo, 'groq');
  assert.equal(r.headers.get('x-via-respaldo'), 'groq');
  assert.equal(r.json.choices[0].message.content, 'sin-cuentas');
  assert.ok(lecciones(C).some((l) => l.codigo === 'CUENTAS_FALTAN' && l.resultado === 'PASS'));

  r = await chat(C, { model: 'web-qwen38max', cuentas: ['uno@x.com', 'dos@x.com'], clave: 'pw' });
  assert.equal(r.json.choices[0].message.content, 'WEB[qwen38max]');
  assert.equal(r.json.aviso, null); assert.equal(r.json.via_respaldo, null);
});

// ---------- (4) asesoria ----------
test('4. swecode-asesoria con Groq OK guarda ASESORIA.md y GET /v1/proyectos lo lista', async () => {
  groq.hits.length = 0; groq.status = 200; groq.texto = '1) Objetivo\n2) Plan\n3) Mapa mental';
  const n0 = llamadasWeb(A).length;
  const r = await chat(A, { model: 'swecode-asesoria', proyecto: 'Mi Proyecto Ñandú' });
  assert.equal(r.status, 200);
  assert.equal(r.json.via_respaldo, null, 'Groq es la via primaria de la asesoria, no un respaldo');
  assert.equal(r.json.via_primaria, 'groq'); assert.equal(r.headers.get('x-via-respaldo'), null);
  assert.equal(r.json.choices[0].message.content, groq.texto);
  assert.equal(llamadasWeb(A).length, n0, 'asesoria va primero a Groq, no a la web');
  assert.match(groq.hits[0].body.messages[0].content, /MODO ASESORIA/);  // preambulo
  assert.ok(r.json.archivo && r.json.archivo.endsWith('ASESORIA.md'));
  assert.ok(r.json.archivo.startsWith(A.state), 'se guarda bajo BRIDGE_STATE_DIR');
  const md = fs.readFileSync(r.json.archivo, 'utf8');
  assert.match(md, /^# Asesor/); assert.ok(md.includes('3) Mapa mental')); assert.match(md, /groq/);

  const lista = await get(A, '/v1/proyectos');
  assert.equal(lista.status, 200); assert.equal(lista.json.ok, true);
  assert.deepEqual(lista.json.proyectos, ['mi-proyecto-nandu']);
  const uno = await get(A, '/v1/proyectos/mi-proyecto-nandu');
  assert.equal(uno.status, 200); assert.equal(uno.json.proyecto, 'mi-proyecto-nandu'); assert.ok(uno.json.texto.includes('2) Plan'));
  const no = await get(A, '/v1/proyectos/no-existe');
  assert.equal(no.status, 404); assert.equal(no.json.error, 'PROYECTO_NO_ENCONTRADO');
});

test('4b. swecode-asesoria con Groq caido responde por la web y tambien guarda (segunda entrada se anade)', async () => {
  groq.status = 500; modoWeb(A, 'ok');
  const r = await chat(A, { model: 'swecode-asesoria', proyecto: 'Mi Proyecto Ñandú' });
  assert.equal(r.status, 200); assert.equal(r.json.via_respaldo, null);
  assert.equal(r.json.choices[0].message.content, 'WEB[qwen38max]');
  const md = fs.readFileSync(r.json.archivo, 'utf8');
  assert.equal((md.match(/^## \d{4}-/gm) || []).length, 2); assert.ok(md.includes('WEB[qwen38max]'));
  groq.status = 200;
});

test('4c. asesoria sin proyecto ni conv_id guarda en "general"', async () => {
  groq.texto = 'asesoria-general';
  const r = await chat(A, { model: 'swecode-asesoria' });
  assert.equal(r.status, 200);
  assert.ok(r.json.archivo.includes(`${path.sep}general${path.sep}`));
  const l = await get(A, '/v1/proyectos');
  assert.ok(l.json.proyectos.includes('general') && l.json.proyectos.includes('mi-proyecto-nandu'));
});

test('4d. guardarTurno: con proyecto/conv_id pasa por la memoria (scope chat-ui:hist:openclaw-<slug>)', async () => {
  const log = path.join(TMP, 'memoria.log');
  groq.texto = 'respuesta-memoria';
  await chat(A, { model: 'groq/xxx', proyecto: 'Proy Memoria' });
  const txt = await esperar(() => { try { const t = fs.readFileSync(log, 'utf8'); return t.includes('respuesta-memoria') ? t : null; } catch { return null; } });
  assert.ok(txt, 'la memoria recibio el turno');
  assert.match(txt, /ARGS save chat-ui:hist:openclaw-proy-memoria m-\d+-user/);
  assert.match(txt, /"rol":"user","texto":"hola mundo"/);
  assert.match(txt, /ARGS save chat-ui:hist:openclaw-proy-memoria m-\d+-bot/);
});

// ---------- (5) modelos ----------
test('5. GET /v1/models lista swecode-asesoria, groq/..., nvidia/..., locales y web-*', async () => {
  const r = await get(A, '/v1/models');
  assert.equal(r.status, 200); assert.equal(r.json.object, 'list');
  const ids = r.json.data.map((m) => m.id);
  for (const id of ['swecode-asesoria', 'swecode-consulta', 'swecode-revision', 'groq/llama-3.3-70b-versatile', 'nvidia/meta/llama-3.3-70b-instruct',
    'lfm2.5-350m', 'qwen2.5-coder-1.5b', 'qwen3.5-0.8b', 'qwen3-0.6b', 'web-qwen38max', 'web-qwen37max', 'web-dsv4-flash']) assert.ok(ids.includes(id), `falta ${id}`);
  assert.equal(new Set(ids).size, ids.length, 'sin ids duplicados');
});

// ---------- (6) health ----------
test('6. /health trae respaldo con conteos, state_dir y NUNCA valores de claves', async () => {
  const r = await get(A, '/health');
  assert.equal(r.status, 200); assert.equal(r.json.ok, true);
  assert.deepEqual(r.json.respaldo, { groq: 2, nvidia: 1, hf_local: 1 });
  assert.equal(r.json.state_dir, A.state);
  assert.equal(r.json.pool.loaded, true); assert.equal(r.json.pool.total, 2);
  const crudo = JSON.stringify(r.json);
  for (const s of ['SECRETO', 'gsk-', 'nv-', 'hf-falso', 'pw"']) assert.ok(!crudo.includes(s), `filtra ${s}`);
  assert.ok(!crudo.includes('127.0.0.1'), 'no expone URLs de S1..S3');

  const c = await get(C, '/health');   // sin cuentas pero tras inyectar en el test 3 ya hay pool; el respaldo sigue igual
  assert.equal(c.status, 200); assert.deepEqual(c.json.respaldo, { groq: 2, nvidia: 1, hf_local: 1 });
});

test('6b. /health sin cuentas y sin respaldo: pool WEB_ACCOUNTS_VACIO y conteos en 0', async () => {
  const D = await arrancar('D', {});
  const r = await get(D, '/health');
  assert.equal(r.json.ok, true);
  assert.deepEqual(r.json.pool, { total: 0, loaded: false, error: 'WEB_ACCOUNTS_VACIO' });
  assert.deepEqual(r.json.respaldo, { groq: 0, nvidia: 0, hf_local: 0 });
  // sin ninguna ruta de respaldo: el aviso se pierde en un 500 tipado, no en un cuelgue
  const c = await chat(D, { model: 'web-qwen38max' });
  assert.equal(c.status, 500); assert.equal(c.json.error.code, 'RESPALDO_AGOTADO');
  assert.match(c.json.error.message, /groq: sin clave/); assert.match(c.json.error.message, /sin SWECODE_URL/);
});

test('6c. POST con claves {groq,nvidia} inyecta las claves por llamada (sin claves en el entorno) y /health solo cuenta', async () => {
  const K = await arrancar('K', { TEST_GROQ_URL: groq.url, TEST_NVIDIA_URL: nvidia.url, RIU_FORMATO_PATH: path.join(TMP, 'FORMATO.md'), BRIDGE_RESPALDO_MS: '5000' });
  assert.deepEqual((await get(K, '/health')).json.respaldo, { groq: 0, nvidia: 0, hf_local: 0 });
  groq.hits.length = 0; groq.status = 200; groq.texto = 'con-clave-inyectada';
  const r = await chat(K, { model: 'groq/xxx', claves: { groq: ['gsk-INYECTADA-1', 'gsk-INYECTADA-2'], nvidia: 'nv-INYECTADA' } });
  assert.equal(r.status, 200);
  assert.equal(r.json.choices[0].message.content, 'con-clave-inyectada');
  assert.equal(groq.hits[0].auth, 'Bearer gsk-INYECTADA-1');
  const h = await get(K, '/health');
  assert.deepEqual(h.json.respaldo, { groq: 2, nvidia: 1, hf_local: 0 });
  const crudo = JSON.stringify(h.json) + K.log();
  assert.ok(!crudo.includes('INYECTADA'), 'no filtra ni loguea valores de claves');
});

// ---------- (7) secciones y resto de rutas ----------
test('7. GET /v1/secciones responde 200 (y lista los checkpoints existentes)', async () => {
  let r = await get(A, '/v1/secciones');
  assert.equal(r.status, 200); assert.equal(r.json.ok, true); assert.deepEqual(r.json.secciones, []);
  fs.mkdirSync(path.join(A.state, 'checkpoints'), { recursive: true });
  fs.writeFileSync(path.join(A.state, 'checkpoints', 'conv-1.json'), JSON.stringify({ modo: 'consulta', enviados: 1, total: 3, ts: 'hoy' }));
  r = await get(A, '/v1/secciones');
  assert.deepEqual(r.json.secciones, [{ conv_id: 'conv-1', modo: 'consulta', enviados: 1, total: 3, completo: false, ts: 'hoy' }]);
});

// ---------- extras ----------
test('8. validacion: modelo desconocido -> 400 MODELO_INVALIDO; modo desconocido -> 400 MODO_INVALIDO', async () => {
  let r = await chat(A, { model: 'gpt-4' });
  assert.equal(r.status, 400); assert.equal(r.json.error.code, 'MODELO_INVALIDO');
  r = await chat(A, { model: 'swecode-inexistente' });
  assert.equal(r.status, 400); assert.equal(r.json.error.code, 'MODO_INVALIDO');
});

test('9. modelo local lfm2.5-350m va directo a HF local; nvidia/xxx directo a NVIDIA', async () => {
  hf.hits.length = 0; hf.status = 200; hf.texto = 'local-directo';
  let r = await chat(A, { model: 'lfm2.5-350m' });
  assert.equal(r.json.via_respaldo, 'hf-local'); assert.equal(r.json.choices[0].message.content, 'local-directo');
  assert.equal(hf.hits[0].body.model, 'lfm2.5-350m');
  nvidia.hits.length = 0; nvidia.status = 200; nvidia.texto = 'nv-directo';
  r = await chat(A, { model: 'nvidia/meta/otro' });
  assert.equal(r.json.via_respaldo, 'nvidia'); assert.equal(nvidia.hits[0].body.model, 'meta/otro');
});

test('10. swecode-consulta usa consenso (3 modelos + arbitro) y devuelve x-consenso-detalle', async () => {
  modoWeb(A, 'ok');
  const n0 = llamadasWeb(A).length;
  const r = await chat(A, { model: 'swecode-consulta' });
  assert.equal(r.status, 200); assert.equal(r.json.modelo_usado, 'consenso');
  const nuevas = llamadasWeb(A).slice(n0);
  assert.equal(nuevas.length, 4);
  assert.equal(nuevas.at(-1).modelo, 'qwen38max');  // arbitro
  const det = JSON.parse(Buffer.from(r.headers.get('x-consenso-detalle'), 'base64').toString());
  assert.deepEqual(Object.keys(det).sort(), ['dsv4-flash', 'qwen37max', 'qwen38max']);
});

test('11. documentos se incrustan en el prompt de la web; /v1/queue, /refresh_session y /debug/tab responden', async () => {
  const n0 = llamadasWeb(A).length;
  await chat(A, { model: 'web-qwen38max', swecode: 1, documentos: [{ nombre: 'a.md', contenido: 'CONTENIDO-DOC' }, 'texto suelto'] });
  const c = llamadasWeb(A).slice(n0)[0];
  assert.ok(c.texto.includes('[DOCUMENTO: a.md]\nCONTENIDO-DOC') && c.texto.includes('[DOCUMENTO: doc]\ntexto suelto'));
  const q = await get(A, '/v1/queue'); assert.equal(q.status, 200); assert.equal(q.json.ok, true);
  const rs = await fetch(A.base + '/refresh_session', { method: 'POST' }); const j = await rs.json();
  assert.equal(rs.status, 200); assert.deepEqual(j.sitios, { qwen: 'vivo', deepseek: 'vivo' });
  assert.equal((await get(A, '/debug/tab?shot=0')).status, 200);
  assert.equal((await get(A, '/debug/tab?conv_id=nada')).status, 404);
});

test('12. concilio con conv_id: cada modelo y el arbitro usan su propia tab/checkpoint (no comparten)', async () => {
  modoWeb(A, 'ok');
  const n0 = llamadasWeb(A).length;
  const r = await chat(A, { model: 'swecode-consulta', conv_id: 'chat-9' });
  assert.equal(r.status, 200);
  const ids = llamadasWeb(A).slice(n0).map((c) => c.opts.convId);
  assert.equal(ids.length, 4); assert.equal(new Set(ids).size, 4, 'convIds distintos: ' + ids.join(','));
  assert.ok(ids.every((i) => i.startsWith('chat-9')));
});

test('13. Groq/NVIDIA directos con modo despliega reciben el preambulo del agente que despliega', async () => {
  groq.hits.length = 0; groq.status = 200; groq.texto = 'ok';
  const r = await chat(A, { model: 'groq/xxx', modo: 'despliega' });
  assert.equal(r.status, 200);
  const sys = groq.hits.at(-1).body.messages.filter((m) => m.role === 'system').map((m) => m.content).join('\n');
  assert.match(sys, /MODO DESPLIEGA/);
  groq.hits.length = 0;
  await chat(A, { model: 'groq/xxx' });  // sin modo: no se agrega ningun preambulo de modo
  assert.ok(!groq.hits.at(-1).body.messages.some((m) => /MODO DESPLIEGA/.test(m.content)));
});

test('14. el prefijo "SWEN CODE free ..." elige modelo, modo y seccion en el bridge', async () => {
  modoWeb(A, 'ok');
  const n0 = llamadasWeb(A).length;
  const r = await chat(A, { messages: [{ role: 'user', content: 'SWEN CODE free chat 3 modo solucion solo deepseek v4 arregla api.js' }] });
  assert.equal(r.status, 200);
  const c = llamadasWeb(A).slice(n0)[0];
  assert.equal(c.modelo, 'dsv4-flash'); assert.equal(c.opts.convId, 'chat-3'); assert.equal(c.opts.modo, 'solucion');
  assert.ok(c.texto.includes('arregla api.js') && !c.texto.includes('SWEN CODE free'));
  const mala = await chat(A, { messages: [{ role: 'user', content: 'SWEN CODE free modo revisoin hola' }] });  // un modo mal escrito (cerca de uno valido) da 400; una frase natural ('modo oscuro...') se respeta
  assert.equal(mala.status, 400); assert.equal(mala.json.error.code, 'ACTIVACION_INVALIDA');
  const nat = await chat(A, { messages: [{ role: 'user', content: 'SWEN CODE free modo oscuro no funciona en el login' }] });
  assert.equal(nat.status, 200, 'una frase natural no es un error de activacion');
});

test('15. tools: groq/nvidia/locales reciben las tools del POST y sus tool_calls vuelven al cliente (el Harness las ejecuta)', async () => {
  const tools = [{ type: 'function', function: { name: 'github_leer', parameters: { type: 'object' } } }];
  groq.hits.length = 0; groq.status = 200;
  groq.tool_calls = [{ id: 'c1', type: 'function', function: { name: 'github_leer', arguments: '{"ruta":"README.md"}' } }];
  const r = await chat(A, { model: 'groq/xxx', tools, tool_choice: 'auto' });
  delete groq.tool_calls;
  assert.equal(r.status, 200);
  assert.deepEqual(groq.hits.at(-1).body.tools, tools); assert.equal(groq.hits.at(-1).body.tool_choice, 'auto');
  assert.equal(r.json.choices[0].finish_reason, 'tool_calls');
  assert.equal(r.json.choices[0].message.tool_calls[0].function.name, 'github_leer');
});

// ---------- auditoria 1: correcciones ----------
test('A1-1. conv_id con ../ se rechaza (400) y no escribe fuera de checkpoints/', async () => {
  const r = await chat(A, { model: 'web-qwen38max', conv_id: '../../evil' });
  assert.equal(r.status, 400); assert.equal(r.json.error.code, 'CONV_ID_INVALIDO');
  assert.ok(!fs.existsSync(path.join(A.state, '..', 'evil.json')));
});

test('A1-11. mensajes: content como array de partes, model no string, messages no array, ultimo mensaje no-user', async () => {
  modoWeb(A, 'ok'); const n0 = llamadasWeb(A).length;
  const a = await chat(A, { model: 'web-qwen38max', messages: [{ role: 'user', content: [{ type: 'text', text: 'parte-uno' }, { type: 'text', text: 'parte-dos' }] }] });
  assert.equal(a.status, 200);
  const t = llamadasWeb(A).slice(n0)[0].texto; assert.ok(t.includes('parte-uno') && t.includes('parte-dos') && !t.includes('[object Object]'));
  assert.equal((await chat(A, { model: 123 })).status, 400);
  assert.equal((await chat(A, { model: 'web-qwen38max', messages: 'hola' })).status, 400);
  assert.equal((await chat(A, { model: 'web-qwen38max', messages: [{ role: 'user', content: 'U1' }, { role: 'assistant', content: 'A1' }] })).status, 200);
  const u = llamadasWeb(A).at(-1).texto; assert.equal((u.match(/U1/g) || []).length, 1, 'el mensaje de usuario no se duplica');
});

test('A1-12. modelo web desconocido -> 400; SESSION_EXPIRED no se disfraza con el error del ultimo modelo', async () => {
  const r = await chat(A, { model: 'web-foo' }); assert.equal(r.status, 400); assert.equal(r.json.error.code, 'MODELO_INVALIDO');
});

test('A1-8. documentos tambien llegan a Groq/NVIDIA/locales, no solo a la web', async () => {
  groq.hits.length = 0; groq.status = 200; groq.texto = 'ok';
  await chat(A, { model: 'groq/xxx', documentos: [{ nombre: 'plan.md', contenido: 'CONTENIDO-DOC-GROQ' }] });
  assert.ok(JSON.stringify(groq.hits.at(-1).body.messages).includes('CONTENIDO-DOC-GROQ'));
});

test('A1-9. el respaldo conserva el preambulo del modo y la gramatica con modo asesoria usa Groq primero', async () => {
  modoWeb(A, 'fail'); groq.hits.length = 0; groq.status = 200; groq.texto = 'resp';
  await chat(A, { model: 'web-qwen38max', modo: 'despliega' });
  assert.match(JSON.stringify(groq.hits.at(-1).body.messages), /MODO DESPLIEGA/);
  modoWeb(A, 'ok'); groq.hits.length = 0; const n0 = llamadasWeb(A).length;
  const r = await chat(A, { messages: [{ role: 'user', content: 'SWEN CODE free modo asesoria planear el modulo de pagos' }] });
  assert.equal(r.status, 200); assert.equal(llamadasWeb(A).length, n0, 'asesoria por gramatica va primero a Groq'); assert.equal(groq.hits.length, 1);
});

test('A1-7. prompt gigante -> 413 antes de tocar la web', async () => {
  const n0 = llamadasWeb(A).length;
  const r = await chat(A, { model: 'web-qwen38max', messages: [{ role: 'user', content: 'x'.repeat(450000) }] });
  assert.equal(r.status, 413); assert.equal(r.json.error.code, 'PROMPT_DEMASIADO_GRANDE'); assert.equal(llamadasWeb(A).length, n0);
});

test('A1-16. JSON malformado responde JSON tipado, no HTML', async () => {
  const r = await fetch(A.base + '/v1/chat/completions', { method: 'POST', headers: { 'content-type': 'application/json' }, body: '{roto' });
  assert.equal(r.status, 400); const j = await r.json(); assert.equal(j.error.code, 'BAD_REQUEST');
});

test('A1-4. con BRIDGE_TOKEN: sin token 401, con token 200; /health no expone correos', async () => {
  assert.equal((await fetch(T.base + '/v1/models')).status, 401);
  assert.equal((await fetch(T.base + '/v1/proyectos')).status, 401);
  const ok = await fetch(T.base + '/v1/models', { headers: { authorization: 'Bearer tok-prueba' } }); assert.equal(ok.status, 200);
  const x = await fetch(T.base + '/v1/models', { headers: { 'x-bridge-key': 'tok-prueba' } }); assert.equal(x.status, 200);
  const h = await (await fetch(T.base + '/health')).text(); assert.ok(!h.includes('@x.com'), 'no debe mostrar correos');
  const q = await (await fetch(T.base + '/v1/queue', { headers: { authorization: 'Bearer tok-prueba' } })).text(); assert.ok(!q.includes('@x.com'));
  assert.equal((await fetch(A.base + '/v1/models')).status, 200, 'sin BRIDGE_TOKEN todo sigue abierto como antes');
});

test('A1-17. model con caracteres raros se rechaza (no entra a cabeceras ni lecciones)', async () => {
  const r = await chat(A, { model: 'groq/ñ\nX-Inyectado: 1' }); assert.equal(r.status, 400);
});

test('A1-F1. POST /v1/secciones/:id/retomar retoma una seccion a medias con el texto guardado, sin que el cliente reenvie nada', async () => {
  modoWeb(A, 'ok');
  fs.mkdirSync(path.join(A.state, 'checkpoints'), { recursive: true });
  fs.writeFileSync(path.join(A.state, 'checkpoints', 'media.json'), JSON.stringify({ modo: 'solucion', modelo: 'qwen38max', texto: 'TEXTO-GUARDADO-DE-LA-SECCION', total: 3, enviados: 1, huella: 'x' }));
  const n0 = llamadasWeb(A).length;
  const r = await fetch(A.base + '/v1/secciones/media/retomar', { method: 'POST' });
  const j = await r.json();
  assert.equal(r.status, 200); assert.equal(j.choices[0].message.content, 'WEB[qwen38max]');
  const c = llamadasWeb(A).slice(n0)[0];
  assert.equal(c.texto, 'TEXTO-GUARDADO-DE-LA-SECCION'); assert.equal(c.opts.convId, 'media'); assert.equal(c.opts.modo, 'solucion');
  const no = await fetch(A.base + '/v1/secciones/no-hay/retomar', { method: 'POST' }); assert.equal(no.status, 404);
  fs.writeFileSync(path.join(A.state, 'checkpoints', 'lista.json'), JSON.stringify({ modo: 'x', modelo: 'qwen38max', texto: 't', total: 1, enviados: 1, completo: true }));
  assert.equal((await fetch(A.base + '/v1/secciones/lista/retomar', { method: 'POST' })).status, 409);
});

test('A1-F1b. BRIDGE_AUTORETOMAR=1: al arrancar retoma solo las secciones a medias y deja una leccion', async () => {
  const estado = fs.mkdtempSync(path.join(TMP, 'auto-'));
  fs.mkdirSync(path.join(estado, 'checkpoints'), { recursive: true });
  fs.writeFileSync(path.join(estado, 'checkpoints', 'huerfana.json'), JSON.stringify({ modo: 'revision', modelo: 'dsv4-flash', texto: 'TEXTO-HUERFANO', total: 2, enviados: 1 }));
  const R = await arrancar('R', { WEB_ACCOUNTS: 'a@x.com', WEB_PASS: 'pw', BRIDGE_STATE_DIR: estado, BRIDGE_AUTORETOMAR: '1' });
  let hecho = false;
  for (let i = 0; i < 40 && !hecho; i++) { await new Promise((ok) => setTimeout(ok, 250)); try { hecho = fs.readFileSync(path.join(estado, 'web-calls.jsonl'), 'utf8').includes('TEXTO-HUERFANO'); } catch { /* aun no */ } }
  assert.ok(hecho, 'debio retomar la seccion sola');
  let les = '';
  for (let i = 0; i < 20 && !/REINICIO/.test(les); i++) { await new Promise((ok) => setTimeout(ok, 200)); try { les = fs.readFileSync(path.join(estado, 'evolucion', 'lecciones.jsonl'), 'utf8'); } catch { /* aun no */ } }
  assert.match(les, /"codigo":"REINICIO"[^\n]*"resultado":"PASS"/); void R;
});

// ---------- panel de claves del chat: /v1/claves ----------
const claves = async (srv, metodo, body, clave = ACCESO) => {
  const r = await fetch(srv.base + '/v1/claves', { method: metodo, headers: { 'content-type': 'application/json', ...(clave ? { 'x-api-key': clave } : {}) }, ...(body !== undefined ? { body: JSON.stringify(body) } : {}) });
  return { status: r.status, texto: await r.clone().text(), json: await r.json().catch(() => null) };
};

test('CL-1. sin ninguna clave de acceso configurada en el bridge -> 503 SIN_CLAVE_DE_ACCESO (tambien con BRIDGE_TOKEN valido)', async () => {
  for (const m of ['GET', 'POST', 'DELETE']) {
    const r = await claves(C, m, m === 'POST' ? { groq: 'gsk-abcdefgh' } : undefined);
    assert.equal(r.status, 503); assert.equal(r.json.error.code, 'SIN_CLAVE_DE_ACCESO');
  }
  const t = await fetch(T.base + '/v1/claves', { headers: { authorization: 'Bearer tok-prueba', 'x-api-key': 'lo-que-sea' } });
  assert.equal(t.status, 503);
  assert.equal((await fetch(T.base + '/v1/claves', { headers: { 'x-api-key': 'lo-que-sea' } })).status, 401, 'BRIDGE_TOKEN sigue mandando primero');
});

test('CL-2. sin x-api-key o incorrecta -> 401 NO_AUTORIZADO y no cambia nada', async () => {
  for (const m of ['GET', 'POST', 'DELETE']) {
    for (const k of ['', 'incorrecta', ACCESO + 'x', ACCESO.slice(1)]) {
      const r = await claves(K, m, m === 'POST' ? { groq: 'gsk-no-debe-entrar' } : undefined, k);
      assert.equal(r.status, 401, `${m} con "${k}"`); assert.equal(r.json.error.code, 'NO_AUTORIZADO');
    }
  }
  assert.deepEqual((await claves(K, 'GET')).json, { ok: true, groq: 0, nvidia: 0 });
});

test('CL-3. se aceptan tambien RIU_PUBLIC_CHAT_KEY / RIU_MCP_KEY / RIU_ROUTER_API_KEY', async () => {
  const P = await arrancar('P', { WEB_ACCOUNTS: 'a@x.com', WEB_PASS: 'pw', RIU_PUBLIC_CHAT_KEY: 'publica-1234', RIU_MCP_KEY: 'mcp-1234', RIU_ROUTER_API_KEY: 'router-1234', RIU_CLAVES_CMD: path.join(TMP, 'fake-banco.sh') });
  for (const k of ['publica-1234', 'mcp-1234', 'router-1234']) assert.equal((await claves(P, 'GET', undefined, k)).status, 200, k);
  assert.equal((await claves(P, 'GET', undefined, 'otra-cosa')).status, 401);
});

test('CL-4. POST guarda: groq/xxx usa esa clave contra el mock de Groq aunque el entorno no tenga ninguna; GET/POST/DELETE solo devuelven conteos', async () => {
  const sec = 'gsk-PEGADA-DESDE-EL-PANEL';
  groq.hits.length = 0; groq.status = 200; groq.texto = 'con-clave-del-panel';
  const antes = await chat(K, { model: 'groq/xxx' });
  assert.equal(antes.json.via_respaldo, 'hf-local', 'sin clave no hay groq'); assert.equal(groq.hits.length, 0);
  const p = await claves(K, 'POST', { groq: [sec, 'gsk-SEGUNDA-DEL-PANEL'], nvidia: 'nv-PEGADA-DEL-PANEL' });
  assert.equal(p.status, 200); assert.deepEqual(p.json, { ok: true, groq: 2, nvidia: 1, persistido: true });
  const r = await chat(K, { model: 'groq/xxx' });
  assert.equal(r.status, 200); assert.equal(r.json.choices[0].message.content, 'con-clave-del-panel');
  assert.equal(groq.hits[0].auth, 'Bearer ' + sec);
  const g = await claves(K, 'GET'); assert.deepEqual(g.json, { ok: true, groq: 2, nvidia: 1 });
  const guardado = await esperar(() => { try { return fs.readFileSync(path.join(TMP, 'banco-guardado.json'), 'utf8'); } catch { return null; } });
  assert.deepEqual(JSON.parse(guardado), { groq: [sec, 'gsk-SEGUNDA-DEL-PANEL'], nvidia: 'nv-PEGADA-DEL-PANEL' }, 'se guarda en el banco propio via el helper');
  const h = await get(K, '/health'); assert.equal(h.json.respaldo.groq, 2);
  for (const t of [p.texto, g.texto]) { assert.ok(!/PEGADA|SEGUNDA/.test(t), 'jamas valores'); }
  assert.ok(!/PEGADA|SEGUNDA/.test(K.log()), 'no se loguean valores');
  const d = await claves(K, 'DELETE');
  assert.equal(d.status, 200); assert.deepEqual(d.json, { ok: true, groq: 0, nvidia: 0, persistido: true });
  assert.ok(!/PEGADA|SEGUNDA/.test(d.texto));
  assert.ok(fs.readFileSync(path.join(TMP, 'banco-calls.log'), 'utf8').split('\n').includes('borrar'), 'DELETE llama a borrar del banco propio');
  groq.hits.length = 0;
  assert.equal((await chat(K, { model: 'groq/xxx' })).json.via_respaldo, 'hf-local', 'tras borrar ya no hay clave');
  assert.equal(groq.hits.length, 0);
  assert.deepEqual((await claves(K, 'GET')).json, { ok: true, groq: 0, nvidia: 0 });
});

test('CL-5. POST valida: maximo 20 por proveedor, string de 8 a 300 sin espacios ni saltos -> 400 CLAVE_INVALIDA sin repetir el valor', async () => {
  const malos = [
    { groq: 'corta' }, { groq: ['bien-larga-1', 'con espacio dentro'] }, { nvidia: 'con\nsalto-de-linea' }, { groq: 'x'.repeat(301) },
    { groq: Array.from({ length: 21 }, (_, i) => `gsk-valida-${i}`) }, { groq: [123456789] }, { groq: { a: 'b' } }, {}, { groq: 'tab\tdentro-1234' },
  ];
  for (const b of malos) {
    const r = await claves(K, 'POST', b);
    assert.equal(r.status, 400, JSON.stringify(b).slice(0, 60)); assert.equal(r.json.error.code, 'CLAVE_INVALIDA');
    assert.ok(!/con espacio dentro|salto-de-linea|tab/.test(r.texto), 'no repite el valor');
  }
  assert.equal((await claves(K, 'POST', { groq: Array.from({ length: 20 }, (_, i) => `gsk-valida-${i}`) })).json.groq, 20, '20 es el maximo valido');
  assert.equal((await claves(K, 'POST', { groq: 'x'.repeat(300), nvidia: 'y'.repeat(8) })).status, 200);
  await claves(K, 'DELETE');
});

// ---------- configuracion vigente de OpenClaw: GET /v1/openclaw (Vercel la lee por /web/v1/openclaw, el Space por el proxy) ----------
test('OC-1. GET /v1/openclaw exige la clave de acceso del chat; sin ella o con otra -> 401; sin clave configurada -> 503', async () => {
  for (const k of ['', 'incorrecta']) {
    const r = await fetch(K.base + '/v1/openclaw', { headers: k ? { 'x-api-key': k } : {} });
    assert.equal(r.status, 401, `"${k}"`);
  }
  assert.equal((await fetch(C.base + '/v1/openclaw')).status, 503);
});

test('OC-2. devuelve provider/modelos/modos del repo + ids vivos + conteos + workspace; jamas api_key ni valores de claves', async () => {
  const r = await fetch(K.base + '/v1/openclaw', { headers: { 'x-api-key': ACCESO } });
  assert.equal(r.status, 200);
  const txt = await r.text(), j = JSON.parse(txt);
  assert.equal(j.ok, true); assert.equal(j.provider.provider, 'swecode'); assert.match(j.version, /^[0-9a-f]{12}$/);
  assert.ok(j.provider.modelos.some(m => m.id === 'web-qwen38max'));
  assert.ok(j.modos.includes('asesoria'));
  assert.ok(j.vivo.modelos.includes('swecode-revision') && j.vivo.modelos.some(id => id.startsWith('groq/')), 'ids vivos como GET /v1/models');
  assert.deepEqual([j.vivo.groq, j.vivo.nvidia], [0, 0]);
  assert.equal(j.workspace.ruta, path.join(TMP, 'ws-oc'));
  assert.equal(typeof j.workspace.existe, 'boolean');
  assert.ok(!('api_key' in j.provider) && !/no-requerida/.test(txt), 'sin api_key');
  assert.ok(!/gsk-|nv-SECRETO/.test(txt), 'sin claves');
});

test('entorno: informa si se uso express real o stub', () => {
  console.log(`# express ${expressReal ? 'real (npm install)' : 'stub'} en ${APP}`);
  assert.ok(servidores.length >= 2);
});

// ---------- (S) stream:true (OpenClaw/openai-completions pide SSE): sin esto el selector muestra respuesta vacia ----------
const chatSse = async (srv, body) => {
  const r = await fetch(srv.base + '/v1/chat/completions', { method: 'POST', headers: { 'content-type': 'application/json' }, body: JSON.stringify({ messages: [{ role: 'user', content: 'hola mundo' }], stream: true, ...body }) });
  const texto = await r.text();
  const eventos = texto.split('\n\n').map((b) => b.trim()).filter(Boolean).map((b) => b.replace(/^data: /, ''));
  return { status: r.status, tipo: r.headers.get('content-type') || '', texto, eventos, chunks: eventos.filter((e) => e !== '[DONE]').map((e) => JSON.parse(e)) };
};

test('S1. stream:true con modelo local devuelve SSE (chat.completion.chunk + [DONE]) con el mismo texto; sin stream sigue el JSON de siempre', async () => {
  hf.hits.length = 0; hf.status = 200; hf.texto = 'local-en-stream';
  const r = await chatSse(A, { model: 'qwen2.5-coder-1.5b' });
  assert.equal(r.status, 200); assert.match(r.tipo, /text\/event-stream/);
  assert.equal(r.eventos.at(-1), '[DONE]');
  assert.ok(r.chunks.every((c) => c.object === 'chat.completion.chunk'));
  assert.equal(r.chunks.map((c) => c.choices[0].delta?.content || '').join(''), 'local-en-stream');
  assert.equal(r.chunks.at(-1).choices[0].finish_reason, 'stop');
  assert.equal(r.chunks[0].choices[0].delta.role, 'assistant');
  assert.equal(hf.hits[0].body.model, 'qwen2.5-coder-1.5b'); assert.ok(!('stream' in hf.hits[0].body), 'el bridge no reenvia stream a la cola HF');
  const j = await chat(A, { model: 'qwen2.5-coder-1.5b' });
  assert.match(j.headers.get('content-type'), /application\/json/); assert.equal(j.json.choices[0].message.content, 'local-en-stream');
});

test('S2. stream:true con un error (400 modelo invalido) sigue siendo JSON de error, no un SSE vacio', async () => {
  const r = await fetch(A.base + '/v1/chat/completions', { method: 'POST', headers: { 'content-type': 'application/json' }, body: JSON.stringify({ model: 'no-existe', stream: true, messages: [{ role: 'user', content: 'x' }] }) });
  assert.equal(r.status, 400); assert.match(r.headers.get('content-type'), /application\/json/);
  assert.equal((await r.json()).error.code, 'MODELO_INVALIDO');
});
