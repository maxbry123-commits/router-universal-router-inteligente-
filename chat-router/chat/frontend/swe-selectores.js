// swe-selectores.js — selectores SWE CODE y SWEN CODE free del panel «Selector de modelos» (misma mecanica que el selector Groq):
// la pastilla abre una hoja con sus modelos; el elegido queda en window.RIU_SWE[<selector>] = {model_id, label}.
// Al encender el selector, enviar-mensaje.js manda por swe-directo.js (router propio: el bridge), sin pasar por el Router MVP.
import { api } from "./api.js";
import { SWE_LISTAS, EJECUTORES_TOOLS, ETIQUETA_SALIDA, leerEjecutorTools, guardarEjecutorTools, MODELOS_SWE, AGENTES_SWE, WORKFLOWS_SWE, LIQUID_MIRROR, leerSeleccion, guardarSeleccion, requiereHarness, cargarCapacidades, olvidarCapacidades, normalizarCapacidades, estadoOpcion, idCatalogo } from "./swe-directo.js";
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
function pintarSalida() {
  const v = leerEjecutorTools();
  document.querySelectorAll("[data-salida]").forEach((b) => { const on = b.dataset.salida === v; b.setAttribute("aria-pressed", String(on)); b.classList.toggle("on", on); });
}
function filaSalida() {
  const f = document.createElement("div"); f.className = "sel-salida sh-salida"; f.setAttribute("role", "group"); f.setAttribute("aria-label", "Salida de las tools");
  EJECUTORES_TOOLS.forEach((e) => { const b = document.createElement("button"); b.type = "button"; b.className = "pill salida-op"; b.dataset.salida = e; b.textContent = ETIQUETA_SALIDA[e]; f.append(b); });
  return f;
}
document.addEventListener("click", (e) => { const b = e.target.closest("[data-salida]"); if (b) { guardarEjecutorTools(b.dataset.salida); pintarSalida(); pintarControles(); } });
pintarSalida();
// el panel (panel-chat.html) se inyecta despues de cargar este modulo: al aparecer sus botones se repinta el estado guardado
try { const ob = new MutationObserver((ms) => { if (ms.some((m) => [...m.addedNodes].some((n) => n.nodeType === 1 && (n.matches("[data-salida]") || n.querySelector("[data-salida]"))))) pintarSalida(); }); ob.observe(document.documentElement, { childList: true, subtree: true }); } catch (e) {}
// Agente/modelo/workflow (contrato TareaSWE): mismos controles en las hojas de SWE CODE y SWEN CODE free; el estado se guarda en swe-directo.js.
// Lo que el Harness no reporta conectado se muestra NO DISPONIBLE (opcion deshabilitada), nunca como funcional.
let CAP = normalizarCapacidades(null), CAP_LISTA = false;
const CAMPOS_SEL = [["modelo_responde", "MODELO QUE RESPONDE", MODELOS_SWE, "modelo"], ["modelo_tool", "MODELO PARA TOOL", MODELOS_SWE, "modelo"], ["agente_responde", "AGENTE QUE RESPONDE", AGENTES_SWE, "agente"], ["agente_tool", "AGENTE QUE EJECUTA", AGENTES_SWE, "agente"], ["workflow", "WORKFLOW", WORKFLOWS_SWE, "workflow"]];
function controles() {
  const c = document.createElement("div"); c.className = "swe-ctl"; c.setAttribute("role", "group"); c.setAttribute("aria-label", "Agentes, modelos y workflow de SWE");
  const f = document.createElement("div"); f.className = "row fields";
  CAMPOS_SEL.forEach(([k, etq]) => { const l = document.createElement("label"); l.textContent = etq; const sel = document.createElement("select"); sel.dataset.sweCtl = k; sel.setAttribute("aria-label", etq); l.append(sel); f.append(l); });
  const ag = document.createElement("div"); ag.className = "sel-salida"; ag.setAttribute("role", "group"); ag.setAttribute("aria-label", "Modo agéntico");
  const t = document.createElement("span"); t.className = "sel-salida-t"; t.textContent = "MODO AGÉNTICO:";
  const b = document.createElement("button"); b.type = "button"; b.className = "pill salida-op"; b.dataset.sweAgentico = "1"; ag.append(t, b);
  const lq = document.createElement("div"); lq.className = "consil-diagrama lleno swe-liquid"; lq.hidden = true; lq.setAttribute("aria-label", "Liquid Mirror: dos participantes");
  const est = document.createElement("div"); est.className = "fila-desc swe-estado";
  c.append(f, ag, lq, est); return c;
}
function opcion(valor, texto, st, elegido) {
  const o = document.createElement("option"); o.value = valor; o.selected = elegido;
  o.textContent = st.ok ? texto : texto + " — " + (/^incompatible/.test(st.motivo) ? "incompatible" : "NO DISPONIBLE");
  o.disabled = !st.ok; if (!st.ok) o.title = st.motivo; return o;
}
function pintarControles() {
  const sel = leerSeleccion();
  document.querySelectorAll(".swe-ctl").forEach((c) => {
    CAMPOS_SEL.forEach(([k, , lista, tipo]) => {
      const s = c.querySelector(`select[data-swe-ctl="${k}"]`); if (!s) return;
      const modelo = k === "agente_responde" ? sel.modelo_responde : k === "agente_tool" ? (sel.workflow === "liquid_mirror" ? "hf/lfm2.5-350m" : sel.modelo_tool) : undefined;
      s.replaceChildren(...lista.map(([v, etq, desc]) => opcion(v, etq + (tipo === "modelo" && desc ? " · " + desc : ""), estadoOpcion(CAP, tipo, v, modelo), sel[k] === v)));
      s.value = sel[k]; s.disabled = k === "modelo_tool" && sel.workflow === "liquid_mirror";  // Liquid Mirror: el tool es siempre LIQUID 2 — EJECUTOR
    });
    const b = c.querySelector("[data-swe-agentico]"); if (b) { b.textContent = "MODO AGÉNTICO: " + (sel.modo_agentico ? "ON" : "OFF"); b.setAttribute("aria-pressed", String(sel.modo_agentico)); b.classList.toggle("on", sel.modo_agentico); }
    const lq = c.querySelector(".swe-liquid"); lq.hidden = sel.workflow !== "liquid_mirror";
    if (!lq.hidden) {
      const lm = estadoOpcion(CAP, "workflow", "liquid_mirror"); lq.replaceChildren();
      LIQUID_MIRROR.forEach((p, i) => {
        if (i) { const fl = document.createElement("span"); fl.className = "dg-flecha"; fl.textContent = "→ handoff →"; lq.append(fl); }
        const d = document.createElement("span"); d.className = "dg-paso"; d.textContent = `${p.etiqueta} · ${p.servidor} · ${p.modelo.replace("hf/", "")}` + (lm.ok ? "" : " · NO DISPONIBLE"); lq.append(d);
      });
    }
    const e = c.querySelector(".swe-estado");
    e.textContent = requiereHarness(sel)
      ? (CAP_LISTA ? (CAP.harness === "ok" ? "Se envía como tarea al Harness (task_id y checkpoint); lo marcado NO DISPONIBLE no tiene adaptador conectado." : "El Harness no responde: ningún agente ni workflow figura conectado.") : "Consultando al Harness qué agentes están conectados…")
      : "Individual con modo agéntico OFF: responde el modelo elegido abajo, como siempre (los agentes no se activan).";
  });
}
async function refrescarCapacidades(forzar) {
  if (forzar) olvidarCapacidades();
  CAP = await cargarCapacidades(api); CAP_LISTA = true; pintarControles();
}
document.addEventListener("change", (e) => { const s = e.target.closest && e.target.closest("select[data-swe-ctl]"); if (s) { guardarSeleccion({ [s.dataset.sweCtl]: s.value }); pintarSalida(); pintarControles(); } });
document.addEventListener("click", (e) => { const b = e.target.closest && e.target.closest("[data-swe-agentico]"); if (b) { guardarSeleccion({ modo_agentico: !leerSeleccion().modo_agentico }); pintarControles(); } });
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
    caja.append(cab, filaSalida(), controles(), lista); s.append(caja);
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
      const cat = idCatalogo(mid); if (cat) guardarSeleccion({ modelo_responde: cat }); // el modelo que se elige en la lista tambien es MODELO QUE RESPONDE del contrato
      try { localStorage.setItem(K, JSON.stringify({ ...leer(), [id]: mid })); } catch (e) {}
      s.hidden = true; refrescar();
    };
    lista.append(b);
  });
  pintarSalida(); pintarControles(); s.hidden = false; refrescarCapacidades(true);
}
document.addEventListener("click", (e) => { const p = e.target.closest("#sel-swe, #sel-swen"); if (p) hoja(PILLS[p.id]); });
