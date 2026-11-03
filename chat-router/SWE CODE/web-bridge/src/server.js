// server.js — endpoint OpenAI-compatible del puente web (SWEN CODE free)
// POST /v1/chat/completions {model, messages, modo?, conv_id?}
//   model: web-dsv4-flash | web-qwen37max | web-qwen38max | swecode-<modo>
//   swecode-consulta/plan -> fan-out 3 modelos + sintesis Qwen3.8Max
//   otros modos -> objetivo unico (qwen38max por defecto)
// Errores tipados: SESSION_EXPIRED | SELECTOR_BROKEN | CF_CHALLENGE | RATE_LIMITED
import express from 'express';
import { createRequire } from 'node:module';
import { consultarWeb, salud } from './motor.js';
import { consenso } from './consenso.js';
import { consultarClaude, estadoClaude, esCuotaClaude, CLAUDE_MODEL } from './claude_gateway.js';
import { modoValido } from './modos.js';
import { estadoCuentas, estadoTabs, snapshotTab, diagnosticoAcceso, reiniciarSitioInactivo, cerrarPagina, cerrarTodo } from './browser.js';
import { registrarGap, listarGaps, gapPorId, investigarConOpenClaw } from './autoreparacion.js';
import { MODELOS_WEB } from './sites.js';
import path from 'node:path';
import crypto from 'node:crypto';
import { iguales } from './iguales.js';
import { clavesAcceso, claveAccesoDe } from './acceso.js';
import { aplicarDefectos } from './defaults.js';
import { pool, cuentaActual, setCuentas } from './cuentas.js';
import nodeFs from 'node:fs';
import { vigilarWorkspace, vigilarModelosOpenClaw, rutaWorkspace, configVigente, vigilarConfig, espejo, normalizarEjecutor } from './openclaw.js';
import { respaldo, externo, local, esExterno, esLocal, idsRespaldo, estadoRespaldo, estadoMetricas, disponibilidad, disponibilidadLocal, estadosModelosLocales, modeloDefecto, setClaves, limpiarClaves } from './respaldo.js';
import { listarCheckpoints, registrarLeccion, proponerMejoras, checkpointCrudo, checkpointGuardar } from './bloques.js';
import { retomarLocal, retomarPorId, TIPO as TIPO_LOCAL } from './retomar_local.js';
import { idValido as tareaIdValido } from './checkpoint_hf.js';
import { conFormato } from './formato.js';
import { promptHerramientasWeb, extraerLlamadasWeb } from './web_tools.js';
import { estadoContexto, registrarContexto, transferirContexto, tarjetaHandoff } from './contexto_handoff.js';
import { montarAccionesOpenAI } from './openai_acciones.js';
import { guardarTurno, leerTurnos } from './memoria.js';
import { vigilarActualizacion } from './autoactualizar.js';
import { cargarDelBanco, guardarEnBanco, borrarDelBanco, vigilarBanco, diagnosticoBanco, resumenBanco, catalogoProveedores, anadirProveedor } from './clavesbanco.js';
import { publicarEnGithub, traerDeGithub } from './bancogithub.js';
import { guardarAsesoria, leerProyecto, listarProyectos } from './proyectos.js';
import { preambulo } from './modos.js';
import { montarRutasSwe } from './swe_rutas.js';
import { montarResponses } from './responses.js';
import { conSystemPrompt, conSystemPromptTexto, consultarPromptRouter } from './systemprompt.js';

// sin variables nuevas en Hugging Face: SWECODE_URL_S1..S3 y RIU_DEEPSEEK_HARNESS_URL (Harness local del Space) toman su default SOLO si no estan definidas (src/defaults.js)
aplicarDefectos(process.env);

// gramatica "SWEN CODE free ..." (SWE CODE free/activar.js): elige modelo, modo y seccion desde el propio mensaje
let activar = null;
try { activar = createRequire(import.meta.url)(process.env.RIU_ACTIVAR_PATH || '../../../SWE CODE free/activar.js').activar; } catch { console.warn('[bridge] sin activar.js: la gramatica SWEN CODE free queda desactivada (ruta o RIU_ACTIVAR_PATH)'); }
const IDS_DIRECTOS = (id) => /^(groq\/|nvidia\/|deepseek\/|minimax\/|openai\/|lfm2\.5|qwen2\.5-coder|qwen3\.5|qwen3-0\.6b|web-|swecode-)/.test(id);

// Groq/NVIDIA/locales con un modo (p. ej. despliega): reciben el preambulo de ese modo, como el agente que despliega
// system-prompt-on (toggle ON/OFF via /v1/system-prompt-on, defecto ON): si esta ON y la ficha del Router MVP tiene contenido, se fusiona/antepone (systemprompt.js)
const conPreambulo = (msgs, m, forzarOn = false) => conSystemPrompt(m && modoValido(m) ? [{ role: 'system', content: preambulo(m) }, ...msgs] : msgs, process.env, { forzarOn });

// acceso: TODAS las rutas (salvo /health) exigen una de las 4 claves de acceso del chat (x-api-key o Authorization: Bearer <clave>) o BRIDGE_TOKEN (Authorization: Bearer / x-bridge-key / x-api-key).
// BRIDGE_TOKEN es OPCIONAL: el provider de OpenClaw puede usar api_key = clave de acceso. Sin ninguna configurada el bridge responde 503 (ya no queda abierto)
const TOKEN = process.env.BRIDGE_TOKEN || '';
const cab = (req, n) => String((req.headers && req.headers[n]) || '');
const conAcceso = (req) => !!claveAccesoDe(req);  // clave de acceso del chat en x-api-key o Bearer (tiempo constante)
const conToken = (req) => { if (!TOKEN) return false; const t = cab(req, 'authorization').replace(/^Bearer\s+/i, '') || cab(req, 'x-bridge-key') || cab(req, 'x-api-key'); return !!t && iguales(t, TOKEN); };
// propietario autenticado (128-130): hash (nunca la clave) de la clave de acceso del chat o del BRIDGE_TOKEN con que se hizo la peticion. Otra clave = otro propietario.
const propietarioDe = (req) => {
  const k = claveAccesoDe(req) || (conToken(req) ? TOKEN : '');
  return k ? `p-${crypto.createHash('sha256').update('riu-propietario\u0000' + k).digest('hex').slice(0, 24)}` : null;
};
const sinCorreos = (o) => JSON.parse(JSON.stringify(o ?? null, (k, v) => (k === 'email' ? undefined : v)));
const textoDe = (c) => (typeof c === 'string' ? c : Array.isArray(c) ? c.map(p => (typeof p === 'string' ? p : p && typeof p.text === 'string' ? p.text : '')).filter(Boolean).join('\n') : '');
const MAX_PROMPT = parseInt(process.env.BRIDGE_MAX_PROMPT || '400000', 10), MAX_DOCS = 10;

const app = express();
app.set('strict routing', true);          // '/v1/claves/' ya no es '/v1/claves'
app.set('case sensitive routing', true);  // '/V1/CLAVES' tampoco
app.use((req, res, next) => {
  if (req.path === '/health') return next();
  if (!TOKEN && !clavesAcceso().length) return res.status(503).json({ error: { code: 'SIN_CLAVE_DE_ACCESO', message: 'el bridge no tiene clave de acceso configurada (RIU_API_KEY, o BRIDGE_TOKEN)' } });
  return conToken(req) || conAcceso(req) ? next() : res.status(401).json({ error: { code: 'NO_AUTORIZADO', message: 'falta o es invalida la clave de acceso (x-api-key o Authorization: Bearer) o el token del bridge' } });
});
// panel de claves del chat (el proxy del Space reenvia /web/* aqui): ademas exige la clave de acceso del chat en x-api-key. La ruta se normaliza (minusculas, sin barras
// dobles ni finales, sin /./) para que ninguna variante salte la puerta, aunque el enrutado ya sea estricto
const rutaNorm = (p) => { let x = String(p || ''); try { x = decodeURIComponent(x); } catch { /* tal cual */ } return path.posix.normalize(x).toLowerCase().replace(/\/+$/, ''); };
const PROTEGIDAS = ['/v1/claves', '/v1/credenciales', '/v1/openclaw'];
app.use((req, res, next) => {
  const r = rutaNorm(req.path);
  if (!PROTEGIDAS.some(p => r === p || r.startsWith(p + '/'))) return next();
  if (req.method === 'GET' && req.path === '/v1/openclaw' && conToken(req)) return next();  // config de OpenClaw (solo lectura, sin secretos): tambien con BRIDGE_TOKEN. /v1/claves sigue exigiendo la clave de acceso
  if (!clavesAcceso().length) return res.status(503).json({ error: { code: 'SIN_CLAVE_DE_ACCESO', message: 'el bridge no tiene clave de acceso configurada (RIU_API_KEY)' } });
  return conAcceso(req) ? next() : res.status(401).json({ error: { code: 'NO_AUTORIZADO', message: 'falta o es invalida la clave de acceso (x-api-key o Authorization: Bearer)' } });
});
app.use(express.json({ limit: '10mb' }));
montarAccionesOpenAI(app,propietarioDe);
app.get('/v1/claude/estado',async(_req,res)=>{
  // Estado sin direcciones de correo ni tokens, disponible para todas las UI.
  const e=await estadoClaude();
  res.json(e);
}); // OpenAI API explícita, no chatGPT subscripción
// Handoff: rutas autenticadas para recuperación entre selector/modelos/conv_id.
// Sin clave de acceso no se consulta ni se transfiere el contexto de otro usuario.
app.get('/v1/contexto/:id', (req,res) => {
  const r=estadoContexto(req.params.id,propietarioDe(req));
  return r ? res.json({ok:true,contexto:r}) :
    res.status(404).json({ok:false,error:{code:'CONTEXTO_NO_ENCONTRADO'}});
});
app.post('/v1/contexto/transferir', (req,res) => {
  const a=req.body?.origen,b=req.body?.destino;
  if (!/^[A-Za-z0-9_-]{1,80}$/.test(String(a||'')) || !/^[A-Za-z0-9_-]{1,80}$/.test(String(b||'')) || a===b)
    return res.status(400).json({ok:false,error:{code:'CONTEXTO_ID_INVALIDO'}});
  const ok=transferirContexto(a,b,propietarioDe(req));
  return ok ? res.json({ok:true,origen:a,destino:b}) :
    res.status(409).json({ok:false,error:{code:'CONTEXTO_NO_EXISTE_O_DESTINO_OCUPADO'}});
});

const PORT = process.env.BRIDGE_PORT || 7870;
montarResponses(app);  // POST /v1/responses (Codex): traduce a /v1/chat/completions
montarRutasSwe(app);  // /v1/swe/{iniciar,avanzar,estado,aprobar,reanudar} -> Harness DeepSeek; exigen una clave de acceso (Bearer) o BRIDGE_TOKEN

// tarea_id derivado: <conv_id (max 51)>-<sha256([modelo, modo, mensajes]) 12 hex> -> <= 64 y solo [A-Za-z0-9_-]
// con propietario el hash lo incluye: dos usuarios con el mismo conv_id y los mismos mensajes obtienen tareas distintas
const tareaDerivada = (conv, modelo, modo, mensajes, propietario = null) => `${String(conv).slice(0, 51)}-${crypto.createHash('sha256').update(JSON.stringify(propietario ? [modelo, modo ?? null, mensajes, propietario] : [modelo, modo ?? null, mensajes])).digest('hex').slice(0, 12)}`;
// codigo de error -> HTTP (tareas): ajena 403, contexto/otra tarea/corrupta/plan 409
const HTTP_TAREA = { TAREA_AJENA: 403, TAREA_OTRO_CONTEXTO: 409, CHECKPOINT_OTRA_TAREA: 409, VERIFICAR_HERRAMIENTAS_PENDIENTES: 409, CHECKPOINT_CORRUPTO: 409, PLAN_REQUERIDO: 409, OPERACION_NO_PREVISTA: 409 };
// usage OpenAI desde result.metricas (prompt/completion/total tokens reales del proveedor); sin ellos, ceros como siempre
const usageDe = (m) => { const n = (v) => (Number.isFinite(Number(v)) && v !== null ? Number(v) : 0); const p = n(m?.prompt_tokens), c = n(m?.completion_tokens); return { prompt_tokens: p, completion_tokens: c, total_tokens: m && Number.isFinite(Number(m.total_tokens)) && m.total_tokens !== null ? Number(m.total_tokens) : p + c }; };
const esConsenso = (modo) => ['consulta', 'plan'].includes(modo);
// Catálogo REAL del Router para cuando la UI manda Tools ON.
// No se crea ninguna tool nueva, nunca ejecuta herramientas y no conecta a servidores arbitrarios.
async function toolsDeRouter() {
  const key=String(process.env.RIU_API_KEY||process.env.RIU_PUBLIC_CHAT_KEY||'').trim();
  if(!key)return [];
  const puerto=String(process.env.PORT||'7861');
  if(!/^\d{2,5}$/.test(puerto)||+puerto>65535)return [];
  try {
    const r=await fetch('http://127.0.0.1:'+puerto+'/mcp',{
      method:'POST',signal:AbortSignal.timeout(9000),redirect:'error',
      headers:{'content-type':'application/json','x-api-key':key},
      body:JSON.stringify({jsonrpc:'2.0',id:'swen_catalogo',method:'tools/list'})
    });
    if(!r.ok)return [];
    const j=await r.json();
    const items=j?.result?.tools;
    if(!Array.isArray(items))return [];
    return items.filter(x=>x&&typeof x.name==='string'&&/^[A-Za-z_][A-Za-z0-9_.-]{0,100}$/.test(x.name)&&
      x.inputSchema&&typeof x.inputSchema==='object').slice(0,24).map(x=>({
      type:'function',function:{name:x.name,description:String(x.description||'').slice(0,320),
        parameters:x.inputSchema}
    }));
  }catch{return []}
}

const OBJETIVO_UNICO = process.env.SWECODE_OBJETIVO || 'qwen38max';
// fallback dentro de la web antes de escalar a modelos locales
const WEB_FALLBACK = (process.env.WEB_FALLBACK || 'qwen38max,qwen37max,dsv4-flash').split(',');

// deadline duro por request: nunca colgar >120s (proxy/cliente). Devuelve 504 JSON.
const DEADLINE_MS = parseInt(process.env.BRIDGE_DEADLINE_MS || '100000', 10);
// SOLO modelos HF GGUF: el manager remoto puede descargar el archivo y arrancar
// llama-server en frío. SSE keepalive mantiene la conexión dentro del mismo router.
const HF_LOCAL_DEADLINE_MS = Math.max(DEADLINE_MS, 430000);
// latido (opcional, streaming): objeto cuyo .fn reinicia el plazo; cada fragmento recibido cuenta como actividad (el plazo pasa a ser de inactividad)
function conDeadline(p, ms, latido) {
  let t;
  const to = new Promise((_, rej) => { const armar = () => { clearTimeout(t); t = setTimeout(() => rej(Object.assign(new Error(`sin respuesta en ${ms}ms`), { code: 'UPSTREAM_TIMEOUT' })), ms); }; armar(); if (latido) latido.fn = armar; });
  return Promise.race([p, to]).finally(() => clearTimeout(t));
}

async function conFallback(modelo, prompt, opts) {
  const orden = [modelo, ...WEB_FALLBACK.filter(m => m !== modelo)];
  let ultimo;
  for (const m of orden) {
    try { return { salida: await consultarWeb(m, prompt, opts), usado: m }; }
    catch (e) { if (e.code === 'SESSION_EXPIRED' || e.code === 'CUENTAS_FALTAN') throw e; ultimo = e; }  // un fallo de sesion/cuentas no se disfraza con el error del ultimo modelo
  }
  throw ultimo;
}

app.get('/health', async (req, res) => {
  let poolInfo;
  try {
    const n = pool().length;
    let idx = null; try { idx = cuentaActual().index; } catch {}
    poolInfo = { total: n, loaded: true, indices: [...Array(n).keys()], actual: idx };
  } catch { poolInfo = { total: 0, loaded: false, error: 'WEB_ACCOUNTS_VACIO' }; }
  const completo = conToken(req) || conAcceso(req);  // sin credencial valida: banco recortado a contadores y booleanos, sin rutas del disco
  res.json({ ok: true, pool: poolInfo, cuentas: sinCorreos(estadoCuentas()), respaldo: estadoRespaldo(), banco: completo ? diagnosticoBanco() : resumenBanco(diagnosticoBanco()), metricas: estadoMetricas(), ...(completo ? { state_dir: process.env.BRIDGE_STATE_DIR || './state' } : {}) });
});

app.get('/v1/web/diagnostico',async(_req,res)=>{
  try { res.json({ok:true,indicadores:await diagnosticoAcceso()}); }
  catch { res.status(503).json({ok:false,error:{code:'WEB_DIAGNOSTICO_FALLO'}}); }
});
// Panel de recuperación de OpenClaw: lecturas de GAPS sin prompts ni secretos.
app.get('/v1/swen/gaps', (_req,res) => res.json({ok:true,gaps:listarGaps()}));
app.get('/v1/swen/gaps/:id', (req,res) => {
  const g=gapPorId(req.params.id);
  return g ? res.json({ok:true,gap:g}) :
    res.status(404).json({ok:false,error:{code:'GAP_NO_ENCONTRADO'}});
});
app.post('/v1/swen/gaps/:id/investigar', async(req,res) => {
  const r=await investigarConOpenClaw(req.params.id);
  return res.status(r.ok?200:503).json(r);
});
app.get('/v1/queue', (_req, res) => {
  res.json({ ok: true, ...estadoTabs(), cuentas: sinCorreos(estadoCuentas()) });
});

// secciones (conv_id) con checkpoint: OpenClaw ve cuales retomar reenviando el mismo conv_id
app.get('/v1/secciones', (req, res) => res.json({ ok: true, secciones: listarCheckpoints(propietarioDe(req)) }));  // solo las del propietario (o sin dueño)

// asesorias guardadas por proyecto (un ASESORIA.md cada uno): OpenClaw las lee antes de ejecutar
app.get('/v1/proyectos', (_req, res) => res.json({ ok: true, proyectos: listarProyectos() }));
app.get('/v1/proyectos/:nombre', (req, res) => {
  const p = leerProyecto(req.params.nombre);
  p ? res.json({ ok: true, ...p }) : res.status(404).json({ ok: false, error: 'PROYECTO_NO_ENCONTRADO' });
});

// retomar una seccion a medias SIN que el cliente reenvie el texto: usa el texto y el modelo guardados en el checkpoint
async function retomarSeccion(id, { respaldo: conRespaldo = false, propietario = null, interno = false, confirmarCompleta = false } = {}) {
  const ck = checkpointCrudo(id);
  if (!ck || ck.tipo === TIPO_LOCAL) {  // checkpoint de un modelo local HF / Groq / NVIDIA (retomar_local.js): puede estar solo en el Harness si el disco se perdio
    const l = await conDeadline(retomarPorId(id, { hasta: Date.now() + DEADLINE_MS * 0.8, sinRespaldo: !conRespaldo, propietario, interno, confirmarCompleta }), DEADLINE_MS);  // el modelo del checkpoint manda: sin respaldo salvo que el cliente lo pida
    if (l && l.yaCompleto) return { status: 409, error: { code: 'SECCION_YA_COMPLETA' } };
    if (l) return { status: 200, salida: l.salida, modelo: l.usado, local: l };
  }
  if (!ck || !ck.texto || !ck.modelo) return { status: 404, error: { code: 'SECCION_NO_ENCONTRADA' } };
  if (ck.completo || (ck.enviados >= ck.total)) return { status: 409, error: { code: 'SECCION_YA_COMPLETA' } };
  const salida = await conDeadline(consultarWeb(ck.modelo, ck.texto, { modo: ck.modo, convId: id }), DEADLINE_MS);
  return { status: 200, salida, modelo: ck.modelo };
}
app.post('/v1/secciones/:id/retomar', async (req, res) => {
  if (!/^[\w-]{1,80}$/.test(req.params.id)) return res.status(400).json({ error: { code: 'CONV_ID_INVALIDO' } });
  try {
    const r = await retomarSeccion(req.params.id, { respaldo: !!(req.body && req.body.respaldo === true), propietario: propietarioDe(req), confirmarCompleta: !!(req.body && req.body.tarea_completa === true) });
    if (r.error) return res.status(r.status).json({ error: r.error });
    const l = r.local;
    res.json({ id: `retoma-${Date.now()}`, object: 'chat.completion', modelo_usado: r.modelo, ...(l ? { via_respaldo: l.via, ...(l.servidor ? { servidor: l.servidor } : {}), tarea: { id: l.tarea_id, estado: l.estado, secciones: l.secciones } } : {}), choices: [{ index: 0, finish_reason: l ? l.finish_reason : 'stop', message: { role: 'assistant', content: r.salida || '', ...(l && l.tool_calls.length ? { tool_calls: l.tool_calls } : {}) } }] });
  } catch (e) { res.status(HTTP_TAREA[e.code] || (e.code === 'UPSTREAM_TIMEOUT' ? 504 : 502)).json({ error: { code: e.code || 'BRIDGE_ERROR', message: String(e.message).slice(0, 200) } }); }
});

// auto-evolucion: mejoras propuestas por lo que el bridge reparo solo (OpenClaw las aplica con su commit)
app.get('/v1/evolucion', (_req, res) => res.json({ ok: true, propuestas: proponerMejoras() }));
// historial de una sesion/proyecto de OpenClaw, de la misma memoria del chat Yaiwes
app.get('/v1/memoria/:sesion', async (req, res) => {
  if (!process.env.HF_TOKEN) return res.status(503).json({ ok: false, error: { code: 'HF_TOKEN_FALTA', message: 'la memoria compartida necesita HF_TOKEN en el entorno del bridge' } });
  res.json({ ok: true, turnos: await leerTurnos(req.params.sesion) });
});

// claves de Groq/NVIDIA desde el panel del chat: SOLO conteos en las respuestas, jamas valores
const conteo = () => { const { groq, nvidia } = estadoRespaldo(); return { groq, nvidia }; };
const claveOk = (k) => typeof k === 'string' && k.length >= 8 && k.length <= 300 && !/\s/.test(k);
// {groq, nvidia} (string o lista) -> solo los proveedores presentes, o null si algo no vale (maximo 20 por proveedor, cada una con claveOk)
function validarClaves(b) {
  if (!b || typeof b !== 'object' || Array.isArray(b)) return null;
  const nuevas = {};
  for (const prov of ['groq', 'nvidia']) {
    if (b[prov] === undefined) continue;
    const lista = Array.isArray(b[prov]) ? b[prov] : [b[prov]];
    if (lista.length > 20 || !lista.every(claveOk)) return null;
    nuevas[prov] = b[prov];
  }
  return Object.keys(nuevas).length ? nuevas : null;
}
const MSG_CLAVE = 'maximo 20 claves por proveedor, cada una de 8 a 300 caracteres sin espacios ni saltos de linea; envia groq y/o nvidia (string o lista de strings)';
// persistido = GitHub publico el banco (el guardado local va aparte en `local`)
async function persistir(local) { return { local, persistido: local ? await publicarEnGithub().catch(() => false) : false }; }
// Misma fuente cifrada para chat YAIWES, Router MVP y SWE CODE/OpenClaw.
app.get('/v1/credenciales', async (_req, res) => {
  try { res.json(await catalogoProveedores()); }
  catch { res.status(503).json({ ok:false, error:{ code:'BANCO_NO_DISPONIBLE' } }); }
});
app.post('/v1/credenciales', async (req, res) => {
  const x = req.body || {};
  if (!x || typeof x !== 'object' || typeof x.secret !== 'string' ||
      x.secret.length < 8 || x.secret.length > 300 || /\s/.test(x.secret) ||
      !/^(auto|[a-z][a-z0-9_-]{1,31})$/.test(String(x.proveedor || 'auto')) ||
      !['api_key','sdk'].includes(x.tipo || 'api_key')) {
    return res.status(400).json({ ok:false, error:{ code:'REGISTRO_INVALIDO' } });
  }
  try {
    const guardado = await anadirProveedor(x);
    res.json({ ...guardado, ...(await persistir(true)) });
  } catch { res.status(503).json({ ok:false, error:{ code:'BANCO_NO_GUARDADO' } }); }
});
app.get('/v1/claves', (_req, res) => res.json({ ok: true, ...conteo() }));
app.post('/v1/claves', async (req, res) => {
  const nuevas = validarClaves(req.body);
  if (!nuevas) return res.status(400).json({ error: { code: 'CLAVE_INVALIDA', message: MSG_CLAVE } });
  // El banco cifrado es fuente de verdad: nunca confirmar ni aplicar una escritura que no se pudo guardar.
  const local = await guardarEnBanco(nuevas).catch(() => false);
  if (!local) return res.status(503).json({ ok: false, error: { code: 'BANCO_NO_GUARDADO', message: 'No se guardaron las claves en el banco cifrado' } });
  setClaves(nuevas);
  res.json({ ok: true, ...conteo(), ...(await persistir(true)) });
});
app.delete('/v1/claves', async (_req, res) => {
  const local = await borrarDelBanco().catch(() => false);
  if (!local) return res.status(503).json({ ok: false, error: { code: 'BANCO_NO_BORRADO', message: 'No se pudo borrar el banco cifrado' } });
  limpiarClaves();
  res.json({ ok: true, ...conteo(), ...(await persistir(true)) });  // se publica el banco ya vacio
});

// toggle ON/OFF del system-prompt de la ficha del Router MVP (systemprompt.js); defecto ON. Afecta a TODOS los modelos (Groq/NVIDIA/HF local/web-*)
// del chat directo y de OpenClaw, via conPreambulo/prompt en /v1/chat/completions (mismo pipeline)
app.get('/v1/system-prompt-on', async (_req, res) => {
  try { res.json({ ok: true, on: await consultarPromptRouter() }); }
  catch { res.status(503).json({ ok:false, error:{code:'ROUTER_PROMPT_NO_VERIFICADO'} }); }
});
app.post('/v1/system-prompt-on', async (req, res) => {
  const on = req.body && typeof req.body.on === 'boolean' ? req.body.on : null;
  if (on === null) return res.status(400).json({ error: { code: 'VALOR_INVALIDO', message: 'on: boolean' } });
  try {res.json({ ok:true, on:await consultarPromptRouter(on) });}
  catch {res.status(503).json({ ok:false, error:{code:'ROUTER_PROMPT_NO_CONFIRMADO'} });}
});

const idsModelos = () => {
  const base = Object.keys(MODELOS_WEB).map(m => `web-${m}`);
  const modos = ['revision','solucion','arquitectura','archivos','prompt_code','consulta','despliega','asesoria'].map(m => `swecode-${m}`);
  return [...base, 'web-claude-sonnet', ...modos, ...idsRespaldo()];
};
app.get('/v1/models', (_req, res) => res.json({ object: 'list', data: idsModelos().map(id => ({ id, object: 'model' })) }));
// disponibilidad real de los modelos Groq/NVIDIA (GET /models de cada proveedor): DISPONIBLE | NO DISPONIBLE | SIN VERIFICAR; jamas cambia de modelo en silencio ni muestra claves
app.get('/v1/modelos/disponibilidad', async (_req, res) => {
  try {
    const estadoHF = await disponibilidadLocal();
    const locales = estadosModelosLocales(idsRespaldo().filter(id => !id.includes('/')), estadoHF);
    // GET /v1/models prueba salud sin generar tokens: un 503 real de S1/S2/S3
    // se presenta como NO DISPONIBLE, no como modelo listo para usar.
    // El selector necesita el estado EFECTIVO de las credenciales (entorno + banco cifrado).
    // GET /v1/claves informa solo sobre el banco y puede exigir permisos distintos;
    // no usar ese contador para decidir falsamente que un modelo esta NO CONFIGURADO.
    const cuentas = estadoRespaldo();
    res.json({ ok: true, modelos: await disponibilidad(), locales, slots_hf: estadoHF.slots.map(s => ({ slot: s.slot, estado: s.estado, ...(s.motivo ? { motivo: s.motivo } : {}) })),
      configurados: Object.fromEntries(Object.entries(cuentas).map(([k, n]) => [k, n > 0])) });
  } catch (e) {
    res.status(502).json({ ok: false, error: { code: 'DISPONIBILIDAD_FALLO', message: 'No se pudo consultar el catálogo' } });
  }
});

// configuracion vigente de OpenClaw (providers, modelos, modos, workspace): solo lectura, sin secretos (conteos de claves, jamas valores)
app.get('/v1/openclaw', (_req, res) => {
  const c = configVigente();
  if (!c) return res.status(404).json({ ok: false, error: { code: 'CONFIG_NO_ENCONTRADA', message: 'falta SWE CODE free/provider-openclaw.json (RIU_OPENCLAW_DIR)' } });
  const ruta = rutaWorkspace();
  res.json({ ok: true, ...c, vivo: { modelos: idsModelos(), ...conteo() }, workspace: { ruta, existe: nodeFs.existsSync(ruta) }, espejo: espejo() });  // espejo de emergencia: catalogo del Router para OpenClaw (solo nombres)
});

// herramienta nativa: el agente la llama cuando ve SESSION_EXPIRED
app.post('/refresh_session', async (_req, res) => {
  try { const s = await salud(); res.json({ ok: true, sitios: s }); }
  catch (e) { res.status(503).json({ ok: false, error: e.code || e.message }); }
});

// SSE (stream:true): chat.completion.chunk (role -> content -> tool_calls -> finish_reason -> [DONE]). Groq/NVIDIA: los fragmentos REALES del proveedor se reenvian al instante (sse.delta);
// lo que no llega por streaming (web, HF local, checkpoint) se emite al terminar, en trozos, SOLO lo que falte (sse.flujo.texto = lo ya entregado: nunca se duplica).
// Mientras se espera, cada SSE_KEEPALIVE_MS se abre el stream y se envia ": keepalive" para que ningun proxy corte la conexion; antes de abrirlo los errores siguen siendo JSON.
const SSE_KEEPALIVE_MS = parseInt(process.env.BRIDGE_SSE_KEEPALIVE_MS || '15000', 10), SSE_TROZO = 200;
function trozosDe(texto, max = SSE_TROZO) {
  const t = String(texto || ''), out = [];
  for (let i = 0; i < t.length;) {
    let f = Math.min(i + max, t.length);
    const c = t.charCodeAt(f - 1);
    if (f < t.length && c >= 0xD800 && c <= 0xDBFF) f--;  // no partir un par sustituto (emoji)
    out.push(t.slice(i, f)); i = f;
  }
  return out;
}
function crearSse(req, res) {
  const pide = !!req.body && req.body.stream === true;
  const s = { pide, activo: false, id: `webchat-${Date.now()}`, created: Math.floor(Date.now() / 1000), model: `swecode:${pide ? req.body.model : ''}`, extra: {}, timer: null, flujo: { texto: '' }, rol: false, latido: { fn: null }, ac: new AbortController() };
  if (pide) res.on('close', () => { if (!res.writableEnded) s.ac.abort(); });  // cliente desconectado: se cancela la conexion con el proveedor
  s.signal = s.ac.signal;
  s.abrir = () => { if (!s.activo && !res.headersSent) { s.activo = true; res.writeHead(200, { 'content-type': 'text/event-stream; charset=utf-8', 'cache-control': 'no-cache', connection: 'keep-alive' }); } };
  s.vigilar = () => { if (pide && !s.timer) { s.timer = setInterval(() => { s.abrir(); if (s.activo) res.write(': keepalive\n\n'); }, SSE_KEEPALIVE_MS); res.on('close', s.parar); } };
  s.parar = () => { clearInterval(s.timer); s.timer = null; };
  s.chunk = (delta, finish_reason = null, extra = {}) => res.write(`data: ${JSON.stringify({ id: s.id, object: 'chat.completion.chunk', created: s.created, model: s.model, ...s.extra, choices: [{ index: 0, delta, finish_reason }], ...extra })}\n\n`);
  s.error = (code, message, detail) => { s.abrir(); s.chunk({}, 'error', { error: { code, message, detail } }); res.end('data: [DONE]\n\n'); };
  s.rolInicial = () => { if (!s.rol) { s.abrir(); s.chunk({ role: 'assistant', content: '' }); s.rol = true; } };
  s.delta = (texto) => { if (res.writableEnded) return; s.rolInicial(); for (const t of trozosDe(texto)) s.chunk({ content: t }); if (s.latido.fn) s.latido.fn(); };  // fragmento real del proveedor
  s.inicio = (i, conVia = true) => { s.extra = { ...s.extra, modelo_usado: i.usado, via_respaldo: conVia ? i.via : null }; if (!res.headersSent) { res.setHeader('x-modelo-usado', i.usado); if (conVia) res.setHeader('x-via-respaldo', i.via); } };  // proveedor que va a responder
  return s;
}

// Canal EXCLUSIVO del provider OpenClaw: su cliente OpenAI-compatible NO
// incluye "origen" en el JSON. Este alias añade el origen en el servidor,
// sin depender de botones ni de cabeceras configurables del navegador.
// El middleware de autentificacion general YA corrio y este alias no expone
// rutas de claves, status, tools ni otros endpoints privilegiados.
app.post('/openclaw/v1/chat/completions', (req, _res, next) => {
  req.body = { ...(req.body || {}), origen: 'openclaw' };
  req.url = '/v1/chat/completions';
  next();
});
app.get('/openclaw/v1/models', (_req, res) => res.json({ object:'list', data: idsModelos().map(id => ({ id, object:'model' })) }));

app.post('/v1/chat/completions', async (req, res) => {
  const sse = crearSse(req, res);
  try {
    let { model = 'swecode-consulta', messages: mensajesIn = [], modo, conv_id, proyecto, documentos, cuentas, clave: claveReq, claves: clavesReq } = req.body;
    if (typeof model !== 'string' || !/^[\w.\/:-]{1,100}$/.test(model)) return res.status(400).json({ error: { code: 'MODELO_INVALIDO', model: String(model).slice(0, 50) } });
    if (!Array.isArray(mensajesIn)) return res.status(400).json({ error: { code: 'MENSAJES_INVALIDOS', message: 'messages debe ser una lista' } });
    mensajesIn = mensajesIn.filter(m => m && typeof m === 'object').map(m => ({ ...m, content: textoDe(m.content) }));
    const iUlt = mensajesIn.map(m => m.role).lastIndexOf('user');
    const act = activar && iUlt >= 0 ? activar(mensajesIn[iUlt].content) : null;
    if (act && act.error) return res.status(400).json({ error: { code: 'ACTIVACION_INVALIDA', message: act.error } });
    if (act) {  // "SWEN CODE free [modo m] [solo modelo] [chat n] texto": el mensaje manda sobre el modelo/modo/seccion del POST
      model = act.modelo === 'consenso' ? `swecode-${act.modo}` : (IDS_DIRECTOS(act.modelo) ? act.modelo : model);
      if (act.modo === 'asesoria') model = 'swecode-asesoria';  // la asesoria por gramatica tambien va primero a Groq
      modo = act.modo; conv_id = act.conv_id || conv_id;
      mensajesIn = mensajesIn.map((m, i) => (i === iUlt ? { ...m, content: act.prompt } : m));
    }
    // claves/cuentas por llamada: solo con la clave de acceso del chat (BRIDGE_TOKEN solo no basta) y validadas igual que el panel
    const clavesValidas = clavesReq === undefined || clavesReq === null ? null : validarClaves(clavesReq);
    if ((clavesReq != null || cuentas) && !conAcceso(req)) return res.status(401).json({ error: { code: 'NO_AUTORIZADO', message: 'claves/cuentas por llamada exigen la clave de acceso (x-api-key)' } });
    if (clavesReq != null && !clavesValidas) return res.status(400).json({ error: { code: 'CLAVE_INVALIDA', message: MSG_CLAVE } });
    if (conv_id != null && !/^[\w-]{1,80}$/.test(String(conv_id))) return res.status(400).json({ error: { code: 'CONV_ID_INVALIDO', message: 'conv_id: letras, numeros, - y _ (max 80)' } });
    if (model.startsWith('web-') && model !== 'web-claude-sonnet' && !MODELOS_WEB[model.slice(4)]) return res.status(400).json({ error: { code: 'MODELO_INVALIDO', model } });
    if (Array.isArray(documentos) && documentos.length > MAX_DOCS) return res.status(413).json({ error: { code: 'DEMASIADOS_DOCUMENTOS', max: MAX_DOCS } });
    // La UI nativa de OpenClaw no incorpora un boton: sus tareas y tool_calls
    // llevan la ficha activada aunque el chat YAIWES haya apagado SU interruptor.
    const forzarPromptOpenClaw = req.body.origen === 'openclaw' || req.body.ejecutor_tools === 'openclaw';
    const messages = conFormato(mensajesIn);  // formato de salida del chat Yaiwes tambien para OpenClaw
    // credenciales vienen de OpenClaw por llamada (vía plugins->harness); env solo respaldo
    if (cuentas) setCuentas(cuentas, claveReq);
    if (clavesValidas) {
      // Aun en el envio autenticado, NO aplicar claves si la persistencia cifrada fallo.
      const local = await guardarEnBanco(clavesValidas).catch(() => false);
      if (!local) return res.status(503).json({ error: { code: 'BANCO_NO_GUARDADO', message: 'No se guardaron las claves en el banco cifrado' } });
      setClaves(clavesValidas);
      publicarEnGithub().catch(() => {});  // copia cifrada opcional; el resultado permanente se consulta en el panel
    }
    const iU = messages.map(m => m.role).lastIndexOf('user');
    const ultimo = iU >= 0 ? messages[iU].content : '';
    const anterior = messages.filter((m, i) => i !== iU).map(m => `${m.role}: ${m.content}`).join('\n');
    let prompt = anterior ? `${anterior}\nuser: ${ultimo}` : ultimo;
    // documentos: [{nombre, contenido}] o strings — se incrustan al prompt y tambien llegan a Groq/NVIDIA/locales como mensaje
    const docs = (Array.isArray(documentos) ? documentos : [])
      .map(d => typeof d === 'string' ? { nombre: 'doc', contenido: d } : d)
      .filter(d => d && d.contenido)
      .map(d => `[DOCUMENTO: ${d.nombre || 'doc'}]\n${String(d.contenido).slice(0, 100000)}`)
      .join('\n\n');
    if (docs) prompt = `${prompt}\n\n${docs}`;
    if (prompt.length > MAX_PROMPT) return res.status(413).json({ error: { code: 'PROMPT_DEMASIADO_GRANDE', max: MAX_PROMPT } });
    let mensajesM = docs ? [...messages, { role: 'user', content: docs }] : messages;
    // Handoff exacto desde el checkpoint anterior. El modelo NO usa una IA local para resumirlo.
    const origenContexto = req.body.contexto_de;
    if (origenContexto != null && (typeof origenContexto !== 'string' || !/^[A-Za-z0-9_-]{1,80}$/.test(origenContexto)))
      return res.status(400).json({ error:{ code:'CONTEXTO_ID_INVALIDO' } });
    if (origenContexto && conv_id && origenContexto !== conv_id)
      transferirContexto(origenContexto, String(conv_id), propietarioDe(req));
    const handoff = tarjetaHandoff({ conv_id:conv_id == null ? null : String(conv_id),
      origen:origenContexto, propietario:propietarioDe(req), modelo:model });
    if (handoff) mensajesM = [{role:'system',content:handoff},...mensajesM];
    const promptFicha = conSystemPromptTexto(handoff ? handoff + '\n\n' + prompt : prompt, process.env, { forzarOn: forzarPromptOpenClaw });  // idem conPreambulo, pero para los modelos web-*/consenso (prompt de texto plano, no mensajes)

    let modeloWeb, modoUso = modo || 'consulta', salida, usado = model;
    if (model.startsWith('web-')) {
      modeloWeb = model.slice(4);
    } else if (model.startsWith('swecode-')) {
      modoUso = model.slice(8);
      if (!modoValido(modoUso)) return res.status(400).json({ error: { code: 'MODO_INVALIDO', modo: modoUso } });
    } else if (!esExterno(model) && !esLocal(model)) {
      return res.status(400).json({ error: { code: 'MODELO_INVALIDO', model } });
    }
    let via = null, aviso = null, viaPrimaria = null, llamadas = [], fin = 'stop', tarea = null, metricas = null, servidor = null, toolsInvalidas = [], consensoDetalle = null, flagClaude = null;
    // tarea_id (cuerpo o cabecera x-tarea-id): modelos locales/Groq/NVIDIA con checkpoint universal (retomar_local.js).
    // Sin tarea_id pero con conv_id se DERIVA <conv_id>-<sha256 de [modelo, modo, mensajes] (12)>: el mismo envio reintentado reanuda, uno distinto es tarea nueva. Sin conv_id nada cambia.
    const explicito = esExterno(model) || esLocal(model), pideRespaldo = req.body.respaldo === true;
    // Sonnet MAX y el consejo de 4 modelos requieren margen real de razonamiento.
    // Los demás modelos conservan exactamente sus plazos originales.
    const plazoModelo = model === 'web-claude-sonnet' ? Math.max(DEADLINE_MS, 320000)
      : model === 'swecode-consulta' || model === 'swecode-plan' ? Math.max(DEADLINE_MS, 415000)
      // Primera apertura Chromium + restauración de sesión + generación:
      // el plazo global de 100 s anterior cortaba incluso antes de leer respuesta.
      : model.startsWith('web-') ? Math.max(DEADLINE_MS, 250000)
      : esLocal(model) ? HF_LOCAL_DEADLINE_MS : DEADLINE_MS;
    let tareaId = req.body.tarea_id != null ? req.body.tarea_id : req.headers['x-tarea-id'];
    if ((tareaId == null || tareaId === '') && explicito && conv_id != null && conv_id !== '') tareaId = tareaDerivada(conv_id, model, modo, mensajesM, propietarioDe(req));
    const origen = ['yaiwes', 'openclaw'].includes(req.body.origen) ? req.body.origen : undefined;  // origen del contrato: ruta del checkpoint en el Harness
    const usaTarea = tareaId != null && tareaId !== '' && explicito;
    if (usaTarea && !tareaIdValido(String(tareaId))) return res.status(400).json({ error: { code: 'TAREA_ID_INVALIDO', message: 'tarea_id: letras, numeros, - y _ (max 64)' } });
    if (usaTarea && !res.headersSent) res.setHeader('x-tarea-id', String(tareaId));  // 128: el id de la tarea viaja siempre; se reenvia tal cual para reanudar
    const catalogo = req.body.tools === true ? await toolsDeRouter() : undefined;
    const extra = { tools: Array.isArray(req.body.tools) ? req.body.tools : catalogo, tool_choice: req.body.tool_choice };
    // UI Tools ON se resuelve con tools/list REAL: el bridge sólo produce tool_calls
    // pendientes. El Harness/ejecutor verifica permisos, aprobación y recibos.
    // streaming real (stream:true): Groq/NVIDIA entregan fragmentos por onDelta -> sse.delta; flujo = lo ya entregado al cliente (el failover continua desde ahi, sin repetir)
    sse.model = `swecode:${model}`;
    const ac1 = new AbortController();  // primer intento; si vence el plazo se cancela antes del respaldo (no puede seguir escribiendo en el mismo stream)
    // Una sola señal alcanza al proveedor incluso sin upstream SSE (locales), sin duplicar rutas.
    const streamOpts = (senal) => ({ ...(sse.pide ? { onDelta: sse.delta, flujo: sse.flujo, onInicio: sse.inicio } : {}), opts: { signal: senal } });

    const ejecutar = async () => {
    if (usaTarea) {
      // 129: propietario (hash de la clave usada), proyecto, sesion (conv_id), workflow y operacion quedan vinculados al tarea_id. 140: la tarea solo es DONE si el cliente/workflow lo confirma
      // (tarea_completa:true | x-tarea-completa:1). 141: objetivo + operaciones_previstas, exigidos POR DEFECTO con tools (efectos); BRIDGE_EXIGIR_CONFIRMACION=0 lo desactiva (el cuerpo no puede apagarlo); sin tools nada cambia
      const b = req.body, str = (v) => (typeof v === 'string' && v.trim() ? v.trim() : null);
      const vinculo = { propietario: propietarioDe(req), proyecto: str(proyecto), sesion: conv_id != null ? String(conv_id) : null, workflow: str(b.workflow), operacion: str(b.operacion) };
      const plan = b.objetivo !== undefined || b.operaciones_previstas !== undefined ? { objetivo: b.objetivo, operaciones: b.operaciones_previstas } : undefined;
      const r = await retomarLocal(String(tareaId), model, conPreambulo(mensajesM, modo, forzarPromptOpenClaw), { ...extra, ...vinculo, plan, exigirPlan: b.exigir_confirmacion === true || String(process.env.BRIDGE_EXIGIR_CONFIRMACION ?? '').trim() !== '0', confirmarCompleta: b.tarea_completa === true || req.headers['x-tarea-completa'] === '1', origen, sinRespaldo: !pideRespaldo, hasta: Date.now() + plazoModelo * 0.9, flushChars: parseInt(process.env.BRIDGE_CHECKPOINT_FLUSH_CHARS, 10) || undefined, flushMs: Number.isFinite(parseInt(process.env.BRIDGE_CHECKPOINT_FLUSH_MS, 10)) ? parseInt(process.env.BRIDGE_CHECKPOINT_FLUSH_MS, 10) : undefined, ...(sse.pide ? { onDelta: sse.delta, flujo: sse.flujo, onInicio: sse.inicio, opts: { signal: AbortSignal.any([sse.signal, ac1.signal]) } } : {}) }); salida = r.salida; usado = r.usado || model; via = r.via; llamadas = r.tool_calls || []; fin = r.finish_reason || 'stop'; metricas = r.metricas || null; servidor = r.servidor || null;
      tarea = { id: r.tarea_id, estado: r.estado, fase: r.fase, secciones: r.secciones, reanudado: r.reanudado, desde_checkpoint: r.desde_checkpoint };
    } else if (esExterno(model)) {
      const r = await externo(model, conPreambulo(mensajesM, modo, forzarPromptOpenClaw), { extra, ...streamOpts(AbortSignal.any([sse.signal, ac1.signal])) }); toolsInvalidas = r.tools_invalidas || []; salida = r.salida; usado = r.usado; via = r.via; llamadas = r.tool_calls || []; fin = r.finish_reason || 'stop'; metricas = r.metricas || null;
    } else if (esLocal(model)) {
      const r = await local(model, conPreambulo(mensajesM, modo, forzarPromptOpenClaw), { extra, ...streamOpts(AbortSignal.any([sse.signal, ac1.signal])) }); toolsInvalidas = r.tools_invalidas || []; salida = r.salida; usado = r.usado; via = r.via; llamadas = r.tool_calls || []; fin = r.finish_reason || 'stop'; metricas = r.metricas || null; servidor = r.servidor || null;
    } else if (modeloWeb) {
      // Sólo con esquema de herramientas explícito: el texto WEB NO es una tool_call por defecto.
      // No se llama a otro LLM para "traducir" JSON; tampoco se ejecutan tools aquí.
      if (modeloWeb === 'claude-sonnet') {
        // Claude trabaja con el agente OpenClaw swen-council, razonamiento max y
        // rotación NATIVA de perfiles Anthropic. Sin modelo traductor ni scraping.
        usado = CLAUDE_MODEL;
        try {
          const r = await consultarClaude(promptFicha + promptHerramientasWeb(extra.tools), { convId:String(conv_id||'consulta') });
          salida = r.texto;
        } catch (e) {
          if (!esCuotaClaude(e.code)) throw e;
          flagClaude = { codigo:'CLAUDE_SONNET_SIN_CUENTA_DISPONIBLE',
            mensaje:'No quedan perfiles Anthropic elegibles en OpenClaw. La tarea se mantiene pendiente para recuperación.' };
          salida = '🚩 Claude Sonnet 5.5 · ' + flagClaude.codigo + '. Se conservó el contexto; los demás modelos y tareas pueden continuar.';
          fin = 'error';
        }
      } else {
        const site = modeloWeb.startsWith('qwen') ? 'qwen' : modeloWeb === 'dsv4-flash' ? 'deepseek' : null;
        try {
          salida = await consultarWeb(modeloWeb, promptFicha + promptHerramientasWeb(extra.tools), { modo: modoUso, convId: conv_id });
        } catch(e) {
          // ÚNICO reintento válido: navegación fallida ANTES del envío.
          // No repetir respuestas parciales, tools, cuotas o sesiones expiradas.
          if (e.code!=='WEB_SITIO_NO_RESPONDE'||!site||sse.signal.aborted) throw e;
          const reciclaje=await reiniciarSitioInactivo(site);
          if(!reciclaje.ok) throw e;
          salida = await consultarWeb(modeloWeb, promptFicha + promptHerramientasWeb(extra.tools), { modo: modoUso, convId: conv_id });
        }
      }
      if (!flagClaude) {
        const contratoWeb = extraerLlamadasWeb(salida, extra.tools);
        salida = contratoWeb.texto;
        llamadas = contratoWeb.tool_calls;
        fin = contratoWeb.finish_reason;
      }
      usado = modeloWeb === 'claude-sonnet' ? CLAUDE_MODEL : modeloWeb;
    } else if (modoUso === 'asesoria') {
      // asesoria previa a ejecutar: primero Groq (las claves del chat Yaiwes), si no responde la web de SWE CODE free
      try {
        const r = await externo(`groq/${modeloDefecto('groq')}`, conSystemPrompt([{ role: 'system', content: preambulo('asesoria') }, ...mensajesM], process.env, { forzarOn: forzarPromptOpenClaw }),
                                { ...streamOpts(AbortSignal.any([sse.signal, ac1.signal])) });
        toolsInvalidas = r.tools_invalidas || []; salida = r.salida; usado = r.usado; viaPrimaria = 'groq'; llamadas = r.tool_calls || []; fin = r.finish_reason || 'stop'; metricas = r.metricas || null;
      } catch (e) {
        if (sse.signal.aborted || sse.flujo.texto) throw e; // no combinar respuesta parcial SSE con modelo diferente
        const r = await conFallback(OBJETIVO_UNICO, promptFicha, { modo: modoUso, convId: conv_id });
        salida = r.salida; usado = r.usado;
      }
    } else if (esConsenso(modoUso)) {
      const r = await consenso(promptFicha + promptHerramientasWeb(extra.tools), { modo: modoUso, convId: conv_id });
      const rTools = extraerLlamadasWeb(r.final, extra.tools);
      salida = rTools.texto; llamadas = rTools.tool_calls; fin = rTools.finish_reason;
      usado = 'qwen38max';
      const claudeOpinion = String(r.por_modelo['claude-sonnet'] || '');
      if (claudeOpinion.startsWith('🚩')) {
        flagClaude = { codigo:claudeOpinion.includes('CLAUDE_SONNET_SIN_CUENTA_DISPONIBLE')
          ? 'CLAUDE_SONNET_SIN_CUENTA_DISPONIBLE' : 'CLAUDE_SONNET_NO_DISPONIBLE',
          mensaje:'El consejero Claude no respondió; Ask Cónsil continúa con Qwen árbitro.' };
        salida = [salida, claudeOpinion].filter(Boolean).join('\n\n');
      }
      consensoDetalle = { arbitro:'qwen38max', opiniones:Object.fromEntries(
        Object.entries(r.por_modelo).map(([k,v])=>[k,String(v).slice(0,3500)])),
        decision:String(r.final).slice(0,3500), modificable_por_operador:true };
    } else {
      const r = await conFallback(OBJETIVO_UNICO, promptFicha, { modo: modoUso, convId: conv_id });
      salida = r.salida; usado = r.usado;
    }
    };
    // Checkpoint ANTES de solicitar respuesta: sobrevive a caída del navegador/bridge.
    // Al terminar se completa el mismo turno; no hay llamadas LLM para el resumen.
    if (conv_id) try {
      const identModelo = model.startsWith('web-') ? model.slice(4) :
        model.startsWith('swecode-') ? 'qwen38max' : model;
      registrarContexto({conv_id:String(conv_id),propietario:propietarioDe(req),
        modelo:identModelo,modo:modoUso,proyecto,entrada:ultimo,salida:'',estado:'CONTINUAR'});
    } catch { /* no se bloquea el envío por fallo del disco */ }
    sse.vigilar();
    try {
      await conDeadline(ejecutar(), plazoModelo, sse.pide ? sse.latido : null);
      if (toolsInvalidas.length) throw Object.assign(new Error('Tool calls invalidas: no se entregan al ejecutor'), { code: 'TOOL_CALL_INVALIDA' });
      if ((!salida || !String(salida).trim()) && !llamadas.length) throw Object.assign(new Error('respuesta vacia del modelo web'), { code: 'EMPTY_RESPONSE' });
    } catch (e) {
      if (e.code === 'UPSTREAM_TIMEOUT') ac1.abort();  // el intento colgado (tambien el de una tarea con checkpoint) no puede seguir escribiendo en el stream
      if (e.code === 'MODO_INVALIDO' || e.code === 'TOOL_CALL_INVALIDA' || usaTarea || sse.signal.aborted) throw e;  // cliente desconectado: no se gasta mas respaldo. Con tarea_id retomarLocal ya probo local/Groq/NVIDIA y guardo el checkpoint: el cliente reintenta con el mismo tarea_id
      if (e.code === 'UPSTREAM_TIMEOUT' && conv_id) await cerrarPagina(conv_id).catch(() => {});  // la tab colgada liberaba su slot solo al cerrarse
      // SWE CODE free: JAMÁS cambiar un modelo WEB ni Ask Cónsil a Groq/NVIDIA/Liquid
      // si fallan. Conservar error/FLAG, checkpoint y selector. Otros selectores
      // conservan su política de respaldo original.
      if (model.startsWith('web-') || model.startsWith('swecode-') || (explicito && !pideRespaldo))
        throw e.code === 'EXTERNO_FALLO' && e.status === 404
          ? Object.assign(e, { code: 'NO_DISPONIBLE', message: `modelo ${model} no disponible en el proveedor (HTTP 404); ${e.message}` }) : e;
      // auto-reparacion: sesion caida -> re-login/rotacion de correo y UN reintento; si sigue mal, respaldo Groq -> NVIDIA -> HF local
      if (e.code === 'SESSION_EXPIRED') {
        try { await salud(); salida = null; await conDeadline(ejecutar(), 50000); registrarLeccion({ codigo: 'SESSION_EXPIRED', accion: 'salud() + reintento', resultado: 'PASS', modelo: model }); } catch { registrarLeccion({ codigo: 'SESSION_EXPIRED', accion: 'salud() + reintento', resultado: 'FAIL', modelo: model }); }
      }
      if ((!salida || !String(salida).trim()) && !llamadas.length) {
        const ac2 = new AbortController();  // si vence el plazo del respaldo se cancela antes de responder el error
        const r = await conDeadline(respaldo(conPreambulo(mensajesM, model.startsWith('swecode-') ? modoUso : modo, forzarPromptOpenClaw), { extra, ...streamOpts(AbortSignal.any([sse.signal, ac2.signal])) }), DEADLINE_MS, sse.pide ? sse.latido : null).catch((e2) => { if (e2.code === 'UPSTREAM_TIMEOUT') ac2.abort(); throw e2; });  // con texto ya entregado, el respaldo CONTINUA desde ahi (sse.flujo), no repite
        toolsInvalidas = r.tools_invalidas || []; llamadas = r.tool_calls || []; fin = r.finish_reason || 'stop'; metricas = r.metricas || null; servidor = r.servidor || null;
        salida = r.salida; usado = r.usado; via = r.via; aviso = e.code || null;
        registrarLeccion({ codigo: e.code || 'WEB_FALLO', accion: 'respaldo ' + r.via, resultado: 'PASS', modelo: model });  // p. ej. CUENTAS_FALTAN: OpenClaw sabe que debe reenviar cuentas y clave
      }
    }
    if (toolsInvalidas.length) throw Object.assign(new Error('Tool calls invalidas: no se entregan al ejecutor'), { code: 'TOOL_CALL_INVALIDA' });
    if (llamadas.length && fin !== 'tool_calls') fin = 'tool_calls';  // R4: con tool_calls el finish_reason SIEMPRE lo dice (un 'stop' haria que el cliente ignore las llamadas); texto y tool_calls viajan juntos
    let archivo = null;
    if (modoUso === 'asesoria') { try { archivo = guardarAsesoria(proyecto || conv_id, { texto: salida, via: via || viaPrimaria || 'web', modelo: usado }); } catch { /* guardar es mejor esfuerzo */ } }
    if (proyecto || conv_id) guardarTurno(proyecto || conv_id, ultimo, salida, usado).catch(() => {});  // misma memoria del chat Yaiwes (mejor esfuerzo)
    // Registro de continuidad en disco existente, sin una llamada LLM de "resumen".
    // Una tool sin resultado conserva WAIT_TOOLS y no se vuelve a ejecutar automáticamente.
    if (conv_id) try {
      registrarContexto({ conv_id:String(conv_id), propietario:propietarioDe(req), modelo:usado,
        modo:modoUso, proyecto, entrada:ultimo, salida,
        tool_calls:llamadas, resultado_tools:mensajesIn.filter(m=>m.role==='tool').map(m=>({
          id:String(m.tool_call_id||'').slice(0,100), resultado:String(m.content||'').slice(0,4000) })),
        estado: fin==='stop'?'RESPUESTA_COMPLETA':'CONTINUAR' });
    } catch { /* fallo de disco no puede inventar un handoff; el historial principal permanece */ }
    // ejecutor_tools: 'openclaw' = las tools las ejecuta OpenClaw (se devuelven tal cual y la seccion queda WAIT_TOOLS); 'swe' (defecto) no cambia nada
    const ejecutor = normalizarEjecutor(req.body.ejecutor_tools), esOc = ejecutor === 'openclaw' && conv_id != null;
    if (esOc) {
      try {
        const previo = checkpointCrudo(conv_id) || {};
        if (previo.tipo === TIPO_LOCAL) { /* el checkpoint de la tarea (retomar_local) ya guarda el lote ESPERANDO_TOOLS con sus tool_calls */ }
        else if (llamadas.length) checkpointGuardar(conv_id, { ...previo, modo: previo.modo || modoUso, estado: 'WAIT_TOOLS', modelo: usado, proveedor: via || viaPrimaria || null, pendientes: { texto: salida || '', tool_calls: llamadas } });  // R4: las llamadas pendientes quedan guardadas, no solo el estado
        else if (previo.estado === 'WAIT_TOOLS' && mensajesM.at(-1)?.role === 'tool') checkpointGuardar(conv_id, { ...previo, estado: 'CONTINUAR', pendientes: null });
      } catch { /* el checkpoint es mejor esfuerzo */ }
    }
    if (!res.headersSent) { res.setHeader('x-modelo-usado', usado); if (via) res.setHeader('x-via-respaldo', via); }

    if (sse.pide) {  // OpenClaw (openai-completions) pide SSE: lo que llego por streaming real ya se entrego; se emite SOLO lo que falte + tool_calls + finish_reason + [DONE]
      sse.parar(); sse.model = `swecode:${model}`; sse.extra = { modelo_usado: usado, via_respaldo: via, ...(servidor ? { servidor } : {}), ...(metricas ? { metricas } : {}), ...(tarea ? { tarea } : {}), ...(consensoDetalle ? { consenso_detalle: consensoDetalle } : {}), ...(flagClaude ? { flag_claude: flagClaude } : {}), ...(esOc ? { ejecutor_tools: 'openclaw' } : {}) };
      sse.abrir(); sse.rolInicial();
      const yaEntregado = sse.flujo.texto, completo = String(salida || '');
      for (const t of trozosDe(completo.startsWith(yaEntregado) ? completo.slice(yaEntregado.length) : '')) sse.chunk({ content: t });
      if (llamadas.length) sse.chunk({ tool_calls: llamadas.map((t, i) => ({ index: i, ...t })) });
      sse.chunk({}, fin, { usage: usageDe(metricas) });
      return res.end('data: [DONE]\n\n');
    }
    res.json({
      id: `webchat-${Date.now()}`, object: 'chat.completion', created: Math.floor(Date.now()/1000),
      model: `swecode:${model}`, modelo_usado: usado, via_respaldo: via, via_primaria: viaPrimaria, aviso, archivo, ...(servidor ? { servidor } : {}), ...(metricas ? { metricas } : {}), ...(tarea ? { tarea } : {}), ...(consensoDetalle ? { consenso_detalle: consensoDetalle } : {}), ...(flagClaude ? { flag_claude: flagClaude } : {}), ...(esOc ? { ejecutor_tools: 'openclaw' } : {}),
      choices: [{ index: 0, finish_reason: fin, message: { role: 'assistant', content: salida || '', ...(llamadas.length ? { tool_calls: llamadas } : {}) } }],
      usage: usageDe(metricas),
    });
  } catch (e) {
    const code = e.code || 'BRIDGE_ERROR';
    // Registro duradero, sin prompts/tokens/datos de cuentas. OpenClaw puede
    // investigar con herramientas de lectura; no aplica parches de LLM sin validar.
    const gap = registrarGap({code,modelo:req.body?.model,convId:req.body?.conv_id});
    if(gap.nuevo && !gap.estado.startsWith('🚩') && process.env.OPENCLAW_ENABLE==='1') {
      void investigarConOpenClaw(gap.id).catch(()=>null);
    }
    sse.parar();
    if (sse.pide && sse.signal.aborted) return;  // el cliente ya no esta
    if (sse.activo) return res.writableEnded ? undefined : sse.error(code, e.message, e.detail);  // error tras abrir el stream: chunk con el error + [DONE]
    if (res.headersSent) return;
    const st = code === 'SESSION_EXPIRED' ? 503 : code === 'UPSTREAM_TIMEOUT' ? 504 : code === 'EMPTY_RESPONSE' ? 502 : HTTP_TAREA[code] ? HTTP_TAREA[code] : ['EXTERNO_FALLO', 'HF_LOCAL_FALLO', 'NO_DISPONIBLE'].includes(code) ? 502 : 500;
    res.status(st).json({ error: { code, message: e.message, detail: e.detail,
      gap_id:gap.id, flag:gap.estado, accion:gap.accion } });
  }
});


// Diagnóstico (Centinela): GET /debug/tab?conv_id=&shot=0|1 → url, title, screenshot_png_base64
// Acceso vía proxy: GET /web/debug/tab (sin cambiar proxy.py)
app.get('/debug/tab', async (req, res) => {
  try {
    const convId = req.query.conv_id || null;
    const shot = String(req.query.shot ?? '1') !== '0';
    const out = await snapshotTab(convId, { shot });
    if (out.ok === false) return res.status(404).json(out);
    res.json(out);
  } catch (e) {
    res.status(500).json({ ok: false, error: e.message });
  }
});

// errores de express (JSON malformado, body enorme): siempre JSON tipado
app.use((err, _req, res, _next) => res.status(err.status || 400).json({ error: { code: err.type === 'entity.too.large' ? 'BODY_DEMASIADO_GRANDE' : 'BAD_REQUEST', message: String(err.message || err).slice(0, 200) } }));

// cierre limpio: sin esto un reinicio del Space deja el perfil de Chromium bloqueado
for (const sig of ['SIGTERM', 'SIGINT']) process.on(sig, async () => { try { await cerrarTodo(); } catch { /* sigue */ } process.exit(0); });

// BRIDGE_AUTORETOMAR (activo por defecto; '0' lo apaga): al arrancar, retoma una a una las secciones que quedaron a medias (si hay cuentas en el entorno)
if (process.env.BRIDGE_AUTORETOMAR !== '0') {
  setTimeout(async () => {
    for (const sec of listarCheckpoints().filter(c => !c.completo && c.estado !== 'RESPUESTA_COMPLETA')) {  // RESPUESTA_COMPLETA: ya respondio, solo espera la confirmacion del cliente
      try { await retomarSeccion(sec.conv_id, { interno: true }); registrarLeccion({ codigo: 'REINICIO', accion: 'retoma automatica ' + sec.conv_id, resultado: 'PASS' }); }
      catch { registrarLeccion({ codigo: 'REINICIO', accion: 'retoma automatica ' + sec.conv_id, resultado: 'FAIL' }); }
    }
  }, 3000);
}

// auto-reparacion de cableado de OpenClaw: openclaw.sh borra su home en cada arranque y no recrea el workspace del agente
if (process.env.OPENCLAW_ENABLE === '1' || process.env.BRIDGE_REPARAR_OPENCLAW === '1') {
  vigilarWorkspace();
  vigilarModelosOpenClaw(idsModelos); // sin reiniciar el Space, sin claves externas en el gateway
}

// el bridge se actualiza solo cuando llega codigo nuevo de SWE CODE / SWE CODE free (sin reiniciar el Space); BRIDGE_AUTOACTUALIZAR=0 lo apaga
vigilarActualizacion();
vigilarBanco();  // y cada 60 s
vigilarConfig();  // config de OpenClaw (GET /v1/openclaw) al dia cada 60 s
traerDeGithub().catch(() => false).then(() => cargarDelBanco()).then((n) => { if (n) console.warn(`[bridge] ${n} clave(s) de Groq/NVIDIA cargadas del banco`); }).catch(() => {});  // puente al banco: Router MVP (solo lectura) + banco propio

app.listen(PORT, () => console.log(`web-bridge escuchando :${PORT}`));
