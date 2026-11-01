// retomar_local.js — recuperacion (checkpoint universal) para modelos locales HF (lfm2.5-350m, qwen2.5-coder-1.5b, qwen3.5-0.8b, qwen3-0.6b), Groq y NVIDIA.
// retomarLocal(tareaId, modelo, mensajes, extra): hasta 12 vueltas con local()/externo() y, si fallan, respaldo(); el checkpoint se guarda tras CADA seccion
// (checkpoint_hf.js: Harness DeepSeek + local), de modo que un reinicio o una caida de API continua donde quedo y no repite lo hecho.
//   - misma tarea = misma huella sha256([modelo, mensajes]); otro contenido con el mismo tarea_id -> CHECKPOINT_OTRA_TAREA
//   - DONE: devuelve el resultado guardado SIN llamar al modelo
//   - continua SOLO si finish_reason === 'length' (asistente parcial + "Continua exactamente donde termino")
//   - tool_calls: cada una con id unico y su resultado guardado; una ya hecha no se repite; una "iniciada" sin resultado se VERIFICA antes de reintentar
//     (extra.verificarHerramienta) o se corta con VERIFICAR_HERRAMIENTAS_PENDIENTES. Sin extra.ejecutarHerramienta (las corre el Harness) se devuelven tal cual (WAIT_TOOLS).
//   - contexto separado por modelo: contextos[<modelo que respondio>] = secciones que dio; al cambiar de API el nuevo modelo recibe el texto ya generado, no el estado del otro
// Estados (vocabulario de bloques.js): CONTINUAR | WAIT_TOOLS | DONE | ERROR + RESPUESTA_COMPLETA (el modelo termino su respuesta con finish_reason=stop, pero la TAREA no se da por terminada:
// 140). DONE solo llega cuando el cliente/workflow lo confirma (extra.confirmarCompleta). `fase` = vocabulario de la instruccion 139: RESPUESTA_PARCIAL | ESPERANDO_TOOLS | OPERACION_INICIADA |
// OPERACION_CONFIRMADA | RECONCILIAR | RESPUESTA_COMPLETA | DONE | ERROR.
// Propietario (128-130): extra.propietario (hash de la clave de acceso usada, jamas la clave) se guarda en st.vinculo junto a proyecto/sesion/workflow/operacion; otro propietario -> TAREA_AJENA (403);
// otro proyecto/sesion/workflow/operacion con el mismo tarea_id -> TAREA_OTRO_CONTEXTO (409).
// Streaming (137-138, R5): con extra.onDelta (+ extra.flujo = lo ya entregado al cliente) la respuesta se entrega al instante y el texto CONFIRMADO se vuelca al checkpoint cada
// extra.flushChars caracteres o extra.flushMs (st.stream); una caida a mitad deja ese texto en el checkpoint y el reintento CONTINUA desde ahi (sin repetirlo y reponiendolo al cliente nuevo una sola vez).
// Plan (141): extra.plan {objetivo, operaciones:[nombres]} (obligatorio con tools si extra.exigirPlan); un tool_call fuera de operaciones -> OPERACION_NO_PREVISTA. Nunca se guardan claves.
// extra: { env, tools, tool_choice, origen (yaiwes|openclaw|bridge), sinRespaldo (true: el fallo del modelo pedido NO cae a otro modelo), opts (red de respaldo.js), ejecutarHerramienta(t), verificarHerramienta(t), hasta (epoch ms), maxVueltas, fetch, timeoutCheckpointMs }
import crypto from 'node:crypto';
import path from 'node:path';
import { local, externo, respaldo, esLocal, esExterno, claves } from './respaldo.js';
import { guardarCheckpoint, leerCheckpoint, sanear, idValido, origenValido } from './checkpoint_hf.js';
import { estadoDir, herramientaEjecutada, herramientaResultado, herramientaConfirmar } from './bloques.js';

export const TIPO = 'retomar_local';
export const MAX_VUELTAS = 12;
export const FLUSH_CHARS = 1500, FLUSH_MS = 3000;
const CONTINUAR = 'Continúa exactamente donde terminó, sin repetir';

const falla = (code, message, detail) => Object.assign(new Error(message), { code, ...(detail ? { detail } : {}) });
const FASE = { CONTINUAR: 'RESPUESTA_PARCIAL', WAIT_TOOLS: 'ESPERANDO_TOOLS', DONE: 'DONE', ERROR: 'ERROR', RESPUESTA_COMPLETA: 'RESPUESTA_COMPLETA' };
const CAMPOS_VINCULO = ['proyecto', 'sesion', 'workflow', 'operacion'];
const limpiaVinculo = (v) => (typeof v === 'string' && v.trim() ? v.trim().slice(0, 120) : null);
export const vinculoDe = (extra = {}) => ({ propietario: limpiaVinculo(extra.propietario), proyecto: limpiaVinculo(extra.proyecto), sesion: limpiaVinculo(extra.sesion), workflow: limpiaVinculo(extra.workflow), operacion: limpiaVinculo(extra.operacion) });
// 130: una tarea con propietario solo la recupera ese propietario; sin propietario guardado (checkpoint previo) la adopta el primer llamador autenticado.
export function verificarVinculo(st, extra = {}) {
  const pedido = vinculoDe(extra), guardado = st.vinculo || {};
  if (guardado.propietario && guardado.propietario !== pedido.propietario) throw falla('TAREA_AJENA', 'la tarea pertenece a otro propietario');
  for (const k of CAMPOS_VINCULO) if (guardado[k] && pedido[k] && guardado[k] !== pedido[k]) throw falla('TAREA_OTRO_CONTEXTO', `el tarea_id esta vinculado a otro ${k}`);
  st.vinculo = { propietario: guardado.propietario || pedido.propietario, ...Object.fromEntries(CAMPOS_VINCULO.map((k) => [k, guardado[k] || pedido[k]])) };
}
const secretosDe = (env) => [...claves('GROQ_API_KEY', env), ...claves('NVIDIA_API_KEY', env)];

export function huellaDe(modelo, mensajes, secretos = []) {
  return crypto.createHash('sha256').update(JSON.stringify([String(modelo), sanear(mensajes ?? [], secretos)])).digest('hex');
}

// una sola ejecucion a la vez por tarea_id (dos llamados simultaneos no duplican trabajo: el 2º ve el checkpoint del 1º)
const cerrojos = new Map();
async function bajoCerrojo(id, fn) {
  const previo = cerrojos.get(id) || Promise.resolve();
  let libre; const mio = new Promise((r) => { libre = r; }), cola = previo.then(() => mio);
  cerrojos.set(id, cola);
  await previo;
  try { return await fn(); } finally { libre(); if (cerrojos.get(id) === cola) cerrojos.delete(id); }
}

const cancelada = () => falla('ABORTADO', 'peticion cancelada por el cliente');
export async function retomarLocal(tareaId, modelo, mensajes, extra = {}) {
  if (extra.opts?.signal?.aborted) throw cancelada();
  if (!idValido(tareaId)) throw falla('TAREA_ID_INVALIDO', 'tarea_id: letras, numeros, - y _ (1 a 64)');
  if (!esLocal(modelo) && !esExterno(modelo)) throw falla('MODELO_NO_SOPORTADO', 'solo modelos locales HF o groq/ nvidia/: ' + String(modelo).slice(0, 60));
  if (!Array.isArray(mensajes)) throw falla('MENSAJES_INVALIDOS', 'mensajes debe ser una lista');
  return bajoCerrojo(tareaId, () => {
    if (extra.opts?.signal?.aborted) throw cancelada();
    return ejecutar(tareaId, modelo, mensajes, extra || {});
  });
}

async function ejecutar(tareaId, modelo, mensajes, extra) {
  const env = extra.env || process.env, secretos = secretosDe(env);
  const ck = { env, fetch: extra.fetch, timeoutMs: extra.timeoutCheckpointMs, secretos, origen: extra.origen };
  const limite = Math.min(extra.maxVueltas || MAX_VUELTAS, MAX_VUELTAS);
  // los ayudantes de herramientas de bloques.js leen BRIDGE_STATE_DIR del proceso: solo se usan si es el mismo directorio que el de este checkpoint
  const usaBloques = path.resolve(env.BRIDGE_STATE_DIR || estadoDir()) === estadoDir();
  const huella = huellaDe(modelo, mensajes, secretos);

  let st = await leerCheckpoint(tareaId, ck);
  const reanudado = !!st;
  if (st && st.tipo === TIPO) verificarVinculo(st, extra);  // 130: antes que nada, ni siquiera se dice si el contenido coincide
  if (st && (st.tipo !== TIPO || st.huella !== huella)) throw falla('CHECKPOINT_OTRA_TAREA', `el checkpoint ${tareaId} es de otra tarea (otros mensajes o modelo): usa otro tarea_id`);
  if (!st) { st = { tipo: TIPO, version: 1, tarea_id: tareaId, huella, modelo, mensajes: sanear(mensajes, secretos), origen: origenValido(extra.origen) || 'bridge', estado: 'CONTINUAR', fase: 'RESPUESTA_PARCIAL', completo: false, conversacion: [], parcial: '', secciones: [], contextos: {}, herramientas: {}, lote: null, resultado: null, creado: new Date().toISOString() }; verificarVinculo(st, extra); }
  st.herramientas = st.herramientas || {}; st.conversacion = st.conversacion || []; st.secciones = st.secciones || []; st.contextos = st.contextos || {}; st.parcial = st.parcial || '';
  // 137-138: texto confirmado de una vuelta que se corto a mitad (caida entre checkpoints): pasa a lo ya generado y el modelo CONTINUA desde ahi
  if (st.stream && typeof st.stream.texto === 'string') {
    if (st.stream.texto) { st.parcial += st.stream.texto; st.secciones.push({ n: st.secciones.length + 1, vuelta: st.stream.vuelta, pedido: modelo, usado: st.stream.usado || modelo, finish_reason: 'interrumpido', caracteres: st.stream.texto.length, ts: new Date().toISOString(), recuperado_de_stream: true }); }
    delete st.stream; st.estado = 'CONTINUAR'; st.fase = 'RESPUESTA_PARCIAL';
  }

  const uso = { visto: false, p: 0, c: 0, t: 0 };  // usage de las llamadas de ESTA ejecucion (no se persiste)
  // todos los guardados en cola (un volcado incremental no pisa a uno posterior); un fallo de un volcado incremental no rompe la generacion
  let cola = Promise.resolve();
  const guardar = (exigirRemoto = false) => {
    const p = cola.then(() => guardarCheckpoint(tareaId, st, exigirRemoto ? { ...ck, exigirRemoto: true } : ck));
    cola = p.catch(() => {}); return p;
  };
  const poner = (estado, fase = FASE[estado]) => { st.estado = estado; st.fase = fase; };
  const ultima = () => st.secciones[st.secciones.length - 1] || {};
  const salida = (o) => ({ salida: st.parcial, tool_calls: [], finish_reason: 'stop', via: ultima().via || null, usado: ultima().usado || null, servidor: ultima().servidor || null, ...(uso.visto ? { metricas: { prompt_tokens: uso.p, completion_tokens: uso.c, total_tokens: uso.t } } : {}), tarea_id: tareaId, estado: st.estado, fase: st.fase, secciones: st.secciones.length, reanudado, desde_checkpoint: false, ...o });
  const entregaLote = (o) => salida({ salida: st.lote.assistant.content || '', tool_calls: st.lote.assistant.tool_calls, finish_reason: 'tool_calls', ...o });

  // ---- 141: objetivo y operaciones previstas confirmados antes de que haya efectos ----
  const tieneTools = Array.isArray(extra.tools) && extra.tools.length > 0;
  if (extra.plan && typeof extra.plan === 'object') {
    const objetivo = typeof extra.plan.objetivo === 'string' ? extra.plan.objetivo.trim().slice(0, 2000) : '';
    const operaciones = Array.isArray(extra.plan.operaciones) ? extra.plan.operaciones.filter((x) => typeof x === 'string' && x.trim()).map((x) => x.trim().slice(0, 120)).slice(0, 100) : [];
    if (objetivo && operaciones.length && !st.plan) { st.plan = { objetivo: sanear(objetivo, secretos), operaciones, confirmado_en: new Date().toISOString() }; }
  }
  if (extra.exigirPlan && tieneTools && !st.plan) throw falla('PLAN_REQUERIDO', 'con herramientas (efectos) hay que confirmar el objetivo y las operaciones previstas antes de ejecutar (objetivo + operaciones_previstas)');
  const verificarPlan = (tcs) => {
    if (!st.plan) return;
    const fuera = tcs.map((c) => c.function?.name ?? c.name ?? '').filter((n) => !st.plan.operaciones.includes('*') && !st.plan.operaciones.includes(n));
    if (fuera.length) { throw falla('OPERACION_NO_PREVISTA', `el modelo pidio operaciones fuera de las confirmadas: ${[...new Set(fuera)].join(', ').slice(0, 200)}`); }
  };

  // ---- 140: finish_reason=stop NO cierra la tarea; solo la confirmacion del cliente/workflow ----
  const confirmar = async () => { if (st.estado === 'DONE') return; poner('DONE'); st.completo = true; st.confirmado_en = new Date().toISOString(); await guardar(); };
  if (st.estado === 'DONE' && st.resultado) return salida({ ...st.resultado, salida: st.resultado.salida, desde_checkpoint: true });
  if (st.estado === 'RESPUESTA_COMPLETA' && st.resultado) {  // ya respondio: se devuelve lo guardado, sin volver a llamar al modelo
    if (extra.confirmarCompleta) await confirmar();
    return salida({ ...st.resultado, salida: st.resultado.salida, desde_checkpoint: true });
  }
  if (st.estado === 'WAIT_TOOLS' && st.lote && !extra.ejecutarHerramienta) return entregaLote({ desde_checkpoint: true });  // las corre el Harness: mismos ids, sin volver a llamar al modelo

  // ---- streaming: lo entregado al cliente (extra.flujo) y el volcado incremental ----
  const transmite = typeof extra.onDelta === 'function';
  const cliente = extra.flujo && typeof extra.flujo === 'object' ? extra.flujo : { texto: '' };
  const aCliente = (t) => { if (!t) return; cliente.texto += t; try { extra.onDelta(t); } catch { /* un fallo del consumidor no corta al modelo */ } };
  const sincronizar = () => {  // lo ya generado (reanudacion) que ESTE cliente aun no recibio: una sola vez
    if (transmite && st.parcial.length > cliente.texto.length && st.parcial.startsWith(cliente.texto)) aCliente(st.parcial.slice(cliente.texto.length));
  };
  const flushChars = Math.max(1, extra.flushChars ?? FLUSH_CHARS), flushMs = Math.max(0, extra.flushMs ?? FLUSH_MS);

  let usadoV = null;  // proveedor que empezo a responder la vuelta en curso (onInicio)
  const llamar = async (msgs, flujoV, alDelta) => {
    const ex = { tools: extra.tools, tool_choice: extra.tool_choice };
    const opts = { ...extra.opts, continuaciones: 0 };  // una respuesta por vuelta: este bucle ya continua (finish_reason length) y guarda el checkpoint entre vueltas
    const st_ = transmite ? { onDelta: alDelta, flujo: flujoV, onInicio: (i) => { usadoV = i?.usado || null; try { extra.onInicio?.(i); } catch { /* informativo */ } } } : {};
    try { return await (esExterno(modelo) ? externo(modelo, msgs, { env, extra: ex, opts, ...st_ }) : local(modelo, msgs, { env, extra: ex, opts, ...st_ })); }
    catch (e1) {
      if (extra.sinRespaldo) throw Object.assign(falla(e1.code || 'MODELO_FALLO', sanear(String(e1.message), secretos)), Number.isInteger(e1.status) ? { status: e1.status } : {});  // el modelo pedido manda: no se cambia de modelo en silencio
      try { return await respaldo(msgs, { env, extra: ex, opts, ...st_ }); }  // con flujoV: el respaldo continua desde el texto ya entregado
      catch (e2) { throw falla(e2.code || 'RESPALDO_AGOTADO', sanear(`${e1.message} -> ${e2.message}`, secretos)); }
    }
  };

  // ---- herramientas del lote actual ----
  const registrar = async (t, resultado) => {
    if (usaBloques) { try { herramientaConfirmar(tareaId, t.id, resultado); } catch { /* el checkpoint propio lo guarda igual */ } }
    st.herramientas[t.id] = { resultado: sanear(resultado === undefined ? null : resultado, secretos), ts: new Date().toISOString() };
    t.estado = 'hecha'; st.fase = 'OPERACION_CONFIRMADA'; await guardar();
  };
  const yaHecha = (t) => {
    if (st.herramientas[t.id]) return true;
    if (usaBloques && herramientaEjecutada(tareaId, t.id)) { st.herramientas[t.id] = { resultado: herramientaResultado(tareaId, t.id), ts: new Date().toISOString() }; return true; }
    return false;
  };
  const resolverLote = async () => {
    const lote = st.lote;
    const sinConfirmar = lote.herramientas.filter((t) => !yaHecha(t) && t.estado === 'iniciada');
    if (sinConfirmar.length && !extra.verificarHerramienta) { poner('WAIT_TOOLS', 'RECONCILIAR'); await guardar(); throw falla('VERIFICAR_HERRAMIENTAS_PENDIENTES', `herramientas iniciadas sin confirmar (${sinConfirmar.map((t) => t.id).join(', ')}): verificar si se hicieron antes de reintentar`, { ids: sinConfirmar.map((t) => t.id) }); }
    for (const t of lote.herramientas) {
      if (yaHecha(t)) { t.estado = 'hecha'; continue; }
      if (t.estado === 'iniciada') {
        st.fase = 'RECONCILIAR';
        const v = await extra.verificarHerramienta({ ...t });
        if (v && v.hecha) { await registrar(t, v.resultado); continue; }
      }
      t.estado = 'iniciada'; st.fase = 'OPERACION_INICIADA';
      // Si hay Harness configurado, una escritura SOLO local no autoriza efectos.
      // Guardar + releer remoto antes de invocar el ejecutor; nunca asumir exito por disco efimero.
      await guardar(!!env.RIU_DEEPSEEK_HARNESS_URL);
      await registrar(t, await extra.ejecutarHerramienta({ ...t }));
    }
    st.conversacion.push(lote.assistant, ...lote.herramientas.map((t) => ({ role: 'tool', tool_call_id: t.id, content: JSON.stringify(st.herramientas[t.id].resultado) })));
    st.lote = null; st.parcial = ''; poner('CONTINUAR'); await guardar();
  };
  const idsUsados = () => new Set([...Object.keys(st.herramientas), ...st.conversacion.flatMap((m) => (m.tool_calls || []).map((t) => t.id))]);
  const unicas = (llamadas) => {
    const usados = idsUsados(), vistos = new Set();
    return llamadas.map((c, i) => {
      let id = typeof c.id === 'string' && c.id.trim() ? c.id.trim() : `tc_${tareaId}_${st.secciones.length}_${i}`, k = 1;
      const base = id;
      while (usados.has(id) || vistos.has(id)) id = `${base}__${++k}`;
      vistos.add(id);
      return { ...c, id };
    });
  };

  // ---- bucle ----
  let vueltas = 0;
  for (;;) {
    if (extra.opts?.signal?.aborted) throw cancelada();
    if (st.lote) await resolverLote();
    if (vueltas >= limite || (vueltas > 0 && extra.hasta && Date.now() > extra.hasta)) {  // fuera de tope/plazo: lo parcial; el siguiente llamado sigue desde el checkpoint
      poner('CONTINUAR'); await guardar();
      return salida({ finish_reason: 'length', parcial: true });
    }
    sincronizar();
    const msgs = [...mensajes, ...st.conversacion, ...(st.parcial ? [{ role: 'assistant', content: st.parcial }, { role: 'user', content: CONTINUAR }] : [])];
    vueltas++;
    const n = st.secciones.length + 1, flujoV = { texto: '' };
    let pend = 0, ultimoVolcado = Date.now(); usadoV = null;
    const alDelta = (t) => {  // fragmento real del proveedor: al cliente al instante y, por bloques, al checkpoint (texto confirmado)
      aCliente(t); pend += t.length;
      if (pend >= flushChars || Date.now() - ultimoVolcado >= flushMs) {
        pend = 0; ultimoVolcado = Date.now();
        st.stream = { vuelta: vueltas, usado: usadoV || modelo, texto: flujoV.texto }; poner('CONTINUAR', 'RESPUESTA_PARCIAL');
        guardar().catch(() => {});
      }
    };
    let r;
    try { r = await llamar(msgs, flujoV, alDelta); }
    catch (e) {
      await cola;  // lo volcado en curso termina antes de decidir
      if (transmite && flujoV.texto) { st.parcial += flujoV.texto; st.secciones.push({ n, vuelta: vueltas, pedido: modelo, usado: usadoV || modelo, finish_reason: 'interrumpido', caracteres: flujoV.texto.length, ts: new Date().toISOString() }); }  // lo recibido se conserva: el reintento continua desde ahi
      delete st.stream;
      st.estado = 'ERROR'; st.fase = st.parcial ? 'RESPUESTA_PARCIAL' : 'ERROR'; st.ultimo_error = String(sanear(e.message, secretos)).slice(0, 500); await guardar(); throw e;
    }
    delete st.ultimo_error; delete st.stream;

    const usado = r.usado || modelo, texto = r.salida || '';
    const m = r.metricas;
    if (m && Number.isFinite(m.total_tokens)) { uso.visto = true; uso.p += m.prompt_tokens || 0; uso.c += m.completion_tokens || 0; uso.t += m.total_tokens; }
    st.secciones.push({ n, vuelta: vueltas, pedido: modelo, usado, via: r.via, ...(r.servidor ? { servidor: r.servidor } : {}), finish_reason: r.finish_reason, caracteres: texto.length, ts: new Date().toISOString() });
    const cx = st.contextos[usado] || { secciones: [], caracteres: 0 };
    st.contextos[usado] = { secciones: [...cx.secciones, n], caracteres: cx.caracteres + texto.length };
    st.parcial += texto;
    if (transmite && !r.tool_calls?.length) sincronizar();  // lo que no llego por streaming (p. ej. modelo local HF) se entrega ahora

    const llamadas = Array.isArray(r.tool_calls) ? r.tool_calls : [];
    if (Array.isArray(r.tools_invalidas) && r.tools_invalidas.length) {
      poner('ERROR'); st.ultimo_error = 'TOOL_CALL_INVALIDA'; await guardar();
      throw falla('TOOL_CALL_INVALIDA', 'Tool calls invalidas: checkpoint guardado sin ejecutar efectos');
    }
    if (llamadas.length) {
      const tcs = unicas(llamadas);
      try { verificarPlan(tcs); } catch (e) { poner('ERROR'); st.ultimo_error = String(e.message).slice(0, 500); await guardar(); throw e; }
      st.lote = { assistant: { role: 'assistant', content: st.parcial || null, tool_calls: tcs }, herramientas: tcs.map((c) => ({ id: c.id, nombre: c.function?.name ?? c.name ?? null, argumentos: c.function?.arguments ?? c.arguments ?? null, estado: 'pendiente' })) };
      poner('WAIT_TOOLS'); await guardar();
      if (!extra.ejecutarHerramienta) return entregaLote({ finish_reason: 'tool_calls' });
      continue;
    }
    if (r.finish_reason === 'length') { poner('CONTINUAR'); await guardar(); continue; }
    // finish_reason=stop: la RESPUESTA termino, la tarea no se da por terminada hasta confirmarlo
    poner('RESPUESTA_COMPLETA'); st.completo = false;
    st.resultado = { salida: st.parcial, tool_calls: [], finish_reason: r.finish_reason || 'stop', via: r.via, usado };
    await guardar();
    if (extra.confirmarCompleta) await confirmar();
    return salida({ finish_reason: st.resultado.finish_reason });
  }
}

// retoma una tarea SOLO con su id, con el modelo y los mensajes guardados en el checkpoint (POST /v1/secciones/:id/retomar).
// null si no hay checkpoint de este sistema (p. ej. es una seccion web); {yaCompleto:true} si la tarea esta confirmada (DONE).
// extra.propietario: quien pide (TAREA_AJENA si no es el dueño). extra.interno: la propia puesta en marcha del bridge retoma en nombre del dueño guardado.
export async function retomarPorId(id, extra = {}) {
  let ck;
  try { ck = await leerCheckpoint(id, { env: extra.env, fetch: extra.fetch, timeoutMs: extra.timeoutCheckpointMs }); }
  catch (e) { if (e.code === 'CHECKPOINT_CORRUPTO') throw e; return null; }
  if (!ck || ck.tipo !== TIPO) return null;
  const ex = extra.interno ? { ...extra, propietario: ck.vinculo?.propietario } : extra;
  verificarVinculo(JSON.parse(JSON.stringify(ck)), ex);  // 130: nadie recupera una tarea ajena (ni su estado) solo con el id
  if (ck.estado === 'DONE' || ck.completo) return { yaCompleto: true };
  return retomarLocal(id, ck.modelo, ck.mensajes, ex);
}
