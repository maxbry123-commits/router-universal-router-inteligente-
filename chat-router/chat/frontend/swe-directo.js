// swe-directo.js — los modelos de SWE CODE / SWEN CODE free del selector responden por su router propio (el bridge), sin pasar por el Router MVP.
// El chat llama POST /v1/chat/completions del mismo origen (el proxy del Space manda web-* y swecode-* al bridge); mismo historial, misma sesion.
const REAL = { "hf-liquid-lfm25": "lfm2.5-350m", "swe-agent-lfm25": "lfm2.5-350m", "swe-openhands-lfm25": "lfm2.5-350m",
  "swe-codex-qwen25-15b": "qwen2.5-coder-1.5b", "hf-qwen25-coder-15b": "qwen2.5-coder-1.5b", "swe-opencode-qwen35-08b": "qwen3.5-0.8b" };
const LOCALES = ["lfm2.5-350m", "qwen2.5-coder-1.5b", "qwen3.5-0.8b", "qwen3-0.6b"];

export const esSwe = (id) => typeof id === "string" && (/^(web-|swecode-)/.test(id) || id in REAL || LOCALES.includes(id));

export function armar({ model, historial = [], mensaje, sesion, proyecto }) {
  return { model: REAL[model] || model, messages: [...historial, { role: "user", content: mensaje }], conv_id: sesion, ...(proyecto ? { proyecto } : {}) };
}

export async function enviarSwe(api, datos) {
  const r = await api("/v1/chat/completions", { method: "POST", body: armar(datos) });
  const texto = r && r.choices && r.choices[0] && r.choices[0].message && r.choices[0].message.content;
  if (!texto) {
    const e = (r && r.error) || {};
    return { reply: "GAP: " + (e.code || "SIN_RESPUESTA") + (e.message ? " · " + e.message : ""), tools: [], finish_reason: null };
  }
  const via = r.via_respaldo ? ` · respondió ${r.via_respaldo}` : "";
  return { reply: texto, tools: [], finish_reason: r.choices[0].finish_reason || null, nota: `SWE · ${r.modelo_usado || datos.model}${via}` };
}
