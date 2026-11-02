// pensando-3d.js — cubo 3D del pensamiento dentro de la salida del chat, nunca en la caja de escritura.
// Usa el estado real del chat (ocupado); si el sistema pide menos movimiento, queda quieto.
import { el, cargarCss } from "./ventanas-comun.js";
export function montarPensando3D({ root, q }) {
  const hist = q("#histories"); if (!hist || hist.dataset.p3d) return;
  hist.dataset.p3d = "1"; cargarCss("pensando-3d");
  const css = document.getElementById("css-pensando-3d"); if (css) css.href = "/chat/ui/pensando-3d.css?v=87312";
  const w = el("div", "p3d"); w.hidden = true; w.setAttribute("role", "status"); w.setAttribute("aria-live", "polite");
  w.innerHTML = '<div class="p3d-escena" aria-hidden="true"><div class="p3d-cubo"><i class="f1"></i><i class="f2"></i><i class="f3"></i><i class="f4"></i><i class="f5"></i><i class="f6"></i></div><div class="p3d-anillo a1"></div><div class="p3d-anillo a2"></div></div><div class="p3d-txt"><strong>Pensando…</strong><span class="p3d-t">0 s</span></div>';
  // El único cubo se reubica al historial activo cuando cambia la pestaña.
  // No se añaden elementos al composer ni se clonan animaciones.
  const t = w.querySelector(".p3d-t"); let ini = 0;
  const ocupado = () => { try { const c = window.RIU_CHAT && window.RIU_CHAT.chat(); return !!(c && c.ocupado); } catch (e) { return false; } };
  const id = setInterval(() => {
    if (!root.isConnected) { clearInterval(id); return; }
    const o = ocupado();
    const target = [...hist.querySelectorAll(".chat-history")]
      .find(h => !h.hidden && h.offsetParent !== null);
    if (!o || !target) { if (!w.hidden) w.hidden = true; return; }
    if (w.parentElement !== target) target.append(w);
    if (w.hidden) { w.hidden = false; ini = Date.now(); }
    t.textContent = Math.floor((Date.now() - ini) / 1000) + " s";
  }, 300);
}
