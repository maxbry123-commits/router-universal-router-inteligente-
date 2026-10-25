// chat-contexto.js — engancha el contexto (constitución, workflows encendidos, claves compartidas) al envío del chat sin tocar panel-chat.js:
// envuelve window.RIU_HARNESS (api.js). Sin nada encendido el mensaje y los anclados salen exactamente igual que antes.
import { aplicarAMensaje, ampliarAnclados, datosGobernanza } from "./contexto.js";
export function instalarContexto() {
  const o = window.RIU_HARNESS; if (typeof o !== "function" || o.__riuCtx) return;
  const w = (args) => {
    const a = Object.assign({}, args); let oficial = null; try { oficial = sessionStorage.getItem("riu_const_oficial"); } catch (e) {}
    const esFichaLiteral = a.qwen && (a.qwen.ficha_qwen === "2" || a.qwen.ficha_qwen === "3");  // ficha 2/3: el prompt del Director es verbatim; las instrucciones fijas viajan aparte
    if (esFichaLiteral) {
      if (oficial && a.instrucciones_fijas) a.instrucciones_fijas = oficial + "\n" + a.instrucciones_fijas;
      else if (oficial) a.instrucciones_fijas = oficial;
    } else {
      a.message = aplicarAMensaje(String(a.message || ""), oficial);
    }
    a.anclados = ampliarAnclados(Array.isArray(a.anclados) ? a.anclados : []);
    const g = datosGobernanza(); if (g) Object.assign(a, g);
    return o(a);
  };
  w.__riuCtx = true; window.RIU_HARNESS = w;
}
