// swe_rutas.test.mjs — rutas /v1/swe/* del bridge (OpenClaw -> bridge -> Harness DeepSeek). Servidor Harness falso local; sin red real ni claves reales.
import test, { before, after } from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import http from 'node:http';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { montarRutasSwe, llamarHarness, consultarCapacidades, OPERACIONES_SWE, TIMEOUT_HARNESS_MS, TIMEOUT_AVANZAR_MS } from '../src/swe_rutas.js';
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
const OP_TOKEN = 'token-de-operador-de-prueba';
const ENV = { BRIDGE_TOKEN: TOKEN, BRIDGE_OPERATOR_TOKEN: OP_TOKEN, RIU_DEEPSEEK_HARNESS_URL: URL_HARNESS, RIU_API_KEY: CLAVE_HARNESS };
const AUTH = { authorization: 'Bearer ' + TOKEN };
const AUTH_OP = { ...AUTH, 'x-operator-token': OP_TOKEN };

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

test('autenticacion OBLIGATORIA: sin BRIDGE_TOKEN las 5 rutas responden 503 y no llaman al Harness (no heredan el acceso libre de las rutas publicas)', async () => {
  const log = [], app = montar({ RIU_DEEPSEEK_HARNESS_URL: URL_HARNESS, RIU_API_KEY: CLAVE_HARNESS }, harnessOk(log));
  assert.deepEqual(Object.keys(app.rutas).sort(), ['/v1/swe/aprobar', '/v1/swe/avanzar', '/v1/swe/estado', '/v1/swe/iniciar', '/v1/swe/reanudar', 'GET /v1/swe/capacidades']);
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

test('aprobar identifica al operador (cabecera x-operador) y NO confia en el campo aprobacion ni en un operador del cuerpo', async () => {
  let log = [], app = montar(ENV, harnessOk(log));
  const cuerpo = { task_id: 'openclaw-001', origen: 'openclaw', op_id: 'op-0123abcd', aprobacion: true, operador: 'intruso', aprobado_por: 'intruso' };
  let r = await llamar(app, 'aprobar', { body: cuerpo, headers: AUTH_OP });
  assert.equal(r.codigo, 400); assert.equal(r.cuerpo.error.code, 'OPERADOR_REQUERIDO'); assert.equal(log.length, 0, 'sin operador identificado no se aprueba');
  r = await llamar(app, 'aprobar', { body: cuerpo, headers: { ...AUTH_OP, 'x-operador': 'mal operador!' } });
  assert.equal(r.codigo, 400); assert.equal(r.cuerpo.error.code, 'OPERADOR_REQUERIDO');
  r = await llamar(app, 'aprobar', { body: { ...cuerpo, op_id: undefined }, headers: { ...AUTH_OP, 'x-operador': 'antonio.director' } });
  assert.equal(r.codigo, 400); assert.equal(r.cuerpo.error.code, 'OP_ID_INVALIDO');
  r = await llamar(app, 'aprobar', { body: cuerpo, headers: { ...AUTH_OP, 'x-operador': 'antonio.director' } });
  assert.equal(r.codigo, 200);
  const e = JSON.parse(log[0].init.body);
  assert.equal(e.tool, 'swe_aprobar'); assert.deepEqual(e.args, { task_id: 'openclaw-001', origen: 'openclaw', op_id: 'op-0123abcd', operador: 'antonio.director' });
});

test('aprobar exige BRIDGE_OPERATOR_TOKEN distinto del token del bridge (x-operator-token): sin el, 401; sin configurarlo, 503; el BRIDGE_TOKEN no vale como token de operador', async () => {
  const cuerpo = { task_id: 'openclaw-001', origen: 'openclaw', op_id: 'op-0123abcd' }, log = [];
  const app = montar(ENV, harnessOk(log));
  const cab = { ...AUTH, 'x-operador': 'antonio.director' };
  for (const h of [cab, { ...cab, 'x-operator-token': 'otro' }, { ...cab, 'x-operator-token': TOKEN }, { ...cab, 'x-operator-token': OP_TOKEN + 'x' }, { ...cab, 'x-operator-token': '' }]) {
    const r = await llamar(app, 'aprobar', { body: cuerpo, headers: h });
    assert.equal(r.codigo, 401, JSON.stringify(h)); assert.equal(r.cuerpo.error.code, 'OPERADOR_NO_AUTORIZADO');
  }
  assert.equal(log.length, 0, 'sin token de operador no se llega al Harness');
  const sin = montar({ ...ENV, BRIDGE_OPERATOR_TOKEN: undefined }, harnessOk(log));
  const r503 = await llamar(sin, 'aprobar', { body: cuerpo, headers: { ...cab, 'x-operator-token': OP_TOKEN } });
  assert.equal(r503.codigo, 503); assert.equal(r503.cuerpo.error.code, 'OPERATOR_TOKEN_NO_CONFIGURADO');
  const igual = montar({ ...ENV, BRIDGE_OPERATOR_TOKEN: TOKEN }, harnessOk(log));
  assert.equal((await llamar(igual, 'aprobar', { body: cuerpo, headers: { ...cab, 'x-operator-token': TOKEN } })).codigo, 503, 'un token de operador igual al del bridge se considera no configurado');
  assert.equal(log.length, 0);
  assert.equal((await llamar(app, 'aprobar', { body: cuerpo, headers: { ...cab, 'x-operator-token': OP_TOKEN } })).codigo, 200);
  // las demas operaciones NO piden el token de operador
  assert.equal((await llamar(app, 'estado', { body: { task_id: 'a-1' }, headers: AUTH })).codigo, 200);
});

test('aprobar: ya NO hay operador por defecto desde RIU_SWE_OPERADOR; sin cabecera x-operador -> OPERADOR_REQUERIDO aunque el entorno lo traiga', async () => {
  const log = [], app = montar({ ...ENV, RIU_SWE_OPERADOR: 'director-env' }, harnessOk(log));
  const r = await llamar(app, 'aprobar', { body: { task_id: 'openclaw-001', origen: 'openclaw', op_id: 'op-0123abcd' }, headers: AUTH_OP });
  assert.equal(r.codigo, 400); assert.equal(r.cuerpo.error.code, 'OPERADOR_REQUERIDO'); assert.equal(log.length, 0);
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
  const sin = montar({ RIU_DEEPSEEK_HARNESS_URL: URL_HARNESS, RIU_API_KEY: CLAVE_HARNESS }, harnessOk(log));
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
  A = await arrancar('swe-A', { BRIDGE_TOKEN: TOKEN, BRIDGE_OPERATOR_TOKEN: OP_TOKEN, RIU_DEEPSEEK_HARNESS_URL: url, RIU_API_KEY: CLAVE_HARNESS });
  B = await arrancar('swe-B', { RIU_DEEPSEEK_HARNESS_URL: url, RIU_API_KEY: CLAVE_HARNESS });  // sin BRIDGE_TOKEN
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
  const ap = await post(A, 'aprobar', { task_id: 'openclaw-001', op_id: 'op-1', aprobacion: true }, { ...AUTH_OP, 'x-operador': 'antonio.director' });
  assert.equal(ap.status, 200); assert.equal(vistos.at(-1).body.args.operador, 'antonio.director'); assert.ok(!('aprobacion' in vistos.at(-1).body.args));
  assert.ok(!JSON.stringify(r.json).includes(CLAVE_HARNESS));
});

test('server.js: sin token 401 con BRIDGE_TOKEN; SIN BRIDGE_TOKEN las rutas SWE se rechazan (503) aunque las demas rutas sigan abiertas', async () => {
  vistos.length = 0;
  assert.equal((await post(A, 'estado', { task_id: 'a-1' })).status, 401);
  const rB = await post(B, 'estado', { task_id: 'a-1' });
  assert.equal(rB.status, 503, JSON.stringify(rB.json)); assert.equal(rB.json.error.code, 'BRIDGE_TOKEN_NO_CONFIGURADO');
  assert.equal((await post(B, 'iniciar', TAREA, AUTH)).status, 503);
  assert.equal(vistos.length, 0);
  assert.equal((await fetch(B.base + '/health')).status, 200);
});

test('server.js: el montaje es UNA linea de import y UNA de montaje (B edita el SSE en el mismo archivo)', () => {
  const src = fs.readFileSync(path.join(QUI, '..', 'src', 'server.js'), 'utf8');
  assert.equal((src.match(/swe_rutas\.js/g) || []).length, 1);
  assert.equal((src.match(/montarRutasSwe\(/g) || []).length, 1);
  assert.ok(src.indexOf('montarRutasSwe(') > src.indexOf('express.json('), 'se monta despues del parser JSON');
});

test('server.js: GET /v1/swe/capacidades por HTTP real (Bearer o x-bridge-key); sin token 401; sin BRIDGE_TOKEN 503; no es una ruta POST', async () => {
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
  const b = await get(B, AUTH); assert.equal(b.status, 503); assert.equal(b.json.error.code, 'BRIDGE_TOKEN_NO_CONFIGURADO');
  assert.equal(vistos.length, n, 'sin autenticacion no se llama al Harness');
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
