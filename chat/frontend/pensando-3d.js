// pensando-3d.js — el cubo va en la fila de controles: cubo, borrar, detener, inicio.
import { el, cargarCss } from "./ventanas-comun.js";
const ESC = [
  ["cubo", "Pensando…", "cubo.png"],
  ["orbe", "Pensando…", "orbe.png"],
  ["red", "Pensando…", "red.png"],
  ["anillos", "Pensando…", "anillos.png"],
];
const fila = () => {
  let f = document.getElementById("fila-mando");
  const comp = document.querySelector("#composer");
  if (!f && comp) { f = document.createElement("div"); f.id = "fila-mando"; comp.before(f); }
  return f;
};
const borrar = () => {
  let b = document.getElementById("btn-borrar-mando");
  if (b) return b;
  b = document.createElement("button");
  b.type = "button"; b.id = "btn-borrar-mando"; b.className = "secondary";
  b.title = "Borrar"; b.setAttribute("aria-label", "Borrar");
  b.innerHTML = '<svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" stroke-width="1.8" aria-hidden="true"><path d="M4 7h16M9 7V5h6v2M8 7l1 13h6l1-13"/></svg>';
  b.onclick = () => {
    const inp = document.getElementById("message"); if (inp) inp.value = "";
    const c = window.RIU_CHAT && window.RIU_CHAT.chat();
    if (c) { c.tareaParada = ""; c.colaMensajes = []; }
    const cola = document.getElementById("cola-chat"); if (cola) cola.remove();
    const av = document.getElementById("reactivar-tarea"); if (av && c && !c.ocupado) av.remove();
  };
  return b;
};
const ordenar = (w) => {
  const f = fila(); if (!f) return;
  const det = document.getElementById("btn-detener");
  const ini = document.getElementById("reactivar-tarea");
  f.replaceChildren(w, borrar());
  if (det) f.append(det);
  if (ini) f.append(ini);
};
export function montarPensando3D({ root, q }) {
  const comp = q("#composer"); if (!comp || comp.dataset.p3d) return; comp.dataset.p3d = "1"; cargarCss("pensando-3d");
  const w = el("div", "p3d"); w.hidden = true; w.dataset.esc = "cubo"; w.setAttribute("role", "status"); w.setAttribute("aria-live", "polite");
  w.innerHTML = '<div class="p3d-escena" aria-hidden="true"><img class="p3d-vis" alt=""><div class="p3d-cubo"><i class="f1"></i><i class="f2"></i><i class="f3"></i><i class="f4"></i><i class="f5"></i><i class="f6"></i></div><div class="p3d-anillo a1"></div><div class="p3d-anillo a2"></div><div class="p3d-anillo a3"></div></div><div class="p3d-txt"><strong>Pensando…</strong><span class="p3d-t">0 s</span></div>';
  ordenar(w);
  const t = w.querySelector(".p3d-t"), nom = w.querySelector("strong"), img = w.querySelector(".p3d-vis");
  const base = new URL("./p3d/", import.meta.url);
  img.addEventListener("load", () => w.classList.add("p3d-foto"));
  img.addEventListener("error", () => w.classList.remove("p3d-foto"));
  let ini = 0, paso = -1;
  const ocupado = () => { try { const c = window.RIU_CHAT && window.RIU_CHAT.chat(); return !!(c && c.ocupado); } catch (e) { return false; } };
  const id = setInterval(() => {
    if (!root.isConnected) { clearInterval(id); return; }
    ordenar(w);
    const o = ocupado();
    if (o && w.hidden) { w.hidden = false; ini = Date.now(); paso = -1; }
    if (!o && !w.hidden) { w.hidden = true; paso = -1; }
    if (w.hidden) return;
    const n = Math.floor((Date.now() - ini) / 4000) % ESC.length;
    if (n !== paso) {
      paso = n; w.dataset.esc = ESC[n][0]; nom.textContent = "Pensando…";
      img.src = new URL(ESC[n][2], base).href;
    }
    t.textContent = Math.floor((Date.now() - ini) / 1000) + " s";
  }, 300);
}
