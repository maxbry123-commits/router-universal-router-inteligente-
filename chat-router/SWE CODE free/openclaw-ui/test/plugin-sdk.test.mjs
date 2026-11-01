// Test de CARGA con el SDK REAL de OpenClaw (openclaw/plugin-sdk/*) y E2E contra las rutas REALES del bridge (web-bridge/src/swe_rutas.js sobre HTTP local).
// Harness y Router son dobles (fetchFn inyectado en el bridge): no hay red externa ni claves reales. NO sustituye una prueba en un Gateway/Control UI de OpenClaw.
import test, { before, after } from 'node:test';
import assert from 'node:assert/strict';
import crypto from 'node:crypto';
import fs from 'node:fs';
import http from 'node:http';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import entry from '../dist/index.js';
import { build } from 'esbuild';
import { contract } from '../dist/contract.js';
import { leerConfig, crearCliente } from '../dist/bridge.js';
import { armarTarea, SELECCION_DEFECTO } from '../dist/selector-core.js';
import { montarRutasSwe } from '../../../SWE CODE/web-bridge/src/swe_rutas.js';

const AQUI = path.dirname(fileURLToPath(import.meta.url));
const manifiesto = JSON.parse(fs.readFileSync(path.join(AQUI, '..', 'openclaw.plugin.json'), 'utf8'));
const TOKEN = 'token-del-bridge-de-prueba', TOK_ANA = 'token-individual-ana-prueba', CLAVE_ROUTER = 'clave-router-de-prueba-xyz';
// La UI se empaqueta como lo hace `openclaw plugins build` (esbuild, navegador); el CSS no importa para la carga.
const { outputFiles } = await build({ entryPoints: [path.join(AQUI, '..', 'src', 'control-ui.ts')], bundle: true, format: 'esm', platform: 'browser', write: false, loader: { '.css': 'empty' }, logLevel: 'silent' });
const controlUi = (await import('data:text/javascript;base64,' + Buffer.from(outputFiles[0].text).toString('base64'))).default;
const sha = (t) => crypto.createHash('sha256').update(t).digest('hex');

// ---- carga con el SDK real ----
test('el id del plugin coincide en manifiesto, contrato, backend y UI; las tools declaradas en el manifiesto son las del contrato', () => {
  assert.equal(manifiesto.id, 'swe-selector'); assert.equal(contract.pluginId, manifiesto.id); assert.equal(entry.id, manifiesto.id); assert.equal(controlUi.id, manifiesto.id);
  const tools = Object.values(contract.operations).filter((o) => o.tool).map((o) => o.tool.name).sort();
  assert.deepEqual(tools, [...manifiesto.contracts.tools].sort());
  assert.deepEqual(Object.keys(contract.operations).sort(), ['aprobar', 'avanzar', 'capacidades', 'estado', 'iniciar', 'reanudar', 'tool', 'tools']);
});

function apiFalsa() {
  const acciones = new Map(), tools = new Map(), servicios = [];
  return { acciones, tools, api: { id: 'swe-selector', pluginConfig: {}, registerSessionAction: (a) => acciones.set(a.id, a), session: { controls: { registerSessionAction: (a) => acciones.set(a.id, a) } },  // 2026.10.9 publicado: api.registerSessionAction; main: api.session.controls.registerSessionAction
    registerTool: (f, o) => tools.set(o.name, f), registerCommand() {}, registerService: (s) => servicios.push(s) } };
}
test('register(): una session-action por operacion (query=operator.read, action=operator.write) y una tool de agente por operacion con tool', () => {
  const { api, acciones, tools } = apiFalsa();
  entry.register(api);
  assert.equal(acciones.size, 8);
  for (const [id, op] of Object.entries(contract.operations)) assert.deepEqual(acciones.get(id).requiredScopes, [op.kind === 'query' ? 'operator.read' : 'operator.write'], id);
  assert.deepEqual([...tools.keys()].sort(), [...manifiesto.contracts.tools].sort());
});

test('UI: activate() registra pagina, navegacion y panel con el id del plugin (mecanismo oficial registerPage/registerNavigation/registerPanel)', () => {
  const reg = [], host = { ui: { registerNavigation: (x) => (reg.push(['nav', x.id]), () => {}), registerPage: (x) => (reg.push(['page', x.id]), () => {}), registerPanel: (x) => (reg.push(['panel', x.id]), () => {}) } };
  const dispose = controlUi.activate(host);
  assert.deepEqual(reg.sort(), [['nav', 'swe'], ['page', 'swe'], ['panel', 'swe-panel']]); assert.equal(typeof dispose, 'function');
});

// ---- E2E: backend del plugin -> bridge real (swe_rutas.js) -> Harness/Router dobles ----
let servidor, base, vistoHarness = [], vistoRouter = [], vistoBridge = [];
before(async () => {
  const rutas = {}; const app = { get: (p, f) => (rutas['GET ' + p] = f), post: (p, f) => (rutas[p] = f) };
  const fetchFn = async (url, init) => {
    const body = init?.body ? JSON.parse(init.body) : null;
    if (url.startsWith('http://harness.invalid')) {
      vistoHarness.push(body);
      if (body.action === 'status') return { ok: true, status: 200, json: async () => ({ status: 'ok', result: { swe: { agentes: { 'swe-agent': { disponible: true, estado: 'DISPONIBLE' }, codex: { disponible: false, estado: 'NO INSTALADO', motivo: 'codex no esta instalado' } }, workflows: { individual: { disponible: true } }, modelos: { 'hf/lfm2.5-350m': { disponible: true } } } } }) };
      return { ok: true, status: 200, json: async () => ({ status: 'ok', result: { ok: true, task_id: body.args.task_id, estado: 'PENDIENTE', operador: body.args.operador } }) };
    }
    vistoRouter.push({ url, body, clave: init.headers['X-API-Key'] });
    if (body.method === 'tools/list') return { ok: true, status: 200, json: async () => ({ result: { tools: [{ name: 'salud' }, { name: 'github_escribir' }] } }) };
    return { ok: true, status: 200, json: async () => ({ result: { structuredContent: { status: 'ok', via: 'router' }, isError: false } }) };
  };
  montarRutasSwe(app, { env: { BRIDGE_TOKEN: TOKEN, BRIDGE_APROBADORES: `ana:${sha(TOK_ANA)}`, RIU_DEEPSEEK_HARNESS_URL: 'http://harness.invalid', RIU_API_KEY: CLAVE_ROUTER, RIU_ROUTER_URL: 'http://127.0.0.1:7861' }, fetchFn });
  servidor = http.createServer((req, res) => {
    let d = ''; req.on('data', (c) => (d += c)); req.on('end', () => {
      vistoBridge.push({ metodo: req.method, ruta: req.url, auth: req.headers.authorization, op: req.headers['x-operador'] });
      const clave = (req.method === 'GET' ? 'GET ' : '') + req.url.replace(/^(\/v1\/swe\/tools)\/[^/]+$/, '$1/:id');
      const f = rutas[clave]; if (!f) { res.writeHead(404); return res.end('{}'); }
      const r = { c: 200, status(c) { r.c = c; return r; }, json(o) { res.writeHead(r.c, { 'content-type': 'application/json' }); res.end(JSON.stringify(o)); return r; } };
      f({ headers: req.headers, body: d ? JSON.parse(d) : {}, params: { id: req.url.split('/').pop() }, path: req.url }, r);
    });
  });
  await new Promise((ok) => servidor.listen(0, '127.0.0.1', ok)); base = `http://127.0.0.1:${servidor.address().port}`;
});
after(() => servidor.close());

function handlers(env) {
  const { api, acciones, tools } = apiFalsa(); const guardado = { ...process.env };
  Object.assign(process.env, env); entry.register(api);
  const NOMBRE_TOOL = { capacidades: 'swe_capacidades', tools: 'swe_tools_catalogo', estado: 'swe_estado', tool: 'swe_tool_llamar' };
  const llamar = async (id, payload, source = 'session-action') => {
    Object.assign(process.env, env);
    if (source === 'tool') { const f = tools.get(NOMBRE_TOOL[id]); assert.ok(f, `no hay tool de agente para ${id}`); const r = await f({}).execute('call-1', payload); return r.details ?? JSON.parse(r.content[0].text); }  // como lo llama el modelo
    return (await acciones.get(id).handler({ payload })).result;  // como lo llama la UI nativa (session-action)
  };
  return { llamar, tools, restaurar: () => { for (const k of Object.keys(env)) delete process.env[k]; Object.assign(process.env, guardado); } };
}
test('E2E: capacidades e iniciar llegan al Harness por las rutas reales del bridge con origen openclaw y aprobacion false; la clave nunca vuelve en la respuesta', async () => {
  const h = handlers({ RIU_SWE_BRIDGE_URL: base, BRIDGE_TOKEN: TOKEN });
  try {
    const cap = await h.llamar('capacidades', {});
    assert.equal(cap.ok, true); assert.equal(cap.datos.harness, 'ok'); assert.equal(cap.datos.agentes.codex.estado, 'NO INSTALADO');
    const tarea = armarTarea({ sel: SELECCION_DEFECTO, mensaje: 'hola', task_id: 'oc-e2e-1' });
    const r = await h.llamar('iniciar', tarea);
    assert.equal(r.ok, true, JSON.stringify(r)); assert.equal(r.datos.estado, 'PENDIENTE');
    const enviado = vistoHarness.at(-1); assert.equal(enviado.tool, 'swe_iniciar'); assert.equal(enviado.args.origen, 'openclaw'); assert.equal(enviado.args.aprobacion, false);
    assert.deepEqual(Object.keys(enviado.args).sort(), Object.keys(tarea).sort());
    assert.equal(vistoBridge.at(-1).auth, 'Bearer ' + TOKEN);
    for (const op of ['avanzar', 'estado', 'reanudar']) { const x = await h.llamar(op, { task_id: 'oc-e2e-1' }); assert.equal(x.ok, true, op); assert.equal(vistoHarness.at(-1).tool, 'swe_' + op); }
    assert.ok(!JSON.stringify([cap, r]).includes(TOKEN) && !JSON.stringify([cap, r]).includes(CLAVE_ROUTER));
  } finally { h.restaurar(); }
});
test('E2E: aprobar exige operador real con SU token; el nombre llega al Harness como operador; token ajeno -> 401', async () => {
  const h = handlers({ RIU_SWE_BRIDGE_URL: base, BRIDGE_TOKEN: TOKEN });
  try {
    const mal = await h.llamar('aprobar', { task_id: 'oc-e2e-1', op_id: 'op-1', operador: 'ana', token_operador: 'otro' });
    assert.deepEqual([mal.ok, mal.http, mal.codigo], [false, 401, 'OPERADOR_NO_AUTORIZADO']);
    const bien = await h.llamar('aprobar', { task_id: 'oc-e2e-1', op_id: 'op-1', operador: 'ana', token_operador: TOK_ANA });
    assert.equal(bien.ok, true); assert.equal(vistoHarness.at(-1).args.operador, 'ana'); assert.ok(!JSON.stringify(bien).includes(TOK_ANA));
    assert.ok(![...h.tools.keys()].some((n) => /aprob|iniciar|avanzar|reanudar/.test(n)), 'el agente no tiene tools para aprobar ni para lanzar/avanzar tareas: solo la UI con operador');
  } finally { h.restaurar(); }
});
test('E2E UI3: catalogo de tools y llamada a una tool de lectura por el bridge al Router con la clave del bridge; con efectos y sin operador humano se rechaza', async () => {
  const h = handlers({ RIU_SWE_BRIDGE_URL: base, BRIDGE_TOKEN: TOKEN });
  try {
    const cat = await h.llamar('tools', {});
    assert.equal(cat.ok, true); assert.equal(cat.datos.vivo.router, 'ok'); assert.ok(cat.datos.tools.find((t) => t.id === 'salud').estado === 'DISPONIBLE' && cat.datos.tools.find((t) => t.id === 'agente').estado === 'BLOQUEADA_POR_ROUTER');
    assert.ok(cat.datos.gaps.some((g) => g.id === 'anclaje'));
    const s = await h.llamar('tool', { id: 'salud' }, 'tool');
    assert.equal(s.ok, true); assert.equal(vistoRouter.at(-1).clave, CLAVE_ROUTER);
    const ef = await h.llamar('tool', { id: 'github_escribir', args: { repo: 'r', ruta: 'a', contenido: 'c' } }, 'tool');
    assert.deepEqual([ef.ok, ef.http, ef.codigo], [false, 403, 'OPERADOR_REQUERIDO']);
    const credencialesDelModelo = await h.llamar('tool', { id: 'github_escribir', args: { repo: 'r', ruta: 'a', contenido: 'c' }, operador: 'ana', token_operador: TOK_ANA }, 'tool');
    assert.deepEqual([credencialesDelModelo.ok, credencialesDelModelo.codigo], [false, 'OPERADOR_REQUERIDO'], 'un modelo no puede usar credenciales de operador aunque las ponga en los argumentos');
    const humano = await h.llamar('tool', { id: 'github_escribir', args: { repo: 'r', ruta: 'a', contenido: 'c' }, operador: 'ana', token_operador: TOK_ANA });
    assert.equal(humano.ok, true);
  } finally { h.restaurar(); }
});
test('sin BRIDGE_TOKEN o con URL invalida: codigo estable, sin llamar a nadie; la URL del bridge solo https o http local', async () => {
  const antes = vistoBridge.length;
  const h = handlers({ RIU_SWE_BRIDGE_URL: base, BRIDGE_TOKEN: '' });
  try { const r = await h.llamar('capacidades', {}); assert.deepEqual([r.ok, r.codigo], [false, 'BRIDGE_TOKEN_NO_CONFIGURADO']); } finally { h.restaurar(); }
  assert.equal(vistoBridge.length, antes);
  assert.deepEqual(leerConfig({ RIU_SWE_BRIDGE_URL: 'http://evil.example.com', BRIDGE_TOKEN: 'x' }), { error: 'BRIDGE_URL_INVALIDA' });
  assert.deepEqual(leerConfig({ BRIDGE_TOKEN: 'x' }), { url: 'http://127.0.0.1:7870', token: 'x' });
  const c = crearCliente({ url: base, token: TOKEN }, { fetchFn: async () => { throw new TypeError('connect ECONNREFUSED ' + TOKEN); } });
  const r = await c.estado({ task_id: 'a' }); assert.deepEqual([r.ok, r.codigo], [false, 'BRIDGE_NO_DISPONIBLE']); assert.ok(!JSON.stringify(r).includes(TOKEN));
});
