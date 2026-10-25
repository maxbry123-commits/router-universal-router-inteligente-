// riu-navegacion.js — navegación con indicador/rebote/proximidad (RUI 17, 02, 05), aviso sin conexión y orbe de estado (RUI 20). Dividido de chat-riu2.js sin cambiar la lógica.
import { $, crear } from "./riu-util.js";
export function navegacion() {
  const nav = $("#navigation");
  if (!nav || nav.dataset.riu) return;
  nav.dataset.riu = "1"; nav.classList.add("con-ind");
  const ind = crear("span", "nav-ind"); ind.setAttribute("aria-hidden", "true"); nav.append(ind);
  const mover = () => {
    const a = nav.querySelector("[aria-current=page]"); if (!a) return;
    ind.style.cssText = matchMedia("(max-width:720px)").matches
      ? "left:" + a.offsetLeft + "px;top:" + (a.offsetTop + a.offsetHeight - 3) + "px;width:" + a.offsetWidth + "px;height:3px"
      : "left:0;top:" + a.offsetTop + "px;width:3px;height:" + a.offsetHeight + "px";
  };
  new MutationObserver(mover).observe(nav, { attributes: true, attributeFilter: ["aria-current"], subtree: true });
  addEventListener("resize", mover); mover();
  nav.addEventListener("click", (e) => { const b = e.target.closest("button"); if (!b) return; b.classList.remove("rebote"); void b.offsetWidth; b.classList.add("rebote"); });
  if (matchMedia("(hover:hover) and (pointer:fine) and (min-width:721px)").matches) {
    const bs = () => [...nav.querySelectorAll("button")];
    nav.addEventListener("pointermove", (e) => bs().forEach((b) => { const r = b.getBoundingClientRect(); const k = Math.max(0, 1 - Math.abs(e.clientY - (r.top + r.height / 2)) / 90); b.style.transform = "translateX(" + (k * 8).toFixed(1) + "px)"; }));
    nav.addEventListener("pointerleave", () => bs().forEach((b) => { b.style.transform = ""; }));
  }
}

export function sinConexion() {
  if (window.__riuRed) return; window.__riuRed = true;
  const nota = (m) => { const n = $("#notice"); if (n) n.textContent = m; };
  addEventListener("offline", () => nota("Sin conexión: tus mensajes no se enviarán hasta que vuelva internet"));
  addEventListener("online", () => nota("Conexión recuperada"));
}

// RUI 20 matrix-orb: orbe del estado de la conexión (naranja girando = sin verificar, verde = conectado, rojo = fallo)
export function orbeConexion() {
  const c = $("#connection"); if (!c || window.__riuOrbe) return; window.__riuOrbe = true;
  const o = crear("span", "riu-orbe"), w = crear("span", "riu-estado"); o.setAttribute("aria-hidden", "true"); c.before(w); w.append(o, c);
  const act = () => {
    const t = (c.textContent || "").toLowerCase();
    o.dataset.e = /error|ca[ií]do|fall|sin conexi|offline|desconect|bloquead|no disponible|timeout/.test(t) ? "mal" : (/conectad|disponible|\bok\b|listo|activo|en l[ií]nea|online|verificad/.test(t) && !/sin verificar/.test(t)) ? "bien" : "espera";
    c.title = c.textContent;
  };
  new MutationObserver(act).observe(c, { childList: true, characterData: true, subtree: true }); act();
}
