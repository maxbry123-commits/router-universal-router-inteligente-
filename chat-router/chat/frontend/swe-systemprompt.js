// swe-systemprompt.js — ON/OFF del system prompt de la ficha del Router MVP, aplicado por el bridge a TODOS los modelos
// (chat directo SWE CODE/SWEN CODE free y lo que llega desde OpenClaw: mismo pipeline en server.js). Defecto ON.
// GET/POST {apiBase}/v1/system-prompt-on (web-bridge/src/systemprompt.js + server.js). Mismo patron de base/clave que swe-claves.js.
const RUTA = "/v1/system-prompt-on";
const cfg = () => (typeof window !== "undefined" && window.RIU_CONFIG) || {};
async function resolverBase() {
  const c = cfg(); if (c.apiBase) return c.apiBase;
  try { const m = await import("./api.js"); await m.api("/health").catch(() => {}); } catch (e) {}
  return cfg().apiBase || cfg().proxyDestino || "";
}
async function llamar(metodo, cuerpo) {
  const base = await resolverBase(), c = cfg(), h = { "Content-Type": "application/json" };
  let k = ""; try { k = sessionStorage.getItem("riu_clave") || ""; } catch (e) {}
  h[c.authHeader || "X-API-Key"] = k;
  const r = await fetch(String(base).replace(/\/$/, "") + RUTA, { method: metodo, headers: h, body: cuerpo === undefined ? undefined : JSON.stringify(cuerpo) });
  let p = {}; try { p = await r.json(); } catch (e) {}
  return typeof p.on === "boolean" ? p.on : true;  // defecto ON si el bridge no responde (mismo defecto que systemprompt.js del servidor)
}
let estado = true, cargado = false;
export const systemPromptOnCache = () => estado;
export async function cargarSystemPromptOn() {
  if (cargado) return estado;
  try { estado = await llamar("GET"); } catch (e) { /* defecto ON, no rompe el selector */ }
  cargado = true;
  return estado;
}
export async function alternarSystemPromptOn() {
  const quiero = !estado;
  try { estado = await llamar("POST", { on: quiero }); } catch (e) { /* si falla el POST, el estado local no cambia */ }
  return estado;
}
