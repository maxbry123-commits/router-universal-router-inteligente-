// riu-campana.js — campana de avisos (RUI 14). Dividido de chat-riu2.js sin cambiar la lógica.
import { $, crear, leer, escribir, SVG } from "./riu-util.js";
import { cargar } from "./apariencia-aplicar.js";
// ---------- GLOBAL (una sola vez): campana de avisos (RUI 14), nav con indicador/rebote/proximidad (RUI 17, 02, 05), sin conexion ----------
export function campana() {
  const aviso = $("#notice");
  if (window.__riuCampana || !aviso) return;
  window.__riuCampana = true;
  const lista = leer("riu_avisos_v1", []);
  const b = crear("button", "riu-campana"); b.type = "button"; b.title = "Avisos"; b.setAttribute("aria-label", "Avisos"); b.setAttribute("aria-expanded", "false");
  b.innerHTML = SVG('<path d="M6 8a6 6 0 0 1 12 0c0 7 3 8 3 8H3s3-1 3-8"/><path d="M10.3 21a1.9 1.9 0 0 0 3.4 0"/>', 20);
  const ins = crear("span", "riu-insignia"); ins.hidden = true; b.append(ins);
  const colocar = () => {
    const bar = $("#movil-bar"), slot = $("#campana-slot"), acceso = $(".access");
    const destino = (bar && !bar.hidden && slot) ? slot : (acceso || slot);
    if (!destino) return;
    if (destino === slot) slot.replaceChildren(b); else if (b.parentNode !== destino) destino.prepend(b);
  };
  colocar();
  try { matchMedia("(max-width:720px)").addEventListener("change", colocar); } catch (e) {}
  const panel = crear("div", "riu-avisos"); panel.hidden = true; panel.setAttribute("role", "dialog"); panel.setAttribute("aria-label", "Avisos");
  document.body.append(panel);
  let nuevos = 0;
  const hora = (t) => new Date(t).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
  const pintar = () => {
    panel.replaceChildren();
    const cab = crear("div", "riu-avisos-cab"); cab.append(crear("strong", "", "Avisos"));
    const v = crear("button", "mini", "Vaciar"); v.type = "button";
    v.addEventListener("click", () => { lista.length = 0; escribir("riu_avisos_v1", lista); pintar(); });
    cab.append(v); panel.append(cab);
    if (!lista.length) panel.append(crear("div", "fila-desc", "Sin avisos todavía"));
    [...lista].reverse().forEach((a) => { const f = crear("div", "riu-aviso"); f.append(crear("small", "", hora(a.t)), crear("span", "", a.m)); panel.append(f); });
  };
  const insignia = () => { ins.hidden = nuevos < 1; ins.textContent = nuevos > 9 ? "9+" : String(nuevos); };
  let ult = "", ultT = 0;
  new MutationObserver(() => {
    const m = (aviso.textContent || "").trim(); if (!m) return;
    const t = Date.now(); if (m === ult && t - ultT < 1500) return; ult = m; ultT = t;
    const err = /error|no se pudo|fall|sin conexi|denegad|negado|HTTP [45]|BRIDGE|caído/i.test(m); aviso.classList.toggle("err", err);
    setTimeout(() => { if ((aviso.textContent || "").trim() === m) aviso.textContent = ""; }, Math.round((Number(cargar().avisoSeg) || 4.5) * 1000 * (err ? 2 : 1)));  // toast: se limpia solo; el historial queda en la campana
    lista.push({ t, m: m.slice(0, 220) }); if (lista.length > 30) lista.shift(); escribir("riu_avisos_v1", lista);
    if (panel.hidden) { nuevos++; insignia(); b.classList.remove("suena"); void b.offsetWidth; b.classList.add("suena"); } else pintar();
  }).observe(aviso, { childList: true, characterData: true, subtree: true });
  const abrir = (s) => { panel.hidden = !s; b.setAttribute("aria-expanded", String(s)); if (s) { nuevos = 0; insignia(); pintar(); } };
  b.addEventListener("click", (e) => { e.stopPropagation(); abrir(panel.hidden); });
  document.addEventListener("click", (e) => { if (!panel.hidden && !panel.contains(e.target)) abrir(false); });
  document.addEventListener("keydown", (e) => { if (e.key === "Escape") abrir(false); });
}
