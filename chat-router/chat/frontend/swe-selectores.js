// swe-selectores.js — selectores SWE CODE y SWEN CODE free del panel «Selector de modelos» (misma mecanica que el selector Groq):
// la pastilla abre una hoja con sus modelos; el elegido queda en window.RIU_SWE[<selector>] = {model_id, label}.
// Al encender el selector, enviar-mensaje.js manda por swe-directo.js (router propio: el bridge), sin pasar por el Router MVP.
import { api } from "./api.js";
import { camposFijos, entradaParaCatalogo, SWE_LISTAS, EJECUTORES_TOOLS, ETIQUETA_SALIDA, leerEjecutorTools, guardarEjecutorTools, MODELOS_SWE, AGENTES_SWE, WORKFLOWS_SWE, LIQUID_MIRROR, leerSeleccion, guardarSeleccion, requiereHarness, cargarCapacidades, olvidarCapacidades, normalizarCapacidades, estadoOpcion, idCatalogo, agruparOpciones, lineaNoInstalados, leerSecciones, guardarSeccion } from "./swe-directo.js";
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
// Hoja unica y compacta de SWE CODE / SWEN CODE free: cabecera fija (titulo + X), cuerpo con scroll propio y tres secciones plegables
// (Modelo | Agentes | Workflow y salida). Los controles de agente/ejecutor/workflow/modo agentico/salida existen UNA sola vez en el documento
// (un nodo que se mueve a la hoja abierta); los selectores Groq y NVIDIA solo eligen modelo y no los traen.
const nombreDe = (lista, id) => (lista.find((x) => x[0] === id) || [id, id])[1];
const SALIDA_CORTA = { swe: "SWE-agent", openclaw: "OpenClaw" };
// Salida de las tools (SWE | OpenClaw): mismo estado en el panel Selectores y en la hoja; se guarda en localStorage y viaja como `ejecutor_tools` (swe-directo.js).
function pintarSalida() {
  const v = leerEjecutorTools();
  document.querySelectorAll("[data-salida]").forEach((b) => { const on = b.dataset.salida === v; b.setAttribute("aria-pressed", String(on)); b.classList.toggle("on", on); });
}
function filaSalida() {  // una sola fila: «Salida: [SWE-agent | OpenClaw]» como control segmentado
  const w = document.createElement("div"); w.className = "swe-fila-salida";
  const t = document.createElement("span"); t.className = "sel-salida-t"; t.textContent = "Salida:";
  const f = document.createElement("div"); f.className = "swe-seg"; f.setAttribute("role", "group"); f.setAttribute("aria-label", "Salida de las tools");
  EJECUTORES_TOOLS.forEach((e) => { const b = document.createElement("button"); b.type = "button"; b.dataset.salida = e; b.setAttribute("aria-label", ETIQUETA_SALIDA[e]); b.textContent = SALIDA_CORTA[e]; f.append(b); });
  w.append(t, f); return w;
}
document.addEventListener("click", (e) => { const b = e.target.closest("[data-salida]"); if (b) { guardarEjecutorTools(b.dataset.salida); pintarSalida(); pintarControles(); } });
pintarSalida();
// el panel (panel-chat.html) se inyecta despues de cargar este modulo: al aparecer sus botones se repinta el estado guardado
try { const ob = new MutationObserver((ms) => { if (ms.some((m) => [...m.addedNodes].some((n) => n.nodeType === 1 && (n.matches("[data-salida]") || n.querySelector("[data-salida]"))))) pintarSalida(); }); ob.observe(document.documentElement, { childList: true, subtree: true }); } catch (e) {}
// Agente/modelo/workflow (contrato TareaSWE): el estado se guarda en swe-directo.js.
// Lo que el Harness no reporta conectado queda agrupado al final y deshabilitado (y nombrado en una linea gris), nunca como funcional.
let CAP = normalizarCapacidades(null), CAP_LISTA = false, CTL = null;
const ROTULOS = { agente_responde: "AGENTE QUE RESPONDE", modelo_responde: "MODELO QUE RESPONDE", agente_tool: "AGENTE QUE EJECUTA", modelo_tool: "MODELO PARA TOOL", workflow: "WORKFLOW" };
const LISTAS = { agente_responde: [AGENTES_SWE, "agente"], agente_tool: [AGENTES_SWE, "agente"], modelo_responde: [MODELOS_SWE, "modelo"], modelo_tool: [MODELOS_SWE, "modelo"], workflow: [WORKFLOWS_SWE, "workflow"] };
const el = (tag, cls, txt) => { const n = document.createElement(tag); if (cls) n.className = cls; if (txt != null) n.textContent = txt; return n; };
function seccion(id, titulo) {
  const d = el("details", "sh-sec"); d.dataset.sec = id; d.open = leerSecciones()[id];
  const sm = el("summary"); sm.append(el("span", "sh-sec-t", titulo), el("span", "sh-res"));
  const c = el("div", "sh-sec-cuerpo"); d.append(sm, c); return d;
}
document.addEventListener("toggle", (e) => { const d = e.target; if (d && d.matches && d.matches("details.sh-sec") && d.dataset.sec) guardarSeccion(d.dataset.sec, d.open); }, true);  // 'toggle' no burbujea: captura
function selector(k) { const s = el("select"); s.dataset.sweCtl = k; s.setAttribute("aria-label", ROTULOS[k]); return s; }
function controles() {
  const c = el("div", "swe-ctl"); c.setAttribute("role", "group"); c.setAttribute("aria-label", "Agentes, modelos y workflow de SWE");
  const ag = seccion("agentes", "Agentes"), a = ag.querySelector(".sh-sec-cuerpo");
  const rej = el("div", "swe-rej");
  [["Responde", "agente_responde", "modelo_responde"], ["Ejecuta", "agente_tool", "modelo_tool"]].forEach(([t, a1, m1]) => {
    const r = el("div", "swe-rej-fila"); r.append(el("span", "swe-rej-t", t), selector(a1), selector(m1)); rej.append(r);
  });
  const mo = el("div", "sel-salida"); mo.setAttribute("role", "group"); mo.setAttribute("aria-label", "Modo agéntico");
  const b = el("button", "pill salida-op"); b.type = "button"; b.dataset.sweAgentico = "1"; b.setAttribute("aria-label", "MODO AGÉNTICO");
  mo.append(el("span", "sel-salida-t", "Modo agéntico:"), b);
  a.append(rej, mo, el("p", "fila-desc swe-fijo"), el("p", "fila-desc swe-noinst"), el("p", "fila-desc swe-estado"));
  const wf = seccion("workflow", "Workflow y salida"), w = wf.querySelector(".sh-sec-cuerpo");
  const fw = el("div", "swe-rej-fila swe-wf"); fw.append(el("span", "swe-rej-t", "Workflow"), selector("workflow"));
  const lq = el("div", "consil-diagrama lleno swe-liquid"); lq.hidden = true; lq.setAttribute("aria-label", "Liquid Mirror: dos participantes");
  w.append(fw, filaSalida(), lq);
  c.append(ag, wf); return c;
}
function llenar(s, tipo, g, actual) {  // disponibles arriba; el resto, al final y deshabilitado, en su grupo
  const op = (x, ok) => { const o = el("option", null, x.etq); o.value = x.id; o.selected = x.id === actual; o.disabled = !ok; if (!ok) o.title = x.motivo; return o; };
  s.replaceChildren(...g.ok.map((x) => op(x, true)));
  [[g.noInstalado, tipo === "agente" ? "No instalados" : "No disponibles"], [g.incompatible, "Incompatibles con este modelo"]].forEach(([l, t]) => { if (!l.length) return; const og = el("optgroup"); og.label = t; og.append(...l.map((x) => op(x, false))); s.append(og); });
  s.value = actual;
}
function pintarControles() {
  const sel = leerSeleccion();
  document.querySelectorAll(".swe-ctl").forEach((c) => {
    Object.keys(ROTULOS).forEach((k) => {
      const s = c.querySelector(`select[data-swe-ctl="${k}"]`); if (!s) return;
      const [lista, tipo] = LISTAS[k];
      const modelo = k === "agente_responde" ? sel.modelo_responde : k === "agente_tool" ? (sel.workflow === "liquid_mirror" ? "hf/lfm2.5-350m" : sel.modelo_tool) : undefined;
      if (camposFijos(sel.workflow).has(k)) {  // el workflow ya fija este dato (workflows.py): el control no influye, asi que se rotula y no se puede tocar
        const o = el("option", null, "fijo por el workflow"); o.value = sel[k]; o.selected = true; s.replaceChildren(o);
        s.disabled = true; s.dataset.fijo = "1"; s.classList.remove("no-ok"); s.classList.add("fijo"); s.title = ROTULOS[k] + ": fijo por el workflow " + nombreDe(WORKFLOWS_SWE, sel.workflow) + " (este control no influye)";
        return;
      }
      delete s.dataset.fijo; s.classList.remove("fijo");
      llenar(s, tipo, agruparOpciones(CAP, tipo, lista, modelo), sel[k]);
      s.disabled = false;
      const st = estadoOpcion(CAP, tipo, sel[k], modelo); s.classList.toggle("no-ok", !st.ok); s.title = st.ok ? "" : ROTULOS[k] + ": " + st.motivo;
    });
    const b = c.querySelector("[data-swe-agentico]"); if (b) { b.textContent = sel.modo_agentico ? "ON" : "OFF"; b.setAttribute("aria-pressed", String(sel.modo_agentico)); b.classList.toggle("on", sel.modo_agentico); }
    const lq = c.querySelector(".swe-liquid"); lq.hidden = sel.workflow !== "liquid_mirror";
    if (!lq.hidden) {
      const lm = estadoOpcion(CAP, "workflow", "liquid_mirror"); lq.replaceChildren();
      LIQUID_MIRROR.forEach((p, i) => {
        if (i) lq.append(el("span", "dg-flecha", "→ handoff →"));
        lq.append(el("span", "dg-paso", `${p.etiqueta} · ${p.servidor} · ${p.modelo.replace("hf/", "")}` + (lm.ok ? "" : " · NO DISPONIBLE")));
      });
    }
    const ni = c.querySelector(".swe-noinst"); ni.textContent = CAP_LISTA ? lineaNoInstalados(agruparOpciones(CAP, "agente", AGENTES_SWE)) : "Consultando qué agentes están conectados…"; ni.hidden = !ni.textContent;
    c.querySelector('[data-sec="agentes"] .sh-res').textContent = `${nombreDe(AGENTES_SWE, sel.agente_responde)} → ${nombreDe(AGENTES_SWE, sel.agente_tool)} · ${sel.modo_agentico ? "ON" : "OFF"}`;
    c.querySelector('[data-sec="workflow"] .sh-res').textContent = `${nombreDe(WORKFLOWS_SWE, sel.workflow)} · ${SALIDA_CORTA[leerEjecutorTools()]}`;
    const fj = c.querySelector(".swe-fijo"); if (fj) { const f = camposFijos(sel.workflow); fj.hidden = !f.size; fj.textContent = f.size ? `Fijo por el workflow ${nombreDe(WORKFLOWS_SWE, sel.workflow)}: agente y modelo que responden, y modelo de Ejecuta (no influyen; cada paso usa su modelo).` : ""; }
    const e = c.querySelector(".swe-estado");
    e.textContent = requiereHarness(sel)
      ? (CAP_LISTA ? (CAP.harness === "ok" ? "Se envía como tarea al Harness (task_id y checkpoint); lo no instalado no se puede elegir." : CAP.harness === "sin_respuesta" ? "El Harness no responde: ningún agente ni workflow figura conectado." : "El Harness no reporta agentes: ningún agente ni workflow figura conectado.") : "Consultando al Harness qué agentes están conectados…")
      : "Individual con modo agéntico OFF: responde el modelo elegido, como siempre (los agentes no se activan).";
  });
}
async function refrescarCapacidades(forzar) {
  if (forzar) olvidarCapacidades();
  CAP = await cargarCapacidades(api); CAP_LISTA = true; pintarControles();
}
let abierta = null;  // selector (swe-code | swen-code-free) cuya hoja esta abierta
function elegirModelo(id, mid, etiqueta) {  // misma eleccion para la lista de la hoja y el desplegable «Responde»
  S[id] = { model_id: mid, label: etiqueta };
  try { localStorage.setItem(K, JSON.stringify({ ...leer(), [id]: mid })); } catch (e) {}
}
document.addEventListener("change", (e) => {
  const s = e.target.closest && e.target.closest("select[data-swe-ctl]"); if (!s) return;
  guardarSeleccion({ [s.dataset.sweCtl]: s.value });
  if (s.dataset.sweCtl === "modelo_responde" && abierta) {  // el desplegable «Responde» y la lista de modelos de la hoja no pueden contradecirse: lo enviado es lo que dice
    const mid = entradaParaCatalogo(abierta, s.value, S[abierta].model_id);
    if (mid) { elegirModelo(abierta, mid, SWE_LISTAS[abierta].modelos.find((m) => m[0] === mid)[1]); refrescar(); marcarLista(abierta); }
  }
  pintarSalida(); pintarControles();
});
function marcarLista(id) {  // repinta la marca ✓ de la lista de la hoja abierta
  const lista = document.getElementById("sh-" + id + "-lista"); if (!lista) return;
  lista.querySelectorAll("button.fila").forEach((b) => { const on = b.dataset.id === S[id].model_id; b.classList.toggle("on", on); b.setAttribute("aria-pressed", String(on)); b.querySelector(".fila-ck")?.remove(); if (on) b.append(el("span", "fila-ck", "✓")); });
  const r = document.querySelector("#sh-" + id + ' [data-sec="modelo"] .sh-res'); if (r) r.textContent = S[id].label;
}
document.addEventListener("click", (e) => { const b = e.target.closest && e.target.closest("[data-swe-agentico]"); if (b) { guardarSeleccion({ modo_agentico: !leerSeleccion().modo_agentico }); pintarControles(); } });
function hoja(id) {
  const l = SWE_LISTAS[id];
  let s = document.getElementById("sh-" + id);
  if (!s) {
    s = el("div", "sheet swe-hoja"); s.id = "sh-" + id; s.hidden = true; s.setAttribute("role", "dialog"); s.setAttribute("aria-modal", "true"); s.setAttribute("aria-label", l.titulo);
    const caja = el("div", "va-caja");
    const cab = el("div", "row va-head swe-cab");  // pegajosa: titulo + X siempre a la vista
    const x = el("button", "secondary sh-cerrar", "✕"); x.type = "button"; x.setAttribute("aria-label", "Cerrar");
    cab.append(el("strong", null, l.titulo), x);
    const cuerpo = el("div", "swe-cuerpo"), mod = seccion("modelo", "Modelo");
    const lista = el("div", "list"); lista.id = "sh-" + id + "-lista"; mod.querySelector(".sh-sec-cuerpo").append(lista);
    cuerpo.append(mod); caja.append(cab, cuerpo); s.append(caja);
    s.addEventListener("click", (e) => { if (e.target === s || e.target.closest(".sh-cerrar")) { s.hidden = true; abierta = null; } });
    document.addEventListener("keydown", (e) => { if (e.key === "Escape") { s.hidden = true; abierta = null; } });
    document.body.append(s);
  }
  const cuerpo = s.querySelector(".swe-cuerpo"), lista = s.querySelector("#sh-" + id + "-lista"); lista.replaceChildren();
  cuerpo.append(CTL || (CTL = controles()));  // el unico juego de controles pasa a esta hoja (sale de la otra)
  const est = leerSecciones(); s.querySelectorAll("details.sh-sec").forEach((d) => { d.open = est[d.dataset.sec]; });
  s.querySelector('[data-sec="modelo"] .sh-res').textContent = S[id].label;
  l.modelos.forEach(([mid, etiqueta, desc]) => {
    const on = S[id].model_id === mid;
    const b = el("button", "fila" + (on ? " on" : "")); b.type = "button"; b.dataset.id = mid; b.setAttribute("aria-pressed", String(on));
    const nom = el("span", "fila-nom"); nom.append(el("span", null, etiqueta)); if (desc) nom.append(el("span", "fila-desc", desc));
    b.append(nom); if (on) b.append(el("span", "fila-ck", "✓"));
    b.onclick = () => {
      elegirModelo(id, mid, etiqueta);
      const cat = idCatalogo(mid); if (cat) guardarSeleccion({ modelo_responde: cat }); // el modelo que se elige en la lista tambien es MODELO QUE RESPONDE del contrato
      try { window.RIU_SELECTORES && window.RIU_SELECTORES.encender(id); } catch (e) {}  // elegir un modelo enciende ESTE selector: el mensaje sale a este modelo y no a otro ficha activa
      const otra = document.getElementById("sh-modelos"); if (otra) otra.hidden = true;  // la hoja «Selector de modelos» no se queda tapando el composer
      s.hidden = true; abierta = null; refrescar();
    };
    lista.append(b);
  });
  abierta = id; pintarSalida(); pintarControles(); s.hidden = false; cuerpo.scrollTop = 0; refrescarCapacidades(true);
}
document.addEventListener("click", (e) => { const p = e.target.closest("#sel-swe, #sel-swen"); if (p) hoja(PILLS[p.id]); });
