// watchdog-avisos.js — avisos del plugin watchdog del Router en la campana compacta (la campana guarda todo lo que pasa por #notice).
// Cada 60 s (solo con la pestaña visible) pide /plugins/watchdog/call/alertas {desde} y pasa cada aviso nuevo por tell().
import { plugin } from "./api.js";
const K = "riu_wd_desde";
export function montarWatchdog({ tell }) {
  if (window.__riuWatchdog) return; window.__riuWatchdog = true;
  let desde = Number(localStorage.getItem(K) || 0) || (Date.now() / 1000 - 3600);
  let ocupado = false;
  async function mirar() {
    if (ocupado || document.hidden) return; ocupado = true;
    try {
      const r = await plugin("watchdog", "alertas", { desde });
      const lista = Array.isArray(r.alertas) ? r.alertas : [];
      lista.forEach((a, i) => setTimeout(() => tell((a.nivel === "ok" ? "✅ " : "⚠️ ") + a.mensaje), i * 1700));  // de a uno: la campana los guarda todos
      if (lista.length) desde = Math.max(...lista.map((a) => Number(a.ts) || 0));
      else if (r.ahora && !localStorage.getItem(K)) desde = Number(r.ahora);
      localStorage.setItem(K, String(desde));
    } catch (e) { /* sin watchdog en el Router: no se avisa nada (no es un fallo del chat) */ }
    ocupado = false;
  }
  setTimeout(mirar, 8000);
  setInterval(mirar, 60000);
  document.addEventListener("visibilitychange", () => { if (!document.hidden) mirar(); });
}
