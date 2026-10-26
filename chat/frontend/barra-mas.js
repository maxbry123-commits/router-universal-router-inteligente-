// Celular: tres grupos, ninguna fila que se desplace.
// Refuta 1: Detener iba en el menú. Es el corte del proceso, va fuera, al lado de Enviar.
// Refuta 2: nowrap + overflow:hidden recortaba Enviar (el círculo azul se salía).
// Refuta 3: archivos, ancla, sandbox, Auto y el cuaderno no son la misma fila.
//   Accion (fuera): adjuntar, micrófono, detener, enviar.
//   Contexto (selector): archivos, anclar, sandbox, copiar, claves, workflows.
//   Cuaderno (selector): loop, cola, watchdog, prompt, skills y el resto de ventanas.
// El modelo sigue en su selector, debajo de la caja. Auto sale de la fila de iconos.
const CONTEXTO = ["btn-archivos", "btn-ancla", "btn-sandbox", "btn-copiar-input"];
const TRABAJO = ["btn-loop", "btn-cola", "btn-watchdog", "btn-tools", "btn-agentes", "btn-prompt"];
const INTERRUPTORES = ["btn-tools", "btn-agentes", "btn-prompt"];
const VENTANAS = ["btn-tareas", "btn-comandos", "btn-sesion", "btn-reglas", "btn-mcp", "btn-pendientes", "btn-conexiones", "btn-room", "btn-power"];
const CUADERNO = VENTANAS;
const PILLS_CTX = ["ancla", "btn-proyectos", "pill-claves", "pill-workflows"];
const PILLS_TRAB = ["btn-llm-tool", "btn-agent-access-lock"];
const PILLS_CUAD = ["mas", "motor", "btn-motor-on", "pill-constitucion"];
const PILLS = [...PILLS_CTX, ...PILLS_TRAB, ...PILLS_CUAD];
const movil = () => matchMedia("(max-width:720px)").matches;

const st = document.createElement("style");
st.textContent = "@media(max-width:720px){"
  + "#composer{display:flex !important;flex-direction:column !important;max-width:100%;min-width:0;overflow:visible;padding:6px 8px 4px !important;border-radius:16px !important}"
  + "#composer #message{order:1;min-height:36px !important;max-height:64px !important;padding:4px 6px !important;font-size:16px}"
  + "#composer .composer-bar{order:2;display:flex !important;flex-wrap:wrap !important;overflow:visible !important;align-items:center;gap:4px !important;max-width:100%;min-width:0}"
  + ".ctl-int>.row.fields:not(:has(button:not([hidden]))){display:none !important}"
  + "#composer .composer-bar::after{content:\"\" !important;display:block !important;flex:1 0 100% !important;height:0 !important;order:4 !important}"
  + "#composer .composer-bar>button.secondary:not(#btn-tools):not(#btn-agentes):not(#btn-prompt){width:34px !important;min-width:34px !important;max-width:34px !important;height:34px !important;min-height:34px !important;flex:0 0 34px !important;padding:0 !important;border-radius:50% !important}"
  + "#composer #btn-tools,#composer #btn-agentes,#composer #btn-prompt{order:4;width:auto !important;max-width:none !important;height:34px !important;min-height:34px !important;flex:0 0 auto !important;aspect-ratio:auto !important;border-radius:999px !important;padding:0 12px !important}"
  + "#composer #btn-detener{order:5;display:inline-flex !important;margin-left:8px !important}"
  + "#composer #btn-paralelo{order:5 !important;margin-left:auto !important;height:34px !important;min-height:34px !important;width:auto !important;max-width:none !important;flex:0 0 auto !important;border-radius:999px !important;padding:0 12px !important}"
  + "#composer .composer-bar>.action{order:6;position:static !important;margin-left:8px !important;flex:0 0 auto !important;width:auto !important;min-width:132px !important;max-width:none !important;height:46px !important;min-height:46px !important;padding:0 22px !important;border-radius:12px !important}"
  + "#composer .composer-bar>.action::after{content:\"Enviar\" !important;display:inline !important;font-size:15px !important}"
  + "#composer .composer-bar>.p3d{flex:1 1 100% !important;order:-1;max-width:100%}"
  + "#composer #btn-selector-modelos{order:3 !important;margin:4px 0 0 !important;align-self:stretch;width:100%;min-height:34px !important;height:34px;box-sizing:border-box;padding:0 10px !important}"
  + "#composer > #mode-selector-mount{order:4;display:flex;align-items:center;margin-top:4px;max-width:100%}"
  + ".riu-hoja .riu-lista{display:flex;flex-direction:column;gap:4px}"
  + ".riu-hoja .riu-lista button{width:100% !important;max-width:100%;height:auto !important;min-height:34px !important;aspect-ratio:auto;border-radius:12px;display:inline-flex;align-items:center;justify-content:flex-start;gap:8px;padding:4px 10px !important}"
  + ".riu-hoja .riu-lista .pill{max-width:none !important;width:100% !important;flex:1 1 auto !important}"
  + ".riu-hoja .mas-sec{font-size:11px;letter-spacing:.04em;text-transform:uppercase;opacity:.6;padding:8px 4px 0}"
  + ".chat-history{min-height:0 !important;flex:1 1 auto}"
  + "#mas-pop{position:fixed;left:12px;right:12px;z-index:60;display:grid;grid-template-columns:1fr 1fr;gap:6px;max-height:46dvh;overflow-y:auto;padding:8px;border-radius:16px;background:var(--surface);border:1px solid var(--border);box-shadow:0 12px 32px rgba(0,0,0,.5)}"
  + "#mas-pop[hidden]{display:none !important}"
  + "#mas-pop button{width:100% !important;max-width:none !important;height:auto !important;min-height:40px !important;aspect-ratio:auto !important;border-radius:12px !important;padding:8px 10px !important;display:inline-flex;align-items:center;justify-content:flex-start;gap:8px}"
  + "}";
document.head.append(st);

function panel(id, titulo) {
  let p = document.getElementById(id);
  if (p) return p;
  p = document.createElement("div");
  p.id = id;
  p.className = "sheet riu-hoja";
  p.hidden = true;
  p.setAttribute("role", "dialog");
  p.setAttribute("aria-modal", "true");
  p.setAttribute("aria-label", titulo);
  const caja = document.createElement("div");
  caja.className = "va-caja";
  const head = document.createElement("div");
  head.className = "row va-head";
  const t = document.createElement("strong");
  t.innerHTML = titulo;
  const x = document.createElement("button");
  x.type = "button";
  x.className = "secondary sh-cerrar";
  x.textContent = "✕";
  x.setAttribute("aria-label", "Cerrar");
  x.onclick = (ev) => { ev.stopPropagation(); p.hidden = true; };
  const list = document.createElement("div");
  list.className = "list riu-lista";
  head.append(t, x);
  caja.append(head, list);
  p.append(caja);
  p.addEventListener("click", (ev) => { if (ev.target === p) p.hidden = true; });
  document.body.append(p);
  return p;
}
function listaDe(hoja) { return hoja.querySelector(".riu-lista") || hoja; }

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

function svg(d) {
  return '<svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">' + d + "</svg>";
}
const ICO = {
  archivos: '<path d="M4 6h6l2 2h8v11H4z"/>',
  loop: '<path d="M4 12a8 8 0 0 1 13.5-5.5L20 4"/><path d="M20 4v5h-5"/><path d="M20 12a8 8 0 0 1-13.5 5.5L4 20"/><path d="M4 20v-5h5"/>',
  config: '<circle cx="12" cy="12" r="3"/><path d="M12 3v2M12 19v2M3 12h2M19 12h2M5.6 5.6l1.4 1.4M17 17l1.4 1.4M18.4 5.6 17 7M7 17l-1.4 1.4"/>',
};
function grupo(id, icono, hoja, etiqueta) {
  const bar = document.querySelector("#composer .composer-bar");
  if (!bar) return null;
  let b = document.getElementById(id);
  if (!b) {
    b = document.createElement("button");
    b.type = "button";
    b.id = id;
    b.className = "secondary grp";
    b.setAttribute("aria-haspopup", "menu");
    b.setAttribute("aria-expanded", "false");
    b.setAttribute("aria-controls", hoja);
    b.addEventListener("click", () => abrir(hoja, b));
  }
  if (!b.querySelector("svg")) b.innerHTML = svg(icono);
  b.setAttribute("aria-label", etiqueta);
  const env = bar.querySelector(".action");
  if (b.parentNode !== bar) bar.insertBefore(b, env || null);
  return b;
}

function abrir(id, boton) {
  const propio = document.getElementById(id);
  document.querySelectorAll(".riu-hoja").forEach((p) => { if (p !== propio) p.hidden = true; });
  document.querySelectorAll(".grp").forEach((g) => { if (g !== boton) g.setAttribute("aria-expanded", "false"); });
  const on = propio.hidden;
  propio.hidden = !on;
  boton.setAttribute("aria-expanded", String(on));
}

function meter(id, hoja) {
  const b = document.getElementById(id);
  const destino = listaDe(hoja);
  if (!b || b.parentNode === destino) return;
  rotulo(b);
  destino.append(b);
}

const NOMBRE = { mas: "Más opciones", motor: "Panel del motor", "pill-claves": "Claves", "pill-workflows": "Workflows", "pill-constitucion": "Constitución" };
function meterPill(id, hoja) {
  const b = document.getElementById(id);
  if (!b) return;
  if (!b._casa) { b._casa = b.parentNode; b._sig = b.nextSibling; }
  if (b.dataset.orig == null) b.dataset.orig = b.textContent;
  meter(id, hoja);
  let sig = NOMBRE[id] || "";
  if (id === "ancla") {
    const fuente = b.textContent.includes("Constitución") ? b.textContent : (b.dataset.orig || "");
    sig = "Handoff · Constitución " + (fuente.includes(" ON") ? "ON" : "OFF");
  }
  if (sig && b.textContent !== sig) b.textContent = sig;
}
function devolverPills() {
  PILLS.forEach((id) => {
    const b = document.getElementById(id);
    if (!b || !b._casa || !b._casa.isConnected || b.parentNode === b._casa) return;
    if (b.dataset.orig != null) b.textContent = b.dataset.orig;
    const sig = b._sig && b._sig.parentNode === b._casa ? b._sig : null;
    b._casa.insertBefore(b, sig);
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
  [...CONTEXTO, ...TRABAJO, ...CUADERNO].forEach((id) => {
    const b = document.getElementById(id);
    if (!b || b.parentNode === fila || (b.parentNode && b.parentNode.id === "mas-pop")) return;
    quitarRotulo(b);
    fila.insertBefore(b, env || null);
  });
  const mirror = document.querySelector("#mirror-selector-mount");
  if (mirror && mirror.parentNode !== fila) fila.insertBefore(mirror, document.querySelector("#btn-detener") || env || null);
  document.querySelectorAll(".mas-atajo").forEach((n) => n.remove());
  devolverPills();
  ["ctx-panel", "trab-panel", "mas-panel"].forEach((id) => { const p = document.getElementById(id); if (p) p.hidden = true; });
  document.querySelectorAll(".grp").forEach((g) => g.remove());
  devolverAuto();
}

function firma(hoja) {
  const n = listaDe(hoja);
  return [...n.children].map((x) => x.classList.contains("mas-sec") ? "s:" + x.textContent : x.id || x.className).join("|");
}

const FUERA = ["btn-loop", "btn-cola", "btn-watchdog", "btn-tareas", "btn-comandos", "btn-sesion", "btn-reglas", "btn-mcp", "btn-pendientes", "btn-conexiones", "btn-room", "btn-power"];
function menu() {
  const fila = bar();
  if (!fila) return;
  let pop = document.getElementById("mas-pop");
  if (!movil()) {
    if (!pop) return;
    const env = fila.querySelector(".action");
    [...pop.children].forEach((b) => { if (b.id) { quitarRotulo(b); fila.insertBefore(b, env); } });
    pop.hidden = true;
    return;
  }
  if (!pop) {
    pop = document.createElement("div");
    pop.id = "mas-pop";
    pop.hidden = true;
    pop.setAttribute("role", "menu");
    document.body.append(pop);
    pop.addEventListener("click", (ev) => { if (ev.target.closest("button")) pop.hidden = true; });
  }
  FUERA.forEach((id) => { const b = document.getElementById(id); if (!b || b.parentNode === pop) return; rotulo(b); pop.append(b); });
  let btn = document.getElementById("btn-mas");
  if (!btn) {
    btn = document.createElement("button");
    btn.type = "button";
    btn.id = "btn-mas";
    btn.className = "secondary";
    btn.setAttribute("aria-label", "Más");
    btn.setAttribute("aria-expanded", "false");
    btn.innerHTML = svg('<path d="M4 7h16M4 12h16M4 17h16"/>');
    btn.addEventListener("click", (ev) => {
      ev.stopPropagation();
      const p = document.getElementById("mas-pop");
      const c = document.getElementById("composer");
      if (!p || !c) return;
      p.style.bottom = Math.max(8, window.innerHeight - c.getBoundingClientRect().top + 8) + "px";
      p.hidden = !p.hidden;
      btn.setAttribute("aria-expanded", String(!p.hidden));
    });
  }
  const env = fila.querySelector(".action");
  if (btn.parentNode !== fila) fila.insertBefore(btn, env);
}
function tres() {
  const ctx = panel("ctx-panel", "Archivos");
  const trab = panel("trab-panel", "LOOP");
  const cuad = panel("mas-panel", "Ventanas");
  grupo("btn-grp-ctx", ICO.archivos, "ctx-panel", "Archivos");
  grupo("btn-grp-trab", ICO.loop, "trab-panel", "LOOP");
  grupo("btn-grp-cuad", ICO.config, "mas-panel", "Ventanas");
  CONTEXTO.forEach((id) => meter(id, ctx));
  TRABAJO.forEach((id) => meter(id, trab));
  CUADERNO.forEach((id) => meter(id, cuad));
  PILLS_CTX.forEach((id) => meterPill(id, ctx));
  PILLS_TRAB.forEach((id) => meterPill(id, trab));
  PILLS_CUAD.forEach((id) => meterPill(id, cuad));
  parqueAuto();
  const mas = document.getElementById("btn-mas");
  if (mas) mas.remove();
  const pop = document.getElementById("mas-pop");
  if (pop) pop.hidden = true;
}
let ocupado = false;
function colocar() {
  if (ocupado) return;
  ocupado = true;
  try {
    if (!movil()) { devolver(); menu(); return; }
    tres();
  } finally { ocupado = false; }
}

document.addEventListener("click", (ev) => {
  if (ev.target.closest(".riu-hoja, .grp, #mas-pop, #btn-mas")) return;
  document.querySelectorAll(".riu-hoja").forEach((p) => { p.hidden = true; });
  const mas = document.getElementById("mas-pop");
  if (mas) mas.hidden = true;
  document.querySelectorAll(".grp").forEach((g) => g.setAttribute("aria-expanded", "false"));
});
document.addEventListener("click", (ev) => {
  const p = ev.target.closest(".riu-hoja");
  if (!p || p.hidden || ev.target.closest(".sh-cerrar") || !ev.target.closest(".riu-lista button")) return;
  p.hidden = true;
  document.querySelectorAll(".grp").forEach((g) => g.setAttribute("aria-expanded", "false"));
});

new MutationObserver(() => colocar()).observe(document.body, { childList: true, subtree: true });
matchMedia("(max-width:720px)").addEventListener("change", colocar);
colocar();
