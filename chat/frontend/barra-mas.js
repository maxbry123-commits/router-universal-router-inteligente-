// En el celular, LOOP, Cola, Watchdog y el resto de controles viven en un solo botón.
const st = document.createElement("style");
st.textContent = "@media(max-width:720px){.riu-bv-acc{display:none !important}.riu-bienvenida{justify-content:flex-start;padding-top:8px}#composer #message{min-height:44px !important;max-height:96px !important}}";
document.head.append(st);
const IDS = ["btn-prompt", "btn-loop", "btn-cola", "btn-watchdog", "btn-mcp", "btn-pendientes", "btn-conexiones", "btn-room", "btn-power", "btn-sandbox", "btn-copiar-input"];
const movil = () => matchMedia("(max-width:720px)").matches;

function armar() {
  const bar = document.querySelector("#composer .composer-bar");
  if (!bar || document.querySelector("#btn-mas")) return null;
  const comp = document.querySelector("#composer");
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
  };
  comp.append(panel);
  panel.addEventListener("click", (ev) => { if (!ev.target.closest("button")) return; panel.hidden = true; b.setAttribute("aria-expanded", "false"); });
  bar.insertBefore(b, bar.querySelector(".action") || null);
  return panel;
}

function nombre(b) {
  if (b.querySelector(".mas-nom")) return;
  const n = document.createElement("span");
  n.className = "mas-nom";
  n.textContent = (b.getAttribute("aria-label") || b.title || "").replace(/^Activar el |^Permitir que el modelo use /, "");
  b.append(n);
}

function colocar() {
  const panel = document.querySelector("#mas-panel") || armar();
  if (!panel) return;
  if (!movil()) return;
  IDS.forEach((id) => {
    const b = document.getElementById(id);
    if (!b || b.parentNode === panel) return;
    nombre(b);
    panel.append(b);
  });
}

const ver = () => { colocar(); };
new MutationObserver(ver).observe(document.body, { childList: true, subtree: true });
ver();
