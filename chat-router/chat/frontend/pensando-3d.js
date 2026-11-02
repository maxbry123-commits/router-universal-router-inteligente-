// pensando-3d.js — cubo 3D junto al botón Enviar mientras trabaja el chat.
// Usa el estado real del chat (ocupado); si el sistema pide menos movimiento, queda quieto.
import { el, cargarCss } from "./ventanas-comun.js";
export function montarPensando3D({ root, q }) {
  const barra = q("#composer .composer-bar");
  if (!barra || barra.dataset.p3d) return;
  barra.dataset.p3d = "1"; cargarCss("pensando-3d");
  const css = document.getElementById("css-pensando-3d"); if (css) css.href = "/chat/ui/pensando-3d.css?v=87313";
  const w = el("div", "p3d"); w.hidden = true; w.setAttribute("role", "status"); w.setAttribute("aria-live", "polite");
  w.innerHTML = '<div class="p3d-escena" aria-hidden="true"><div class="p3d-cubo"><i class="f1"></i><i class="f2"></i><i class="f3"></i><i class="f4"></i><i class="f5"></i><i class="f6"></i></div><div class="p3d-anillo a1"></div><div class="p3d-anillo a2"></div></div><div class="p3d-txt"><strong>Pensando…</strong><span class="p3d-t">0 s</span></div>';
  // Una sola animación, antes del botón Enviar y después de Detener.
  const enviar = barra.querySelector(".action");
  if (enviar) barra.insertBefore(w, enviar);
  else barra.append(w);
  const t = w.querySelector(".p3d-t"); let ini = 0;
  const hist = q("#histories");
  const estado = document.createElement("div");
  estado.className = "p3d-salida-estado";
  estado.setAttribute("role", "status");
  estado.setAttribute("aria-live", "polite");
  estado.textContent = "Pensando…";
  estado.hidden = true;
  const ocupado = () => { try { const c = window.RIU_CHAT && window.RIU_CHAT.chat(); return !!(c && c.ocupado); } catch (e) { return false; } };
  const id = setInterval(() => {
    if (!root.isConnected) { clearInterval(id); return; }
    const o = ocupado();
    if (!o) {
      w.hidden = true;
      estado.hidden = true;
      if (estado.parentElement) estado.remove();
      return;
    }
    if (w.hidden) { w.hidden = false; ini = Date.now(); }
    t.textContent = Math.floor((Date.now() - ini) / 1000) + " s";
    const salida = hist && [...hist.querySelectorAll(".chat-history")]
      .find(h => !h.hidden && h.offsetParent !== null);
    if (salida) {
      // Mostrar estado verdadero, tras la última respuesta, sin copiar razonamiento privado.
      if (estado.parentElement !== salida || estado !== salida.lastElementChild) salida.append(estado);
      estado.hidden = false;
    } else estado.hidden = true;
  }, 300);
}
