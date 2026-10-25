// En el celular la caja queda baja: la respuesta usa el resto.
// IA, Agentes, Auto y el resto viven en un menú que no se sale de la pantalla.
const st = document.createElement("style");
st.textContent = "@media(max-width:720px){"
  + ".riu-bv-titulo{font-size:18px !important}"
  + ".riu-bienvenida{justify-content:center;padding-top:0}"
  + "#composer{padding:8px 8px 6px !important;display:flex !important;flex-direction:column !important}"
  + "#composer #btn-selector-modelos{order:3 !important;margin:6px 0 0 !important;align-self:stretch;width:100%;min-height:44px;box-sizing:border-box}"
  + "#composer #message{min-height:40px !important;height:40px;max-height:88px !important}"
  + "#composer .composer-chips:empty{display:none !important}"
  + "#composer .composer-bar{flex-wrap:nowrap !important;gap:6px !important}"
  + "#composer .composer-bar>button.secondary{width:34px !important;min-width:34px !important;height:34px !important}"
  + "#composer .composer-bar::after{display:none !important;content:none !important}"
  + "#composer .composer-bar>.action{position:static !important;margin-left:auto !important;min-width:40px !important;width:40px !important;height:40px !important;min-height:40px !important;padding:0 !important;border-radius:50% !important;justify-content:center}"
  + "#composer .composer-bar>.action .env-txt{display:none !important}"
  + "#mode-selector-mount{flex:0 0 auto;display:flex;align-items:center}"
  + "#mas-panel{position:fixed;z-index:80;left:12px;right:12px;display:grid;grid-template-columns:minmax(0,1fr) minmax(0,1fr);gap:6px;padding:8px;border-radius:16px;background:var(--surface,#1e1e1e);border:1px solid var(--border);overflow:auto;box-shadow:0 12px 32px rgba(0,0,0,.5)}"
  + "#mas-panel[hidden]{display:none !important}"
  + "#mas-panel button{width:auto !important;max-width:100%;height:auto !important;min-width:0;min-height:40px;aspect-ratio:auto;border-radius:12px;display:inline-flex;align-items:center;justify-content:flex-start;gap:8px;padding:6px 10px}"
  + "#mas-panel .mas-nom{min-width:0;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;font-size:13px}"
  + "#mas-panel #mode-selector-mount{grid-column:1 / -1}"
  + "}";
document.head.append(st);

const ATAJOS = [["Archivos", "#btn-archivos"], ["Anclaje", "#btn-ancla"], ["Claves", "#pill-claves"], ["Workflows", "#pill-workflows"]];
const IDS = ["btn-tools", "btn-agentes", "btn-prompt", "btn-loop", "btn-cola", "btn-tareas", "btn-comandos", "btn-sesion", "btn-reglas", "btn-watchdog", "btn-mcp", "btn-pendientes", "btn-conexiones", "btn-room", "btn-power", "btn-sandbox", "btn-copiar-input", "btn-detener"];
function atajos(panel) {
  if (panel.querySelector(".mas-atajo")) return;
  ATAJOS.forEach(([n, sel]) => {
    const b = document.createElement("button");
    b.type = "button"; b.className = "secondary mas-atajo"; b.textContent = n;
    b.addEventListener("click", () => { const x = document.querySelector(sel); if (x) x.click(); });
    panel.append(b);
  });
}
function cuentaTareas() {
  const b = document.getElementById("btn-tareas"); if (!b) return;
  let n = 0;
  try { n = (JSON.parse(localStorage.getItem("riu_tareas_v1") || "{}").tareas || []).filter((t) => t && t.on).length; } catch (e) {}
  b.setAttribute("aria-label", n ? "Tareas, " + n + " encendidas" : "Tareas");
  const s = b.querySelector(".mas-nom"); if (s) s.textContent = b.getAttribute("aria-label");
}
const movil = () => matchMedia("(max-width:720px)").matches;

function armar() {
  const bar = document.querySelector("#composer .composer-bar");
  if (!bar || document.querySelector("#btn-mas")) return null;
  const b = document.createElement("button");
  b.type = "button";
  b.id = "btn-mas";
  b.className = "secondary";
  b.title = "Configuración";
  b.setAttribute("aria-label", "Configuración");
  b.setAttribute("aria-expanded", "false");
  b.innerHTML = '<svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M4 7h16M8 12h12M4 17h10"/></svg>';
  const panel = document.createElement("div");
  panel.id = "mas-panel";
  panel.hidden = true;
  b.onclick = () => {
    const abrir = panel.hidden;
    panel.hidden = !abrir;
    b.setAttribute("aria-expanded", String(abrir));
    if (abrir) ubicar();
  };
  document.body.append(panel);
  panel.addEventListener("click", (ev) => {
    if (!ev.target.closest("button")) return;
    panel.hidden = true;
    b.setAttribute("aria-expanded", "false");
  });
  bar.insertBefore(b, bar.querySelector(".action") || null);
  return panel;
}

function ubicar() {
  const panel = document.querySelector("#mas-panel");
  const comp = document.querySelector("#composer");
  if (!panel || !comp || panel.hidden) return;
  const r = comp.getBoundingClientRect();
  const alto = Math.max(160, Math.min(window.innerHeight * 0.62, r.top - 16));
  panel.style.bottom = Math.round(window.innerHeight - r.top + 8) + "px";
  panel.style.maxHeight = Math.round(alto) + "px";
}

function nombre(b) {
  if (b.querySelector(".mas-nom") || !b.querySelector("svg") || b.textContent.trim()) return;
  const n = document.createElement("span");
  n.className = "mas-nom";
  n.textContent = b.getAttribute("aria-label") || b.title || "";
  b.append(n);
}

function colocar() {
  const panel = document.querySelector("#mas-panel") || armar();
  if (!panel || !movil()) return;
  IDS.forEach((id) => {
    const b = document.getElementById(id);
    if (!b || b.parentNode === panel) return;
    nombre(b);
    panel.append(b);
  });
  atajos(panel);
  cuentaTareas();
  const chips = document.querySelector("#composer .composer-chips");
  if (chips && !chips.childElementCount) chips.remove();
}

new MutationObserver(() => colocar()).observe(document.body, { childList: true, subtree: true });
colocar();
