// swe_rutas.js — rutas /v1/swe/{iniciar,avanzar,estado,aprobar,reanudar} y GET /v1/swe/capacidades del bridge (backend de OpenClaw).
// OpenClaw UI -> (aqui) -> Harness DeepSeek (POST {RIU_DEEPSEEK_HARNESS_URL}/invoke) -> agentes/adaptadores. El bridge NO ejecuta herramientas ni adaptadores Python:
// solo valida y reenvia. RIU_API_KEY vive solo en este backend. Contrato de tarea: el mismo de YAIWES (chat-router/agentes/adaptadores/contrato.py, origen "openclaw").
// Autenticacion OBLIGATORIA: sin BRIDGE_TOKEN configurado estas rutas se rechazan (503); no heredan el acceso libre de las rutas publicas con el token vacio.
import { iguales } from './iguales.js';

export const OPERACIONES_SWE = { iniciar: 'swe_iniciar', avanzar: 'swe_avanzar', estado: 'swe_estado', aprobar: 'swe_aprobar', reanudar: 'swe_reanudar' };
const PERMITIDAS = new Set(Object.values(OPERACIONES_SWE));
export const TIMEOUT_HARNESS_MS = 60000;
export const TIMEOUT_AVANZAR_MS = 1800000;  // swe_avanzar / swe_reanudar corren el flujo entero en el Harness (minutos): RIU_SWE_AVANZAR_TIMEOUT_MS
const ORIGEN = 'openclaw';
const TASK_ID = /^[A-Za-z0-9_-]{1,64}$/, SEGMENTO = /^[A-Za-z0-9_-]{0,64}$/, OP_ID = /^[A-Za-z0-9_-]{1,80}$/, OPERADOR = /^[A-Za-z0-9_.@-]{2,64}$/, CODIGO = /^[A-Z][A-Z0-9_]{2,63}$/;
const CAMPOS = ['task_id', 'origen', 'mensaje', 'workflow', 'modelo_responde', 'modelo_lector', 'modelo_tool', 'modelo_revisor', 'agente_responde', 'agente_tool', 'agente_verificador', 'modo_agentico', 'aprobacion', 'sesion', 'proyecto'];
const OBLIGATORIOS = CAMPOS.slice(0, 11);
const MAX_MENSAJE = 200000;

// POST {RIU_DEEPSEEK_HARNESS_URL}/invoke con el cuerpo dado; devuelve cuerpo.result. Los mensajes de error son codigos fijos: jamas llevan la URL ni la clave.
async function postHarness(payload, { env, fetchFn }) {
  const largo = payload.action === 'invoke' && (payload.tool === 'swe_avanzar' || payload.tool === 'swe_reanudar');
  const base = String(env.RIU_DEEPSEEK_HARNESS_URL || '').trim().replace(/\/+$/, ''), clave = env.RIU_API_KEY;
  if (!base || !clave) throw new Error('HARNESS_NO_CONFIGURADO');
  const pos = (v) => (Number.parseInt(v, 10) > 0 ? Number.parseInt(v, 10) : 0);
  const ms = largo ? pos(env.RIU_SWE_AVANZAR_TIMEOUT_MS) || TIMEOUT_AVANZAR_MS : pos(env.RIU_SWE_HARNESS_TIMEOUT_MS) || TIMEOUT_HARNESS_MS;
  const ctl = new AbortController(), t = setTimeout(() => ctl.abort(), ms);
  let r;
  try {
    r = await fetchFn(`${base}/invoke`, { method: 'POST', headers: { 'content-type': 'application/json', 'X-API-Key': clave }, body: JSON.stringify(payload), signal: ctl.signal, redirect: 'error' });
    if (!r.ok) throw new Error(`HARNESS_HTTP_${r.status}`);
    let cuerpo = null;
    try { cuerpo = await r.json(); } catch { /* cuerpo no JSON: fallo de ejecucion */ }
    if (!cuerpo || cuerpo.status !== 'ok' || !cuerpo.result || typeof cuerpo.result !== 'object') {
      throw Object.assign(new Error('HARNESS_EJECUCION_FALLIDA'), typeof (cuerpo && cuerpo.error) === 'string' && CODIGO.test(cuerpo.error) ? { codigo: cuerpo.error } : {});  // solo un codigo estable; texto libre (rutas, trazas) se descarta
    }
    return cuerpo.result;
  } catch (e) {
    if (/^HARNESS_(HTTP_\d+|EJECUCION_FALLIDA)$/.test(e && e.message)) throw e;
    throw new Error(e && (e.name === 'AbortError' || e.name === 'TimeoutError') ? 'HARNESS_TIMEOUT' : 'HARNESS_NO_DISPONIBLE');
  } finally { clearTimeout(t); }
}

// Llama a una operacion SWE del Harness (solo las cinco permitidas).
export async function llamarHarness(operacion, datos, { env = process.env, fetchFn = fetch } = {}) {
  if (typeof operacion !== 'string' || !PERMITIDAS.has(operacion)) throw new Error('OPERACION_NO_PERMITIDA');
  return postHarness({ action: 'invoke', tool: operacion, args: datos }, { env, fetchFn });
}

// ---- capacidades (solo lectura): el `status` del Harness -> result.swe.{agentes,workflows,modelos}, saneado igual que GET /chat/swe/capacidades de YAIWES ----
// El catalogo vive en agentes/adaptadores/modelos.py y el Harness solo emite ids de ese catalogo; aqui no se copia: se descarta lo que no tenga la forma esperada.
const ID_CAP = /^[A-Za-z0-9][A-Za-z0-9._/-]{0,79}$/;
const SECRETO = /(?:sk-(?:sp-)?[A-Za-z0-9_-]{12,}|github_pat_[A-Za-z0-9_]{12,}|gh[pousr]_[A-Za-z0-9]{12,}|hf_[A-Za-z0-9]{20,}|gsk_[A-Za-z0-9]{12,}|nvapi-[A-Za-z0-9_-]{12,})/g;
const GRUPOS = ['agentes', 'workflows', 'modelos'];
export function sanearCapacidades(result) {
  const swe = simple(result) && simple(result.swe) ? result.swe : {}, salida = {};
  for (const g of GRUPOS) {
    salida[g] = {};
    const entradas = simple(swe[g]) ? swe[g] : {};
    for (const [k, v] of Object.entries(entradas)) {
      if (!ID_CAP.test(k) || k.includes('..') || !simple(v) || typeof v.disponible !== 'boolean') continue;
      const e = { disponible: v.disponible };
      if (typeof v.motivo === 'string' && v.motivo) e.motivo = v.motivo.replace(SECRETO, '[REDACTADO]').slice(0, 200);
      if (g === 'agentes' && Array.isArray(v.modelos)) e.modelos = v.modelos.filter((m) => typeof m === 'string' && ID_CAP.test(m) && !m.includes('..'));
      salida[g][k] = e;
    }
  }
  return salida;
}
export async function consultarCapacidades({ env = process.env, fetchFn = fetch } = {}) {
  const vacio = { agentes: {}, workflows: {}, modelos: {} };
  if (!String(env.RIU_DEEPSEEK_HARNESS_URL || '').trim()) return { harness: 'no_configurado', ...vacio };
  if (!env.RIU_API_KEY) return { harness: 'sin_credencial', ...vacio };
  try { return { harness: 'ok', ...sanearCapacidades(await postHarness({ action: 'status' }, { env, fetchFn })) }; }
  catch { return { harness: 'no_disponible', ...vacio }; }
}

const invalido = (code) => Object.assign(new Error(code), { http: 400 });
const simple = (o) => !!o && typeof o === 'object' && !Array.isArray(o);

// iniciar = el contrato TareaSWE exacto (la validacion de catalogo —modelos, agentes, workflow— la hace el contrato Python en el Harness, aqui no se copia el catalogo)
function argsIniciar(b) {
  if (!simple(b)) throw invalido('CONTRATO_INVALIDO');
  if (Object.keys(b).some((k) => !CAMPOS.includes(k))) throw invalido('CAMPOS_DESCONOCIDOS');
  if (typeof b.task_id !== 'string' || !TASK_ID.test(b.task_id)) throw invalido('TASK_ID_INVALIDO');
  if (b.origen !== ORIGEN) throw invalido('ORIGEN_INVALIDO');
  if (OBLIGATORIOS.some((k) => !(k in b))) throw invalido('CAMPOS_FALTANTES');
  if (OBLIGATORIOS.some((k) => typeof b[k] !== 'string')) throw invalido('CONTRATO_INVALIDO');
  if (!b.mensaje.trim()) throw invalido('MENSAJE_VACIO');
  if (b.mensaje.length > MAX_MENSAJE) throw invalido('MENSAJE_DEMASIADO_LARGO');
  if (['modo_agentico', 'aprobacion'].some((k) => k in b && typeof b[k] !== 'boolean')) throw invalido('CONTRATO_INVALIDO');
  if (['sesion', 'proyecto'].some((k) => k in b && (typeof b[k] !== 'string' || !SEGMENTO.test(b[k])))) throw invalido('CONTRATO_INVALIDO');
  const args = {}; for (const k of CAMPOS) if (k in b) args[k] = b[k];
  args.aprobacion = false;  // la aprobacion NO es un campo del cliente ni del modelo: solo swe_aprobar con operador identificado
  return args;
}
// avanzar/estado/reanudar/aprobar: solo la referencia de la tarea; el resto del cuerpo se descarta
function argsReferencia(b) {
  const x = simple(b) ? b : {};
  if (typeof x.task_id !== 'string' || !TASK_ID.test(x.task_id)) throw invalido('TASK_ID_INVALIDO');
  if (x.origen !== undefined && x.origen !== ORIGEN) throw invalido('ORIGEN_INVALIDO');
  const args = { task_id: x.task_id, origen: ORIGEN };
  for (const k of ['sesion', 'proyecto']) if (x[k] !== undefined && x[k] !== '') { if (typeof x[k] !== 'string' || !SEGMENTO.test(x[k])) throw invalido('CONTRATO_INVALIDO'); args[k] = x[k]; }
  return args;
}
// quien aprueba: SOLO la cabecera x-operador (ya no hay operador por defecto en el entorno); el Harness lo valida contra RIU_SWE_OPERADORES
function operadorDe(req) {
  const h = req.headers && req.headers['x-operador'];
  const op = h !== undefined ? String(h) : '';
  if (!OPERADOR.test(op)) throw invalido('OPERADOR_REQUERIDO');  // aprobar exige un operador identificado
  return op;
}

const respuesta = (res, codigo, error) => res.status(codigo).json({ ok: false, error });

// aprobar pide ADEMAS un token propio (BRIDGE_OPERATOR_TOKEN, cabecera x-operator-token), distinto del BRIDGE_TOKEN que usa todo el que habla con el bridge.
function exigirOperador(req, res, env) {
  const op = env.BRIDGE_OPERATOR_TOKEN || '';
  if (!op || op === (env.BRIDGE_TOKEN || '')) return respuesta(res, 503, { code: 'OPERATOR_TOKEN_NO_CONFIGURADO', message: 'aprobar exige BRIDGE_OPERATOR_TOKEN (distinto de BRIDGE_TOKEN)' });
  const t = String((req.headers || {})['x-operator-token'] || '');
  if (!t || !iguales(t, op)) return respuesta(res, 401, { code: 'OPERADOR_NO_AUTORIZADO' });
  return null;
}

// Autenticacion obligatoria compartida por todas las rutas /v1/swe/*: devuelve null si pasa, o la respuesta de rechazo ya enviada.
function exigirToken(req, res, env) {
  const token = env.BRIDGE_TOKEN || '';
  if (!token) return respuesta(res, 503, { code: 'BRIDGE_TOKEN_NO_CONFIGURADO', message: 'las rutas /v1/swe/* exigen BRIDGE_TOKEN en el bridge' });
  const h = req.headers || {}, bearer = /^Bearer\s+(.+)$/i.exec(String(h.authorization || '')), t = (bearer && bearer[1]) || String(h['x-bridge-key'] || '');
  if (!t || !iguales(t, token)) return respuesta(res, 401, { code: 'NO_AUTORIZADO' });
  return null;
}

export function montarRutasSwe(app, { env = process.env, fetchFn = fetch } = {}) {
  // GET /v1/swe/capacidades: solo lectura, sin secretos, misma autenticacion obligatoria. La UI de OpenClaw marca NO DISPONIBLE lo que no figura conectado.
  app.get('/v1/swe/capacidades', async (req, res) => exigirToken(req, res, env) || res.json(await consultarCapacidades({ env, fetchFn })));
  for (const [ruta, operacion] of Object.entries(OPERACIONES_SWE)) {
    app.post(`/v1/swe/${ruta}`, async (req, res) => {
      const rechazo = exigirToken(req, res, env) || (operacion === 'swe_aprobar' ? exigirOperador(req, res, env) : null); if (rechazo) return rechazo;
      let args;
      try {
        args = operacion === 'swe_iniciar' ? argsIniciar(req.body) : argsReferencia(req.body);
        if (operacion === 'swe_aprobar') {
          const op_id = simple(req.body) ? req.body.op_id : undefined;
          if (typeof op_id !== 'string' || !OP_ID.test(op_id)) throw invalido('OP_ID_INVALIDO');
          args = { ...args, op_id, operador: operadorDe(req) };  // operador = quien aprueba segun el servidor; `aprobacion`/`operador` del cuerpo no cuentan
        }
      } catch (e) { return respuesta(res, e.http || 400, { code: e.message }); }
      try { return res.json({ ok: true, resultado: await llamarHarness(operacion, args, { env, fetchFn }) }); }
      catch (e) { return respuesta(res, 502, { code: 'SWE_HARNESS_ERROR', causa: String(e.message).slice(0, 60), ...(e.codigo ? { codigo_harness: e.codigo } : {}) }); }
    });
  }
}
