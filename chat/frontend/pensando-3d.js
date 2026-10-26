// pensando-3d.js — holograma sin tarjeta. Mientras el chat trabaja cambia de escenario: orbe, cubo, red, anillos.
import { el, cargarCss } from "./ventanas-comun.js";
const ESC = [
  ["orbe", "Voz local…", "orbe.png"],
  ["cubo", "Pensando…", "cubo.png"],
  ["red", "Red…", "red.png"],
  ["anillos", "Principios…", "anillos.png"],
];
// Los 22 componentes RUI (el skill del chat no trae 25). Mismos nombres que apariencia-extra.js.
const RUI = [
  ["01", "Carpeta"], ["02", "Rebote"], ["03", "Riel"], ["04", "Cajón"], ["05", "Proximidad"],
  ["06", "Duración"], ["07", "Orbe fluido"], ["08", "Lectura"], ["09", "Código"], ["10", "PIN"],
  ["11", "Letras"], ["12", "Actividad"], ["13", "Reacción"], ["14", "Campana"], ["15", "Pasos"],
  ["16", "Revelado"], ["17", "Indicador"], ["18", "Cerrar"], ["19", "Contador"], ["20", "Orbe matriz"],
  ["21", "Tareas"], ["22", "Voz"],
];
export function montarPensando3D({ root, q }) {
  const f = q("#composer"); if (!f || f.dataset.p3d) return; f.dataset.p3d = "1"; cargarCss("pensando-3d");
  const w = el("div", "p3d"); w.hidden = true; w.dataset.esc = "orbe"; w.setAttribute("role", "status"); w.setAttribute("aria-live", "polite");
  w.innerHTML = '<div class="p3d-escena" aria-hidden="true"><img class="p3d-vis" alt=""><div class="p3d-cubo"><i class="f1"></i><i class="f2"></i><i class="f3"></i><i class="f4"></i><i class="f5"></i><i class="f6"></i></div><div class="p3d-anillo a1"></div><div class="p3d-anillo a2"></div><div class="p3d-anillo a3"></div></div><div class="p3d-txt"><strong>Voz local…</strong><span class="p3d-t">0 s</span><span class="p3d-rui">RUI 07 · Orbe fluido</span></div>';
  f.append(w);
  const t = w.querySelector(".p3d-t"), nom = w.querySelector("strong"), img = w.querySelector(".p3d-vis"), rui = w.querySelector(".p3d-rui");
  const base = new URL("./p3d/", import.meta.url);
  img.addEventListener("load", () => w.classList.add("p3d-foto"));
  img.addEventListener("error", () => w.classList.remove("p3d-foto"));
  let ini = 0, paso = -1, pasoR = -1;
  const ocupado = () => { try { const c = window.RIU_CHAT && window.RIU_CHAT.chat(); return !!(c && c.ocupado); } catch (e) { return false; } };
  const id = setInterval(() => {
    if (!root.isConnected) { clearInterval(id); return; }
    const o = ocupado();
    if (o && w.hidden) { w.hidden = false; ini = Date.now(); paso = -1; pasoR = -1; }
    if (!o && !w.hidden) { w.hidden = true; paso = -1; }
    if (w.hidden) return;
    const n = Math.floor((Date.now() - ini) / 4000) % ESC.length;
    if (n !== paso) {
      paso = n; w.dataset.esc = ESC[n][0]; nom.textContent = ESC[n][1];
      img.src = new URL(ESC[n][2], base).href;
    }
    const r = Math.floor((Date.now() - ini) / 2000) % RUI.length;
    if (r !== pasoR) { pasoR = r; w.dataset.rui = RUI[r][0]; rui.textContent = "RUI " + RUI[r][0] + " · " + RUI[r][1]; }
    t.textContent = Math.floor((Date.now() - ini) / 1000) + " s";
  }, 300);
}
