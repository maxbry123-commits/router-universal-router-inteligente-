// seguridad.test.mjs — integracion de server.js REAL: puerta de acceso global, variantes de ruta, /health recortado, claves por llamada,
// ids de modelo autorizados, plazo del respaldo y autoretomar por defecto. Claves FALSAS; proveedores simulados con node:http.
import test, { before, after } from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import http from 'node:http';
import path from 'node:path';
import { ACCESO_TEST } from './helpers/acceso.mjs';
import { prepararApp, arrancar, limpiar, registrarMock, TMP } from './helpers/bridge_app.mjs';

const TOK = 'token-del-bridge-seguridad';
const sin = { 'x-api-key': '' };            // "sin clave de acceso" (el wrapper de fetch no inyecta la de pruebas)
const bearer = { 'x-api-key': '', authorization: 'Bearer ' + TOK };
let G, N, H, grq, hang, bancoLog;
const llamadasBanco = () => { try { return fs.readFileSync(bancoLog, 'utf8').split('\n').filter(Boolean); } catch { return []; } };
const leer = async (r) => { const texto = await r.text(); let json = null; try { json = JSON.parse(texto); } catch { /* no JSON */ } return { status: r.status, json, texto }; };
const jget = async (srv, ruta, headers = {}) => leer(await fetch(srv.base + ruta, { headers }));
const jpost = async (srv, ruta, body, headers = {}, metodo = 'POST') => leer(await fetch(srv.base + ruta, { method: metodo, headers: { 'content-type': 'application/json', ...headers }, ...(body !== undefined ? { body: JSON.stringify(body) } : {}) }));
const chat = (srv, body, headers = {}) => jpost(srv, '/v1/chat/completions', { messages: [{ role: 'user', content: 'hola mundo' }], ...body }, headers);
const esperar = async (fn, ms = 6000) => { const t0 = Date.now(); while (Date.now() - t0 < ms) { const v = await fn(); if (v) return v; await new Promise((r) => setTimeout(r, 100)); } return null; };

before(async () => {
  prepararApp();
  // motor falso controlable por entorno (MOTOR_MODO=fail: la web falla y se va al respaldo)
  fs.writeFileSync(path.join(TMP, 'app', 'src', 'motor.js'), `export async function consultarWeb(m) { if (process.env.MOTOR_MODO === 'fail') throw Object.assign(new Error('roto'), { code: 'SELECTOR_BROKEN' }); return 'WEB[' + m + ']'; }\nexport async function salud() { return {}; }\n`);
  fs.writeFileSync(path.join(TMP, 'app', 'preload.mjs'), `const r = await import('./src/respaldo.js');\nif (process.env.TEST_GROQ_URL) r.BASES.groq = process.env.TEST_GROQ_URL;\n`);
  grq = { hits: [], modo: 'ok' };
  const s = http.createServer((req, res) => {
    let d = ''; req.on('data', (c) => d += c); req.on('end', () => {
      grq.hits.push({ auth: req.headers.authorization, body: d ? JSON.parse(d) : null });
      if (grq.modo === 'colgar') return;
      res.writeHead(200, { 'content-type': 'application/json' });
      res.end(JSON.stringify({ choices: [{ finish_reason: 'stop', message: { role: 'assistant', content: 'de-groq' } }] }));
    });
  }).listen(0, '127.0.0.1'); registrarMock(s); await new Promise((r) => s.on('listening', r));
  grq.url = `http://127.0.0.1:${s.address().port}`;
  bancoLog = path.join(TMP, 'banco.log');
  fs.writeFileSync(path.join(TMP, 'fake-banco.sh'), `#!/bin/sh\necho "$1" >> "${bancoLog}"\nif [ "$1" = "leer" ]; then echo '{"groq": [], "nvidia": []}'; elif [ "$1" = "diagnostico" ]; then echo '{"propio": {"existe": true, "abre_con": 0}}'; else cat > /dev/null; echo '{"ok": true}'; fi\n`, { mode: 0o755 });
  const base = { RIU_CLAVES_CMD: path.join(TMP, 'fake-banco.sh'), TEST_GROQ_URL: grq.url, BRIDGE_RESPALDO_MS: '8000' };
  G = await arrancar('G', { ...base, __sinAcceso: true, BRIDGE_TOKEN: TOK, RIU_API_KEY: ACCESO_TEST });
  N = await arrancar('N', { ...base, __sinAcceso: true });
  H = await arrancar('H', { ...base, __sinAcceso: true, RIU_API_KEY: 'k-api', RIU_PUBLIC_CHAT_KEY: 'k-publica', RIU_MCP_KEY: 'k-mcp', RIU_ROUTER_API_KEY: 'k-router' });
});
after(() => limpiar());

// ---- (1) puerta de /v1/claves y /v1/openclaw: variantes de mayusculas y barras ----
test('S1. /v1/claves y /v1/openclaw: las variantes con barra final, mayusculas o barras dobles NO saltan la puerta (401 sin clave de acceso, incluso con BRIDGE_TOKEN valido)', async () => {
  const variantes = ['/v1/claves', '/v1/claves/', '/V1/CLAVES', '/v1/Claves', '/v1/claves//', '//v1/claves', '/v1/openclaw', '/v1/openclaw/', '/V1/OPENCLAW', '/v1/OpenClaw/', '/v1/claves/.', '/v1/claves/?x=1'];
  const n0 = llamadasBanco().length;
  for (const cab of [sin, bearer]) for (const metodo of ['GET', 'POST', 'DELETE']) for (const v of variantes) {
    const r = await jpost(G, v, metodo === 'POST' ? { groq: 'gsk-no-debe-entrar' } : undefined, cab, metodo);
    assert.equal(r.status, 401, `${metodo} ${v} ${JSON.stringify(cab)} -> ${r.status} ${r.texto.slice(0, 80)}`);
  }
  assert.equal(llamadasBanco().length, n0, 'ninguna variante llego a tocar el banco');
  assert.deepEqual((await jget(G, '/v1/claves', { 'x-api-key': ACCESO_TEST })).json, { ok: true, groq: 0, nvidia: 0 }, 'ni se guardo nada');
});

test('S1b. con la clave de acceso, la ruta exacta funciona y las variantes con barra final o mayusculas ya no existen (strict + case sensitive routing)', async () => {
  const k = { 'x-api-key': ACCESO_TEST };
  assert.equal((await jget(G, '/v1/claves', k)).status, 200);
  for (const v of ['/v1/claves/', '/V1/CLAVES', '/v1/Claves']) assert.equal((await jget(G, v, k)).status, 404, v);
  assert.match(fs.readFileSync(path.join(TMP, 'app', 'src', 'server.js'), 'utf8'), /app\.set\('strict routing', true\)[\s\S]*app\.set\('case sensitive routing', true\)|app\.set\('case sensitive routing', true\)[\s\S]*app\.set\('strict routing', true\)/);
});

// ---- (2) puerta global ----
test('S2. sin BRIDGE_TOKEN ya NO queda abierto: toda ruta (salvo /health) exige BRIDGE_TOKEN o una de las 4 claves de acceso en x-api-key; sin ninguna configurada -> 503', async () => {
  for (const ruta of ['/v1/models', '/v1/queue', '/v1/proyectos', '/v1/secciones', '/v1/evolucion', '/debug/tab']) {
    assert.equal((await jget(H, ruta, sin)).status, 401, ruta);
    assert.equal((await jget(H, ruta, { 'x-api-key': 'otra' })).status, 401, ruta);
  }
  for (const k of ['k-api', 'k-publica', 'k-mcp', 'k-router']) assert.equal((await jget(H, '/v1/models', { 'x-api-key': k })).status, 200, k);
  assert.equal((await jpost(H, '/refresh_session', {}, sin)).status, 401);
  const r = await jget(N, '/v1/models', sin);
  assert.equal(r.status, 503); assert.equal(r.json.error.code, 'SIN_CLAVE_DE_ACCESO');
  assert.equal((await jget(N, '/v1/models', { 'x-api-key': 'cualquiera' })).status, 503);
  assert.equal((await chat(N, { model: 'web-qwen38max' }, { 'x-api-key': 'cualquiera' })).status, 503);
  assert.equal((await jget(N, '/health', sin)).status, 200, '/health sigue publico');
});

test('S2b. con BRIDGE_TOKEN: Bearer o x-bridge-key valen en todas las rutas; la clave de acceso en x-api-key tambien; el chat solo manda x-api-key', async () => {
  assert.equal((await jget(G, '/v1/models', sin)).status, 401);
  assert.equal((await jget(G, '/v1/models', bearer)).status, 200);
  assert.equal((await jget(G, '/v1/models', { 'x-api-key': '', 'x-bridge-key': TOK })).status, 200);
  assert.equal((await jget(G, '/v1/models', { 'x-api-key': ACCESO_TEST })).status, 200);
  assert.equal((await jget(G, '/v1/models', { 'x-api-key': '', authorization: 'Bearer ' + TOK + 'x' })).status, 401);
});

test('S2c. /health publico recorta banco.* a contadores y booleanos (sin stderr, codigos http ni rutas); con clave valida trae el detalle completo', async () => {
  const pub = await jget(G, '/health', sin), priv = await jget(G, '/health', { 'x-api-key': ACCESO_TEST });
  assert.equal(pub.status, 200); assert.equal(pub.json.ok, true);
  const b = pub.json.banco;
  assert.deepEqual(Object.keys(b).sort(), ['accesos', 'github', 'local_bytes', 'python']);
  assert.deepEqual(Object.keys(b.github).sort(), ['escrito', 'token']);
  assert.deepEqual(Object.keys(b.python), ['ok']);
  assert.ok(['number', 'object'].includes(typeof b.local_bytes) && typeof b.github.token === 'boolean' && typeof b.accesos === 'number');
  assert.ok(!('state_dir' in pub.json), 'sin ruta del disco');
  assert.ok(!/stderr|"http"|"error"|detalle|abre_con/.test(JSON.stringify(b)));
  const c = priv.json.banco;
  assert.ok('http' in c.github && 'error' in c.github && 'accion' in c.python, 'con clave: detalle completo');
  assert.ok('state_dir' in priv.json);
  assert.ok('state_dir' in (await jget(G, '/health', bearer)).json, 'el BRIDGE_TOKEN valido tambien ve el detalle');
});

// ---- (3) claves / cuentas por llamada ----
test('S3. POST /v1/chat/completions con `claves`/`cuentas`: exige x-api-key de acceso (BRIDGE_TOKEN solo no basta), valida con claveOk y tope 20, y solo persiste si viene autenticada', async () => {
  const k = { 'x-api-key': ACCESO_TEST };
  const n0 = llamadasBanco().filter((x) => x === 'guardar').length;
  // sin x-api-key de acceso (solo BRIDGE_TOKEN): 401 y NO se aplican ni se guardan
  for (const extra of [{ claves: { groq: 'gsk-valida-123456' } }, { cuentas: [{ correo: 'a@x.com' }] }]) {
    const r = await chat(G, { model: 'groq/qwen/qwen3.8-27b', ...extra }, bearer);
    assert.equal(r.status, 401, JSON.stringify(Object.keys(extra))); assert.equal(r.json.error.code, 'NO_AUTORIZADO');
  }
  assert.equal(llamadasBanco().filter((x) => x === 'guardar').length, n0);
  assert.equal((await jget(G, '/v1/claves', k)).json.groq, 0, 'no entro en memoria');
  // con acceso pero invalidas: 400 sin repetir el valor
  for (const malas of [{ groq: 'con espacio dentro' }, { groq: 'corta' }, { groq: Array.from({ length: 21 }, (_, i) => `gsk-valida-${i}-xx`) }, { nvidia: 'x'.repeat(301) }, { groq: [123456789] }, 'texto', [], { groq: { a: 1 } }]) {
    const r = await chat(G, { model: 'groq/qwen/qwen3.8-27b', claves: malas }, k);
    assert.equal(r.status, 400, JSON.stringify(malas).slice(0, 50)); assert.equal(r.json.error.code, 'CLAVE_INVALIDA');
    assert.ok(!/con espacio dentro/.test(r.texto));
  }
  assert.equal(llamadasBanco().filter((x) => x === 'guardar').length, n0);
  // validas y autenticadas: se usan y se persisten
  grq.hits.length = 0; grq.modo = 'ok';
  const ok = await chat(G, { model: 'groq/qwen/qwen3.8-27b', claves: { groq: ['gsk-VALIDA-POR-LLAMADA'] } }, k);
  assert.equal(ok.status, 200, ok.texto.slice(0, 120)); assert.equal(grq.hits[0].auth, 'Bearer gsk-VALIDA-POR-LLAMADA');
  assert.ok(await esperar(() => llamadasBanco().filter((x) => x === 'guardar').length > n0), 'se persistio en el banco');
  assert.ok(!/VALIDA-POR-LLAMADA/.test(G.log()));
  await jpost(G, '/v1/claves', undefined, k, 'DELETE');
});

// ---- (11) ids de modelo autorizados ----
test('S11a. un id groq/ o nvidia/ fuera de MODELOS_API se rechaza con 400 MODELO_INVALIDO antes de tocar al proveedor; los autorizados pasan', async () => {
  const k = { 'x-api-key': ACCESO_TEST };
  grq.hits.length = 0; grq.modo = 'ok';
  for (const m of ['groq/llama-3.3-70b-versatile', 'groq/xxx', 'nvidia/meta/llama-3.3-70b-instruct', 'groq/qwen/qwen3.8-27b-otro']) {
    const r = await chat(G, { model: m, claves: { groq: 'gsk-VALIDA-1234' } }, k);
    assert.equal(r.status, 400, m); assert.equal(r.json.error.code, 'MODELO_INVALIDO');
  }
  assert.equal(grq.hits.length, 0);
  const ok = await chat(G, { model: 'groq/qwen/qwen3.8-27b', claves: { groq: 'gsk-VALIDA-1234' } }, k);
  assert.equal(ok.status, 200); assert.equal(grq.hits[0].body.model, 'qwen/qwen3.8-27b');
  await jpost(G, '/v1/claves', undefined, k, 'DELETE');
});

test('S11b. el respaldo() tras un fallo de la web tambien va con plazo (conDeadline): un proveedor colgado da 504 UPSTREAM_TIMEOUT, no espera BRIDGE_RESPALDO_MS', async () => {
  grq.modo = 'colgar';
  const D = await arrancar('DL', { RIU_CLAVES_CMD: path.join(TMP, 'fake-banco.sh'), TEST_GROQ_URL: grq.url, GROQ_API_KEY: 'gsk-FAKE-DEADLINE', MOTOR_MODO: 'fail', BRIDGE_DEADLINE_MS: '700', BRIDGE_RESPALDO_MS: '30000' });
  const t0 = Date.now();
  const r = await chat(D, { model: 'web-qwen38max' });
  const ms = Date.now() - t0;
  grq.modo = 'ok';
  assert.equal(r.status, 504, r.texto.slice(0, 160)); assert.equal(r.json.error.code, 'UPSTREAM_TIMEOUT');
  assert.ok(ms < 4000, `tardo ${ms} ms`);
});

// ---- (11) BRIDGE_AUTORETOMAR por defecto ----
const huerfana = (estado) => { fs.mkdirSync(path.join(estado, 'checkpoints'), { recursive: true }); fs.writeFileSync(path.join(estado, 'checkpoints', 'huerfana.json'), JSON.stringify({ modo: 'revision', modelo: 'dsv4-flash', texto: 'TEXTO-HUERFANO', total: 2, enviados: 1 })); };
const leccion = (estado) => { try { return fs.readFileSync(path.join(estado, 'evolucion', 'lecciones.jsonl'), 'utf8'); } catch { return ''; } };
test('S11c. BRIDGE_AUTORETOMAR activo por defecto (sin la variable retoma solo); apagado unicamente con "0"', async () => {
  const e1 = fs.mkdtempSync(path.join(TMP, 'auto1-')), e0 = fs.mkdtempSync(path.join(TMP, 'auto0-'));
  huerfana(e1); huerfana(e0);
  await arrancar('AR-def', { BRIDGE_STATE_DIR: e1 });
  await arrancar('AR-off', { BRIDGE_STATE_DIR: e0, BRIDGE_AUTORETOMAR: '0' });
  assert.ok(await esperar(() => /"codigo":"REINICIO"[^\n]*"resultado":"PASS"/.test(leccion(e1)), 9000), 'por defecto retoma la seccion a medias');
  assert.ok(!/REINICIO/.test(leccion(e0)), 'con "0" no retoma');
});

// ---- (8) `persistido` = GitHub publicado ----
test('S8. POST/DELETE /v1/claves: `persistido` indica si GitHub se publico (local aparte); si GitHub falla, persistido:false pero local:true', async () => {
  const gh = { puts: 0, putStatus: 200 };
  const s = http.createServer((req, res) => {
    let d = ''; req.on('data', (c) => d += c); req.on('end', () => {
      const json = (c, o) => { res.writeHead(c, { 'content-type': 'application/json' }); res.end(JSON.stringify(o)); };
      if (req.method === 'GET' && /heads\/banco-claves$/.test(req.url)) return json(200, { object: { sha: 'r1' } });
      if (req.method === 'GET' && /contents\/banco-swe\.bin/.test(req.url)) return json(404, {});
      if (req.method === 'PUT') { gh.puts++; return json(gh.putStatus, { content: { sha: 's1' } }); }
      json(404, {});
    });
  }).listen(0, '127.0.0.1'); registrarMock(s); await new Promise((r) => s.on('listening', r));
  const estado = fs.mkdtempSync(path.join(TMP, 'gh-'));
  fs.writeFileSync(path.join(TMP, 'fake-banco-gh.sh'), `#!/bin/sh\nif [ "$1" = "leer" ]; then echo '{"groq": [], "nvidia": []}'; elif [ "$1" = "diagnostico" ]; then echo '{}'; else cat > /dev/null; printf 'MVPB1-banco-de-prueba-con-relleno' > "$BRIDGE_STATE_DIR/banco-swe.bin"; echo '{"ok": true}'; fi\n`, { mode: 0o755 });
  const B = await arrancar('GH', { __sinAcceso: true, RIU_API_KEY: ACCESO_TEST, BRIDGE_STATE_DIR: estado, RIU_CLAVES_CMD: path.join(TMP, 'fake-banco-gh.sh'), GITHUB_TOKEN: 'gh-falso', RIU_GITHUB_API: `http://127.0.0.1:${s.address().port}`, RIU_REPO: 'o/r' });
  const k = { 'x-api-key': ACCESO_TEST };
  let r = await jpost(B, '/v1/claves', { groq: 'gsk-publicada-1234' }, k);
  assert.equal(r.status, 200); assert.equal(r.json.persistido, true); assert.equal(r.json.local, true); assert.equal(gh.puts, 1);
  gh.putStatus = 500;
  r = await jpost(B, '/v1/claves', { groq: 'gsk-publicada-5678' }, k);
  assert.equal(r.json.persistido, false); assert.equal(r.json.local, true);
  r = await jpost(B, '/v1/claves', undefined, k, 'DELETE');
  assert.equal(r.json.persistido, false); assert.equal(r.json.local, true);
  gh.putStatus = 200;
  r = await jpost(B, '/v1/claves', undefined, k, 'DELETE');
  assert.equal(r.json.persistido, true);
  assert.ok(!/gsk-publicada/.test(r.texto));
  // sin GITHUB_TOKEN: nada que publicar
  const S = await arrancar('GH0', { __sinAcceso: true, RIU_API_KEY: ACCESO_TEST, RIU_CLAVES_CMD: path.join(TMP, 'fake-banco-gh.sh') });
  r = await jpost(S, '/v1/claves', { groq: 'gsk-publicada-1234' }, k);
  assert.equal(r.json.persistido, false); assert.equal(r.json.local, true);
});
