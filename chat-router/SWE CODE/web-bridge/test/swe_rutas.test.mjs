// swe_rutas.test.mjs — rutas /v1/swe/* del bridge (OpenClaw -> bridge -> Harness DeepSeek). Servidor Harness falso local; sin red real ni claves reales.
import test, { before, after } from 'node:test';
import assert from 'node:assert/strict';
import crypto from 'node:crypto';
import fs from 'node:fs';
import http from 'node:http';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { montarRutasSwe, llamarHarness, consultarCapacidades, sanearCapacidades, ESTADOS_DISPONIBILIDAD, OPERACIONES_SWE, TIMEOUT_HARNESS_MS, TIMEOUT_AVANZAR_MS } from '../src/swe_rutas.js';
import { prepararApp, arrancar, limpiar, registrarMock } from './helpers/bridge_app.mjs';
import './helpers/acceso.mjs';

const QUI = path.dirname(fileURLToPath(import.meta.url));
const CLAVE_HARNESS = 'clave-harness-de-prueba-xyz';
const TOKEN = 'token-del-bridge-de-prueba';
const URL_HARNESS = 'http://harness.invalid';
const CAMPOS = ['task_id', 'origen', 'mensaje', 'workflow', 'modelo_responde', 'modelo_lector', 'modelo_tool', 'modelo_revisor', 'agente_responde', 'agente_tool', 'agente_verificador', 'modo_agentico', 'aprobacion', 'sesion', 'proyecto'];
const TAREA = { task_id: 'openclaw-001', origen: 'openclaw', workflow: 'liquid_mirror', mensaje: 'Revisar y desplegar', modelo_responde: 'hf/lfm2.5-350m', modelo_lector: 'hf/lfm2.5-350m', modelo_tool: 'hf/lfm2.5-350m', modelo_revisor: 'hf/qwen3.5-0.8b', agente_responde: 'openclaw', agente_tool: 'swe-agent', agente_verificador: 'openhands', modo_agentico: true, aprobacion: false, sesion: 'openclaw-001', proyecto: 'swe-code' };

// ---------- doble de express: solo guarda las rutas ----------
const appFalsa = () => { const r = {}; return { rutas: r, post: (p, fn) => { r[p] = fn; }, get: (p, fn) => { r['GET ' + p] = fn; } }; };
const resFalsa = () => { const r = { codigo: 200, cuerpo: null, status(c) { r.codigo = c; return r; }, json(o) { r.cuerpo = o; return r; } }; return r; };
const harnessOk = (log, result = { ok: true, estado: 'PENDIENTE' }) => async (url, init) => { log.push({ url, init }); return { ok: true, status: 200, json: async () => ({ status: 'ok', result }) }; };
const montar = (env, fetchFn) => { const app = appFalsa(); montarRutasSwe(app, { env, fetchFn }); return app; };
const llamar = async (app, ruta, { body = {}, headers = {} } = {}) => { const res = resFalsa(); await app.rutas['/v1/swe/' + ruta]({ headers, body, path: '/v1/swe/' + ruta }, res); return res; };
const OP_TOKEN = 'token-individual-antonio-prueba', OP_BETO = 'token-individual-beto-prueba';
const sha = (t) => crypto.createHash('sha256').update(t).digest('hex');
const APROBADORES = `antonio.director:${sha(OP_TOKEN)},beto:${sha(OP_BETO)}`;  // solo hashes: cada persona tiene su token
const ENV = { BRIDGE_TOKEN: TOKEN, BRIDGE_APROBADORES: APROBADORES, RIU_DEEPSEEK_HARNESS_URL: URL_HARNESS, RIU_API_KEY: CLAVE_HARNESS };
const AUTH = { authorization: 'Bearer ' + TOKEN };
const AUTH_OP = { ...AUTH, 'x-operator-token': OP_TOKEN, 'x-operador': 'antonio.director' };

test('llamarHarness: solo las cinco operaciones; sin base/clave HARNESS_NO_CONFIGURADO; POST /invoke con X-API-Key y {action:"invoke",tool,args}; devuelve result', async () => {
  assert.deepEqual([...Object.entries(OPERACIONES_SWE)], [['iniciar', 'swe_iniciar'], ['avanzar', 'swe_avanzar'], ['estado', 'swe_estado'], ['aprobar', 'swe_aprobar'], ['reanudar', 'swe_reanudar']]);
  const log = [];
  for (const mala of ['guardar', 'llm', 'swe_otra', '', undefined, 'iniciar']) await assert.rejects(() => llamarHarness(mala, {}, { env: ENV, fetchFn: harnessOk(log) }), /OPERACION_NO_PERMITIDA/);
  await assert.rejects(() => llamarHarness('swe_estado', {}, { env: { RIU_API_KEY: CLAVE_HARNESS }, fetchFn: harnessOk(log) }), /HARNESS_NO_CONFIGURADO/);
  await assert.rejects(() => llamarHarness('swe_estado', {}, { env: { RIU_DEEPSEEK_HARNESS_URL: URL_HARNESS }, fetchFn: harnessOk(log) }), /HARNESS_NO_CONFIGURADO/);
  assert.equal(log.length, 0, 'ninguna llamada invalida llega al Harness');
  const r = await llamarHarness('swe_estado', { task_id: 'a-1' }, { env: { ...ENV, RIU_DEEPSEEK_HARNESS_URL: URL_HARNESS + '/' }, fetchFn: harnessOk(log, { estado: 'DONE' }) });
  assert.deepEqual(r, { estado: 'DONE' });
  assert.equal(log[0].url, URL_HARNESS + '/invoke'); assert.equal(log[0].init.method, 'POST');
  assert.equal(log[0].init.headers['X-API-Key'], CLAVE_HARNESS);
  assert.deepEqual(JSON.parse(log[0].init.body), { action: 'invoke', tool: 'swe_estado', args: { task_id: 'a-1' } });
  assert.ok(log[0].init.signal, 'con timeout (AbortSignal)'); assert.equal(TIMEOUT_HARNESS_MS, 60000);
});

test('llamarHarness: HARNESS_HTTP_<status>, HARNESS_EJECUCION_FALLIDA, no disponible y timeout; ningun mensaje trae la URL ni la clave', async () => {
  const f = (impl) => ({ env: ENV, fetchFn: impl });
  await assert.rejects(() => llamarHarness('swe_estado', {}, f(async () => ({ ok: false, status: 502, json: async () => ({}) }))), /^Error: HARNESS_HTTP_502$/);
  await assert.rejects(() => llamarHarness('swe_estado', {}, f(async () => ({ ok: true, status: 200, json: async () => ({ status: 'error', error: 'TASK_ID_INVALIDO' }) }))), (e) => e.message === 'HARNESS_EJECUCION_FALLIDA' && e.codigo === 'TASK_ID_INVALIDO');
  await assert.rejects(() => llamarHarness('swe_estado', {}, f(async () => ({ ok: true, status: 200, json: async () => ({ status: 'error', error: 'Traceback ' + CLAVE_HARNESS }) }))), (e) => e.message === 'HARNESS_EJECUCION_FALLIDA' && !e.codigo);
  await assert.rejects(() => llamarHarness('swe_estado', {}, f(async () => ({ ok: true, status: 200, json: async () => ({ status: 'ok' }) }))), /HARNESS_EJECUCION_FALLIDA/);
  await assert.rejects(() => llamarHarness('swe_estado', {}, f(async () => { throw new TypeError('fetch failed: connect ECONNREFUSED harness.invalid ' + CLAVE_HARNESS); })), (e) => e.message === 'HARNESS_NO_DISPONIBLE');
  await assert.rejects(() => llamarHarness('swe_estado', {}, { env: { ...ENV, RIU_SWE_HARNESS_TIMEOUT_MS: '40' }, fetchFn: (_u, init) => new Promise((_, ko) => init.signal.addEventListener('abort', () => ko(Object.assign(new Error('aborted'), { name: 'TimeoutError' })))) }), (e) => e.message === 'HARNESS_TIMEOUT');
});

test('autenticacion OBLIGATORIA: sin NINGUNA credencial (ni BRIDGE_TOKEN ni clave de acceso) las 5 rutas responden 503 y no llaman al Harness (no heredan el acceso libre de las rutas publicas)', async () => {
  // BRIDGE_TOKEN es opcional: con una clave de acceso configurada (RIU_API_KEY...) ya no es 503 sino 401/200 segun el Bearer (ver sin_variables.test.mjs); 503 = no hay credencial alguna
  const log = [], app = montar({ RIU_DEEPSEEK_HARNESS_URL: URL_HARNESS }, harnessOk(log));
  assert.deepEqual(Object.keys(app.rutas).sort(), ['/v1/swe/aprobar', '/v1/swe/avanzar', '/v1/swe/estado', '/v1/swe/iniciar', '/v1/swe/reanudar', '/v1/swe/tools/:id', 'GET /v1/swe/capacidades', 'GET /v1/swe/tools']);
  for (const ruta of Object.keys(OPERACIONES_SWE)) {
    const r = await llamar(app, ruta, { body: TAREA, headers: AUTH });
    assert.equal(r.codigo, 503, ruta); assert.equal(r.cuerpo.ok, false); assert.equal(r.cuerpo.error.code, 'BRIDGE_TOKEN_NO_CONFIGURADO');
    const sin = await llamar(app, ruta, { body: TAREA });
    assert.equal(sin.codigo, 503, ruta + ' sin cabeceras');
  }
  assert.equal(log.length, 0);
});

test('token faltante o incorrecto 401; Bearer y x-bridge-key valen; el token no se compara por prefijo', async () => {
  const log = [], app = montar(ENV, harnessOk(log));
  for (const h of [{}, { authorization: 'Bearer otro' }, { 'x-bridge-key': 'otro' }, { authorization: 'Bearer ' + TOKEN + 'x' }, { authorization: 'Bearer ' }, { authorization: TOKEN.slice(0, 5) }]) {
    const r = await llamar(app, 'estado', { body: { task_id: 'a-1' }, headers: h }); assert.equal(r.codigo, 401, JSON.stringify(h)); assert.equal(r.cuerpo.error.code, 'NO_AUTORIZADO');
  }
  assert.equal(log.length, 0);
  assert.equal((await llamar(app, 'estado', { body: { task_id: 'a-1' }, headers: AUTH })).codigo, 200);
  assert.equal((await llamar(app, 'estado', { body: { task_id: 'a-1' }, headers: { 'x-bridge-key': TOKEN } })).codigo, 200);
});

test('iniciar: contrato exacto, origen openclaw, aprobacion siempre false, sin campos ajenos; devuelve {ok:true, resultado}', async () => {
  const log = [], app = montar(ENV, harnessOk(log, { ok: true, task_id: 'openclaw-001', estado: 'PENDIENTE' }));
  const r = await llamar(app, 'iniciar', { body: { ...TAREA, aprobacion: true }, headers: AUTH });
  assert.equal(r.codigo, 200); assert.deepEqual(r.cuerpo, { ok: true, resultado: { ok: true, task_id: 'openclaw-001', estado: 'PENDIENTE' } });
  const enviado = JSON.parse(log[0].init.body);
  assert.equal(enviado.tool, 'swe_iniciar'); assert.deepEqual(Object.keys(enviado.args).sort(), [...CAMPOS].sort());
  assert.equal(enviado.args.aprobacion, false, 'la aprobacion no la da el cliente ni el modelo');
  for (const [mal, esperado] of [[{ origen: 'yaiwes' }, 'ORIGEN_INVALIDO'], [{ origen: undefined }, 'ORIGEN_INVALIDO'], [{ task_id: '../x' }, 'TASK_ID_INVALIDO'], [{ task_id: 'x'.repeat(65) }, 'TASK_ID_INVALIDO'], [{ task_id: 5 }, 'TASK_ID_INVALIDO'], [{ estado: 'DONE' }, 'CAMPOS_DESCONOCIDOS'], [{ tool: 'guardar' }, 'CAMPOS_DESCONOCIDOS'], [{ mensaje: '' }, 'MENSAJE_VACIO'], [{ modo_agentico: 'si' }, 'CONTRATO_INVALIDO'], [{ sesion: 'a b' }, 'CONTRATO_INVALIDO'], [{ mensaje: 'x'.repeat(200001) }, 'MENSAJE_DEMASIADO_LARGO']]) {
    const body = { ...TAREA, ...mal }; for (const k of Object.keys(mal)) if (mal[k] === undefined) delete body[k];
    const e = await llamar(app, 'iniciar', { body, headers: AUTH });
    assert.equal(e.codigo, 400, JSON.stringify(mal)); assert.equal(e.cuerpo.error.code, esperado, JSON.stringify(mal));
  }
  const falta = { ...TAREA }; delete falta.agente_tool;
  assert.equal((await llamar(app, 'iniciar', { body: falta, headers: AUTH })).cuerpo.error.code, 'CAMPOS_FALTANTES');
  assert.equal((await llamar(app, 'iniciar', { body: 'texto', headers: AUTH })).codigo, 400);
  assert.equal(log.length, 1, 'solo la primera llamada valida llego al Harness');
});

test('avanzar/estado/reanudar: solo task_id, origen, sesion y proyecto cruzan; aprobacion/operador/op_id/tool del cuerpo se descartan', async () => {
  const log = [], app = montar(ENV, harnessOk(log));
  const sucio = { task_id: 'openclaw-001', origen: 'openclaw', sesion: 'openclaw-001', proyecto: 'swe-code', aprobacion: true, operador: 'intruso', op_id: 'x', reconciliacion: { resultado: 'confirmada' }, tool: 'guardar', max_pasos: 99 };
  for (const [ruta, tool] of [['avanzar', 'swe_avanzar'], ['estado', 'swe_estado'], ['reanudar', 'swe_reanudar']]) {
    log.length = 0;
    const r = await llamar(app, ruta, { body: sucio, headers: AUTH }); assert.equal(r.codigo, 200, ruta);
    const e = JSON.parse(log[0].init.body); assert.equal(e.tool, tool); assert.deepEqual(e.args, { task_id: 'openclaw-001', origen: 'openclaw', sesion: 'openclaw-001', proyecto: 'swe-code' });
  }
  log.length = 0;
  assert.equal((await llamar(app, 'estado', { body: { task_id: 'a-1' }, headers: AUTH })).codigo, 200);
  assert.deepEqual(JSON.parse(log[0].init.body).args, { task_id: 'a-1', origen: 'openclaw' }, 'sin origen en el cuerpo se asume openclaw (es el origen de este bridge)');
  assert.equal((await llamar(app, 'estado', { body: { task_id: 'a-1', origen: 'yaiwes' }, headers: AUTH })).codigo, 400);
  assert.equal((await llamar(app, 'avanzar', { body: { task_id: 'a b' }, headers: AUTH })).cuerpo.error.code, 'TASK_ID_INVALIDO');
  assert.equal(log.length, 1);
});

test('aprobar identifica a un OPERADOR REAL (x-operador + su token individual) y NO confia en aprobacion ni en un operador del cuerpo', async () => {
  let log = [], app = montar(ENV, harnessOk(log));
  const cuerpo = { task_id: 'openclaw-001', origen: 'openclaw', op_id: 'op-0123abcd', aprobacion: true, operador: 'intruso', aprobado_por: 'intruso' };
  const sinNombre = { ...AUTH, 'x-operator-token': OP_TOKEN };
  let r = await llamar(app, 'aprobar', { body: cuerpo, headers: sinNombre });
  assert.equal(r.codigo, 403); assert.equal(r.cuerpo.error.code, 'OPERADOR_REQUERIDO'); assert.equal(log.length, 0, 'sin operador identificado no se aprueba');
  r = await llamar(app, 'aprobar', { body: cuerpo, headers: { ...sinNombre, 'x-operador': 'mal operador!' } });
  assert.equal(r.codigo, 403); assert.equal(r.cuerpo.error.code, 'OPERADOR_REQUERIDO');
  r = await llamar(app, 'aprobar', { body: cuerpo, headers: { ...sinNombre, 'x-operador': 'intruso' } });
  assert.equal(r.codigo, 403); assert.equal(r.cuerpo.error.code, 'OPERADOR_NO_AUTORIZADO', 'operador no registrado');
  r = await llamar(app, 'aprobar', { body: { ...cuerpo, op_id: undefined }, headers: AUTH_OP });
  assert.equal(r.codigo, 400); assert.equal(r.cuerpo.error.code, 'OP_ID_INVALIDO');
  r = await llamar(app, 'aprobar', { body: cuerpo, headers: AUTH_OP });
  assert.equal(r.codigo, 200);
  const e = JSON.parse(log[0].init.body);
  assert.equal(e.tool, 'swe_aprobar'); assert.deepEqual(e.args, { task_id: 'openclaw-001', origen: 'openclaw', op_id: 'op-0123abcd', operador: 'antonio.director' });
  r = await llamar(app, 'aprobar', { body: cuerpo, headers: { ...AUTH, 'x-operador': 'beto', 'x-operator-token': OP_BETO } });
  assert.equal(r.codigo, 200); assert.equal(JSON.parse(log[1].init.body).args.operador, 'beto');
});

test('aprobar: el token de OTRO operador, el BRIDGE_TOKEN o uno vacio no identifican a nadie (401); sin aprobadores configurados 503; las demas rutas no lo piden', async () => {
  const cuerpo = { task_id: 'openclaw-001', origen: 'openclaw', op_id: 'op-0123abcd' }, log = [];
  const app = montar(ENV, harnessOk(log));
  const cab = { ...AUTH, 'x-operador': 'antonio.director' };
  for (const h of [cab, { ...cab, 'x-operator-token': 'otro' }, { ...cab, 'x-operator-token': TOKEN }, { ...cab, 'x-operator-token': OP_BETO }, { ...cab, 'x-operator-token': OP_TOKEN + 'x' }, { ...cab, 'x-operator-token': '' }]) {
    const r = await llamar(app, 'aprobar', { body: cuerpo, headers: h });
    assert.equal(r.codigo, 401, JSON.stringify(h)); assert.equal(r.cuerpo.error.code, 'OPERADOR_NO_AUTORIZADO');
  }
  assert.equal(log.length, 0, 'sin token propio no se llega al Harness');
  for (const valor of [undefined, '', 'antonio.director', 'antonio.director:no-es-hash']) {
    const sin = montar({ ...ENV, BRIDGE_APROBADORES: valor, BRIDGE_OPERATOR_TOKEN: OP_TOKEN }, harnessOk(log));  // el antiguo token compartido ya no cuenta
    const r503 = await llamar(sin, 'aprobar', { body: cuerpo, headers: { ...cab, 'x-operator-token': OP_TOKEN } });
    assert.equal(r503.codigo, 503, String(valor)); assert.equal(r503.cuerpo.error.code, 'APROBADORES_NO_CONFIGURADOS');
  }
  const igual = montar({ ...ENV, BRIDGE_APROBADORES: 'antonio.director:' + sha(TOKEN) }, harnessOk(log));
  assert.equal((await llamar(igual, 'aprobar', { body: cuerpo, headers: { ...cab, 'x-operator-token': TOKEN } })).codigo, 503, 'un token de operador igual al del bridge se considera no configurado');
  assert.equal(log.length, 0);
  assert.equal((await llamar(app, 'aprobar', { body: cuerpo, headers: { ...cab, 'x-operator-token': OP_TOKEN } })).codigo, 200);
  assert.equal((await llamar(app, 'estado', { body: { task_id: 'a-1' }, headers: AUTH })).codigo, 200);
});

test('aprobar: no hay operador por defecto (RIU_SWE_OPERADOR no se usa); sin x-operador -> OPERADOR_REQUERIDO aunque el entorno lo traiga', async () => {
  const log = [], app = montar({ ...ENV, RIU_SWE_OPERADOR: 'director-env' }, harnessOk(log));
  const r = await llamar(app, 'aprobar', { body: { task_id: 'openclaw-001', origen: 'openclaw', op_id: 'op-0123abcd' }, headers: { ...AUTH, 'x-operator-token': OP_TOKEN } });
  assert.equal(r.codigo, 403); assert.equal(r.cuerpo.error.code, 'OPERADOR_REQUERIDO'); assert.equal(log.length, 0);
});

test('llamarHarness: fetch con redirect:"error" (una redireccion del Harness no arrastra la X-API-Key a otro host)', async () => {
  const log = [];
  await llamarHarness('swe_estado', { task_id: 'a-1' }, { env: ENV, fetchFn: harnessOk(log) });
  assert.equal(log[0].init.redirect, 'error');
});

test('un fallo del Harness es 502 SWE_HARNESS_ERROR con la causa tecnica (sin URL ni credenciales) y NUNCA se registran credenciales', async () => {
  const consola = []; const originales = {};
  for (const m of ['log', 'warn', 'error', 'info']) { originales[m] = console[m]; console[m] = (...a) => consola.push(a.join(' ')); }
  try {
    for (const [fetchFn, causa, codigoHarness] of [
      [async () => ({ ok: false, status: 401, json: async () => ({}) }), 'HARNESS_HTTP_401', undefined],
      [async () => ({ ok: true, status: 200, json: async () => ({ status: 'error', error: 'TAREA_NO_ENCONTRADA' }) }), 'HARNESS_EJECUCION_FALLIDA', 'TAREA_NO_ENCONTRADA'],
      [async () => { throw new TypeError('fetch failed http://harness.invalid ' + CLAVE_HARNESS); }, 'HARNESS_NO_DISPONIBLE', undefined]]) {
      const app = montar(ENV, fetchFn);
      const r = await llamar(app, 'estado', { body: { task_id: 'a-1' }, headers: AUTH });
      assert.equal(r.codigo, 502); assert.equal(r.cuerpo.ok, false); assert.equal(r.cuerpo.error.code, 'SWE_HARNESS_ERROR'); assert.equal(r.cuerpo.error.causa, causa); assert.equal(r.cuerpo.error.codigo_harness, codigoHarness);
      const texto = JSON.stringify(r.cuerpo); assert.ok(!texto.includes(CLAVE_HARNESS) && !texto.includes('harness.invalid') && !texto.includes(TOKEN), texto);
    }
    const sinCfg = await llamar(montar({ BRIDGE_TOKEN: TOKEN }, harnessOk([])), 'estado', { body: { task_id: 'a-1' }, headers: AUTH });
    assert.equal(sinCfg.codigo, 502); assert.equal(sinCfg.cuerpo.error.causa, 'HARNESS_NO_CONFIGURADO');
  } finally { for (const m of Object.keys(originales)) console[m] = originales[m]; }
  assert.ok(!consola.join('\n').includes(CLAVE_HARNESS) && !consola.join('\n').includes(TOKEN), 'ni la clave del Harness ni el token salen en logs');
});

// ---------- GET /v1/swe/capacidades (solo lectura): el status del Harness saneado, para la UI de OpenClaw ----------
const SWE_STATUS = { agentes: { opencode: { disponible: true, motivo: '' }, codex: { disponible: false, motivo: 'codex no esta instalado', token: 'no-debe-salir' }, 'claude-code': { disponible: true, motivo: '', modelos: ['nvidia/z-ai/glm-5.3', 7] }, '../raro': { disponible: true }, malo: { disponible: 'si' } },
  workflows: { individual: { disponible: true, motivo: '' }, liquid_mirror: { disponible: false, motivo: 'falta SWECODE_URL_S2 ' + 'x'.repeat(400) } },
  modelos: { 'hf/lfm2.5-350m': { disponible: true, motivo: '' }, 'groq/qwen/qwen3.8-27b': { disponible: false, motivo: 'no figura en GET /models gsk_clavefalsa1234567890' } } };
const leer = async (app, { headers = {} } = {}) => { const res = resFalsa(); await app.rutas['GET /v1/swe/capacidades']({ headers, path: '/v1/swe/capacidades', method: 'GET' }, res); return res; };

test('capacidades: autenticacion OBLIGATORIA igual que /v1/swe/* (503 sin BRIDGE_TOKEN, 401 con token malo) y sin tocar el Harness', async () => {
  const log = [];
  const sin = montar({ RIU_DEEPSEEK_HARNESS_URL: URL_HARNESS }, harnessOk(log));  // sin credencial alguna (BRIDGE_TOKEN es opcional: con una clave de acceso ya no es 503)
  for (const h of [AUTH, {}]) { const r = await leer(sin, { headers: h }); assert.equal(r.codigo, 503); assert.equal(r.cuerpo.error.code, 'BRIDGE_TOKEN_NO_CONFIGURADO'); }
  const con = montar(ENV, harnessOk(log));
  for (const h of [{}, { authorization: 'Bearer otro' }, { 'x-bridge-key': TOKEN + 'x' }]) { const r = await leer(con, { headers: h }); assert.equal(r.codigo, 401, JSON.stringify(h)); assert.equal(r.cuerpo.error.code, 'NO_AUTORIZADO'); }
  assert.equal(log.length, 0);
});

test('capacidades: pide action "status" al Harness (nada de invoke ni tools), con X-API-Key solo en el backend, y devuelve lo mismo que GET /chat/swe/capacidades de YAIWES, saneado y sin secretos', async () => {
  const log = [], app = montar(ENV, harnessOk(log, { servicio: 'deepseek_harness', acciones: ['status', 'invoke', 'llm'], swe: SWE_STATUS }));
  for (const h of [AUTH, { 'x-bridge-key': TOKEN }]) {
    log.length = 0;
    const r = await leer(app, { headers: h });
    assert.equal(r.codigo, 200, JSON.stringify(r.cuerpo));
    assert.equal(log.length, 1); assert.equal(log[0].url, URL_HARNESS + '/invoke'); assert.equal(log[0].init.headers['X-API-Key'], CLAVE_HARNESS);
    assert.deepEqual(JSON.parse(log[0].init.body), { action: 'status' }, 'solo lectura: ni tool ni args');
    assert.deepEqual(Object.keys(r.cuerpo).sort(), ['agentes', 'harness', 'modelos', 'workflows']);
    assert.equal(r.cuerpo.harness, 'ok');
    assert.deepEqual(r.cuerpo.agentes, { opencode: { disponible: true }, codex: { disponible: false, motivo: 'codex no esta instalado' }, 'claude-code': { disponible: true, modelos: ['nvidia/z-ai/glm-5.3'] } });  // sin `token`, sin claves raras, solo ids de modelo validos
    assert.equal(r.cuerpo.workflows.individual.disponible, true); assert.equal(r.cuerpo.workflows.liquid_mirror.disponible, false); assert.ok(r.cuerpo.workflows.liquid_mirror.motivo.length <= 200);
    assert.equal(r.cuerpo.modelos['hf/lfm2.5-350m'].disponible, true); assert.equal(r.cuerpo.modelos['groq/qwen/qwen3.8-27b'].disponible, false);
    const texto = JSON.stringify(r.cuerpo); assert.ok(!texto.includes('gsk_') && !texto.includes('no-debe-salir') && !texto.includes(CLAVE_HARNESS) && !texto.includes(TOKEN) && !texto.includes('harness.invalid'), texto);
  }
});

test('capacidades: sin informe del Harness no inventa nada; estados harness no_configurado / sin_credencial / no_disponible', async () => {
  const vacio = { agentes: {}, workflows: {}, modelos: {} };
  let r = await leer(montar({ BRIDGE_TOKEN: TOKEN, RIU_API_KEY: CLAVE_HARNESS }, harnessOk([])), { headers: AUTH }); assert.deepEqual(r.cuerpo, { harness: 'no_configurado', ...vacio }); assert.equal(r.codigo, 200);
  r = await leer(montar({ BRIDGE_TOKEN: TOKEN, RIU_DEEPSEEK_HARNESS_URL: URL_HARNESS }, harnessOk([])), { headers: AUTH }); assert.deepEqual(r.cuerpo, { harness: 'sin_credencial', ...vacio });
  r = await leer(montar(ENV, async () => { throw new TypeError('fetch failed ' + CLAVE_HARNESS); }), { headers: AUTH }); assert.deepEqual(r.cuerpo, { harness: 'no_disponible', ...vacio });
  r = await leer(montar(ENV, async () => ({ ok: false, status: 502, json: async () => ({}) })), { headers: AUTH }); assert.deepEqual(r.cuerpo, { harness: 'no_disponible', ...vacio });
  r = await leer(montar(ENV, harnessOk([], { servicio: 'deepseek_harness' })), { headers: AUTH }); assert.deepEqual(r.cuerpo, { harness: 'ok', ...vacio }, 'status viejo sin result.swe: lista vacia, no se presume nada conectado');
  r = await leer(montar(ENV, harnessOk([], { servicio: 'deepseek_harness', swe: { error: 'DISPONIBILIDAD_NO_COMPROBADA' } })), { headers: AUTH }); assert.deepEqual(r.cuerpo, { harness: 'ok', ...vacio });
  assert.equal(JSON.stringify(r.cuerpo).includes(CLAVE_HARNESS), false);
});

test('consultarCapacidades exportada: respeta RIU_SWE_HARNESS_TIMEOUT_MS (HARNESS_TIMEOUT -> no_disponible)', async () => {
  const r = await consultarCapacidades({ env: { ...ENV, RIU_SWE_HARNESS_TIMEOUT_MS: '30' }, fetchFn: (_u, init) => new Promise((_, ko) => init.signal.addEventListener('abort', () => ko(Object.assign(new Error('aborted'), { name: 'TimeoutError' })))) });
  assert.equal(r.harness, 'no_disponible');
});

test('164/37: la disponibilidad del Harness conserva los SEIS estados; la lista es la de disponibilidad.py; desconocido o incoherente nunca es DISPONIBLE', () => {
  const py = fs.readFileSync(path.join(QUI, '..', '..', '..', 'agentes', 'adaptadores', 'disponibilidad.py'), 'utf8');
  const reales = [...(/^ESTADOS = \(([^)]*)\)/m.exec(py)[1]).matchAll(/"([^"]+)"/g)].map((m) => m[1]);
  assert.deepEqual([...ESTADOS_DISPONIBILIDAD], reales, 'sin deriva con disponibilidad.py');
  assert.equal(reales.length, 6);
  const r = sanearCapacidades({ swe: {
    agentes: { codex: { disponible: false, estado: 'NO INSTALADO', veredicto: 'NO DISPONIBLE', verificado: true, causa: 'binario_ausente', intentable: false, motivo: 'no instalado' },
      openhands: { disponible: false, estado: 'SIN VERIFICAR', veredicto: 'SIN VERIFICAR', verificado: false, causa: 'comprobacion_fallida' },
      opencode: { disponible: true, estado: 'SIN VERIFICAR' }, 'claude-code': { disponible: true, estado: 'INVENTADO' },
      'swe-agent': { disponible: false, estado: 'NO CONFIGURADO', causa: '../mal', intentable: 'si' }, openclaw: { disponible: true } },
    workflows: { liquid_mirror: { disponible: false, estado: 'NO COMPATIBLE', causa: 'dependencias' } },
    modelos: { 'groq/qwen/qwen3.8-27b': { disponible: false, estado: 'NO DISPONIBLE EN PROVEEDOR', causa: 'ausente_en_get_models', nombre: 'Qwen3.8 27B', proveedor: 'groq', nota: 'x'.repeat(400) },
      'nvidia/z-ai/glm-5.3': { disponible: false, estado: 'SIN VERIFICAR', intentable: true, verificado: false } } } });
  assert.deepEqual([r.agentes.codex.estado, r.agentes.codex.veredicto, r.agentes.codex.causa, r.agentes.codex.intentable, r.agentes.codex.verificado], ['NO INSTALADO', 'NO DISPONIBLE', 'binario_ausente', false, true]);
  assert.deepEqual([r.agentes.openhands.estado, r.agentes.openhands.verificado], ['SIN VERIFICAR', false], 'comprobacion fallida != NO INSTALADO');
  assert.equal(r.agentes.opencode.disponible, false, 'disponible + SIN VERIFICAR es incoherente');
  assert.equal(r.agentes['claude-code'].disponible, false); assert.ok(!('estado' in r.agentes['claude-code']));
  assert.ok(!('causa' in r.agentes['swe-agent']) && !('intentable' in r.agentes['swe-agent']));
  assert.deepEqual(r.agentes.openclaw, { disponible: true }, 'sin estado en el Harness no se inventa uno');
  assert.equal(r.workflows.liquid_mirror.estado, 'NO COMPATIBLE');
  assert.equal(r.modelos['groq/qwen/qwen3.8-27b'].nombre, 'Qwen3.8 27B'); assert.ok(r.modelos['groq/qwen/qwen3.8-27b'].nota.length <= 200);
  assert.deepEqual([r.modelos['nvidia/z-ai/glm-5.3'].estado, r.modelos['nvidia/z-ai/glm-5.3'].intentable], ['SIN VERIFICAR', true]);
});

// ---------- UI3: tools de OpenClaw = funciones del chat Yaiwes por MCP/HTTP al Router (clave del entorno del bridge, nunca en el navegador) ----------
const RUTA_ROUTER = 'http://127.0.0.1:7861', CLAVE_ROUTER = 'clave-router-de-prueba-xyz';
const ENV_T = { ...ENV, RIU_ROUTER_URL: RUTA_ROUTER, RIU_API_KEY: CLAVE_ROUTER };
const routerFalso = (log, { visibles = ['salud', 'github_escribir', 'almacen', 'agente'], http = 200, cuerpo, rpcError } = {}) => async (url, init) => {
  const body = init && init.body ? JSON.parse(init.body) : null;
  log.push({ url, init, body });
  if (http !== 200) return { ok: false, status: http, json: async () => ({ detail: 'Herramienta bloqueada: agentes=false' }) };
  if (url === RUTA_ROUTER + '/mcp' && body.method === 'tools/list') return { ok: true, status: 200, json: async () => ({ jsonrpc: '2.0', id: body.id, result: { tools: visibles.map((name) => ({ name })) } }) };
  if (url === RUTA_ROUTER + '/mcp') return { ok: true, status: 200, json: async () => (rpcError ? { jsonrpc: '2.0', id: body.id, error: { code: -32000, message: rpcError } } : { jsonrpc: '2.0', id: body.id, result: { content: [{ type: 'text', text: '{"ok":true}' }], structuredContent: cuerpo || { ok: true }, isError: false } }) };
  return { ok: true, status: 200, json: async () => ({ status: 'ok', result: cuerpo || { ok: true } }) };
};
const llamarTool = async (app, id, { body = {}, headers = AUTH } = {}) => { const res = resFalsa(); await app.rutas['/v1/swe/tools/:id']({ headers, body, params: { id }, path: '/v1/swe/tools/' + id }, res); return res; };
const listarTools = async (app, headers = AUTH) => { const res = resFalsa(); await app.rutas['GET /v1/swe/tools']({ headers, path: '/v1/swe/tools' }, res); return res; };

test('tools: GET /v1/swe/tools exige BRIDGE_TOKEN y devuelve el catalogo con el estado REAL que el Router da a cada tool (Agentes OFF = no visible)', async () => {
  const log = [];
  const app = montar(ENV_T, routerFalso(log, { visibles: ['salud', 'github_escribir'] }));
  assert.equal((await listarTools(app, {})).codigo, 401);
  assert.equal((await listarTools(montar({ ...ENV_T, BRIDGE_TOKEN: '', RIU_API_KEY: undefined, RIU_ROUTER_API_KEY: CLAVE_ROUTER }, routerFalso(log)))).codigo, 401, 'con una clave de acceso configurada y sin BRIDGE_TOKEN, un Bearer ajeno es 401');
  assert.equal((await listarTools(montar({ ...ENV_T, BRIDGE_TOKEN: '', RIU_API_KEY: undefined }, routerFalso(log)))).codigo, 503, 'sin ninguna credencial 503');
  assert.equal(log.length, 0);
  const r = await listarTools(app);
  assert.equal(r.codigo, 200); assert.equal(r.cuerpo.ok, true); assert.equal(r.cuerpo.vivo.router, 'ok');
  const por = Object.fromEntries(r.cuerpo.tools.map((t) => [t.id, t]));
  assert.equal(por.salud.estado, 'DISPONIBLE'); assert.equal(por.agente.estado, 'BLOQUEADA_POR_ROUTER', 'el Router no la lista: Agentes OFF o conexion apagada');
  assert.ok(r.cuerpo.gaps.some((g) => g.id === 'anclados-navegador') && r.cuerpo.gaps.some((g) => g.id === 'workflow-loop-yaiwes'));
  const txt = JSON.stringify(r.cuerpo); assert.ok(!txt.includes(CLAVE_ROUTER) && !txt.includes(TOKEN) && !txt.includes('127.0.0.1:7861'));
  assert.equal(log[0].init.headers['X-API-Key'], CLAVE_ROUTER); assert.equal(log[0].body.method, 'tools/list'); assert.equal(log[0].init.redirect, 'error');
});

test('tools: sin clave del Router o con el Router caido el catalogo sale igual y marca ROUTER_NO_DISPONIBLE (nada se inventa como disponible)', async () => {
  let r = await listarTools(montar({ ...ENV, RIU_API_KEY: undefined, RIU_ROUTER_URL: RUTA_ROUTER }, routerFalso([])));
  assert.equal(r.cuerpo.vivo.router, 'sin_credencial'); assert.ok(r.cuerpo.tools.filter((t) => t.via !== 'harness').every((t) => t.estado === 'ROUTER_NO_DISPONIBLE'));
  for (const id of ['harness_status', 'workflows']) assert.equal(r.cuerpo.tools.find((t) => t.id === id).estado, 'HARNESS_NO_DISPONIBLE', 'depende del Harness, no del Router');
  r = await listarTools(montar(ENV_T, async () => { throw new TypeError('fetch failed ' + CLAVE_ROUTER); }));
  assert.equal(r.cuerpo.vivo.router, 'no_disponible'); assert.ok(!JSON.stringify(r.cuerpo).includes(CLAVE_ROUTER));
});

test('tools: una tool MCP de solo lectura se reenvia por JSON-RPC tools/call al Router con la clave del entorno; el cuerpo del cliente no puede cambiar tool ni ruta', async () => {
  const log = [], app = montar(ENV_T, routerFalso(log));
  const r = await llamarTool(app, 'salud', { body: { args: { x: 1 }, tool: 'github_escribir', ruta: '/otra', url: 'http://malo' } });
  assert.equal(r.codigo, 200, JSON.stringify(r.cuerpo)); assert.equal(r.cuerpo.ok, true);
  assert.equal(log.length, 1); assert.equal(log[0].url, RUTA_ROUTER + '/mcp'); assert.equal(log[0].init.method, 'POST');
  assert.equal(log[0].init.headers['X-API-Key'], CLAVE_ROUTER);
  assert.deepEqual([log[0].body.jsonrpc, log[0].body.method, log[0].body.params.name, log[0].body.params.arguments], ['2.0', 'tools/call', 'salud', { x: 1 }]);
  assert.ok(!JSON.stringify(r.cuerpo).includes(CLAVE_ROUTER));
  assert.equal((await llamarTool(app, 'no_existe')).codigo, 404);
  assert.equal((await llamarTool(app, '__proto__')).codigo, 404);
  assert.equal((await llamarTool(app, 'salud', { headers: {} })).codigo, 401);
  assert.equal((await llamarTool(app, 'salud', { body: { args: 'no-objeto' } })).codigo, 400);
});

test('tools: lo que tiene EFECTOS exige operador identificado (x-operador + su token) ANTES de llegar al Router; por_accion solo para las acciones con efectos', async () => {
  const log = [], app = montar(ENV_T, routerFalso(log));
  let r = await llamarTool(app, 'github_escribir', { body: { args: { repo: 'r', ruta: 'a', contenido: 'c' } } });
  assert.equal(r.codigo, 403); assert.equal(r.cuerpo.error.code, 'OPERADOR_REQUERIDO');
  r = await llamarTool(app, 'github_escribir', { body: { args: {} }, headers: { ...AUTH, 'x-operador': 'antonio.director', 'x-operator-token': OP_BETO } });
  assert.equal(r.codigo, 401); assert.equal(log.length, 0, 'sin operador verificado no se toca el Router');
  r = await llamarTool(app, 'github_escribir', { body: { args: { repo: 'r', ruta: 'a', contenido: 'c' } }, headers: AUTH_OP });
  assert.equal(r.codigo, 200); assert.equal(log[0].body.params.name, 'github_escribir');
  log.length = 0;
  assert.equal((await llamarTool(app, 'almacen', { body: { accion: 'leer', args: { nombre: 'x' } } })).codigo, 200, 'leer no tiene efectos');
  assert.deepEqual(log[0].body.params.arguments, { nombre: 'x', accion: 'leer' });
  assert.equal((await llamarTool(app, 'almacen', { body: { accion: 'guardar', args: { nombre: 'x', valor: 'y' } } })).codigo, 403);
  assert.equal((await llamarTool(app, 'almacen', { body: { accion: 'borrar_todo' } })).codigo, 400, 'accion fuera del catalogo');
  assert.equal(log.length, 1);
  assert.equal((await llamarTool(app, 'almacen', { body: { accion: 'guardar', args: { nombre: 'x', valor: 'y' } }, headers: AUTH_OP })).codigo, 200);
});

test('tools: plugins HTTP (loop, cola, watchdog, motor_archivos) van por /plugins/{plugin}/call/{accion} con accion validada contra el catalogo', async () => {
  const log = [], app = montar(ENV_T, routerFalso(log, { cuerpo: { estado: 'corriendo' } }));
  let r = await llamarTool(app, 'loop', { body: { accion: 'estado', args: { proceso_id: 'p-1' } } });
  assert.equal(r.codigo, 200); assert.deepEqual(r.cuerpo.resultado, { estado: 'corriendo' });
  assert.equal(log[0].url, RUTA_ROUTER + '/plugins/nct_loop/call/estado'); assert.deepEqual(log[0].body, { proceso_id: 'p-1' });
  assert.equal((await llamarTool(app, 'loop', { body: { accion: 'gobernar', args: { objetivo: 'x' } } })).codigo, 403, 'gobernar lanza procesos: operador');
  assert.equal((await llamarTool(app, 'loop', { body: { accion: '../x' } })).codigo, 400);
  assert.equal((await llamarTool(app, 'loop', { body: {} })).codigo, 400, 'plugin sin accion');
  assert.equal((await llamarTool(app, 'cola', { body: { accion: 'listar' } })).codigo, 200); assert.equal(log.at(-1).url, RUTA_ROUTER + '/plugins/cola50/call/listar');
  assert.equal((await llamarTool(app, 'watchdog', { body: { accion: 'estado' } })).codigo, 200); assert.equal(log.at(-1).url, RUTA_ROUTER + '/plugins/watchdog48/call/estado');
  assert.equal((await llamarTool(app, 'motor_archivos', { body: { accion: 'raiz' } })).codigo, 200); assert.equal(log.at(-1).url, RUTA_ROUTER + '/plugins/motor_archivos/call/raiz');
  assert.equal((await llamarTool(app, 'motor_archivos', { body: { accion: 'transferir', args: { origen: 'a', destino: 'b' } } })).codigo, 403);
});

test('tools: chat_send solo reenvia campos declarados (anclados, constitucion...) a POST /chat/send; harness_status devuelve capacidades saneadas', async () => {
  const log = [], app = montar(ENV_T, routerFalso(log, { cuerpo: { reply: 'hola' } }));
  let r = await llamarTool(app, 'chat_send', { body: { args: { message: 'x', anclados: ['archivo:a'], constitucion: { texto: 'ley' }, tool: 'malo' } }, headers: AUTH_OP });
  assert.equal(r.codigo, 400); assert.equal(r.cuerpo.error.code, 'CAMPOS_DESCONOCIDOS');
  r = await llamarTool(app, 'chat_send', { body: { args: { message: 'x', anclados: ['archivo:a'], constitucion: { texto: 'ley' } } }, headers: AUTH_OP });
  assert.equal(r.codigo, 200); assert.equal(log.at(-1).url, RUTA_ROUTER + '/chat/send'); assert.deepEqual(log.at(-1).body.constitucion, { texto: 'ley' });
  const h = montar(ENV_T, async (url, init) => ({ ok: true, status: 200, json: async () => ({ status: 'ok', result: { swe: { agentes: { codex: { disponible: false, motivo: 'no instalado' } } } } }) }));
  r = await llamarTool(h, 'harness_status');
  assert.equal(r.codigo, 200); assert.equal(r.cuerpo.resultado.agentes.codex.disponible, false);
});

test('tools: errores del Router sin filtrar URL ni clave; 403 del Router (Agentes OFF) se traduce con el nombre del permiso; JSON-RPC error visible; sin clave 503', async () => {
  let app = montar(ENV_T, routerFalso([], { http: 403 }));
  let r = await llamarTool(app, 'salud');
  assert.equal(r.codigo, 403); assert.equal(r.cuerpo.error.code, 'ROUTER_BLOQUEADO'); assert.equal(r.cuerpo.error.permiso, 'agentes=false');
  r = await llamarTool(montar(ENV_T, routerFalso([], { http: 500 })), 'salud');
  assert.equal(r.codigo, 502); assert.equal(r.cuerpo.error.code, 'ROUTER_HTTP_500');
  r = await llamarTool(montar(ENV_T, routerFalso([], { rpcError: 'Herramienta bloqueada: agentes=false ' + CLAVE_ROUTER })), 'salud');
  assert.equal(r.codigo, 502); assert.equal(r.cuerpo.error.code, 'ROUTER_RPC_ERROR'); assert.ok(!JSON.stringify(r.cuerpo).includes(CLAVE_ROUTER), 'el mensaje del Router no arrastra la clave'); assert.match(r.cuerpo.error.message, /agentes=false/);
  r = await llamarTool(montar(ENV_T, async () => { throw new TypeError('connect ECONNREFUSED 127.0.0.1:7861 ' + CLAVE_ROUTER); }), 'salud');
  assert.equal(r.codigo, 502); assert.equal(r.cuerpo.error.code, 'ROUTER_NO_DISPONIBLE'); assert.ok(!JSON.stringify(r.cuerpo).includes('7861') && !JSON.stringify(r.cuerpo).includes(CLAVE_ROUTER));
  r = await llamarTool(montar({ ...ENV, RIU_API_KEY: undefined, RIU_ROUTER_URL: RUTA_ROUTER }, routerFalso([])), 'salud');
  assert.equal(r.codigo, 503); assert.equal(r.cuerpo.error.code, 'ROUTER_NO_CONFIGURADO');
  r = await llamarTool(montar({ ...ENV_T, RIU_ROUTER_URL: 'http://evil.example.com' }, routerFalso([])), 'salud');
  assert.equal(r.codigo, 503); assert.equal(r.cuerpo.error.code, 'ROUTER_URL_INVALIDA');
});

// ---------- integracion: server.js real (express o su stub), Harness falso por HTTP ----------
let harnessFalso, A, B, vistos = [];
before(async () => {
  prepararApp();
  harnessFalso = http.createServer((req, res) => {
    let d = ''; req.on('data', (c) => d += c); req.on('end', () => {
      let body = null; try { body = JSON.parse(d); } catch { /* ignore */ }
      vistos.push({ url: req.url, clave: req.headers['x-api-key'], body });
      res.writeHead(200, { 'content-type': 'application/json' });
      if (body && body.action === 'status') return res.end(JSON.stringify({ status: 'ok', result: { servicio: 'deepseek_harness', acciones: ['status', 'invoke', 'llm'], swe: SWE_STATUS } }));
      res.end(JSON.stringify({ status: 'ok', result: { ok: true, task_id: body && body.args && body.args.task_id, estado: 'PENDIENTE' } }));
    });
  });
  await new Promise((ok) => harnessFalso.listen(0, '127.0.0.1', ok)); registrarMock(harnessFalso);
  const url = `http://127.0.0.1:${harnessFalso.address().port}`;
  A = await arrancar('swe-A', { BRIDGE_TOKEN: TOKEN, BRIDGE_APROBADORES: APROBADORES, RIU_DEEPSEEK_HARNESS_URL: url, RIU_API_KEY: CLAVE_HARNESS });
  B = await arrancar('swe-B', { RIU_DEEPSEEK_HARNESS_URL: url, RIU_API_KEY: CLAVE_HARNESS });  // sin BRIDGE_TOKEN (opcional): la clave de acceso RIU_API_KEY vale como Bearer
});
after(() => limpiar());
const post = async (srv, ruta, body, headers = {}) => { const r = await fetch(srv.base + '/v1/swe/' + ruta, { method: 'POST', headers: { 'content-type': 'application/json', ...headers }, body: JSON.stringify(body) }); return { status: r.status, json: await r.json().catch(() => null) }; };

test('server.js: con BRIDGE_TOKEN las 5 rutas llegan al Harness (X-API-Key solo en el backend) y devuelven {ok:true, resultado}', async () => {
  vistos.length = 0;
  const r = await post(A, 'iniciar', TAREA, AUTH);
  assert.equal(r.status, 200, JSON.stringify(r.json)); assert.deepEqual(r.json, { ok: true, resultado: { ok: true, task_id: 'openclaw-001', estado: 'PENDIENTE' } });
  assert.equal(vistos[0].url, '/invoke'); assert.equal(vistos[0].clave, CLAVE_HARNESS); assert.equal(vistos[0].body.tool, 'swe_iniciar'); assert.equal(vistos[0].body.action, 'invoke');
  for (const [ruta, tool] of [['avanzar', 'swe_avanzar'], ['estado', 'swe_estado'], ['reanudar', 'swe_reanudar']]) {
    const x = await post(A, ruta, { task_id: 'openclaw-001' }, { 'x-bridge-key': TOKEN }); assert.equal(x.status, 200, ruta); assert.equal(vistos.at(-1).body.tool, tool);
  }
  const ap = await post(A, 'aprobar', { task_id: 'openclaw-001', op_id: 'op-1', aprobacion: true }, AUTH_OP);
  assert.equal(ap.status, 200); assert.equal(vistos.at(-1).body.args.operador, 'antonio.director'); assert.ok(!('aprobacion' in vistos.at(-1).body.args));
  assert.ok(!JSON.stringify(r.json).includes(CLAVE_HARNESS));
});

test('server.js: sin token 401 con BRIDGE_TOKEN; SIN BRIDGE_TOKEN (opcional) las rutas SWE piden Bearer = clave de acceso: sin Bearer o con el token ajeno 401, con RIU_API_KEY 200', async () => {
  vistos.length = 0;
  assert.equal((await post(A, 'estado', { task_id: 'a-1' })).status, 401);
  const rB = await post(B, 'estado', { task_id: 'a-1' });
  assert.equal(rB.status, 401, JSON.stringify(rB.json)); assert.equal(rB.json.error.code, 'NO_AUTORIZADO');
  assert.equal((await post(B, 'iniciar', TAREA, AUTH)).status, 401);
  assert.equal(vistos.length, 0);
  const okB = await post(B, 'estado', { task_id: 'a-1' }, { authorization: 'Bearer ' + CLAVE_HARNESS });
  assert.equal(okB.status, 200, JSON.stringify(okB.json)); assert.equal(vistos.at(-1).body.tool, 'swe_estado'); vistos.length = 0;
  assert.equal((await fetch(B.base + '/health')).status, 200);
});

test('server.js: el montaje es UNA linea de import y UNA de montaje (B edita el SSE en el mismo archivo)', () => {
  const src = fs.readFileSync(path.join(QUI, '..', 'src', 'server.js'), 'utf8');
  assert.equal((src.match(/swe_rutas\.js/g) || []).length, 1);
  assert.equal((src.match(/montarRutasSwe\(/g) || []).length, 1);
  assert.ok(src.indexOf('montarRutasSwe(') > src.indexOf('express.json('), 'se monta despues del parser JSON');
});

test('server.js: GET /v1/swe/capacidades por HTTP real (Bearer o x-bridge-key); sin token 401; sin BRIDGE_TOKEN solo vale Bearer = clave de acceso; no es una ruta POST', async () => {
  vistos.length = 0;
  const get = async (srv, headers = {}) => { const r = await fetch(srv.base + '/v1/swe/capacidades', { headers }); return { status: r.status, json: await r.json().catch(() => null) }; };
  const ok = await get(A, AUTH);
  assert.equal(ok.status, 200, JSON.stringify(ok.json)); assert.equal(ok.json.harness, 'ok');
  assert.equal(ok.json.agentes.opencode.disponible, true); assert.equal(ok.json.modelos['groq/qwen/qwen3.8-27b'].disponible, false);
  assert.equal(vistos.at(-1).body.action, 'status'); assert.equal(vistos.at(-1).clave, CLAVE_HARNESS);
  assert.ok(!JSON.stringify(ok.json).includes(CLAVE_HARNESS) && !JSON.stringify(ok.json).includes('gsk_'));
  assert.equal((await get(A, { 'x-bridge-key': TOKEN })).status, 200);
  const n = vistos.length;
  assert.equal((await get(A)).status, 401); assert.equal((await get(A, { authorization: 'Bearer mal' })).status, 401);
  const b = await get(B, AUTH); assert.equal(b.status, 401); assert.equal(b.json.error.code, 'NO_AUTORIZADO');
  assert.equal(vistos.length, n, 'sin autenticacion no se llama al Harness');
  assert.equal((await get(B, { authorization: 'Bearer ' + CLAVE_HARNESS })).status, 200, 'sin BRIDGE_TOKEN, la clave de acceso en Bearer abre capacidades');
  const post = await fetch(A.base + '/v1/swe/capacidades', { method: 'POST', headers: { 'content-type': 'application/json', ...AUTH }, body: '{}' });
  assert.ok(post.status === 404 || post.status === 405, 'solo GET (status ' + post.status + ')');
});

// ---- auditoria 9: avanzar/reanudar ejecutan el flujo entero en el Harness (minutos): timeout largo propio; el resto 60 s ----
test('9: swe_avanzar y swe_reanudar usan RIU_SWE_AVANZAR_TIMEOUT_MS (defecto 1800000); iniciar/estado/aprobar y capacidades siguen en 60 s', async () => {
  assert.equal(TIMEOUT_AVANZAR_MS, 1800000);
  const plazos = []; const real = globalThis.setTimeout;
  globalThis.setTimeout = (fn, ms, ...r) => { if (typeof ms === 'number' && ms >= 1000) plazos.push(ms); return real(fn, ms, ...r); };
  try {
    const f = harnessOk([]);
    const medir = async (op, env = ENV) => { plazos.length = 0; await llamarHarness(op, { task_id: 'a-1', origen: 'openclaw' }, { env, fetchFn: f }); return plazos[0]; };
    assert.equal(await medir('swe_avanzar'), 1800000); assert.equal(await medir('swe_reanudar'), 1800000);
    for (const op of ['swe_iniciar', 'swe_estado', 'swe_aprobar']) assert.equal(await medir(op), 60000, op);
    assert.equal(await medir('swe_avanzar', { ...ENV, RIU_SWE_AVANZAR_TIMEOUT_MS: '900000' }), 900000);
    assert.equal(await medir('swe_reanudar', { ...ENV, RIU_SWE_AVANZAR_TIMEOUT_MS: 'x' }), 1800000, 'valor invalido: defecto');
    assert.equal(await medir('swe_estado', { ...ENV, RIU_SWE_HARNESS_TIMEOUT_MS: '45000' }), 45000, 'RIU_SWE_HARNESS_TIMEOUT_MS sigue mandando en las cortas');
    plazos.length = 0; await consultarCapacidades({ env: ENV, fetchFn: f }); assert.equal(plazos[0], 60000);
  } finally { globalThis.setTimeout = real; }
});

// ---------- REPLICAS de lectura (anclaje, constitucion, contexto) y tool workflows: el Router se simula; el bridge arma el resultado con su calculo propio ----------
const routerChat = (log, { archivos = ['nota.txt', 'bin.dat'], contenido = { 'nota.txt': 'hola mundo', 'bin.dat': Buffer.from([1, 0, 2]) }, caidos = [] } = {}) => async (url, init) => {
  const body = JSON.parse(init.body), ruta = url.slice(RUTA_ROUTER.length);
  log.push({ ruta, body, clave: init.headers['X-API-Key'] });
  const ok = (x) => ({ ok: true, status: 200, json: async () => x });
  if (caidos.includes(ruta) || (ruta === '/mcp' && caidos.includes(body.params.name))) return { ok: false, status: 500, json: async () => ({}) };
  if (ruta === '/plugins/puente_chat/call/archivos') return ok({ status: 'ok', result: { archivos, persistente: true } });
  if (ruta === '/plugins/puente_chat/call/proyecto') return ok({ status: 'ok', result: body.op === 'list' ? { proyectos: [{ project_id: 'p1', anclas: ['enlace:x'] }] } : { ok: true, proyecto: { project_id: body.project_id, items: ['archivo:nota.txt'] } } });
  if (ruta === '/plugins/puente_chat/call/sandbox') return ok({ status: 'ok', result: { sandbox: 'sandbox de ' + body.sesion, encendido: true } });
  if (ruta === '/almacen') { const n = Object.keys(contenido).find((k) => body.nombre.endsWith('/' + k)); return ok({ valor: Buffer.from(contenido[n] ?? '').toString('base64') }); }
  if (ruta === '/mcp' && body.params.name === 'yaiwes_md') return ok({ jsonrpc: '2.0', id: 1, result: { structuredContent: { texto: 'info del proyecto', encendido: true }, isError: false } });
  if (ruta === '/mcp' && body.params.name === 'pendientes') return ok({ jsonrpc: '2.0', id: 1, result: { structuredContent: { pendientes: [{ texto: 'tarea A', hecho: false }, { texto: 'tarea B', hecho: true }] }, isError: false } });
  return ok({ status: 'ok', result: {} });
};

test('replica anclaje: archivos, proyectos (solo list|get) y leer_archivo con la ruta del Router; solo lectura, sin operador, clave del entorno', async () => {
  const log = [], app = montar(ENV_T, routerChat(log));
  let r = await llamarTool(app, 'anclaje', { body: { accion: 'archivos', args: { destino: 'proyecto', project_id: 'p1' } } });
  assert.equal(r.codigo, 200, JSON.stringify(r.cuerpo)); assert.deepEqual(r.cuerpo.resultado, { destino: 'proyecto', project_id: 'p1', archivos: ['nota.txt', 'bin.dat'] });
  assert.deepEqual(log[0].body, { destino: 'proyecto', project_id: 'p1' }); assert.equal(log[0].clave, CLAVE_ROUTER);
  r = await llamarTool(app, 'anclaje', { body: { accion: 'proyectos', args: {} } });
  assert.equal(r.cuerpo.resultado.proyectos[0].project_id, 'p1'); assert.deepEqual(log.at(-1).body, { op: 'list' });
  r = await llamarTool(app, 'anclaje', { body: { accion: 'proyectos', args: { project_id: 'p1', op: 'delete' } } });
  assert.deepEqual(log.at(-1).body, { op: 'get', project_id: 'p1' }, 'el cuerpo del cliente no cambia la op: nunca upsert/delete');
  r = await llamarTool(app, 'anclaje', { body: { accion: 'leer_archivo', args: { nombre: 'nota.txt', destino: 'constitucion' } } });
  assert.equal(r.codigo, 200, JSON.stringify(r.cuerpo)); assert.deepEqual(r.cuerpo.resultado, { nombre: 'nota.txt', destino: 'constitucion', binario: false, bytes: 10, texto: 'hola mundo', truncado: false });
  assert.equal(log.at(-1).ruta, '/almacen'); assert.deepEqual(log.at(-1).body, { accion: 'leer', destino: 'hf', nombre: 'chat_archivos/509e21d6a3cc/nota.txt' });
  r = await llamarTool(app, 'anclaje', { body: { accion: 'leer_archivo', args: { nombre: 'bin.dat' } } });
  assert.deepEqual([r.cuerpo.resultado.binario, r.cuerpo.resultado.bytes, 'texto' in r.cuerpo.resultado], [true, 3, false]);
  assert.ok(!JSON.stringify(log.map((x) => x.body)).includes(TOKEN));
});

test('replica anclaje: nombre fuera del indice del Router, con ruta o espacio invalido se rechaza ANTES de leer el almacen; accion desconocida, 400', async () => {
  const log = [], app = montar(ENV_T, routerChat(log));
  for (const [args, codigo, http] of [[{ nombre: 'otro.txt' }, 'ARCHIVO_NO_ENCONTRADO', 404], [{ nombre: '../secreto' }, 'NOMBRE_INVALIDO', 400], [{ nombre: 'a/b.txt' }, 'NOMBRE_INVALIDO', 400], [{ nombre: 'nota.txt', destino: 'raiz' }, 'ESPACIO_INVALIDO', 400], [{ nombre: 'nota.txt', sesion: '../x' }, 'ESPACIO_INVALIDO', 400]]) {
    const r = await llamarTool(app, 'anclaje', { body: { accion: 'leer_archivo', args } });
    assert.deepEqual([r.codigo, r.cuerpo.error.code], [http, codigo], JSON.stringify(args));
  }
  assert.ok(!log.some((x) => x.ruta === '/almacen'), 'nada llego al almacen');
  assert.equal((await llamarTool(app, 'anclaje', { body: { accion: 'borrar', args: {} } })).cuerpo.error.code, 'ACCION_NO_PERMITIDA');
  assert.equal((await llamarTool(app, 'anclaje', { body: { args: {} } })).cuerpo.error.code, 'ACCION_REQUERIDA');
  assert.equal((await llamarTool(app, 'anclaje', { body: { accion: 'proyectos', args: { project_id: '../x' } } })).cuerpo.error.code, 'PROYECTO_INVALIDO');
});

test('replica constitucion: la oficial sale del archivo local aunque el Router este caido; los archivos de constitucion usan destino constitucion y sesion "constitucion" por defecto', async () => {
  const log = [], app = montar(ENV_T, routerChat(log));
  let r = await llamarTool(app, 'constitucion', { body: { accion: 'oficial' } });
  assert.equal(r.codigo, 200); assert.equal(r.cuerpo.resultado.id, 'CONSTITUCION-YAIWES'); assert.match(r.cuerpo.resultado.sha256, /^[0-9a-f]{64}$/); assert.ok(r.cuerpo.resultado.texto.includes('FAIL_CLOSED'));
  assert.equal(log.length, 0, 'la oficial es una lectura local');
  r = await llamarTool(montar({ ...ENV_T, RIU_API_KEY: undefined }, routerChat([])), 'constitucion', { body: { accion: 'oficial' } });
  assert.equal(r.codigo, 200, 'sin clave del Router tambien funciona');
  r = await llamarTool(montar({ ...ENV_T, RIU_CONSTITUCION_PATH: '/no/existe.json' }, routerChat([])), 'constitucion', { body: { accion: 'oficial' } });
  assert.deepEqual([r.codigo, r.cuerpo.error.code], [404, 'CONSTITUCION_NO_ENCONTRADA']); assert.ok(!JSON.stringify(r.cuerpo).includes('/no/existe'));
  r = await llamarTool(app, 'constitucion', { body: { accion: 'archivos', args: { destino: 'chat', sesion: 'x' } } });
  assert.deepEqual(log.at(-1).body, { destino: 'constitucion', sesion: 'x' }, 'el destino queda fijado a constitucion');
  r = await llamarTool(app, 'constitucion', { body: { accion: 'archivos', args: {} } });
  assert.deepEqual(r.cuerpo.resultado, { destino: 'constitucion', sesion: 'constitucion', archivos: ['nota.txt', 'bin.dat'] });
});

test('replica contexto: arma las capas CONSTITUCION + yaiwes.md + SANDBOX + PENDIENTES; una capa caida queda ausente sin tirar las demas', async () => {
  const log = [], app = montar(ENV_T, routerChat(log));
  let r = await llamarTool(app, 'contexto', { body: { accion: 'fijo', args: { sesion: 's1' } } });
  assert.equal(r.codigo, 200, JSON.stringify(r.cuerpo)); const c = r.cuerpo.resultado;
  assert.deepEqual(c.capas.map((x) => x.presente), [true, true, true, true]);
  assert.ok(c.texto.includes('info del proyecto') && c.texto.includes('sandbox de s1') && c.texto.includes('- [ ] tarea A') && c.texto.includes('- [x] tarea B') && c.texto.includes('FAIL_CLOSED'));
  assert.equal(c.constitucion.version, '1.1.0'); assert.ok(!('texto' in c.constitucion));
  assert.deepEqual(log.find((x) => x.ruta === '/plugins/puente_chat/call/sandbox').body, { sesion: 's1' }, 'sin `texto`: solo lectura');
  assert.deepEqual(log.filter((x) => x.ruta === '/mcp').map((x) => [x.body.params.name, x.body.params.arguments]).sort(), [['pendientes', { accion: 'listar' }], ['yaiwes_md', { accion: 'leer' }]]);
  r = await llamarTool(montar(ENV_T, routerChat([], { caidos: ['yaiwes_md', '/plugins/puente_chat/call/sandbox'] })), 'contexto', { body: { accion: 'fijo' } });
  assert.deepEqual(r.cuerpo.resultado.capas.map((x) => x.presente), [true, false, false, true]);
  assert.equal((await llamarTool(app, 'contexto', { body: { accion: 'fijo', args: { sesion: 'a/b' } } })).cuerpo.error.code, 'ESPACIO_INVALIDO');
});

test('tool workflows: devuelve solo los workflows del Harness (con su estado) y no los agentes ni los modelos; sin Harness, "no_configurado" y vacio', async () => {
  const fetchFn = async (url, init) => ({ ok: true, status: 200, json: async () => ({ status: 'ok', result: { swe: { agentes: { codex: { disponible: true } }, workflows: { individual: { disponible: true }, liquid_mirror: { disponible: false, motivo: 'falta SWECODE_URL_S2' } }, modelos: { 'hf/lfm2.5-350m': { disponible: true } } } } }) });
  let r = await llamarTool(montar(ENV, fetchFn), 'workflows');
  assert.equal(r.codigo, 200, JSON.stringify(r.cuerpo)); assert.deepEqual(Object.keys(r.cuerpo.resultado).sort(), ['harness', 'workflows']);
  assert.equal(r.cuerpo.resultado.workflows.liquid_mirror.disponible, false); assert.equal(r.cuerpo.resultado.workflows.individual.disponible, true);
  r = await llamarTool(montar({ BRIDGE_TOKEN: TOKEN }, fetchFn), 'workflows');
  assert.deepEqual(r.cuerpo.resultado, { harness: 'no_configurado', workflows: {} });
});

test('catalogo: las replicas aparecen con su estado (anclaje/contexto dependen de la tool MCP que el Router lista; constitucion, del archivo local) y ninguna pide operador', async () => {
  const log = [], app = montar(ENV_T, routerFalso(log, { visibles: ['almacen', 'yaiwes_md'] }));
  const por = Object.fromEntries((await listarTools(app)).cuerpo.tools.map((t) => [t.id, t]));
  assert.equal(por.anclaje.estado, 'DISPONIBLE'); assert.equal(por.contexto.estado, 'DISPONIBLE'); assert.equal(por.constitucion.estado, 'SIN_VERIFICAR');
  const sin = Object.fromEntries((await listarTools(montar(ENV_T, routerFalso([], { visibles: ['salud'] })))).cuerpo.tools.map((t) => [t.id, t]));
  assert.equal(sin.anclaje.estado, 'BLOQUEADA_POR_ROUTER');
  const falta = Object.fromEntries((await listarTools(montar({ ...ENV_T, RIU_CONSTITUCION_PATH: '/no/existe.json' }, routerFalso([])))).cuerpo.tools.map((t) => [t.id, t]));
  assert.equal(falta.constitucion.estado, 'CONSTITUCION_NO_ENCONTRADA');
  for (const id of ['anclaje', 'constitucion', 'contexto']) assert.equal(por[id].efectos, 'lectura');
});
