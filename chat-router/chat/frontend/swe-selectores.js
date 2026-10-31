// swe-selectores.js — selectores SWE CODE y SWEN CODE free del panel «Selector de modelos» (misma mecanica que el selector Groq):
// la pastilla abre una hoja con sus modelos; el elegido queda en window.RIU_SWE[<selector>] = {model_id, label}.
// Al encender el selector, enviar-mensaje.js manda por swe-directo.js (router propio: el bridge), sin pasar por el Router MVP.
import { SWE_LISTAS, EJECUTORES_TOOLS, leerEjecutorTools, guardarEjecutorTools } from "./swe-directo.js";
const K = "riu_swe_modelo";
const leer = () => { try { return JSON.parse(localStorage.getItem(K) || "{}") || {}; } catch (e) { return {}; } };
const refrescar = () => { try { window.RIU_SELECTORES && window.RIU_SELECTORES.refrescar(); } catch (e) {} };
const S = (window.RIU_SWE = window.RIU_SWE || {});
const guardado = leer();
for (const [id, l] of Object.entries(SWE_LISTAS)) {
  const m = l.modelos.find((x) => x[0] === guardado[id]) || l.modelos[0];
  S[id] = { model_id: m[0], label: m[1] };
}
const PILLS = { "sel-swe": "swe-code", "sel-swen": "swen-code-free" };
// Salida de las tools (SWE | OpenClaw): mismo estado en el panel Selectores y en las hojas; se guarda en localStorage y viaja como `ejecutor_tools` (swe-directo.js).
const ETIQUETA_SALIDA = { swe: "Salida: SWE", openclaw: "Salida: OpenClaw" };
function pintarSalida() {
  const v = leerEjecutorTools();
  document.querySelectorAll("[data-salida]").forEach((b) => { const on = b.dataset.salida === v; b.setAttribute("aria-pressed", String(on)); b.classList.toggle("on", on); });
}
function filaSalida() {
  const f = document.createElement("div"); f.className = "sel-salida sh-salida"; f.setAttribute("role", "group"); f.setAttribute("aria-label", "Salida de las tools");
  EJECUTORES_TOOLS.forEach((e) => { const b = document.createElement("button"); b.type = "button"; b.className = "pill salida-op"; b.dataset.salida = e; b.textContent = ETIQUETA_SALIDA[e]; f.append(b); });
  return f;
}
document.addEventListener("click", (e) => { const b = e.target.closest("[data-salida]"); if (b) { guardarEjecutorTools(b.dataset.salida); pintarSalida(); } });
pintarSalida();
function hoja(id) {
  const l = SWE_LISTAS[id];
  let s = document.getElementById("sh-" + id);
  if (!s) {
    s = document.createElement("div"); s.id = "sh-" + id; s.className = "sheet"; s.hidden = true; s.setAttribute("role", "dialog"); s.setAttribute("aria-label", l.titulo);
    const caja = document.createElement("div"); caja.className = "va-caja";
    const cab = document.createElement("div"); cab.className = "row va-head";
    const t = document.createElement("strong"); t.textContent = l.titulo;
    const x = document.createElement("button"); x.type = "button"; x.className = "secondary sh-cerrar"; x.setAttribute("aria-label", "Cerrar"); x.textContent = "✕";
    cab.append(t, x);
    const lista = document.createElement("div"); lista.className = "list"; lista.id = "sh-" + id + "-lista";
    caja.append(cab, filaSalida(), lista); s.append(caja);
    s.addEventListener("click", (e) => { if (e.target === s || e.target.closest(".sh-cerrar")) s.hidden = true; });
    document.addEventListener("keydown", (e) => { if (e.key === "Escape") s.hidden = true; });
    document.body.append(s);
  }
  const lista = s.querySelector("#sh-" + id + "-lista"); lista.replaceChildren();
  l.modelos.forEach(([mid, etiqueta, desc]) => {
    const on = S[id].model_id === mid;
    const b = document.createElement("button"); b.type = "button"; b.className = "fila" + (on ? " on" : ""); b.dataset.id = mid; b.setAttribute("aria-pressed", String(on));
    b.textContent = etiqueta + (desc ? " · " + desc : "") + (on ? "  ✓" : "");
    b.onclick = () => {
      S[id] = { model_id: mid, label: etiqueta };
      try { localStorage.setItem(K, JSON.stringify({ ...leer(), [id]: mid })); } catch (e) {}
      s.hidden = true; refrescar();
    };
    lista.append(b);
  });
  pintarSalida(); s.hidden = false;
}
document.addEventListener("click", (e) => { const p = e.target.closest("#sel-swe, #sel-swen"); if (p) hoja(PILLS[p.id]); });
