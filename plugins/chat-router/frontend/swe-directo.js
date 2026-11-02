// swe-directo.js — los modelos de SWE CODE / SWEN CODE free del selector responden por su router propio (el bridge), sin pasar por el Router MVP.
// El chat llama POST /v1/chat/completions del mismo origen (el proxy del Space manda web-* y swecode-* al bridge); mismo historial, misma sesion.
import { conReintentos, clasificar, estadoReparacion } from "./swe-autorepair.js";

const REAL = { "hf-liquid-lfm25": "lfm2.5-350m", "swe-agent-lfm25": "lfm2.5-350m", "swe-openhands-lfm25": "lfm2.5-350m",
  "swe-codex-qwen25-15b": "qwen2.5-coder-1.5b", "hf-qwen25-coder-15b": "qwen2.5-coder-1.5b", "swe-opencode-qwen35-08b": "qwen3.5-0.8b", "hf-qwen35-08b": "qwen3.5-0.8b", "hf-qwen3-06b": "qwen3-0.6b" };
const LOCALES = ["lfm2.5-350m", "qwen2.5-coder-1.5b", "qwen3.5-0.8b", "qwen3-0.6b"];
const MAX_HISTORIAL = 20;

export const SWE_LISTAS = {
  "swe-code": { nombre: "SWE CODE", titulo: "SWE CODE · modelos locales (HF)", modelos: [
    ["hf-liquid-lfm25", "Liquid LFM2.5 350M", "HF local"],
    ["hf-qwen25-coder-15b", "Qwen2.5 Coder 1.5B", "HF local"],
    ["hf-qwen35-08b", "Qwen3.5 0.8B", "HF local"],
    ["hf-qwen3-06b", "Qwen3 0.6B", "HF local"]] },
  "swen-code-free": { nombre: "SWEN CODE free", titulo: "SWEN CODE free · cuentas web", modelos: [
    ["swecode-consulta", "Concilio · los 3 web", "los 3 modelos web a la vez + síntesis"],
    ["web-qwen38max", "Qwen 3.8 Max (web)", "Código complejo · via bridge"],
    ["web-qwen37max", "Qwen 3.7 Max (web)", "Razonamiento · via bridge"],
    ["web-dsv4-flash", "DeepSeek V4 Flash (web)", "Código rápido · via bridge"],
    ["hf-liquid-lfm25", "Liquid LFM2.5 350M", "HF local"],
    ["hf-qwen25-coder-15b", "Qwen2.5 Coder 1.5B", "HF local"],
    ["hf-qwen35-08b", "Qwen3.5 0.8B", "HF local"],
    ["hf-qwen3-06b", "Qwen3 0.6B", "HF local"],
    ["groq/qwen/qwen3.8-27b", "Qwen 3.8 Groq", "API Groq"],
    ["nvidia/minimaxai/minimax-m3.1-flash", "MiniMax M3.1 Flash", "API NVIDIA"],
    ["nvidia/meta/muse-glimmer-30b", "Muse Glimmer 30B", "API NVIDIA"],
    ["nvidia/nvidia/nemotron-3-ultra-550b-a55b", "Nemotron 3 Ultra", "API NVIDIA"],
    ["nvidia/z-ai/glm-5.3", "GLM 5.3", "API NVIDIA"]] },
};
export const MODELOS_WEB = [["swecode-consulta", "Concilio · los 3 web"], ["web-qwen38max", "Qwen 3.8 Max (web)"], ["web-qwen37max", "Qwen 3.7 Max (web)"], ["web-dsv4-flash", "DeepSeek V4 Flash (web)"]];
export const MODOS_TRABAJO = [["asesoria", "Asesoría"], ["revision", "Revisión"], ["solucion", "Solución"], ["arquitectura", "Arquitectura"], ["archivos", "Archivos"], ["prompt_code", "Prompt code"], ["despliega", "Despliega"]];
export const esSelectorSwe = (id) => typeof id === "string" && Object.hasOwn(SWE_LISTAS, id);
export const esSwe = (id) => typeof id === "string" && (/^(web-|swecode-|groq\/|nvidia\/|deepseek\/|minimax\/|openai\/)/.test(id) || Object.hasOwn(REAL, id) || LOCALES.includes(id) || (id.startsWith("hf/") && LOCALES.includes(id.slice(3))));
export const EJECUTORES_TOOLS = ["swe", "openclaw"];
const normEjecutor = (v) => (EJECUTORES_TOOLS.includes(v) ? v : "swe");
export const ejecutorDeAgente = (agente) => (agente === "openclaw" ? "openclaw" : "swe");
export function leerEjecutorTools() { return ejecutorDeAgente(leerSeleccion().agente_tool); }
export const MODELOS_SWE = [
  ["hf/lfm2.5-350m", "Liquid LFM2.5 350M"],
  ["hf/qwen2.5-coder-1.5b", "Qwen2.5 Coder 1.5B"],
  ["hf/qwen3.5-0.8b", "Qwen3.5 0.8B"],
  ["hf/qwen3-0.6b", "Qwen3 0.6B"],
];
export const AGENTES_SWE = [["openclaw", "OpenClaw"], ["swe-agent", "SWE-agent"], ["openhands", "OpenHands"], ["opencode", "OpenCode"], ["codex", "Codex"], ["claude-code", "Claude Code"]];
export const WORKFLOWS_SWE = [["individual", "Individual"], ["swe_code", "SWE CODE cuatro pasos"], ["liquid_mirror", "Liquid Mirror"]];
export const LIQUID_MIRROR = [{ id: "liquid1", etiqueta: "LIQUID 1 — LECTOR", servidor: "S2", modelo: "hf/lfm2.5-350m" }, { id: "liquid2", etiqueta: "LIQUID 2 — EJECUTOR", servidor: "S3", modelo: "hf/lfm2.5-350m" }];
const LIQUID = "hf/lfm2.5-350m", REVISOR = "hf/qwen3.5-0.8b", VERIFICADOR = "openhands";
export const SEL_DEFECTO = { modelo_responde: LIQUID, modelo_tool: "hf/qwen2.5-coder-1.5b", agente_responde: "openclaw", agente_tool: "swe-agent", modo_agentico: false, workflow: "individual", modo_trabajo: "" };
const K_SEL = "riu_swe_seleccion";
const en = (lista, v) => typeof v === "string" && lista.some((x) => x[0] === v);
function normSeleccion(x, base) {
  const o = x && typeof x === "object" ? x : {};
  return {
    modelo_responde: en(MODELOS_SWE, o.modelo_responde) || en(MODELOS_WEB, o.modelo_responde) ? o.modelo_responde : base.modelo_responde,
    modelo_tool: en(MODELOS_SWE, o.modelo_tool) ? o.modelo_tool : base.modelo_tool,
    agente_responde: en(AGENTES_SWE, o.agente_responde) ? o.agente_responde : base.agente_responde,
    agente_tool: en(AGENTES_SWE, o.agente_tool) ? o.agente_tool : base.agente_tool,
    modo_agentico: typeof o.modo_agentico === "boolean" ? o.modo_agentico : base.modo_agentico,
    workflow: en(WORKFLOWS_SWE, o.workflow) ? o.workflow : base.workflow,
    modo_trabajo: o.modo_trabajo === "" || en(MODOS_TRABAJO, o.modo_trabajo) ? o.modo_trabajo : base.modo_trabajo || "" };
}
export function leerSeleccion() { try { return normSeleccion(JSON.parse(localStorage.getItem(K_SEL) || "{}"), SEL_DEFECTO); } catch (e) { return { ...SEL_DEFECTO }; } }
function escribirSeleccion(sel) { try { localStorage.setItem(K_SEL, JSON.stringify(sel)); } catch (e) {} return sel; }
export function guardarSeleccion(parcial) {
  return escribirSeleccion(normSeleccion({ ...leerSeleccion(), ...(parcial && typeof parcial === "object" ? parcial : {}) }, leerSeleccion()));
}
export const requiereHarness = (sel) => !!sel && (sel.workflow !== "individual" || sel.modo_agentico === true);
export function idCatalogo(id) {
  const real = Object.hasOwn(REAL, id) ? REAL[id] : id;
  if (LOCALES.includes(real)) return "hf/" + real;
  return en(MODELOS_SWE, id) ? id : null;
}
export const camposFijos = (workflow) => new Set(workflow === "swe_code" || workflow === "liquid_mirror" ? ["modelo_responde", "agente_responde", "modelo_tool"] : []);
export function entradaParaCatalogo(lista, cat, actual) {
  const l = SWE_LISTAS[lista]; if (!l) return null;
  const m = l.modelos.find((x) => idCatalogo(x[0]) === cat);
  return m ? m[0] : actual;
}
export function modeloParaLista(lista, cat, actual) {
  const mid = entradaParaCatalogo(lista, cat, actual);
  return mid || actual;
}
export function modeloGuardado(lista, guardado) {
  const l = SWE_LISTAS[lista], ent = l.modelos.find((x) => x[0] === guardado);
  const cat = typeof guardado === "string" ? idCatalogo(guardado) : null;
  return ent ? guardado : (cat ? modeloParaLista(lista, cat, l.modelos[0][0]) : l.modelos[0][0]);
}
export const AGENTE_CORTO = { codex: "Codex", opencode: "OpenCode", "swe-agent": "SWE-agent", openhands: "OpenHands", openclaw: "OpenClaw", "claude-code": "Claude Code" };
const ident = (v, defecto) => { const t = String(v == null ? "" : v).replace(/[^A-Za-z0-9_-]/g, "-").slice(0, 64); return t || defecto; };

let _cap = { t: 0, v: null };
const capVigente = () => !!_cap.v && Date.now() - _cap.t < 30000;
export const olvidarCapacidades = () => { _cap = { t: 0, v: null }; };
export async function cargarCapacidades(api, { forzar = false } = {}) {
  if (!forzar && capVigente()) return _cap.v;
  let v;
  try {
    v = await conReintentos(() => api("/chat/swe/capacidades"), { max: 2, onLog: (t) => estadoReparacion(t) });
    v = normalizarCapacidades(v);
  } catch (e) { v = normalizarCapacidades(null); v.harness = "sin_respuesta"; }
  _cap = { t: Date.now(), v };
  return v;
}

const TERMINALES = ["DONE", "GAP", "REQUIERE_APROBACION", "RECONCILIAR"];
export const MAX_AVANCES = 24;
const PARA_CHATEAR = "Para chatear: abre SWE CODE/SWEN → Agentes → Modo agéntico OFF y Workflow Individual";
const PARA_AGENTICO = "Enciende SWE CODE/SWEN → Agentes → Modo agéntico ON, o elige Workflow Individual";
const TASK_RE = /^[A-Za-z0-9_-]{1,64}$/, OP_RE = /^[A-Za-z0-9_-]{1,80}$/;
const resultadoDe = (r, op) => {
  const x = r && r.ok === true ? r.resultado : null;
  if (!x || typeof x !== "object") throw new Error("GAP: SWE_HARNESS_ERROR · " + op + " sin resultado");
  return x;
};
const DETENIDO = "PROCESO_DETENIDO";
async function operacion(api, op, cuerpo, signal, headers) {
  let r;
  try {
    r = await conReintentos(
      () => api("/chat/swe/" + op, { method: "POST", body: cuerpo, ...(signal ? { signal } : {}), ...(headers ? { headers } : {}) }),
      { max: 3, onLog: (t) => estadoReparacion(t), clasificar }
    );
  } catch (e) {
    const m = String((e && e.message) || e);
    if (m === DETENIDO) throw new Error(DETENIDO);
    const g = new Error(m.startsWith("GAP:") ? m : "GAP: " + (/^[A-Z][A-Z0-9_]+\b/.test(m) ? m : "SWE_HARNESS_ERROR · " + m));
    if (e && e.status) g.status = e.status;
    throw g;
  }
  return resultadoDe(r, op);
}
const base = ({ task_id, sesion, proyecto }) => {
  if (!TASK_RE.test(String(task_id))) throw new Error("GAP: TASK_ID_INVALIDO");
  return { task_id, origen: "yaiwes", sesion: ident(sesion, ""), proyecto: ident(proyecto, "yaiwes") };
};
export const estadoTareaSwe = async (api, d) => operacion(api, "estado", base(d), d.signal);
export const reanudarTareaSwe = async (api, d) => operacion(api, "reanudar", base(d), d.signal);
export const aprobarTareaSwe = async (api, d) => {
  if (typeof d.op_id !== "string" || !OP_RE.test(d.op_id)) throw new Error("GAP: OP_ID_INVALIDO");
  return operacion(api, "aprobar", { ...base(d), op_id: d.op_id }, d.signal, d.headers);
};
const lineaEvidencia = (e) => (typeof e === "string" ? e : JSON.stringify(e)).slice(0, 300);
const texto = (v) => (typeof v === "string" ? v : v == null ? "" : JSON.stringify(v));
function aRespuesta(x, tarea) {
  const estado = String(x.estado || ""), pasos = Array.isArray(x.pasos_terminados) ? x.pasos_terminados.filter((p) => p && typeof p === "object") : [];
  const idTarea = x.task_id || tarea.task_id;
  if (estado === "GAP") { const e = x.error && typeof x.error === "object" ? x.error : { codigo: x.codigo, mensaje: x.error }; throw new Error("GAP: " + (e.codigo || "GAP") + (e.mensaje ? " · " + texto(e.mensaje) : "")); }
  return { estado, pasos, idTarea, x };
}
export async function enviarTareaSwe(api, { mensaje, sesion, proyecto, task_id, alPaso, parar, signal }) {
  const sel = leerSeleccion();
  const tarea = armarTarea({ sel, mensaje, sesion, proyecto, task_id });
  const r = await operacion(api, "iniciar", tarea, signal);
  return aRespuesta(r, tarea);
}
export async function aprobarYContinuarSwe(api, d, alPaso) {
  const tarea = armarTarea({ sel: leerSeleccion(), mensaje: "(continuación)", sesion: d.sesion, proyecto: d.proyecto, task_id: base(d).task_id });
  const r = await operacion(api, "continuar", { ...base(d), op_id: d.op_id }, d.signal, d.headers);
  return aRespuesta(r, tarea);
}
export function armarTarea({ sel, mensaje, sesion, proyecto, task_id }) {
  return { ...base({ task_id, sesion, proyecto }), mensaje, sel, ejecutor_tools: ejecutorDeAgente(sel.agente_tool) };
}
export function armar({ model, historial = [], mensaje, imagenes = [], sesion, proyecto, ejecutor_tools, modo, tools = false, agente_tool = false, llm_tool = false }) {
  return { model, messages: [...(historial || []).slice(-MAX_HISTORIAL), { role: "user", content: mensaje }], sesion, proyecto, ejecutor_tools: ejecutor_tools || leerEjecutorTools(), modo, tools, agente_tool, llm_tool };
}

export async function leerSSE(response, alEvento, signal) {
  const rd = response.body.getReader(), dec = new TextDecoder();
  let buf = "";
  const cortar = () => { try { rd.cancel().catch(() => {}); } catch (e) {} };
  while (true) {
    if (signal && signal.aborted) { cortar(); throw new Error(DETENIDO); }
    let r; try { r = await rd.read(); } catch (e) { if (signal && signal.aborted) throw new Error(DETENIDO); throw e; }
    if (r.done) break;
    buf += dec.decode(r.value, { stream: true });
    let i; while ((i = buf.indexOf("\n\n")) >= 0) {
      const linea = buf.slice(0, i); buf = buf.slice(i + 2);
      if (!linea.startsWith("data:")) continue;
      const t = linea.slice(5).trim();
      if (t === "[DONE]") return;
      let o; try { o = JSON.parse(t); } catch (e) { return; }
      if (typeof alEvento === "function") alEvento(o);
    }
  }
}
export async function respuestaDeSSE(response, datos) {
  const a = { texto: "", llamadas: [], fin: null, error: null, extra: {} };
  await leerSSE(response, (o) => {
    if (o.error && typeof o.error === "object") a.error = o.error;
    const d = o.choices && o.choices[0] && o.choices[0].delta || {};
    if (typeof d.content === "string" && d.content) { a.texto += d.content; if (typeof datos.alParcial === "function") { try { datos.alParcial(a.texto); } catch (e) {} } }
    if (Array.isArray(d.tool_calls)) a.llamadas.push(...d.tool_calls);
    const c = o.choices && o.choices[0];
    if (c && c.finish_reason) a.fin = c.finish_reason;
  }, datos.signal);
  if (a.fin === "error" && !a.error) a.error = { code: "STREAM_ERROR", message: "el servidor cerró el stream con error" };
  if (!a.error && !a.fin && (a.texto || a.llamadas.length)) a.error = { code: "STREAM_CORTADO", message: "el stream terminó sin finish_reason" };
  return { ...a.extra, ...(a.error ? { error: a.error } : {}), choices: [{ message: { content: a.texto, ...(a.llamadas.length ? { tool_calls: a.llamadas.filter(Boolean) } : {}) }, finish_reason: a.error ? "error" : a.fin }] };
}

export async function enviarSwe(api, datos) {
  const cuerpo = armar(datos), opc = { method: "POST", body: cuerpo, sse: true };
  if (datos.signal) opc.signal = datos.signal;
  let r = await api(rutaSwe(datos.model), opc);
  if (r && r.__sse) r = await respuestaDeSSE(r.__sse, datos);
  const msg = (r && r.choices && r.choices[0] && r.choices[0].message) || {};
  const llamadas = Array.isArray(msg.tool_calls) ? msg.tool_calls.filter(Boolean) : [];
  const nombres = llamadas.map((t) => (t && t.function && t.function.name) || "tool"), quien = cuerpo.ejecutor_tools === "openclaw" ? "OpenClaw" : "SWE-agent";
  if (!msg.content && llamadas.length) return { reply: "Tools pedidas: " + nombres.join(", "), tools: [], pedidas: nombres, tool_calls: llamadas, ejecutor: quien, finish_reason: r.choices[0].finish_reason || "tool_calls", nota: `SWE · ${r.modelo_usado || datos.model} · tools → ${quien}` };
  const texto = msg.content;
  if (!texto) {
    const e = (r && r.error) || {};
    throw new Error("GAP: " + (e.code || "SIN_RESPUESTA") + (e.message ? " · " + e.message : ""));
  }
  const via = r.via_respaldo ? ` · respondió ${r.via_respaldo}` : r.via_primaria ? ` · vía ${r.via_primaria}` : "";
  if (r.error && r.choices[0].finish_reason === "error") {
    return { reply: texto, tools: [], ...(llamadas.length ? { pedidas: nombres, tool_calls: llamadas, ejecutor: quien } : {}), finish_reason: "error", nota: `SWE · ${r.modelo_usado || datos.model}${via} · GAP: ${r.error.code || "STREAM_ERROR"}${r.error.message ? " · " + r.error.message : ""} (respuesta parcial)` };
  }
  return { reply: texto, tools: [], ...(llamadas.length ? { pedidas: nombres, tool_calls: llamadas, ejecutor: quien } : {}), finish_reason: r.choices[0].finish_reason || (llamadas.length ? "tool_calls" : null), nota: `SWE · ${r.modelo_usado || datos.model}${via}${llamadas.length ? " · tools → " + quien : ""}` };
}

function rutaSwe(model) { return "/v1/chat/completions"; }
function normalizarCapacidades(v) { return v && typeof v === "object" ? v : { harness: "sin_respuesta", agentes: [], modelos: [] }; }
export const ETIQUETA_ESTADO = { OK: "", SIN_VERIFICAR: "sin verificar", NO_INSTALADO: "no instalado", NO_CONFIGURADO: "sin clave", NO_DISPONIBLE: "no disponible" };
export function estadoOpcion(cap, tipo, id, extra) {
  const lista = tipo === "agente" ? (cap.agentes || []) : (cap.modelos || []);
  const e = lista.find((x) => x.id === id);
  if (!e) return { ok: false, estado: "SIN_VERIFICAR", motivo: "no reportado" };
  return { ok: e.ok !== false, estado: e.estado || (e.ok !== false ? "OK" : "NO_DISPONIBLE"), motivo: e.motivo || "" };
}
export function opcionesModeloVentana(w, cap, prov, opts = {}) {
  const lista = w === "swen-code-free" ? SWE_LISTAS["swen-code-free"].modelos : SWE_LISTAS["swe-code"].modelos;
  return lista.map(([id, n, desc]) => {
    const cat = idCatalogo(id) || id;
    const st = estadoOpcion(cap, "modelo", cat);
    return { id: cat, nombre: n, ok: st.ok, estado: st.estado, motivo: st.motivo || desc };
  });
}
export function agruparOpciones(items) { return items; }
export function lineaNoInstalados() { return ""; }
export function lineaSinVerificar() { return ""; }
export function lineaOtros() { return ""; }
export const VENTANAS_CENTRAL = ["swe-code", "swen-code-free", "groq", "nvidia"];
