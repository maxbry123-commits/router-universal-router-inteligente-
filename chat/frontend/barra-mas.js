// Celular: tres grupos, ninguna fila que se desplace.
// Refuta 1: Detener iba en el menú. Es el corte del proceso, va fuera, al lado de Enviar.
// Refuta 2: nowrap + overflow:hidden recortaba Enviar (el círculo azul se salía).
// Refuta 3: archivos, ancla, sandbox, Auto y el cuaderno no son la misma fila.
//   Accion (fuera): adjuntar, micrófono, detener, enviar.
//   Contexto (selector): archivos, anclar, sandbox, copiar, claves, workflows.
//   Cuaderno (selector): loop, cola, watchdog, prompt, skills y el resto de ventanas.
// El modelo sigue en su selector, debajo de la caja. Auto sale de la fila de iconos.
const CONTEXTO = ["btn-archivos", "btn-ancla", "btn-sandbox", "btn-copiar-input"];
const TRABAJO = ["btn-loop", "btn-cola", "btn-watchdog"];
const INTERRUPTORES = ["btn-tools", "btn-agentes", "btn-prompt"];
const VENTANAS = ["btn-tareas", "btn-comandos", "btn-sesion", "btn-reglas", "btn-mcp", "btn-pendientes", "btn-conexiones", "btn-room", "btn-power"];
const CUADERNO = [...INTERRUPTORES, ...VENTANAS];
const ATAJOS = [["Claves", "#pill-claves"], ["Workflows", "#pill-workflows"]];
const movil = () => matchMedia("(max-width:720px)").matches;

const st = document.createElement("style");
st.textContent = "@media(max-width:720px){"
  + "#composer{display:flex !important;flex-direction:column !important;max-width:100%;min-width:0;overflow:hidden;padding:6px 8px 4px !important;border-radius:16px !important}"
  + "#composer #message{order:1;min-height:40px !important;max-height:72px !important;padding:4px 6px !important;font-size:16px}"
  + "#composer .composer-bar{order:2;display:flex !important;flex-wrap:wrap !important;overflow:visible !important;align-items:center;gap:4px !important;max-width:100%;min-width:0}"
  + "#composer .composer-bar::after{content:none !important;display:none !important}"
  + "#composer .composer-bar>button.secondary:not(.grp){width:34px !important;min-width:34px !important;max-width:34px !important;height:34px !important;min-height:34px !important;flex:0 0 34px !important}"
  + "#composer #btn-adjunto,#composer #btn-microfono{order:3}"
  + "#composer .composer-bar>button.grp{order:1;flex:1 1 0 !important;width:auto !important;max-width:none !important;min-width:0 !important;min-height:28px !important;height:28px !important;border-radius:999px;padding:0 6px !important;font-size:12px}"
  + "#composer #btn-detener{order:4;display:inline-flex !important;margin-left:auto !important}"
  + "#composer .composer-bar>.action{order:5;position:static !important;margin-left:0 !important;flex:0 0 36px !important;width:36px !important;min-width:36px !important;max-width:36px !important;height:36px !important;min-height:36px !important;padding:0 !important;border-radius:50% !important;overflow:visible !important}"
  + "#composer .composer-bar>.action::after,#composer .composer-bar>.action .env-txt{content:none !important;display:none !important}"
  + "#composer .composer-bar>.p3d{flex:1 1 100% !important;order:-1;max-width:100%}"
  + "#composer #btn-selector-modelos{order:3 !important;margin:4px 0 0 !important;align-self:stretch;width:100%;min-height:34px !important;height:34px;box-sizing:border-box;padding:0 10px !important}"
  + "#composer > #mode-selector-mount{order:4;display:flex;align-items:center;margin-top:4px;max-width:100%}"
  + ".riu-hoja .riu-lista{display:flex;flex-direction:column;gap:4px}"
  + ".riu-hoja .riu-lista button{width:100% !important;max-width:100%;height:auto !important;min-height:34px !important;aspect-ratio:auto;border-radius:12px;display:inline-flex;align-items:center;justify-content:flex-start;gap:8px;padding:4px 10px !important}"
  + ".riu-hoja .mas-nom{font-size:14px}"
  + ".riu-hoja .mas-sec{font-size:11px;letter-spacing:.04em;text-transform:uppercase;opacity:.6;padding:8px 4px 0}"
  + ".chat-history{min-height:0 !important}"
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
  t.textContent = titulo;
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

function atajos(hoja) {
  if (hoja.querySelector(".mas-atajo")) return;
  ATAJOS.forEach(([n, sel]) => {
    const b = document.createElement("button");
    b.type = "button";
    b.className = "secondary mas-atajo";
    b.textContent = n;
    b.addEventListener("click", () => { const x = document.querySelector(sel); if (x) x.click(); });
    listaDe(hoja).append(b);
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
    if (!b || b.parentNode === fila) return;
    quitarRotulo(b);
    fila.insertBefore(b, env || null);
  });
  const mirror = document.querySelector("#mirror-selector-mount");
  if (mirror && mirror.parentNode !== fila) fila.insertBefore(mirror, document.querySelector("#btn-detener") || env || null);
  document.querySelectorAll(".mas-atajo").forEach((n) => n.remove());
  ["ctx-panel", "trab-panel", "mas-panel"].forEach((id) => { const p = document.getElementById(id); if (p) p.hidden = true; });
  document.querySelectorAll(".grp").forEach((g) => g.remove());
  devolverAuto();
}

function firma(hoja) {
  const n = listaDe(hoja);
  return [...n.children].map((x) => x.classList.contains("mas-sec") ? "s:" + x.textContent : x.id || x.className).join("|");
}

function colocar() {
  const fila = bar();
  if (!fila) return;
  if (!movil()) { devolver(); return; }
  const ctx = panel("ctx-panel", "Contexto");
  const trab = panel("trab-panel", "Trabajo");
  const libro = panel("mas-panel", "Cuaderno");
  grupo("btn-contexto", "Contexto", "ctx-panel");
  grupo("btn-trabajo", "Trabajo", "trab-panel");
  grupo("btn-cuaderno", "Cuaderno", "mas-panel");
  CONTEXTO.forEach((id) => meter(id, ctx));
  atajos(ctx);
  TRABAJO.forEach((id) => meter(id, trab));
  const ids = (lista) => lista.filter((id) => document.getElementById(id));
  const want = "s:Interruptores|" + ids(INTERRUPTORES).join("|") + "|s:Ventanas|" + ids(VENTANAS).join("|");
  const libroLista = listaDe(libro);
  if (firma(libro) !== want) {
    const sec = (titulo) => {
      let s = [...libroLista.querySelectorAll(".mas-sec")].find((n) => n.textContent === titulo);
      if (!s) { s = document.createElement("div"); s.className = "mas-sec"; s.textContent = titulo; }
      libroLista.append(s);
    };
    const poner = (id) => { const b = document.getElementById(id); if (!b) return; rotulo(b); libroLista.append(b); };
    sec("Interruptores");
    INTERRUPTORES.forEach(poner);
    sec("Ventanas");
    VENTANAS.forEach(poner);
  }
  const mirror = document.querySelector("#mirror-selector-mount");
  if (mirror && mirror.childElementCount && mirror.parentNode !== libroLista) libroLista.append(mirror);
  parqueAuto();
}

document.addEventListener("click", (ev) => {
  if (ev.target.closest(".riu-hoja, .grp")) return;
  document.querySelectorAll(".riu-hoja").forEach((p) => { p.hidden = true; });
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
