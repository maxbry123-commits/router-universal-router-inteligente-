// apariencia-aplicar.js — aplica en TODO el chat la apariencia guardada: color y tipografía de cada tipo de letra,
// icono de los botones, color de señal y tamaño de interfaz. Solo emite lo que el Director cambió: sin cambios no toca nada.
// Los valores se validan al leer (un dato roto o manipulado en el navegador se ignora).
import { TRAZOS, FUENTES, ROLES, DESTINOS } from "./apariencia-datos.js";
import { iniciarBloqueo } from "./bloqueo-pin.js";
import "./acceso-clave.js";  // restaura la clave recordada al abrir (antes de la primera llamada al servidor)
export const CLAVE = "riu_apariencia_v1";
export const HEX = /^#[0-9a-fA-F]{6}$/;
const lim = (n, a, b, d) => { n = Number(n); return Number.isFinite(n) ? Math.min(b, Math.max(a, n)) : d; };
export function cargar() {
  try { const v = JSON.parse(localStorage.getItem(CLAVE) || "null"); return v && typeof v === "object" && !Array.isArray(v) ? v : {}; } catch (e) { return {}; }
}
export function guardarEstado(est) { try { localStorage.setItem(CLAVE, JSON.stringify(est)); } catch (e) {} aplicar(est); }
export function construirCSS(est) {
  const out = [];
  for (const [id, , sels, d] of ROLES) {
    const t = (est.tipo && est.tipo[id]) || {}, c = est.colores && est.colores[id], r = [];
    if (typeof c === "string" && HEX.test(c)) r.push("color:" + c);
    if (t.fuente && FUENTES[t.fuente] && t.fuente !== d.fuente) r.push("font-family:" + FUENTES[t.fuente]);
    if (t.tam != null && Number(t.tam) !== d.tam) r.push("font-size:" + lim(t.tam, 10, 48, d.tam) + "px");
    if (t.peso != null && Number(t.peso) !== d.peso) r.push("font-weight:" + lim(t.peso, 300, 900, d.peso));
    if (t.esp != null && Number(t.esp) !== d.esp) r.push("letter-spacing:" + lim(t.esp, -1, 4, d.esp) + "px");
    if (t.alto != null && Number(t.alto) !== d.alto) r.push("line-height:" + lim(t.alto, 1, 2.3, d.alto));
    if (t.cursiva === true) r.push("font-style:italic");
    if (t.subrayado === true) r.push("text-decoration:underline");
    if (t.mayus === true) r.push("text-transform:uppercase");
    if (t.alinear === "center" || t.alinear === "right") r.push("text-align:" + t.alinear);
    if (r.length) out.push(sels.split(",").map((s) => "html:root " + s.trim()).join(",") + "{" + r.map((x) => x + "!important").join(";") + "}");
  }
  const esc = lim(est.escala, 90, 115, 100);
  if (esc !== 100) out.push("html:root body{zoom:" + esc / 100 + "}");
  return out.join("\n");
}
function aplicarIconos(map) {
  for (const [id, , sel] of DESTINOS) {
    const b = document.querySelector(sel), s = b && b.querySelector("svg"); if (!s) continue;
    const ic = map && map[id];
    if (ic && TRAZOS[ic]) {
      if (s.dataset.riuOrig === undefined) s.dataset.riuOrig = s.innerHTML;
      if (s.dataset.riuIcono !== ic) { s.innerHTML = TRAZOS[ic]; s.dataset.riuIcono = ic; }
    } else if (s.dataset.riuOrig !== undefined) { s.innerHTML = s.dataset.riuOrig; delete s.dataset.riuOrig; delete s.dataset.riuIcono; }
  }
}
let ordenOriginal = null;
function aplicarOrden(orden) {  // orden del menu lateral elegido en Apariencia (sin orden guardado = el de fabrica)
  const nav = document.querySelector("#navigation"); if (!nav) return;
  const bs = [...nav.querySelectorAll(":scope > button[data-view]")], ids = bs.map((b) => b.dataset.view);
  if (!ordenOriginal) ordenOriginal = ids.slice();
  const base = Array.isArray(orden) && orden.length ? orden : ordenOriginal;
  const resto = [...ordenOriginal, ...ids].filter((v, i, a) => ids.includes(v) && !base.includes(v) && a.indexOf(v) === i);  // lo no elegido conserva el orden de fabrica
  const quiero = [...base.filter((v) => ids.includes(v)), ...resto];
  if (quiero.join() === ids.join()) return;
  quiero.forEach((v) => nav.append(bs.find((b) => b.dataset.view === v)));
  const ind = nav.querySelector(".nav-ind"); if (ind) nav.append(ind);
}
export function aplicar(est = cargar()) {
  let st = document.getElementById("riu-apariencia");
  if (!st) { st = document.createElement("style"); st.id = "riu-apariencia"; document.head.append(st); }
  st.textContent = construirCSS(est);
  const rs = document.documentElement.style;
  if (typeof est.senal === "string" && HEX.test(est.senal)) { rs.setProperty("--active", est.senal); rs.setProperty("--status-blue", est.senal); }
  else { rs.removeProperty("--active"); rs.removeProperty("--status-blue"); }
  aplicarIconos(est.iconos);
  aplicarOrden(est.orden);
}
aplicar();
const panel = document.querySelector("#panel");
if (panel) { let t = 0; new MutationObserver(() => { clearTimeout(t); t = setTimeout(() => aplicarIconos(cargar().iconos), 80); }).observe(panel, { childList: true, subtree: true }); }
iniciarBloqueo();