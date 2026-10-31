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
    ["groq/llama-3.3-70b-versatile", "Groq · Llama 3.3 70B", "respaldo 1 · usa la clave de Configuración"],
    ["nvidia/meta/llama-3.3-70b-instruct", "NVIDIA · Llama 3.3 70B", "respaldo 2 · usa la clave de Configuración"]] },
};
export const esSelectorSwe = (id) => typeof id === "string" && Object.hasOwn(SWE_LISTAS, id);

export const esSwe = (id) => typeof id === "string" && (/^(web-|swecode-|groq\/|nvidia\/)/.test(id) || Object.hasOwn(REAL, id) || LOCALES.includes(id));

// Salida de las tools: quien ejecuta los tool_calls. 'swe' (defecto) = el bridge/Harness como hoy; 'openclaw' = el bridge los devuelve tal cual a OpenClaw (seccion WAIT_TOOLS).
// Contrato en SWE CODE free/ARQUITECTURA.md. Se guarda en localStorage y viaja en cada peticion como `ejecutor_tools`.
export const EJECUTORES_TOOLS = ["swe", "openclaw"];
const K_EJECUTOR = "riu_swe_ejecutor_tools";
const normEjecutor = (v) => (EJECUTORES_TOOLS.includes(v) ? v : "swe");
export function leerEjecutorTools() { try { return normEjecutor(localStorage.getItem(K_EJECUTOR)); } catch (e) { return "swe"; } }
export function guardarEjecutorTools(v) { const x = normEjecutor(v); try { localStorage.setItem(K_EJECUTOR, x); } catch (e) {} return x; }

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
