// chat-contexto.js — engancha el contexto (constitución, workflows encendidos, claves compartidas) al envío del chat sin tocar panel-chat.js:
// envuelve window.RIU_HARNESS (api.js). Sin nada encendido el mensaje y los anclados salen exactamente igual que antes.
import { aplicarAMensaje, ampliarAnclados, datosGobernanza } from "./contexto.js";
import { datosSentinela } from "./sentinela.js";
export function instalarContexto() {
  const o = window.RIU_HARNESS; if (typeof o !== "function" || o.__riuCtx) return;
  const w = (args) => {
    const a = Object.assign({}, args); let oficial = null; try { oficial = sessionStorage.getItem("riu_const_oficial"); } catch (e) {}
    a.message = aplicarAMensaje(String(a.message || ""), oficial); a.anclados = ampliarAnclados(Array.isArray(a.anclados) ? a.anclados : []);
    const g = datosGobernanza(); if (g) Object.assign(a, g);
    Object.assign(a, datosSentinela());  // Constitución sentinela (contrato) / system prompt / archivo real: solo lo encendido
    return o(a);
  };
  w.__riuCtx = true; window.RIU_HARNESS = w;
}
