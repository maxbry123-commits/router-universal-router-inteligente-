// retomar_local.js — recuperacion (checkpoint universal) para modelos locales HF (lfm2.5-350m, qwen2.5-coder-1.5b, qwen3.5-0.8b, qwen3-0.6b), Groq y NVIDIA.
// retomarLocal(tareaId, modelo, mensajes, extra): hasta 12 vueltas con local()/externo() y, si fallan, respaldo(); el checkpoint se guarda tras CADA seccion
// (checkpoint_hf.js: Harness DeepSeek + local), de modo que un reinicio o una caida de API continua donde quedo y no repite lo hecho.
//   - misma tarea = misma huella sha256([modelo, mensajes]); otro contenido con el mismo tarea_id -> CHECKPOINT_OTRA_TAREA
//   - DONE: devuelve el resultado guardado SIN llamar al modelo
//   - continua SOLO si finish_reason === 'length' (asistente parcial + "Continua exactamente donde termino")
//   - tool_calls: cada una con id unico y su resultado guardado; una ya hecha no se repite; una "iniciada" sin resultado se VERIFICA antes de reintentar
//     (extra.verificarHerramienta) o se corta con VERIFICAR_HERRAMIENTAS_PENDIENTES. Sin extra.ejecutarHerramienta (las corre el Harness) se devuelven tal cual (WAIT_TOOLS).
//   - contexto separado por modelo: contextos[<modelo que respondio>] = secciones que dio; al cambiar de API el nuevo modelo recibe el texto ya generado, no el estado del otro
// Estados (vocabulario de bloques.js): CONTINUAR | WAIT_TOOLS | DONE | ERROR. Nunca se guardan claves.
// extra: { env, tools, tool_choice, opts (red de respaldo.js), ejecutarHerramienta(t), verificarHerramienta(t), hasta (epoch ms), maxVueltas, fetch, timeoutCheckpointMs }
import crypto from 'node:crypto';
import path from 'node:path';
import { local, externo, respaldo, esLocal, esExterno, claves } from './respaldo.js';
import { guardarCheckpoint, leerCheckpoint, sanear, idValido } from './checkpoint_hf.js';
import { estadoDir, herramientaEjecutada, herramientaResultado, herramientaConfirmar } from './bloques.js';

export const TIPO = 'retomar_local';
export const MAX_VUELTAS = 12;
const CONTINUAR = 'Continúa exactamente donde terminó, sin repetir';

const falla = (code, message, detail) => Object.assign(new Error(message), { code, ...(detail ? { detail } : {}) });
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

export async function retomarLocal(tareaId, modelo, mensajes, extra = {}) {
  if (!idValido(tareaId)) throw falla('TAREA_ID_INVALIDO', 'tarea_id: letras, numeros, - y _ (1 a 64)');
  if (!esLocal(modelo) && !esExterno(modelo)) throw falla('MODELO_NO_SOPORTADO', 'solo modelos locales HF o groq/ nvidia/: ' + String(modelo).slice(0, 60));
  if (!Array.isArray(mensajes)) throw falla('MENSAJES_INVALIDOS', 'mensajes debe ser una lista');
  return bajoCerrojo(tareaId, () => ejecutar(tareaId, modelo, mensajes, extra || {}));
}

async function ejecutar(tareaId, modelo, mensajes, extra) {
  const env = extra.env || process.env, secretos = secretosDe(env);
  const ck = { env, fetch: extra.fetch, timeoutMs: extra.timeoutCheckpointMs, secretos };
  const limite = Math.min(extra.maxVueltas || MAX_VUELTAS, MAX_VUELTAS);
  // los ayudantes de herramientas de bloques.js leen BRIDGE_STATE_DIR del proceso: solo se usan si es el mismo directorio que el de este checkpoint
  const usaBloques = path.resolve(env.BRIDGE_STATE_DIR || estadoDir()) === estadoDir();
  const huella = huellaDe(modelo, mensajes, secretos);

  let st = await leerCheckpoint(tareaId, ck);
  const reanudado = !!st;
  if (st && (st.tipo !== TIPO || st.huella !== huella)) throw falla('CHECKPOINT_OTRA_TAREA', `el checkpoint ${tareaId} es de otra tarea (otros mensajes o modelo): usa otro tarea_id`);
  if (!st) st = { tipo: TIPO, version: 1, tarea_id: tareaId, huella, modelo, mensajes: sanear(mensajes, secretos), estado: 'CONTINUAR', completo: false, conversacion: [], parcial: '', secciones: [], contextos: {}, herramientas: {}, lote: null, resultado: null, creado: new Date().toISOString() };
  st.herramientas = st.herramientas || {}; st.conversacion = st.conversacion || []; st.secciones = st.secciones || []; st.contextos = st.contextos || {}; st.parcial = st.parcial || '';

  const guardar = () => guardarCheckpoint(tareaId, st, ck);
  const ultima = () => st.secciones[st.secciones.length - 1] || {};
  const salida = (o) => ({ salida: st.parcial, tool_calls: [], finish_reason: 'stop', via: ultima().via || null, usado: ultima().usado || null, tarea_id: tareaId, estado: st.estado, secciones: st.secciones.length, reanudado, desde_checkpoint: false, ...o });
  const entregaLote = (o) => salida({ salida: st.lote.assistant.content || '', tool_calls: st.lote.assistant.tool_calls, finish_reason: 'tool_calls', ...o });

  if (st.estado === 'DONE' && st.resultado) return salida({ ...st.resultado, salida: st.resultado.salida, desde_checkpoint: true });
  if (st.estado === 'WAIT_TOOLS' && st.lote && !extra.ejecutarHerramienta) return entregaLote({ desde_checkpoint: true });  // las corre el Harness: mismos ids, sin volver a llamar al modelo

  const llamar = async (msgs) => {
    const ex = { tools: extra.tools, tool_choice: extra.tool_choice };
    try { return await (esExterno(modelo) ? externo(modelo, msgs, { env, extra: ex, opts: extra.opts }) : local(modelo, msgs, { env, extra: ex, opts: extra.opts })); }
    catch (e1) {
      try { return await respaldo(msgs, { env, extra: ex, opts: extra.opts }); }
      catch (e2) { throw falla(e2.code || 'RESPALDO_AGOTADO', sanear(`${e1.message} -> ${e2.message}`, secretos)); }
    }
  };

  // ---- herramientas del lote actual ----
  const registrar = async (t, resultado) => {
    if (usaBloques) { try { herramientaConfirmar(tareaId, t.id, resultado); } catch { /* el checkpoint propio lo guarda igual */ } }
    st.herramientas[t.id] = { resultado: sanear(resultado === undefined ? null : resultado, secretos), ts: new Date().toISOString() };
    t.estado = 'hecha'; await guardar();
  };
  const yaHecha = (t) => {
    if (st.herramientas[t.id]) return true;
    if (usaBloques && herramientaEjecutada(tareaId, t.id)) { st.herramientas[t.id] = { resultado: herramientaResultado(tareaId, t.id), ts: new Date().toISOString() }; return true; }
    return false;
  };
  const resolverLote = async () => {
    const lote = st.lote;
    const sinConfirmar = lote.herramientas.filter((t) => !yaHecha(t) && t.estado === 'iniciada');
    if (sinConfirmar.length && !extra.verificarHerramienta) throw falla('VERIFICAR_HERRAMIENTAS_PENDIENTES', `herramientas iniciadas sin confirmar (${sinConfirmar.map((t) => t.id).join(', ')}): verificar si se hicieron antes de reintentar`, { ids: sinConfirmar.map((t) => t.id) });
    for (const t of lote.herramientas) {
      if (yaHecha(t)) { t.estado = 'hecha'; continue; }
      if (t.estado === 'iniciada') {
        const v = await extra.verificarHerramienta({ ...t });
        if (v && v.hecha) { await registrar(t, v.resultado); continue; }
      }
      t.estado = 'iniciada'; await guardar();  // marca ANTES de ejecutar: si el proceso muere aqui, el reintento sabe que hay que verificar
      await registrar(t, await extra.ejecutarHerramienta({ ...t }));
    }
    st.conversacion.push(lote.assistant, ...lote.herramientas.map((t) => ({ role: 'tool', tool_call_id: t.id, content: JSON.stringify(st.herramientas[t.id].resultado) })));
    st.lote = null; st.parcial = ''; st.estado = 'CONTINUAR'; await guardar();
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
    if (st.lote) await resolverLote();
    if (vueltas >= limite || (vueltas > 0 && extra.hasta && Date.now() > extra.hasta)) {  // fuera de tope/plazo: lo parcial; el siguiente llamado sigue desde el checkpoint
      st.estado = 'CONTINUAR'; await guardar();
      return salida({ finish_reason: 'length', parcial: true });
    }
    const msgs = [...mensajes, ...st.conversacion, ...(st.parcial ? [{ role: 'assistant', content: st.parcial }, { role: 'user', content: CONTINUAR }] : [])];
    vueltas++;
    let r;
    try { r = await llamar(msgs); }
    catch (e) { st.estado = 'ERROR'; st.ultimo_error = String(sanear(e.message, secretos)).slice(0, 500); await guardar(); throw e; }
    delete st.ultimo_error;

    const usado = r.usado || modelo, n = st.secciones.length + 1, texto = r.salida || '';
    st.secciones.push({ n, vuelta: vueltas, pedido: modelo, usado, via: r.via, finish_reason: r.finish_reason, caracteres: texto.length, ts: new Date().toISOString() });
    const cx = st.contextos[usado] || { secciones: [], caracteres: 0 };
    st.contextos[usado] = { secciones: [...cx.secciones, n], caracteres: cx.caracteres + texto.length };
    st.parcial += texto;

    const llamadas = Array.isArray(r.tool_calls) ? r.tool_calls : [];
    if (llamadas.length) {
      const tcs = unicas(llamadas);
      st.lote = { assistant: { role: 'assistant', content: st.parcial || null, tool_calls: tcs }, herramientas: tcs.map((c) => ({ id: c.id, nombre: c.function?.name ?? c.name ?? null, argumentos: c.function?.arguments ?? c.arguments ?? null, estado: 'pendiente' })) };
      st.estado = 'WAIT_TOOLS'; await guardar();
      if (!extra.ejecutarHerramienta) return entregaLote({ finish_reason: 'tool_calls' });
      continue;
    }
    if (r.finish_reason === 'length') { st.estado = 'CONTINUAR'; await guardar(); continue; }
    st.estado = 'DONE'; st.completo = true;
    st.resultado = { salida: st.parcial, tool_calls: [], finish_reason: r.finish_reason || 'stop', via: r.via, usado };
    await guardar();
    return salida({ finish_reason: st.resultado.finish_reason });
  }
}

// retoma una tarea SOLO con su id, con el modelo y los mensajes guardados en el checkpoint (POST /v1/secciones/:id/retomar).
// null si no hay checkpoint de este sistema (p. ej. es una seccion web); {yaCompleto:true} si ya termino.
export async function retomarPorId(id, extra = {}) {
  let ck;
  try { ck = await leerCheckpoint(id, { env: extra.env, fetch: extra.fetch, timeoutMs: extra.timeoutCheckpointMs }); } catch { return null; }
  if (!ck || ck.tipo !== TIPO) return null;
  if (ck.estado === 'DONE' || ck.completo) return { yaCompleto: true };
  return retomarLocal(id, ck.modelo, ck.mensajes, extra);
}
