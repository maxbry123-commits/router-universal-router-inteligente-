// swe-directo.js — los modelos de SWE CODE / SWEN CODE free del selector responden por su router propio (el bridge), sin pasar por el Router MVP.
// El chat llama POST /v1/chat/completions del mismo origen (el proxy del Space manda web-* y swecode-* al bridge); mismo historial, misma sesion.
import { leerClaves } from "./swe-claves.js";
const REAL = { "hf-liquid-lfm25": "lfm2.5-350m", "swe-agent-lfm25": "lfm2.5-350m", "swe-openhands-lfm25": "lfm2.5-350m",
  "swe-codex-qwen25-15b": "qwen2.5-coder-1.5b", "hf-qwen25-coder-15b": "qwen2.5-coder-1.5b", "swe-opencode-qwen35-08b": "qwen3.5-0.8b" };
const LOCALES = ["lfm2.5-350m", "qwen2.5-coder-1.5b", "qwen3.5-0.8b", "qwen3-0.6b"];
const MAX_HISTORIAL = 20;  // mensajes previos: un modelo de 350M-1.5B o una UI web se desbordan con el chat entero

// dos selectores propios del panel Selectores: [id del modelo, etiqueta, descripcion]
export const SWE_LISTAS = {
  "swe-code": { nombre: "SWE CODE", titulo: "SWE CODE · modelos locales (HF)", modelos: [
    ["hf-liquid-lfm25", "Liquid AI (HF)", "LFM2.5-350M · respondedor principal"],
    ["swe-codex-qwen25-15b", "SWE · Codex escribe", "Qwen2.5-Coder-1.5B"],
    ["swe-opencode-qwen35-08b", "SWE · OpenCode revisa", "Qwen3.5-0.8B"],
    ["swe-agent-lfm25", "SWE · Agent ejecuta", "LFM2.5-350M · tool/agentic"],
    ["swe-openhands-lfm25", "SWE · OpenHands verifica", "LFM2.5-350M"],
    ["hf-qwen25-coder-15b", "Qwen Code (HF)", "Qwen2.5-Coder-1.5B local"]] },
  "swen-code-free": { nombre: "SWEN CODE free", titulo: "SWEN CODE free · cuentas web", modelos: [
    ["swecode-consulta", "Concilio · los 3 web", "los 3 modelos web a la vez + síntesis"],
    ["web-qwen38max", "Qwen 3.8 Max (web)", "Código complejo · via bridge"],
    ["web-qwen37max", "Qwen 3.7 Max (web)", "Razonamiento · via bridge"],
    ["web-dsv4-flash", "DeepSeek V4 Flash (web)", "Código rápido · via bridge"],
    ["swecode-asesoria", "SWE · asesoría", "plan antes de ejecutar"],
    ["swecode-revision", "SWE · revisión", "modo revisión"],
    ["swecode-solucion", "SWE · solución", "modo solución"],
    ["swecode-arquitectura", "SWE · arquitectura", "modo arquitectura"],
    ["swecode-archivos", "SWE · archivos", "modo archivos"],
    ["swecode-prompt_code", "SWE · prompt_code", "modo prompt_code"],
    ["swecode-despliega", "SWE · despliega", "modo despliega"],
    ["groq/qwen/qwen3.8-27b", "Qwen 3.8 Groq", "API Groq"],
    ["nvidia/minimaxai/minimax-m3.1-flash", "MiniMax M3.1 Flash", "API NVIDIA"],
    ["nvidia/meta/muse-glimmer-30b", "Muse Glimmer 30B", "API NVIDIA"],
    ["nvidia/nvidia/nemotron-3-ultra-550b-a55b", "Nemotron 3 Ultra", "API NVIDIA"],
    ["nvidia/z-ai/glm-5.3", "GLM 5.3", "API NVIDIA"]] },
};
export const esSelectorSwe = (id) => typeof id === "string" && Object.hasOwn(SWE_LISTAS, id);

export const esSwe = (id) => typeof id === "string" && (/^(web-|swecode-|groq\/|nvidia\/)/.test(id) || Object.hasOwn(REAL, id) || LOCALES.includes(id));

// Salida de las tools: quien ejecuta los tool_calls. 'swe' (defecto) = el SWE-agent via bridge/Harness como hoy; 'openclaw' = el bridge los devuelve tal cual a OpenClaw (seccion WAIT_TOOLS).
// Contrato en SWE CODE free/ARQUITECTURA.md. Se guarda en localStorage y viaja en cada peticion como `ejecutor_tools`.
export const EJECUTORES_TOOLS = ["swe", "openclaw"];
export const ETIQUETA_SALIDA = { swe: "Salida: SWE-agent", openclaw: "Salida: OpenClaw" };
const K_EJECUTOR = "riu_swe_ejecutor_tools";
const normEjecutor = (v) => (EJECUTORES_TOOLS.includes(v) ? v : "swe");
export function leerEjecutorTools() { try { return normEjecutor(localStorage.getItem(K_EJECUTOR)); } catch (e) { return "swe"; } }
const escribirEjecutor = (x) => { try { localStorage.setItem(K_EJECUTOR, x); } catch (e) {} return x; };
export function guardarEjecutorTools(v) {
  const x = escribirEjecutor(normEjecutor(v));
  escribirSeleccion({ ...leerSeleccion(), agente_tool: x === "openclaw" ? "openclaw" : "swe-agent" });  // el boton de salida y AGENTE QUE EJECUTA son el mismo dato
  return x;
}

// ---- Selectores de agente/modelo/workflow (contrato TareaSWE de chat-router/agentes/adaptadores/contrato.py) ----
// Catalogo unico de agentes/adaptadores/modelos.py: el frontend solo lo refleja; el servidor valida y la disponibilidad real la reporta el Harness.
export const MODELOS_SWE = [
  ["hf/lfm2.5-350m", "Liquid LFM2.5 350M", "HF local"], ["hf/qwen2.5-coder-1.5b", "Qwen2.5 Coder 1.5B", "HF local"],
  ["hf/qwen3.5-0.8b", "Qwen3.5 0.8B", "HF local"], ["hf/qwen3-0.6b", "Qwen3 0.6B", "HF local"],
  ["groq/qwen/qwen3.8-27b", "Qwen 3.8 Groq", "API Groq"], ["nvidia/minimaxai/minimax-m3.1-flash", "MiniMax M3.1 Flash", "API NVIDIA"],
  ["nvidia/meta/muse-glimmer-30b", "Muse Glimmer 30B", "API NVIDIA"], ["nvidia/nvidia/nemotron-3-ultra-550b-a55b", "Nemotron 3 Ultra", "API NVIDIA"],
  ["nvidia/z-ai/glm-5.3", "GLM 5.3", "API NVIDIA"]];
export const AGENTES_SWE = [["openclaw", "OpenClaw"], ["swe-agent", "SWE-agent"], ["openhands", "OpenHands"], ["opencode", "OpenCode"], ["codex", "Codex"], ["claude-code", "Claude Code"]];
export const WORKFLOWS_SWE = [["individual", "Individual"], ["swe_code", "SWE CODE cuatro pasos"], ["liquid_mirror", "Liquid Mirror"]];
// Liquid Mirror: dos participantes propios (mismo modelo, servidores HF independientes), sin mezclar con los modelos web.
export const LIQUID_MIRROR = [{ id: "liquid1", etiqueta: "LIQUID 1 — LECTOR", servidor: "S2", modelo: "hf/lfm2.5-350m" }, { id: "liquid2", etiqueta: "LIQUID 2 — EJECUTOR", servidor: "S3", modelo: "hf/lfm2.5-350m" }];
const LIQUID = "hf/lfm2.5-350m", REVISOR = "hf/qwen3.5-0.8b", VERIFICADOR = "openhands";  // fijos del workflow SWE CODE (workflows.py)
export const SEL_DEFECTO = { modelo_responde: LIQUID, modelo_tool: "hf/qwen2.5-coder-1.5b", agente_responde: "openclaw", agente_tool: "swe-agent", modo_agentico: false, workflow: "individual" };
const K_SEL = "riu_swe_seleccion";
const en = (lista, v) => typeof v === "string" && lista.some((x) => x[0] === v);
function normSeleccion(x, base) {
  const o = x && typeof x === "object" ? x : {};
  return {
    modelo_responde: en(MODELOS_SWE, o.modelo_responde) ? o.modelo_responde : base.modelo_responde,
    modelo_tool: en(MODELOS_SWE, o.modelo_tool) ? o.modelo_tool : base.modelo_tool,
    agente_responde: en(AGENTES_SWE, o.agente_responde) ? o.agente_responde : base.agente_responde,
    agente_tool: en(AGENTES_SWE, o.agente_tool) ? o.agente_tool : base.agente_tool,
    modo_agentico: typeof o.modo_agentico === "boolean" ? o.modo_agentico : base.modo_agentico,
    workflow: en(WORKFLOWS_SWE, o.workflow) ? o.workflow : base.workflow };
}
export function leerSeleccion() { try { return normSeleccion(JSON.parse(localStorage.getItem(K_SEL) || "{}"), SEL_DEFECTO); } catch (e) { return { ...SEL_DEFECTO }; } }
function escribirSeleccion(sel) { try { localStorage.setItem(K_SEL, JSON.stringify(sel)); } catch (e) {} return sel; }
export function guardarSeleccion(parcial) {
  const sel = escribirSeleccion(normSeleccion(parcial, leerSeleccion()));  // un valor invalido no pisa el anterior
  if (parcial && Object.hasOwn(parcial, "agente_tool") && (sel.agente_tool === "openclaw" || sel.agente_tool === "swe-agent")) escribirEjecutor(sel.agente_tool === "openclaw" ? "openclaw" : "swe");
  return sel;
}
export const requiereHarness = (sel) => !!sel && (sel.workflow !== "individual" || sel.modo_agentico === true);
// modelo del selector clasico (alias hf-*, ids locales, groq/, nvidia/) -> id del catalogo; null si no esta registrado (p. ej. web-*, swecode-*)
export function idCatalogo(id) {
  const real = Object.hasOwn(REAL, id) ? REAL[id] : id;
  if (LOCALES.includes(real)) return "hf/" + real;
  return en(MODELOS_SWE, id) ? id : null;
}
const ident = (v, defecto) => { const t = String(v == null ? "" : v).replace(/[^A-Za-z0-9_-]/g, "-").slice(0, 64); return t || defecto; };
export function nuevoTaskId() { return "yaiwes-" + Date.now().toString(36) + Math.random().toString(36).slice(2, 8); }
export function armarTarea({ sel, mensaje, sesion, proyecto, task_id }) {
  const s = normSeleccion(sel, SEL_DEFECTO), lm = s.workflow === "liquid_mirror";
  return { task_id: task_id || nuevoTaskId(), origen: "yaiwes", workflow: s.workflow, mensaje: String(mensaje == null ? "" : mensaje),
    modelo_responde: s.modelo_responde, modelo_lector: LIQUID, modelo_tool: lm ? LIQUID : s.modelo_tool, modelo_revisor: REVISOR,
    agente_responde: s.agente_responde, agente_tool: s.agente_tool, agente_verificador: VERIFICADOR,
    modo_agentico: s.modo_agentico, aprobacion: false,  // la aprobacion NUNCA sale del cliente: la da el operador por /chat/swe/aprobar
    sesion: ident(sesion, ""), proyecto: ident(proyecto, "yaiwes") };
}

// Disponibilidad real: la reporta el Harness (GET /chat/swe/capacidades). Lo que no reporta NO se presenta como funcional.
export function normalizarCapacidades(p) {
  const o = p && typeof p === "object" ? p : {};
  const m = (x) => (x && typeof x === "object" ? x : {});
  return { harness: typeof o.harness === "string" ? o.harness : "desconocido", agentes: m(o.agentes), workflows: m(o.workflows), modelos: m(o.modelos) };
}
export function estadoOpcion(cap, tipo, id, modelo) {
  const e = (tipo === "agente" ? cap.agentes : tipo === "workflow" ? cap.workflows : cap.modelos)[id];
  const motivo = e && typeof e.motivo === "string" && e.motivo ? e.motivo : "";
  if (tipo === "workflow" && id === "individual") return { ok: true, motivo: "" };
  if (tipo === "modelo") return e && e.disponible === false ? { ok: false, motivo: motivo || "no esta en el catalogo del proveedor" } : { ok: true, motivo: "" };
  if (!e || e.disponible !== true) return { ok: false, motivo: motivo || (tipo === "agente" ? "sin adaptador conectado (el Harness no lo reporta)" : "el Harness no lo reporta conectado") };
  if (tipo === "agente" && modelo && Array.isArray(e.modelos) && !e.modelos.includes(modelo)) return { ok: false, motivo: "incompatible con " + modelo };
  return { ok: true, motivo: "" };
}
// Hoja compacta: disponibles arriba; lo que no esta conectado se agrupa aparte (no instalado / incompatible con el modelo) y se muestra en UNA linea, no como filas largas.
export function agruparOpciones(cap, tipo, lista, modelo) {
  const g = { ok: [], noInstalado: [], incompatible: [] };
  for (const [id, etq] of lista) {
    const st = estadoOpcion(cap, tipo, id, modelo), x = { id, etq, motivo: st.motivo };
    (st.ok ? g.ok : /^incompatible/.test(st.motivo) ? g.incompatible : g.noInstalado).push(x);
  }
  return g;
}
export const lineaNoInstalados = (g) => (g.noInstalado.length ? "No instalados: " + g.noInstalado.map((x) => x.etq).join(", ") : "");
// Secciones plegables de la hoja (Modelo | Agentes | Workflow y salida): el estado abierto/cerrado se guarda en localStorage.
export const SECCIONES_DEFECTO = { modelo: true, agentes: false, workflow: false };
const K_SECC = "riu_swe_secciones";
export function leerSecciones() {
  let o = {}; try { o = JSON.parse(localStorage.getItem(K_SECC) || "{}") || {}; } catch (e) {}
  return Object.fromEntries(Object.entries(SECCIONES_DEFECTO).map(([k, v]) => [k, typeof o[k] === "boolean" ? o[k] : v]));
}
export function guardarSeccion(id, abierta) {
  const s = leerSecciones(); if (!Object.hasOwn(SECCIONES_DEFECTO, id)) return s;
  s[id] = !!abierta; try { localStorage.setItem(K_SECC, JSON.stringify(s)); } catch (e) {} return s;
}
const nombreDe = (lista, id) => (lista.find((x) => x[0] === id) || [id, id])[1];
export function validarSeleccion(sel, cap) {
  if (!requiereHarness(sel)) return { ok: true, problemas: [] };
  const problemas = [], mal = (etq, r) => { if (!r.ok) problemas.push(etq + ": " + (/^incompatible/.test(r.motivo) ? "" : "NO DISPONIBLE ") + "(" + r.motivo + ")"); };
  mal("WORKFLOW " + nombreDe(WORKFLOWS_SWE, sel.workflow), estadoOpcion(cap, "workflow", sel.workflow));
  mal("MODELO QUE RESPONDE " + nombreDe(MODELOS_SWE, sel.modelo_responde), estadoOpcion(cap, "modelo", sel.modelo_responde));
  mal("AGENTE QUE RESPONDE " + nombreDe(AGENTES_SWE, sel.agente_responde), estadoOpcion(cap, "agente", sel.agente_responde, sel.modelo_responde));
  if (sel.modo_agentico) {
    const tool = sel.workflow === "liquid_mirror" ? LIQUID : sel.modelo_tool;
    mal("MODELO PARA TOOL " + nombreDe(MODELOS_SWE, tool), estadoOpcion(cap, "modelo", tool));
    mal("AGENTE QUE EJECUTA " + nombreDe(AGENTES_SWE, sel.agente_tool), estadoOpcion(cap, "agente", sel.agente_tool, tool));
    if (sel.workflow !== "individual") mal("AGENTE VERIFICADOR " + nombreDe(AGENTES_SWE, VERIFICADOR), estadoOpcion(cap, "agente", VERIFICADOR, LIQUID));
  }
  return { ok: problemas.length === 0, problemas };
}
let _cap = { t: 0, v: null };
const capVigente = () => !!_cap.v && Date.now() - _cap.t < 30000;
export const olvidarCapacidades = () => { _cap = { t: 0, v: null }; };
export async function cargarCapacidades(api, { forzar = false } = {}) {
  if (!forzar && capVigente()) return _cap.v;
  let v;
  try { v = normalizarCapacidades(await api("/chat/swe/capacidades")); } catch (e) { v = normalizarCapacidades(null); v.harness = "sin_respuesta"; }
  _cap = { t: Date.now(), v };
  return v;
}

// ---- Tarea SWE: el frontend manda el contrato al backend YAIWES (/chat/swe/*), este al Harness, este a los adaptadores. Nunca llama a una herramienta directo. ----
// Parar de avanzar: DONE (hecho), GAP (fallo sin efectos), REQUIERE_APROBACION (espera al operador) y RECONCILIAR (operacion iniciada sin confirmar: la verifica un operador).
const TERMINALES = ["DONE", "GAP", "REQUIERE_APROBACION", "RECONCILIAR"];
export const MAX_AVANCES = 24;
const TASK_RE = /^[A-Za-z0-9_-]{1,64}$/, OP_RE = /^[A-Za-z0-9_-]{1,80}$/;
const resultadoDe = (r, op) => {
  const x = r && r.ok === true ? r.resultado : null;
  if (!x || typeof x !== "object") throw new Error("GAP: SWE_HARNESS_ERROR · " + op + " sin resultado");
  return x;
};
async function operacion(api, op, cuerpo) {
  let r;
  try { r = await api("/chat/swe/" + op, { method: "POST", body: cuerpo }); } catch (e) { const m = String((e && e.message) || e); throw new Error(m.startsWith("GAP:") ? m : "GAP: " + (/^[A-Z][A-Z0-9_]+\b/.test(m) ? m : "SWE_HARNESS_ERROR · " + m)); }
  return resultadoDe(r, op);
}
const base = ({ task_id, sesion, proyecto }) => {
  if (!TASK_RE.test(String(task_id))) throw new Error("GAP: TASK_ID_INVALIDO");
  return { task_id, origen: "yaiwes", sesion: ident(sesion, ""), proyecto: ident(proyecto, "yaiwes") };
};
export const estadoTareaSwe = async (api, d) => operacion(api, "estado", base(d));
export const reanudarTareaSwe = async (api, d) => operacion(api, "reanudar", base(d));
export const aprobarTareaSwe = async (api, d) => {  // quien aprueba es el operador autenticado en el servidor, no un campo del cuerpo; op_id = la operacion que el Harness dejo pendiente
  if (typeof d.op_id !== "string" || !OP_RE.test(d.op_id)) throw new Error("GAP: OP_ID_INVALIDO");
  return operacion(api, "aprobar", { ...base(d), op_id: d.op_id });
};
const lineaEvidencia = (e) => (typeof e === "string" ? e : JSON.stringify(e)).slice(0, 300);
const texto = (v) => (typeof v === "string" ? v : v == null ? "" : JSON.stringify(v));
// El Harness devuelve la "vista" de la tarea: estado, paso_actual, plan, pasos_terminados[{paso,agente,servidor,recibo,resultado,herramientas,evidencias}], resultado_tool, evidencia[], pendiente_aprobacion, error{codigo,mensaje}.
function aRespuesta(x, tarea) {
  const estado = String(x.estado || ""), pasos = Array.isArray(x.pasos_terminados) ? x.pasos_terminados.filter((p) => p && typeof p === "object") : [];
  const idTarea = x.task_id || tarea.task_id;
  if (estado === "GAP") { const e = x.error && typeof x.error === "object" ? x.error : { codigo: x.codigo, mensaje: x.error }; throw new Error("GAP: " + (e.codigo || "GAP") + (e.mensaje ? " · " + texto(e.mensaje) : "")); }
  if (estado === "RECONCILIAR") { const r = x.pendiente_reconciliacion || {}; throw new Error("GAP: RECONCILIAR · la operación " + (r.op_id || "?") + " (" + (r.paso || "?") + ") quedó iniciada sin confirmar" + (r.motivo ? " (" + r.motivo + ")" : "") + ": un operador debe verificar su estado real antes de reanudar la tarea " + idTarea); }
  const pide = estado === "REQUIERE_APROBACION", pend = pide && x.pendiente_aprobacion && typeof x.pendiente_aprobacion === "object" ? x.pendiente_aprobacion : null;
  const final = x.resultado_tool || x.texto || x.resultado || x.reply || (pasos.length ? pasos[pasos.length - 1].resultado : "");
  const evid = [...(Array.isArray(x.evidencia) ? x.evidencia : []), ...(Array.isArray(x.evidencias) ? x.evidencias : [])].map(lineaEvidencia);
  pasos.filter((p) => p.recibo).forEach((p) => evid.push("recibo " + p.paso + " (" + (p.servidor || p.agente || "?") + "): " + p.recibo));
  const permisos = pend && pend.permisos ? Object.keys(pend.permisos).filter((k) => pend.permisos[k]).join(" y ") : "";
  const cabecera = pend ? "Requiere aprobación del operador: paso " + pend.paso + " con " + pend.agente + " (" + pend.modelo + ")" + (permisos ? " · " + permisos : "") + (pend.objetivo ? "\n" + texto(pend.objetivo) : "") : pide ? "Requiere aprobación del operador antes de continuar." : "";
  const reply = [cabecera, texto(final), evid.length ? "Evidencias:\n" + evid.map((e) => "- " + e).join("\n") : ""].filter(Boolean).join("\n\n");
  const tools = [...new Set(pasos.flatMap((p) => (Array.isArray(p.herramientas) ? p.herramientas : []).map((h) => (typeof h === "string" ? h : (h && h.nombre) || "tool"))))];
  return { reply, tools, finish_reason: estado === "DONE" ? "stop" : null, estado, task_id: idTarea, requiere_aprobacion: pide, pendiente: pend,
    nota: `SWE · ${tarea.workflow} · ${tarea.agente_responde}→${tarea.agente_tool} · tarea ${idTarea} · ${estado || "?"}${x.ejecucion_s2_s3 ? " · S2/S3 " + x.ejecucion_s2_s3 : ""}` };
}
const textoPaso = (x) => { const plan = Array.isArray(x.plan) ? x.plan : [], p = plan[x.paso_actual] || plan[plan.length - 1]; return "SWE · " + (x.estado || "?") + (p && p.paso ? " · " + p.paso : "") + (Number.isInteger(x.paso_actual) && plan.length ? " (" + Math.min(x.paso_actual + 1, plan.length) + "/" + plan.length + ")" : ""); };
async function conducir(api, x, tarea, alPaso) {  // avanza paso a paso (el estado se guarda en el Harness en cada paso) hasta un estado terminal o de aprobacion
  const ref = { task_id: tarea.task_id, origen: "yaiwes", sesion: tarea.sesion, proyecto: tarea.proyecto }, avisa = (v) => { try { if (alPaso) alPaso(textoPaso(v), v); } catch (e) {} };
  avisa(x);
  for (let i = 0; i < MAX_AVANCES && !TERMINALES.includes(String(x.estado)); i++) { x = await operacion(api, "avanzar", ref); avisa(x); }
  if (!TERMINALES.includes(String(x.estado))) throw new Error("GAP: SWE_SIN_PROGRESO · la tarea " + tarea.task_id + " sigue en " + (x.estado || "?") + "; reanúdala con el mismo task_id");
  return aRespuesta(x, tarea);
}
export async function enviarTareaSwe(api, { mensaje, sesion, proyecto, task_id, alPaso }) {
  const sel = leerSeleccion(), enCache = capVigente();
  let v = validarSeleccion(sel, await cargarCapacidades(api));
  if (!v.ok && enCache) v = validarSeleccion(sel, await cargarCapacidades(api, { forzar: true }));  // un "no disponible" viejo no se queda pegado: se vuelve a preguntar al Harness
  if (!v.ok) throw new Error("GAP: SELECCION_NO_DISPONIBLE · " + v.problemas.join(" · "));  // no se cambia en silencio a otro modelo ni agente
  const tarea = armarTarea({ sel, mensaje, sesion, proyecto, task_id });
  return conducir(api, await operacion(api, "iniciar", tarea), tarea, alPaso);
}
// el operador pulsa Aprobar: el servidor lo identifica; despues la tarea sigue desde su ultimo checkpoint (mismo task_id)
export async function aprobarYContinuarSwe(api, d, alPaso) {
  const tarea = armarTarea({ sel: leerSeleccion(), mensaje: "(continuación)", sesion: d.sesion, proyecto: d.proyecto, task_id: base(d).task_id });
  return conducir(api, await aprobarTareaSwe(api, d), tarea, alPaso);
}

export function armar({ model, historial = [], mensaje, sesion, proyecto, ejecutor_tools }) {
  const h = historial.slice(-MAX_HISTORIAL);
  let claves = {}; try { claves = leerClaves(); } catch (e) {}  // las claves viajan solo en el cuerpo; nunca en errores ni en la nota
  return { model: Object.hasOwn(REAL, model) ? REAL[model] : model, messages: [...h, { role: "user", content: mensaje }], conv_id: sesion, ejecutor_tools: ejecutor_tools === undefined ? leerEjecutorTools() : normEjecutor(ejecutor_tools), ...(proyecto ? { proyecto } : {}), ...(Object.keys(claves).length ? { claves } : {}) };
}

// El proxy del Space solo manda /v1/* al bridge si el modelo empieza por web-/swecode-; el resto (locales HF, groq/, nvidia/) caeria en el Router
// (400 MODEL_NOT_IN_CERTIFIED_REGISTRY). /web/* va SIEMPRE al bridge (igual que /web/v1/claves): por ahi viajan los demas ids.
export const rutaSwe = (id) => (/^(web-|swecode-)/.test(Object.hasOwn(REAL, id) ? REAL[id] : String(id)) ? "/v1/chat/completions" : "/web/v1/chat/completions");

export async function enviarSwe(api, datos) {
  const r = await api(rutaSwe(datos.model), { method: "POST", body: armar(datos) });
  const msg = (r && r.choices && r.choices[0] && r.choices[0].message) || {};
  const llamadas = Array.isArray(msg.tool_calls) ? msg.tool_calls : [];
  if (!msg.content && llamadas.length) {  // passthrough: las tools las ejecuta el cliente (OpenClaw) o el Harness; no es un fallo
    const nombres = llamadas.map((t) => (t && t.function && t.function.name) || "tool");
    return { reply: "Tools pedidas: " + nombres.join(", "), tools: nombres, finish_reason: r.choices[0].finish_reason || "tool_calls", nota: `SWE · ${r.modelo_usado || datos.model} · tools → ${armar(datos).ejecutor_tools === "openclaw" ? "OpenClaw" : "SWE"}` };
  }
  const texto = msg.content;
  if (!texto) {  // un fallo no se pinta como respuesta del modelo (entraria al historial del turno siguiente)
    const e = (r && r.error) || {};
    throw new Error("GAP: " + (e.code || "SIN_RESPUESTA") + (e.message ? " · " + e.message : ""));
  }
  const via = r.via_respaldo ? ` · respondió ${r.via_respaldo}` : r.via_primaria ? ` · vía ${r.via_primaria}` : "";
  return { reply: texto, tools: [], finish_reason: r.choices[0].finish_reason || null, nota: `SWE · ${r.modelo_usado || datos.model}${via}` };
}
