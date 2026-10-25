// salida-ampliada.js — la ventana de salida usa el espacio que dejaba la sección Selectores: 4 veces su alto normal.
// La caja de escritura queda fija abajo (sticky) y al abrir/recibir respuesta la página baja hasta ella: nunca se pierde Enviar.
const FACTOR = 4;
function medirYAplicar() {
  const sec = document.querySelector("section:has(> #histories)"), h = document.getElementById("histories");
  if (!sec || !h) return false;
  document.documentElement.classList.remove("salida-x4");
  const ind = document.getElementById("btn-selector-modelos");  // el indicador ocupa una fila de la caja: se suma para medir contra el alto de antes
  const base = h.getBoundingClientRect().height + (ind ? ind.getBoundingClientRect().height + 8 : 0);  // alto normal de la salida antes del cambio
  if (base < 50) return false;
  document.documentElement.style.setProperty("--salida-alto", Math.round(base * FACTOR) + "px");
  document.documentElement.classList.add("salida-x4");
  return true;
}
const bajar = () => { const c = document.getElementById("composer"); if (c) window.scrollTo({ top: document.documentElement.scrollHeight, behavior: "instant" }); };
let intentos = 0;
function iniciar() {
  if (!medirYAplicar()) { if (++intentos < 100) setTimeout(iniciar, 100); return; }
  bajar();
  let t; window.addEventListener("resize", () => { clearTimeout(t); t = setTimeout(() => { medirYAplicar(); bajar(); }, 150); });
  const h = document.getElementById("histories");  // respuesta nueva: la página baja para que se vea pegada a la caja de escritura
  new MutationObserver(() => { const r = h.getBoundingClientRect(); if (r.bottom > innerHeight - 40) bajar(); }).observe(h, { childList: true, subtree: true });
}
if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", () => setTimeout(iniciar, 300)); else setTimeout(iniciar, 300);
