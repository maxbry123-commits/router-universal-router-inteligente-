// Celular: tres grupos, ninguna fila que se desplace.
// Refuta 1: Detener iba en el menú. Es el corte del proceso, va fuera, al lado de Enviar.
// Refuta 2: nowrap + overflow:hidden recortaba Enviar (el círculo azul se salía).
// Refuta 3: archivos, ancla, sandbox, Auto y el cuaderno no son la misma fila.
//   Accion (fuera): adjuntar, micrófono, detener, enviar.
//   Contexto (selector): archivos, anclar, sandbox, copiar, claves, workflows.
//   Cuaderno (selector): loop, cola, watchdog, prompt, skills y el resto de ventanas.
// El modelo sigue en su selector, debajo de la caja. Auto sale de la fila de iconos.
const CONTEXTO = ["btn-archivos", "btn-ancla", "btn-sandbox", "btn-copiar-input"];
const INTERRUPTORES = ["btn-tools", "btn-agentes", "btn-prompt"];
const VENTANAS = ["btn-loop", "btn-cola", "btn-tareas", "btn-comandos", "btn-sesion", "btn-reglas", "btn-watchdog", "btn-mcp", "btn-pendientes", "btn-conexiones", "btn-room", "btn-power"];
const CUADERNO = [...INTERRUPTORES, ...VENTANAS];
const ATAJOS = [["Claves", "#pill-claves"], ["Workflows", "#pill-workflows"]];
const movil = () => matchMedia("(max-width:720px)").matches;

const st = document.createElement("style");
st.textContent = "@media(max-width:720px){"
  + "#composer{display:flex !important;flex-direction:column !important;max-width:100%;min-width:0;overflow:hidden}"
  + "#composer #message{order:1}"
  + "#composer .composer-bar{order:2;display:flex !important;flex-wrap:wrap !important;overflow:visible !important;align-items:center;gap:6px !important;max-width:100%;min-width:0}"
  + "#composer .composer-bar::after{content:none !important;display:none !important}"
  + "#composer .composer-bar>button.secondary:not(.grp){width:40px !important;min-width:40px !important;max-width:40px !important;height:40px !important;flex:0 0 40px !important}"
  + "#composer #btn-adjunto,#composer #btn-microfono{order:3}"
  + "#composer .composer-bar>button.grp{order:1;flex:1 1 calc(50% - 8px) !important;width:auto !important;max-width:none !important;min-width:0 !important;min-height:40px !important;height:40px !important;border-radius:999px;padding:0 12px !important;font-size:13px}"
  + "#composer #btn-detener{order:4;display:inline-flex !important;margin-left:auto !important}"
  + "#composer .composer-bar>.action{order:5;position:static !important;margin-left:0 !important;flex:0 0 44px !important;width:44px !important;min-width:44px !important;max-width:44px !important;height:44px !important;min-height:44px !important;padding:0 !important;border-radius:50% !important;overflow:visible !important}"
  + "#composer .composer-bar>.action::after,#composer .composer-bar>.action .env-txt{content:none !important;display:none !important}"
  + "#composer .composer-bar>.p3d{flex:1 1 100% !important;order:-1;max-width:100%}"
  + "#composer #btn-selector-modelos{order:3 !important;margin:6px 0 0 !important;align-self:stretch;width:100%;min-height:44px;box-sizing:border-box}"
  + "#composer > #mode-selector-mount{order:4;display:flex;align-items:center;margin-top:6px;max-width:100%}"
  + "#ctx-panel,#mas-panel{position:fixed;z-index:80;left:12px;right:12px;display:grid;grid-template-columns:minmax(0,1fr) minmax(0,1fr);gap:6px;padding:8px;border-radius:16px;background:var(--surface,#1e1e1e);border:1px solid var(--border);overflow:auto;box-shadow:0 12px 32px rgba(0,0,0,.5)}"
  + "#ctx-panel[hidden],#mas-panel[hidden]{display:none !important}"
  + "#ctx-panel button,#mas-panel button{width:auto !important;max-width:100%;height:auto !important;min-width:0;min-height:44px;aspect-ratio:auto;border-radius:12px;display:inline-flex;align-items:center;justify-content:flex-start;gap:8px;padding:6px 10px}"
  + "#ctx-panel .mas-nom,#mas-panel .mas-nom{min-width:0;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;font-size:13px}"
  + "#mas-panel .mas-sec{grid-column:1 / -1;font-size:11px;letter-spacing:.04em;text-transform:uppercase;opacity:.65;padding:6px 4px 0}"
  + "}";
document.head.append(st);

function panel(id) {
  let p = document.getElementById(id);
  if (p) return p;
  p = document.createElement("div");
  p.id = id;
  p.hidden = true;
  document.body.append(p);
  return p;
}

function rotulo(b) {
  if (b.querySelector(".mas-nom") || !b.querySelector("svg")) return;
  const n = document.createElement("span");
  n.className = "mas-nom";
  n.textContent = b.getAttribute("aria-label") || b.title || "";
  b.append(n);
}

function quitarRotulo(b) {
  const n = b.querySelector(".mas-nom");
  if (n) n.remove();
}

function grupo(id, texto, hoja) {
  const bar = document.querySelector("#composer .composer-bar");
  if (!bar) return null;
  let b = document.getElementById(id);
  if (!b) {
    b = document.createElement("button");
    b.type = "button";
    b.id = id;
    b.className = "secondary grp";
    b.textContent = texto;
    b.setAttribute("aria-haspopup", "menu");
    b.setAttribute("aria-expanded", "false");
    b.setAttribute("aria-controls", hoja);
    b.addEventListener("click", () => abrir(hoja, b));
  }
  const env = bar.querySelector(".action");
  if (b.parentNode !== bar) bar.insertBefore(b, env || null);
  return b;
}

function abrir(id, boton) {
  const propio = document.getElementById(id);
  const otro = document.getElementById(id === "ctx-panel" ? "mas-panel" : "ctx-panel");
  if (otro) otro.hidden = true;
  document.querySelectorAll(".grp").forEach((g) => { if (g !== boton) g.setAttribute("aria-expanded", "false"); });
  const on = propio.hidden;
  propio.hidden = !on;
  boton.setAttribute("aria-expanded", String(on));
  if (on) ubicar(propio);
}

function ubicar(hoja) {
  const comp = document.querySelector("#composer");
  if (!hoja || !comp || hoja.hidden) return;
  const r = comp.getBoundingClientRect();
  hoja.style.bottom = Math.round(window.innerHeight - r.top + 8) + "px";
  hoja.style.maxHeight = Math.round(Math.max(160, Math.min(window.innerHeight * 0.62, r.top - 16))) + "px";
}

function meter(id, hoja) {
  const b = document.getElementById(id);
  if (!b || b.parentNode === hoja) return;
  rotulo(b);
  hoja.append(b);
}

function atajos(hoja) {
  if (hoja.querySelector(".mas-atajo")) return;
  ATAJOS.forEach(([n, sel]) => {
    const b = document.createElement("button");
    b.type = "button";
    b.className = "secondary mas-atajo";
    b.textContent = n;
    b.addEventListener("click", () => { const x = document.querySelector(sel); if (x) x.click(); });
    hoja.append(b);
  });
}

function parqueAuto() {
  const modo = document.querySelector("#mode-selector-mount");
  const comp = document.querySelector("#composer");
  const modelo = document.querySelector("#btn-selector-modelos");
  if (!modo || !comp) return;
  if (modelo && modo.previousSibling !== modelo) modelo.after(modo);
  else if (!modelo && modo.parentNode !== comp) comp.append(modo);
}

function devolverAuto() {
  const modo = document.querySelector("#mode-selector-mount");
  const bar = document.querySelector("#composer .composer-bar");
  const ancla = document.querySelector("#btn-detener");
  if (!modo || !bar || modo.parentNode === bar) return;
  bar.insertBefore(modo, ancla || bar.querySelector(".action") || null);
}

function bar() { return document.querySelector("#composer .composer-bar"); }

function devolver() {
  const fila = bar();
  if (!fila) return;
  const env = fila.querySelector(".action");
  [...CONTEXTO, ...CUADERNO].forEach((id) => {
    const b = document.getElementById(id);
    if (!b || b.parentNode === fila) return;
    quitarRotulo(b);
    fila.insertBefore(b, env || null);
  });
  const mirror = document.querySelector("#mirror-selector-mount");
  if (mirror && mirror.parentNode !== fila) fila.insertBefore(mirror, document.querySelector("#btn-detener") || env || null);
  document.querySelectorAll(".mas-atajo").forEach((n) => n.remove());
  ["ctx-panel", "mas-panel"].forEach((id) => { const p = document.getElementById(id); if (p) p.hidden = true; });
  document.querySelectorAll(".grp").forEach((g) => g.remove());
  devolverAuto();
}

function firma(hoja) {
  return [...hoja.children].map((n) => n.classList.contains("mas-sec") ? "s:" + n.textContent : n.id || n.className).join("|");
}

function colocar() {
  const fila = bar();
  if (!fila) return;
  if (!movil()) { devolver(); return; }
  const ctx = panel("ctx-panel");
  const libro = panel("mas-panel");
  grupo("btn-contexto", "Contexto", "ctx-panel");
  grupo("btn-cuaderno", "Cuaderno", "mas-panel");
  CONTEXTO.forEach((id) => meter(id, ctx));
  atajos(ctx);
  const ids = (lista) => lista.filter((id) => document.getElementById(id));
  const want = "s:Interruptores|" + ids(INTERRUPTORES).join("|") + "|s:Ventanas|" + ids(VENTANAS).join("|");
  if (firma(libro) !== want) {
    const sec = (titulo) => {
      let s = [...libro.querySelectorAll(".mas-sec")].find((n) => n.textContent === titulo);
      if (!s) { s = document.createElement("div"); s.className = "mas-sec"; s.textContent = titulo; }
      libro.append(s);
    };
    const poner = (id) => { const b = document.getElementById(id); if (!b) return; rotulo(b); libro.append(b); };
    sec("Interruptores");
    INTERRUPTORES.forEach(poner);
    sec("Ventanas");
    VENTANAS.forEach(poner);
  }
  const mirror = document.querySelector("#mirror-selector-mount");
  if (mirror && mirror.childElementCount && mirror.parentNode !== libro) libro.append(mirror);
  parqueAuto();
}

document.addEventListener("click", (ev) => {
  if (ev.target.closest("#ctx-panel, #mas-panel, #btn-contexto, #btn-cuaderno")) return;
  document.querySelectorAll("#ctx-panel, #mas-panel").forEach((p) => { p.hidden = true; });
  document.querySelectorAll(".grp").forEach((g) => g.setAttribute("aria-expanded", "false"));
});
["ctx-panel", "mas-panel"].forEach((id) => {
  document.addEventListener("click", (ev) => {
    const p = document.getElementById(id);
    if (!p || p.hidden || !p.contains(ev.target) || !ev.target.closest("button")) return;
    p.hidden = true;
    document.querySelectorAll(".grp").forEach((g) => g.setAttribute("aria-expanded", "false"));
  });
});

new MutationObserver(() => colocar()).observe(document.body, { childList: true, subtree: true });
matchMedia("(max-width:720px)").addEventListener("change", colocar);
addEventListener("resize", () => { ubicar(document.getElementById("ctx-panel")); ubicar(document.getElementById("mas-panel")); });
colocar();
