// swe-selectores.js — SELECTOR CENTRAL UNICO de 4 campos, reutilizado como el MISMO nodo en las ventanas SWE CODE, SWEN CODE free, Groq y NVIDIA:
//   RESPONDE [Agente que responde][Modelo que responde] · EJECUTA [Agente que ejecuta][Modelo para tool] · MODO DE TRABAJO · MODO AGENTICO · WORKFLOW.
// La salida de los tool_calls (ejecutor_tools) NO tiene control propio: se deriva de AGENTE QUE EJECUTA (swe-directo.js leerEjecutorTools).
// Una sola funcion construye los controles (controles()), una sola registra sus eventos (delegados en document, una vez), una sola valida (swe-directo.js validarSeleccion),
// una sola consulta disponibilidad (cargarCapacidades) y una sola serializa el contrato (swe-directo.js leerSeleccion/armarTarea). Abrir una ventana MUEVE el nodo; no clona.
// Cada ventana solo aporta lo suyo: su lista de MODELO QUE RESPONDE (swe-directo.js opcionesModeloVentana), su nota de conexion y su titulo.
import { api, plugin } from "./api.js";
import { systemPromptOnCache, cargarSystemPromptOn, alternarSystemPromptOn } from "./swe-systemprompt.js";
import { camposFijos, modeloParaLista, modeloGuardado, SWE_LISTAS, MODELOS_SWE, MODELOS_WEB, MODOS_TRABAJO, AGENTES_SWE, WORKFLOWS_SWE, LIQUID_MIRROR, leerSeleccion, guardarSeleccion, requiereHarness, cargarCapacidades, olvidarCapacidades, normalizarCapacidades, estadoOpcion, idCatalogo, agruparOpciones, lineaNoInstalados, lineaSinVerificar, lineaOtros, opcionesModeloVentana, ETIQUETA_ESTADO, VENTANAS_CENTRAL } from "./swe-directo.js";
const K = "riu_swe_modelo";
const leer = () => { try { return JSON.parse(localStorage.getItem(K) || "{}") || {}; } catch (e) { return {}; } };
const refrescar = () => { try { window.RIU_SELECTORES && window.RIU_SELECTORES.refrescar(); } catch (e) {} };
const S = (window.RIU_SWE = window.RIU_SWE || {});
const guardado = leer();
for (const id of Object.keys(SWE_LISTAS)) S[id] = modeloGuardado(id, guardado[id]);
const nombreDe = (lista, id) => (lista.find((x) => x[0] === id) || [id, id])[1];
const el = (tag, cls, txt) => { const n = document.createElement(tag); if (cls) n.className = cls; if (txt != null) n.textContent = txt; return n; };

// ---- Las 4 ventanas: lo unico propio de cada una (titulo, pastilla que la abre, nota) ----
const VENTANAS = {
  "swe-code": { titulo: SWE_LISTAS["swe-code"].titulo, pill: "sel-swe" },
  "swen-code-free": { titulo: SWE_LISTAS["swen-code-free"].titulo, pill: "sel-swen" },
  groq: { titulo: "Groq · selector", pill: "sel-groq" },
  nvidia: { titulo: "NVIDIA · selector", pill: "sel-ngt" },
};
const PILLS = Object.fromEntries(Object.entries(VENTANAS).map(([id, v]) => [v.pill, id]));
const ID_SELECTOR = { "swe-code": "swe-code", "swen-code-free": "swen-code-free", groq: "groq", nvidia: "nvidia-groq-team" };

const G = () => (window.RIU_GROQ = window.RIU_GROQ || { lista: [], modelo: "", aviso: "" });
const chatActual = () => { try { return window.RIU_CHAT.chat(); } catch (e) { return null; } };
function modeloVentana(w) {
  if (w === "groq") return G().modelo || "";
  if (w === "nvidia") { const f = (window.RIU_NVIDIA || {}).modelo || (chatActual() || {}).ficha || ""; return f.startsWith("nvidia/") ? f : ""; }
  const m = (S[w] || {}).model_id || ""; return idCatalogo(m) || (MODELOS_WEB.some((x) => x[0] === m) ? m : "");
}
function elegirModeloSwe(w, mid, etiqueta) {
  S[w] = { model_id: mid, label: etiqueta };
  try { localStorage.setItem(K, JSON.stringify({ ...leer(), [w]: mid })); } catch (e) {}
}
function fijarModeloVentana(w, cat) {
  if (w === "groq") { if (window.RIU_GROQ && window.RIU_GROQ.elegir) window.RIU_GROQ.elegir(cat); }
  else if (w === "nvidia") {
    const seleccionado = (window.RIU_CONFIG?.modelos || []).find(m => m.id === cat && m.disponible !== false);
    if (seleccionado) {
      window.RIU_NVIDIA = { ...(window.RIU_NVIDIA || {}), modelo: cat };
      try { localStorage.setItem("riu_nvidia_modelo", cat); } catch (e) {}
      const c = chatActual(); if (c) c.ficha = cat;
    }
  }
  else elegirModeloSwe(w, cat, (SWE_LISTAS[w]?.modelos || []).find((x) => x[0] === cat)?.[1] || cat);
}

const ROTULOS = { modelo_responde: "Modelo que responde", modelo_tool: "Modelo para tool", agente_tool: "Agente que ejecuta", modo_trabajo: "Modo de trabajo", workflow: "Workflow" };
function selector(k) { const s = el("select"); s.dataset.sweCtl = k; s.setAttribute("aria-label", ROTULOS[k]); return s; }
function controles() {
  const c = el("div", "swe-ctl"); c.setAttribute("role", "group"); c.setAttribute("aria-label", "Selector central: agentes, modelos, modo y workflow");
  const st = el("div", "swe-reparacion"); st.id = "swe-reparacion"; st.style.fontSize = "12px"; st.style.marginTop = "4px"; st.setAttribute("role", "status"); c.append(st);
  const nota = el("p", "fila-desc swe-nota");
  const rej = el("div", "swe-rej");
  [["Responde", [["Modelo", "modelo_responde"]]],
   ["Ejecuta", [["Agente", "agente_tool"], ["Modelo para tool", "modelo_tool"]]]].forEach(([t, campos]) => {
    const caja = (micro, k) => { const w = el("span", "swe-sel"), m = el("span", "swe-micro", micro); m.setAttribute("aria-hidden", "true"); w.append(m, selector(k)); return w; };
    const r = el("div", "swe-rej-fila"); r.dataset.sweFila = t.toLowerCase();
    r.append(el("span", "swe-rej-t", t), ...campos.map(([micro, k]) => caja(micro, k))); rej.append(r);
  });
  const lm = el("div", "swe-rej-fila swe-wf swe-bloque"); lm.append(el("span", "swe-rej-t", "Modo de trabajo"), selector("modo_trabajo"));
  const mo = el("div", "sel-salida swe-bloque"); mo.setAttribute("role", "group"); mo.setAttribute("aria-label", "Modo agéntico");
  const b = el("button", "pill salida-op"); b.type = "button"; b.dataset.sweAgentico = "1"; b.setAttribute("aria-label", "MODO AGÉNTICO");
  mo.append(el("span", "sel-salida-t", "Modo agéntico:"), b);
  const sp = el("div", "sel-salida swe-bloque"); sp.setAttribute("role", "group"); sp.setAttribute("aria-label", "System prompt de la ficha");
  const spB = el("button", "pill salida-op"); spB.type = "button"; spB.dataset.sweSystemprompt = "1"; spB.setAttribute("aria-label", "SYSTEM PROMPT");
  sp.append(el("span", "sel-salida-t", "System prompt:"), spB);
  const fw = el("div", "swe-rej-fila swe-wf swe-bloque"); fw.append(el("span", "swe-rej-t", "Workflow"), selector("workflow"));
  const lq = el("div", "consil-diagrama lleno swe-liquid"); lq.hidden = true; lq.setAttribute("aria-label", "Liquid Mirror: dos participantes");
  c.append(nota, rej, lm, mo, sp, fw, lq);
  return c;
}

function llenar(s, items, actual) {
  s.replaceChildren();
  const ok = items.filter((x) => x.ok), mal = items.filter((x) => !x.ok);
  const g = (lista, cls) => { const og = el("optgroup"); og.label = cls; lista.forEach((it) => { const o = el("option", "", it.nombre + (it.estado && it.estado !== "OK" ? " — " + ETIQUETA_ESTADO[it.estado] : "")); o.value = it.id; if (!it.ok) o.disabled = true; og.append(o); }); if (og.children.length) s.append(og); };
  g(ok, "Disponibles"); g(mal, "No disponibles");
  if (actual) s.value = actual;
}
function agrupar(k, sel, w) {
  const items = opcionesModeloVentana(w, CAP, mapaProveedor(w), { web: w === "swen-code-free" });
  const actual = k === "modelo_responde" ? modeloVentana(w) : sel[k];
  return { items, actual };
}

let CTL, VENTANA = "", CAP = normalizarCapacidades(null), opener = null, openerId = "";
function pintarControles() {
  if (!CTL) return;
  const sel = leerSeleccion();
  const w = VENTANA;
  CTL.querySelectorAll("[data-swe-ctl]").forEach((s) => {
    const k = s.dataset.sweCtl;
    if (k === "modelo_responde" || k === "modelo_tool") {
      const { items, actual } = agrupar(k, sel, w);
      llenar(s, items, actual);
    } else if (k === "agente_tool") llenar(s, AGENTES_SWE.map(([id, n]) => ({ id, nombre: n, ok: true })), sel.agente_tool);
    else if (k === "modo_trabajo") llenar(s, [["", "(ninguno)"], ...MODOS_TRABAJO].map(([id, n]) => ({ id, nombre: n, ok: true })), sel.modo_trabajo);
    else if (k === "workflow") llenar(s, WORKFLOWS_SWE.map(([id, n]) => ({ id, nombre: n, ok: true })), sel.workflow);
    const fijo = camposFijos(sel.workflow).has(k);
    s.disabled = fijo;
    s.title = fijo ? "fijo por el workflow" : "";
  });
  const b = CTL.querySelector("[data-swe-agentico]");
  if (b) { b.textContent = sel.modo_agentico ? "ON" : "OFF"; b.classList.toggle("on", sel.modo_agentico); }
  const spB = CTL.querySelector("[data-swe-systemprompt]");
  if (spB) { const on = systemPromptOnCache(); spB.textContent = on ? "ON" : "OFF"; spB.classList.toggle("on", on); }
  const lq = CTL.querySelector(".swe-liquid");
  if (lq) { lq.hidden = sel.workflow !== "liquid_mirror"; if (!lq.hidden) lq.textContent = LIQUID_MIRROR.map((p) => p.etiqueta).join(" → "); }
}

async function refrescarCapacidades(forzar, conFichas = false) {
  try { if (conFichas && window.RIU_FICHAS && window.RIU_FICHAS.recargar) await window.RIU_FICHAS.recargar(); } catch (e) {}
  CAP = await cargarCapacidades(api, { forzar });
  pintarControles();
}

function sincronizar(w) { const m = modeloVentana(w); if (m) guardarSeleccion({ modelo_responde: m }); }

function cerrarHoja(s) { s.hidden = true; VENTANA = ""; if (opener) opener.focus(); opener = null; }
function iconoX() { return '<svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" aria-hidden="true"><path d="M6 6l12 12M18 6L6 18"/></svg>'; }
function hoja(id, desde) {
  const s = document.getElementById("swe-hoja") || (() => { const h = el("div", "swe-hoja"); h.id = "swe-hoja"; h.hidden = true; const c = el("div", "swe-cuerpo"); const x = el("button", "sh-cerrar"); x.type = "button"; x.innerHTML = iconoX(); x.setAttribute("aria-label", "Cerrar"); x.addEventListener("click", () => cerrarHoja(h)); h.append(c, x); document.body.append(h); return h; })();
  if (!CTL) CTL = controles();
  s.querySelector(".swe-cuerpo").append(CTL);
  VENTANA = id; sincronizar(id);
  pintarControles();
  opener = desde || null; openerId = desde && desde.id ? desde.id : "";
  s.hidden = false; s.querySelector(".swe-cuerpo").scrollTop = 0; refrescarCapacidades(true);
  const x = s.querySelector(".sh-cerrar"); if (x) x.focus();
}
document.addEventListener("click", (e) => {
  const p = e.target.closest && e.target.closest("#sel-swe, #sel-swen, #sel-groq, #sel-ngt");
  if (!p) return;
  const activo = window.RIU_SELECTORES?.activo;
  const actual = { "swe-code": "swe-code", "swen-code-free": "swen-code-free", groq: "groq", "nvidia-groq-team": "nvidia" }[activo];
  const destino = PILLS[p.id];
  if (!destino) return;
  e.stopImmediatePropagation();
  e.preventDefault();
  hoja(destino, p);
}, true);
window.addEventListener("riu:fichas", () => { if (VENTANA) { sincronizar(VENTANA); pintarControles(); } });

window.RIU_SWE_CENTRAL = {
  ventanas: VENTANAS_CENTRAL,
  get ventana() { return VENTANA; },
  get nodo() { return CTL; },
  modeloVentana,
  bloqueo(w) {
    if (!VENTANAS[w] || requiereHarness(leerSeleccion())) return "";
    const m = modeloVentana(w) || leerSeleccion().modelo_responde;
    const o = opcionesModeloVentana(w, CAP, mapaProveedor(w), { web: w === "swen-code-free" }).find((x) => x.id === m);
    if (!o || o.ok) return "";
    return `${VENTANAS[w].titulo.split(" · ")[0]}: MODELO QUE RESPONDE ${o.nombre} — ${ETIQUETA_ESTADO[o.estado]}${o.motivo ? " (" + o.motivo + ")" : ""}`;
  },
  refrescar: (forzar = true) => refrescarCapacidades(forzar, true),
  montar(host, w) { if (!CTL) CTL = controles(); host.append(CTL); VENTANA = w; sincronizar(w); pintarControles(); },
};

function mapaProveedor(w) {
  if (w === "groq") return "groq";
  if (w === "nvidia") return "nvidia";
  return "hf";
}
function notaVentana(w) {
  if (w === "swen-code-free") return "cuentas web Qwen/DeepSeek + modos por el bridge";
  if (w === "swe-code") return "modelos locales de HF por el router propio de SWE CODE";
  return "";
}
