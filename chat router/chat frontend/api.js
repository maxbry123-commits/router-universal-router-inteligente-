// api.js — Cliente API del Router (chat UI)
// Cambios: trae util `copiar` al portador final; `chat` acepta flujo + historial + stop; manejo de errores de red
const CFG = window.RIU_CONFIG || {};
let BASE = (CFG.apiBase || "").replace(/[/]+$/, "");

let liveCheckedAt = 0;
let liveRequest = null;
async function liveRouter() {
  if (CFG.routerStopped) throw new Error('Router detenido por orden del Director');
  if (Date.now() - liveCheckedAt < 30000) return BASE;
  if (!liveRequest) live