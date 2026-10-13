// pensando-3d.js — indicador 3D compacto del pensamiento junto al boton Enviar.
// Usa el estado real del chat (ocupado); no tapa ni el historial ni el texto de respuesta.
import { el, cargarCss } from "./ventanas-comun.js";
export function montarPensando3D({ root, q }) {
  const f = q("#composer"); if (!f || f.dataset.p3d) return; f.dataset.p3d = "1"; cargarCss("pensando-3d");
  const barra = f.querySelector(".composer-bar");
  if (!barra) return;
  const enviar = barra.querySelector(".action");
  const w = el("div", "p3d"); w.hidden = true; w.setAttribute("role", "status"); w.setAttribute("aria-live", "polite");
  w.innerHTML = '<div class="p3d-escena" aria-hidden="true"><div class="p3d-cubo"><i class="f1"></i><i class="f2"></i><i class="f3"></i><i class="f4"></i><i class="f5"></i><i class="f6"></i></div><div class="p3d-anillo a1"></div><div class="p3d-anillo a2"></div></div><div class="p3d-txt"><strong>Pensando…</strong><span class="p3d-t">0 s</span></div>';
  if (enviar) barra.insertBefore(w, enviar); else barra.append(w);
  const t = w.querySelector(".p3d-t"); let ini = 0;
  const ocupado = () => { try { const c = window.RIU_CHAT && window.RIU_CHAT.chat(); return !!(c && c.ocupado); } catch (e) { return false; } };
  const id = setInterval(() => {
    if (!root.isConnected) { clearInterval(id); return; }
    const o = ocupado();
    if (o && w.hidden) { w.hidden = false; ini = Date.now(); }
    if (!o && !w.hidden) w.hidden = true;
    if (!w.hidden) t.textContent = Math.floor((Date.now() - ini) / 1000) + " s";
  }, 300);
}
