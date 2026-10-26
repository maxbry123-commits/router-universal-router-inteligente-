// pensando-3d.js — cubo holográfico sin tarjeta. Mientras el chat trabaja cambia de escenario: cubo, orbe, red, anillos.
import { el, cargarCss } from "./ventanas-comun.js";
const ESC = [["cubo", "Pensando…"], ["orbe", "Voz local…"], ["red", "Red…"], ["anillos", "Principios…"]];
export function montarPensando3D({ root, q }) {
  const f = q("#composer"); if (!f || f.dataset.p3d) return; f.dataset.p3d = "1"; cargarCss("pensando-3d");
  const w = el("div", "p3d"); w.hidden = true; w.dataset.esc = "cubo"; w.setAttribute("role", "status"); w.setAttribute("aria-live", "polite");
  w.innerHTML = '<div class="p3d-escena" aria-hidden="true"><div class="p3d-cubo"><i class="f1"></i><i class="f2"></i><i class="f3"></i><i class="f4"></i><i class="f5"></i><i class="f6"></i></div><div class="p3d-anillo a1"></div><div class="p3d-anillo a2"></div><div class="p3d-anillo a3"></div></div><div class="p3d-txt"><strong>Pensando…</strong><span class="p3d-t">0 s</span></div>';
  f.append(w);
  const t = w.querySelector(".p3d-t"), nom = w.querySelector("strong"); let ini = 0, paso = -1;
  const ocupado = () => { try { const c = window.RIU_CHAT && window.RIU_CHAT.chat(); return !!(c && c.ocupado); } catch (e) { return false; } };
  const id = setInterval(() => {
    if (!root.isConnected) { clearInterval(id); return; }
    const o = ocupado();
    if (o && w.hidden) { w.hidden = false; ini = Date.now(); paso = -1; }
    if (!o && !w.hidden) { w.hidden = true; paso = -1; }
    if (w.hidden) return;
    const n = Math.floor((Date.now() - ini) / 4000) % ESC.length;
    if (n !== paso) { paso = n; w.dataset.esc = ESC[n][0]; nom.textContent = ESC[n][1]; }
    t.textContent = Math.floor((Date.now() - ini) / 1000) + " s";
  }, 300);
}
