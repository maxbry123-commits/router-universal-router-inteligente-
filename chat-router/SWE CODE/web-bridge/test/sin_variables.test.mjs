// sin_variables.test.mjs — el bridge debe FUNCIONAR sin que el Director configure variables nuevas en Hugging Face:
// (1) Bearer = clave de acceso, (2) defaults de SWECODE_URL_S1..S3 / RIU_DEEPSEEK_HARNESS_URL, (3) confirmacion (141) activa por defecto SOLO con efectos,
// (4) aprobadores: sin BRIDGE_APROBADORES 503 con el nombre exacto de la variable y el script. Claves FALSAS; servidores simulados con node:http.
import test, { before, after } from 'node:test';
import assert from 'node:assert/strict';
import crypto from 'node:crypto';
import fs from 'node:fs';
import http from 'node:http';
import os from 'node:os';
import path from 'node:path';
import { aplicarDefectos, urlHarnessLocal, esUrlLocal, SWECODE_URLS_PUBLICAS } from '../src/defaults.js';
import { clavesAcceso, ACCESO_VARS } from '../src/acceso.js';
import { montarRutasSwe } from '../src/swe_rutas.js';
import { prepararApp, arrancar, limpiar, registrarMock } from './helpers/bridge_app.mjs';
import './helpers/acceso.mjs';

const CLAVES = { RIU_API_KEY: 'k-api-falsa', RIU_PUBLIC_CHAT_KEY: 'k-publica-falsa', RIU_MCP_KEY: 'k-mcp-falsa', RIU_ROUTER_API_KEY: 'k-router-falsa' };
const sin = { 'x-api-key': '' };  // "sin clave de acceso" (el wrapper de fetch no inyecta la de pruebas)
const disco = (n) => fs.mkdtempSync(path.join(os.tmpdir(), `sv-${n}-`));
const sha = (t) => crypto.createHash('sha256').update(t).digest('hex');
const post = async (srv, ruta, body, headers = {}) => { const r = await fetch(srv.base + ruta, { method: 'POST', headers: { 'content-type': 'application/json', ...headers }, body: JSON.stringify(body) }); return { status: r.status, json: await r.json().catch(() => null) }; };

before(() => { prepararApp(); });
after(() => { limpiar(); });

// ---------------- (1) Authorization: Bearer <clave de acceso> ----------------
test('1. acceso.js: las 4 variables de acceso, en este orden', () => {
  assert.deepEqual(ACCESO_VARS, ['RIU_API_KEY', 'RIU_PUBLIC_CHAT_KEY', 'RIU_MCP_KEY', 'RIU_ROUTER_API_KEY']);
  assert.deepEqual(clavesAcceso({ ...CLAVES, RIU_MCP_KEY: '' }), ['k-api-falsa', 'k-publica-falsa', 'k-router-falsa']);
  assert.deepEqual(clavesAcceso({}), []);
});

test('1. bridge REAL: cada una de las 4 claves de acceso vale como Authorization: Bearer, sin BRIDGE_TOKEN; mala = 401; ninguna configurada = 503', async () => {
  const B = await arrancar('bearer', { __sinAcceso: true, BRIDGE_STATE_DIR: disco('a'), ...CLAVES });
  for (const [v, k] of Object.entries(CLAVES)) {
    const r = await fetch(B.base + '/v1/models', { headers: { ...sin, authorization: `Bearer ${k}` } });
    assert.equal(r.status, 200, `${v} como Bearer`);
    assert.equal((await fetch(B.base + '/v1/models', { headers: { 'x-api-key': k } })).status, 200, `${v} en x-api-key sigue valiendo`);
  }
  for (const h of [{ authorization: 'Bearer otra-clave' }, { authorization: 'Bearer ' }, { authorization: 'Basic ' + CLAVES.RIU_API_KEY }, {}]) {
    const r = await fetch(B.base + '/v1/models', { headers: { ...sin, ...h } });
    assert.equal(r.status, 401, JSON.stringify(h));
    assert.equal((await r.json()).error.code, 'NO_AUTORIZADO');
  }
  assert.equal((await fetch(B.base + '/health', { headers: sin })).status, 200, '/health sigue abierto');
  const N = await arrancar('bearer-ninguna', { __sinAcceso: true, BRIDGE_STATE_DIR: disco('b') });
  const r = await fetch(N.base + '/v1/models', { headers: { ...sin, authorization: 'Bearer cualquiera' } });
  assert.equal(r.status, 503); assert.equal((await r.json()).error.code, 'SIN_CLAVE_DE_ACCESO');
});

test('1. BRIDGE_TOKEN pasa a ser OPCIONAL pero sigue valiendo (Bearer/x-bridge-key); una clave de acceso en Bearer abre tambien el panel /v1/claves; el token NO abre /v1/claves', async () => {
  const B = await arrancar('bearer-token', { __sinAcceso: true, BRIDGE_STATE_DIR: disco('c'), BRIDGE_TOKEN: 'token-bridge-falso', RIU_API_KEY: CLAVES.RIU_API_KEY });
  assert.equal((await fetch(B.base + '/v1/models', { headers: { ...sin, authorization: 'Bearer token-bridge-falso' } })).status, 200);
  assert.equal((await fetch(B.base + '/v1/models', { headers: { ...sin, 'x-bridge-key': 'token-bridge-falso' } })).status, 200);
  assert.equal((await fetch(B.base + '/v1/models', { headers: { ...sin, authorization: `Bearer ${CLAVES.RIU_API_KEY}` } })).status, 200);
  assert.equal((await fetch(B.base + '/v1/claves', { headers: { ...sin, authorization: `Bearer ${CLAVES.RIU_API_KEY}` } })).status, 200);
  assert.equal((await fetch(B.base + '/v1/claves', { headers: { ...sin, authorization: 'Bearer token-bridge-falso' } })).status, 401, 'el token del bridge no abre el panel de claves');
});

test('1. el propietario de una tarea es el mismo con la clave en x-api-key que en Bearer (mismo hash); otra clave = otro propietario', async () => {
  const proveedor = await new Promise((ok) => { const s = http.createServer((req, res) => { let d = ''; req.on('data', (c) => d += c); req.on('end', () => { res.writeHead(200, { 'content-type': 'application/json' }); res.end(JSON.stringify({ choices: [{ finish_reason: 'stop', message: { role: 'assistant', content: 'R' } }] })); }); }).listen(0, '127.0.0.1', () => { registrarMock(s); ok(`http://127.0.0.1:${s.address().port}`); }); });
  const B = await arrancar('prop', { __sinAcceso: true, BRIDGE_STATE_DIR: disco('d'), SWECODE_URL_S1: proveedor, ...CLAVES });
  const cuerpo = { model: 'qwen2.5-coder-1.5b', messages: [{ role: 'user', content: 'hola' }], tarea_id: 'prop-1' };
  assert.equal((await post(B, '/v1/chat/completions', cuerpo, { 'x-api-key': CLAVES.RIU_API_KEY })).status, 200);
  assert.equal((await post(B, '/v1/chat/completions', cuerpo, { ...sin, authorization: `Bearer ${CLAVES.RIU_API_KEY}` })).status, 200, 'misma clave por Bearer = misma tarea');
  const ajena = await post(B, '/v1/chat/completions', cuerpo, { ...sin, authorization: `Bearer ${CLAVES.RIU_MCP_KEY}` });
  assert.equal(ajena.status, 403); assert.equal(ajena.json.error.code, 'TAREA_AJENA');
});

// /v1/swe/*: misma regla (Bearer = BRIDGE_TOKEN o clave de acceso); las claves solo valen en Authorization: Bearer
const appFalsa = () => { const r = {}; return { rutas: r, post: (p, fn) => { r[p] = fn; }, get: (p, fn) => { r['GET ' + p] = fn; } }; };
const resFalsa = () => { const r = { codigo: 200, cuerpo: null, status(c) { r.codigo = c; return r; }, json(o) { r.cuerpo = o; return r; } }; return r; };
const harnessOk = (log) => async (url, init) => { log.push({ url, init }); return { ok: true, status: 200, json: async () => ({ status: 'ok', result: { ok: true, estado: 'PENDIENTE' } }) }; };
const llamar = async (env, ruta, headers, body = { task_id: 'a-1', origen: 'openclaw' }) => {
  const log = [], app = appFalsa(); montarRutasSwe(app, { env, fetchFn: harnessOk(log) });
  const res = resFalsa(); await app.rutas['/v1/swe/' + ruta]({ headers, body }, res); return { res, log };
};
const ENV_H = { RIU_DEEPSEEK_HARNESS_URL: 'http://harness.invalid', RIU_API_KEY: 'k-api-falsa' };

test('1. /v1/swe/*: una clave de acceso en Bearer vale sin BRIDGE_TOKEN; mala 401; nada configurado 503; x-api-key solo NO vale (se mantiene)', async () => {
  for (const [v, k] of Object.entries({ ...CLAVES })) {
    const { res, log } = await llamar({ ...ENV_H, [v]: k }, 'estado', { authorization: `Bearer ${k}` });
    assert.equal(res.codigo, 200, v); assert.equal(log.length, 1);
  }
  let r = await llamar(ENV_H, 'estado', { authorization: 'Bearer otra' }); assert.equal(r.res.codigo, 401); assert.equal(r.log.length, 0);
  r = await llamar(ENV_H, 'estado', { 'x-api-key': 'k-api-falsa' }); assert.equal(r.res.codigo, 401, 'x-api-key no abre /v1/swe/*');
  r = await llamar({ RIU_DEEPSEEK_HARNESS_URL: 'http://harness.invalid' }, 'estado', { authorization: 'Bearer lo-que-sea' });
  assert.equal(r.res.codigo, 503); assert.equal(r.log.length, 0);
  r = await llamar({ ...ENV_H, BRIDGE_TOKEN: 'tok-falso' }, 'estado', { authorization: 'Bearer tok-falso' }); assert.equal(r.res.codigo, 200, 'BRIDGE_TOKEN sigue valiendo');
});

// ---------------- (4) aprobadores ----------------
test('4. aprobar sin BRIDGE_APROBADORES: 503 que nombra la variable exacta y chat-router/DEPLOY/generar-aprobadores.sh; no llama al Harness; no inventa aprobadores', async () => {
  const { res, log } = await llamar({ ...ENV_H }, 'aprobar', { authorization: 'Bearer k-api-falsa', 'x-operador': 'antonio.director', 'x-operator-token': 't' }, { task_id: 'a-1', origen: 'openclaw', op_id: 'op1' });
  assert.equal(res.codigo, 503); assert.equal(res.cuerpo.error.code, 'APROBADORES_NO_CONFIGURADOS');
  assert.match(res.cuerpo.error.message, /BRIDGE_APROBADORES/); assert.match(res.cuerpo.error.message, /chat-router\/DEPLOY\/generar-aprobadores\.sh/);
  assert.equal(log.length, 0);
});

test('4. aprobar: el token de un operador NO puede ser ninguna clave de acceso (ni BRIDGE_TOKEN): 503; con un token propio distinto, pasa', async () => {
  const env = { ...ENV_H, BRIDGE_TOKEN: 'tok-falso' };
  for (const compartida of ['k-api-falsa', 'tok-falso']) {
    const { res, log } = await llamar({ ...env, BRIDGE_APROBADORES: `ana:${sha(compartida)}` }, 'aprobar', { authorization: 'Bearer tok-falso', 'x-operador': 'ana', 'x-operator-token': compartida }, { task_id: 'a-1', origen: 'openclaw', op_id: 'op1' });
    assert.equal(res.codigo, 503, compartida); assert.equal(log.length, 0);
  }
  const ok = await llamar({ ...env, BRIDGE_APROBADORES: `ana:${sha('token-propio-de-ana')}` }, 'aprobar', { authorization: 'Bearer tok-falso', 'x-operador': 'ana', 'x-operator-token': 'token-propio-de-ana' }, { task_id: 'a-1', origen: 'openclaw', op_id: 'op1' });
  assert.equal(ok.res.codigo, 200);
});

// ---------------- (2) defaults sin variables ----------------
test('2. defaults: SWECODE_URL_S1..S3 publicas solo si la variable NO esta (vacia = desactivada a proposito)', () => {
  assert.deepEqual(SWECODE_URLS_PUBLICAS, { S1: 'https://comand-center-1-swe-code-s1.hf.space/v1', S2: 'https://comand-center-1-swe-code-s2.hf.space/v1', S3: 'https://comand-center-1-swe-code-s3.hf.space/v1' });
  const e = aplicarDefectos({});
  assert.equal(e.SWECODE_URL_S1, SWECODE_URLS_PUBLICAS.S1); assert.equal(e.SWECODE_URL_S2, SWECODE_URLS_PUBLICAS.S2); assert.equal(e.SWECODE_URL_S3, SWECODE_URLS_PUBLICAS.S3);
  const mio = aplicarDefectos({ SWECODE_URL_S1: 'http://127.0.0.1:9101/v1', SWECODE_URL_S2: '' });
  assert.equal(mio.SWECODE_URL_S1, 'http://127.0.0.1:9101/v1'); assert.equal(mio.SWECODE_URL_S2, '', 'vacia = a proposito desactivada'); assert.equal(mio.SWECODE_URL_S3, SWECODE_URLS_PUBLICAS.S3);
  const e0 = {}; assert.equal(aplicarDefectos(e0), e0, 'completa el mismo objeto (process.env)');
});

test('2. defaults: RIU_DEEPSEEK_HARNESS_URL = el plugin LOCAL del mismo Space (127.0.0.1:$PORT/plugins/deepseek_harness, 7861 sin PORT) solo con RIU_API_KEY; siempre local', () => {
  assert.equal(aplicarDefectos({ RIU_API_KEY: 'k' }).RIU_DEEPSEEK_HARNESS_URL, 'http://127.0.0.1:7861/plugins/deepseek_harness');
  assert.equal(aplicarDefectos({ RIU_API_KEY: 'k', PORT: '7999' }).RIU_DEEPSEEK_HARNESS_URL, 'http://127.0.0.1:7999/plugins/deepseek_harness');
  for (const malo of ['abc', '0', '70000', '78.5', '-1', '7861/../x', 'http://evil.example']) assert.equal(urlHarnessLocal({ PORT: malo }), 'http://127.0.0.1:7861/plugins/deepseek_harness', `PORT=${malo}`);
  assert.equal(aplicarDefectos({}).RIU_DEEPSEEK_HARNESS_URL, undefined, 'sin RIU_API_KEY el Harness no se podria autenticar: no se inventa');
  assert.equal(aplicarDefectos({ RIU_API_KEY: 'k', RIU_DEEPSEEK_HARNESS_URL: 'https://otro.hf.space/plugins/deepseek_harness' }).RIU_DEEPSEEK_HARNESS_URL, 'https://otro.hf.space/plugins/deepseek_harness');
  assert.equal(aplicarDefectos({ RIU_API_KEY: 'k', RIU_DEEPSEEK_HARNESS_URL: '' }).RIU_DEEPSEEK_HARNESS_URL, '', 'vacia = desactivada a proposito');
  assert.ok(esUrlLocal(urlHarnessLocal({ PORT: '8000' })));
  for (const mala of ['https://comand-center-1-riu-router.hf.space/plugins/deepseek_harness', 'http://evil.example:7861/x', 'http://127.0.0.1.evil.example/x', 'http://user:p@127.0.0.1:7861/x', 'ftp://127.0.0.1/x', 'no es url', '']) assert.equal(esUrlLocal(mala), false, mala);
});

test('2. bridge REAL sin SWECODE_URL_* ni RIU_DEEPSEEK_HARNESS_URL: guarda el checkpoint en el Harness LOCAL (127.0.0.1:$PORT/plugins/deepseek_harness/invoke) con la clave RIU_API_KEY', async () => {
  const vistos = [], almacen = new Map();
  const harness = await new Promise((ok) => { const s = http.createServer((req, res) => { let d = ''; req.on('data', (c) => d += c); req.on('end', () => {
    const j = d ? JSON.parse(d) : {}; vistos.push({ url: req.url, clave: req.headers['x-api-key'], tool: j.tool });
    if (j.tool === 'guardar') almacen.set(j.args.nombre, j.args.valor);
    res.writeHead(200, { 'content-type': 'application/json' }); res.end(JSON.stringify({ status: 'ok', result: j.tool === 'leer' ? { nombre: j.args.nombre, valor: almacen.get(j.args.nombre) ?? null } : { nombre: j.args.nombre, destino: 'hf' } }));
  }); }).listen(0, '127.0.0.1', () => { registrarMock(s); ok(s.address().port); }); });
  const proveedor = await new Promise((ok) => { const s = http.createServer((req, res) => { let d = ''; req.on('data', (c) => d += c); req.on('end', () => { res.writeHead(200, { 'content-type': 'application/json' }); res.end(JSON.stringify({ choices: [{ finish_reason: 'stop', message: { role: 'assistant', content: 'HECHO' } }] })); }); }).listen(0, '127.0.0.1', () => { registrarMock(s); ok(`http://127.0.0.1:${s.address().port}`); }); });
  // el proveedor local se inyecta como S1 explicito (el default publico no se toca en pruebas); lo que se prueba es la URL del Harness por defecto
  const B = await arrancar('harness-local', { __conDefectos: true, BRIDGE_STATE_DIR: disco('e'), PORT: String(harness), RIU_API_KEY: 'clave-harness-falsa', SWECODE_URL_S1: proveedor });
  const r = await post(B, '/v1/chat/completions', { model: 'qwen2.5-coder-1.5b', messages: [{ role: 'user', content: 'hola' }], tarea_id: 'hl-1' });
  assert.equal(r.status, 200); assert.equal(r.json.choices[0].message.content, 'HECHO');
  assert.ok(vistos.length > 0, 'el checkpoint llego al Harness local por defecto');
  assert.ok(vistos.every((v) => v.url === '/plugins/deepseek_harness/invoke' && v.clave === 'clave-harness-falsa'), JSON.stringify(vistos));
  assert.ok(almacen.has('tareas/swe/bridge/hl-1/checkpoint.json'));
});

// ---------------- (3) confirmacion activa por defecto, solo con efectos ----------------
const proveedorTools = () => new Promise((ok) => { const chat = []; const s = http.createServer((req, res) => { let d = ''; req.on('data', (c) => d += c); req.on('end', () => {
  const b = d ? JSON.parse(d) : null; chat.push(b);
  const conTools = b && Array.isArray(b.tools) && b.tools.length;
  res.writeHead(200, { 'content-type': 'application/json' });
  res.end(JSON.stringify({ choices: [{ finish_reason: conTools ? 'tool_calls' : 'stop', message: { role: 'assistant', content: conTools ? null : 'respuesta de chat', ...(conTools ? { tool_calls: [{ id: 'c1', type: 'function', function: { name: 'escribir', arguments: '{}' } }] } : {}) } }] }));
}); }).listen(0, '127.0.0.1', () => { registrarMock(s); ok({ chat, url: `http://127.0.0.1:${s.address().port}` }); }); });
const TOOLS = [{ type: 'function', function: { name: 'escribir', parameters: {} } }];
const msgs = [{ role: 'user', content: 'crea el archivo A' }];

test('3. confirmacion POR DEFECTO: con tools (efectos) y sin objetivo/operaciones_previstas => 409 PLAN_REQUERIDO y el modelo no se llama; con plan pasa; fuera del plan 409; el chat sin tools no pide nada', async () => {
  const p = await proveedorTools();
  const B = await arrancar('conf-defecto', { BRIDGE_STATE_DIR: disco('f'), SWECODE_URL_S1: p.url });
  const M = 'qwen2.5-coder-1.5b';
  const sinPlan = await post(B, '/v1/chat/completions', { model: M, messages: msgs, tarea_id: 'cf-1', tools: TOOLS });
  assert.equal(sinPlan.status, 409); assert.equal(sinPlan.json.error.code, 'PLAN_REQUERIDO'); assert.equal(p.chat.length, 0, 'el modelo no se llamo');
  const falso = await post(B, '/v1/chat/completions', { model: M, messages: msgs, tarea_id: 'cf-1b', tools: TOOLS, exigir_confirmacion: false });
  assert.equal(falso.status, 409, 'un cliente no puede apagar la confirmacion desde el cuerpo: solo el operador con BRIDGE_EXIGIR_CONFIRMACION=0');
  const fuera = await post(B, '/v1/chat/completions', { model: M, messages: msgs, tarea_id: 'cf-2', tools: TOOLS, objetivo: 'crear A', operaciones_previstas: ['leer'] });
  assert.equal(fuera.status, 409); assert.equal(fuera.json.error.code, 'OPERACION_NO_PREVISTA');
  const bien = await post(B, '/v1/chat/completions', { model: M, messages: msgs, tarea_id: 'cf-3', tools: TOOLS, objetivo: 'crear A', operaciones_previstas: ['escribir'] });
  assert.equal(bien.status, 200); assert.equal(bien.json.tarea.fase, 'ESPERANDO_TOOLS'); assert.equal(bien.json.choices[0].message.tool_calls[0].id, 'c1');
  const n = p.chat.length;
  const chat = await post(B, '/v1/chat/completions', { model: M, messages: [{ role: 'user', content: 'hola, que tal' }], tarea_id: 'cf-4' });
  assert.equal(chat.status, 200); assert.equal(chat.json.choices[0].message.content, 'respuesta de chat'); assert.equal(p.chat.length, n + 1);
  const vacias = await post(B, '/v1/chat/completions', { model: M, messages: [{ role: 'user', content: 'otra cosa' }], tarea_id: 'cf-5', tools: [] });
  assert.equal(vacias.status, 200, 'tools vacias = sin efectos');
  const sinTarea = await post(B, '/v1/chat/completions', { model: M, messages: [{ role: 'user', content: 'sin tarea_id' }] });
  assert.equal(sinTarea.status, 200, 'chat normal sin tarea_id: igual que siempre');
});

test('3. BRIDGE_EXIGIR_CONFIRMACION=0 la desactiva (las tools pasan sin plan); BRIDGE_EXIGIR_CONFIRMACION=1 sigue activa', async () => {
  const p = await proveedorTools();
  const off = await arrancar('conf-off', { BRIDGE_STATE_DIR: disco('g'), SWECODE_URL_S1: p.url, BRIDGE_EXIGIR_CONFIRMACION: '0' });
  const M = 'qwen2.5-coder-1.5b';
  const r = await post(off, '/v1/chat/completions', { model: M, messages: msgs, tarea_id: 'cf-off', tools: TOOLS });
  assert.equal(r.status, 200); assert.equal(r.json.tarea.fase, 'ESPERANDO_TOOLS');
  const on = await arrancar('conf-on', { BRIDGE_STATE_DIR: disco('h'), SWECODE_URL_S1: p.url, BRIDGE_EXIGIR_CONFIRMACION: '1' });
  const r2 = await post(on, '/v1/chat/completions', { model: M, messages: msgs, tarea_id: 'cf-on', tools: TOOLS });
  assert.equal(r2.status, 409); assert.equal(r2.json.error.code, 'PLAN_REQUERIDO');
});
