// swe-selectores.js — SELECTOR CENTRAL UNICO de 4 campos, reutilizado como el MISMO nodo en las ventanas SWE CODE, SWEN CODE free, Groq y NVIDIA:
//   RESPONDE [Agente que responde][Modelo que responde] · EJECUTA [Agente que ejecuta][Modelo para tool] · MODO DE TRABAJO · MODO AGENTICO · WORKFLOW.
// La salida de los tool_calls (ejecutor_tools) NO tiene control propio: se deriva de AGENTE QUE EJECUTA (swe-directo.js leerEjecutorTools).
// Una sola funcion construye los controles (controles()), una sola registra sus eventos (delegados en document, una vez), una sola valida (swe-directo.js validarSeleccion),
// una sola consulta disponibilidad (cargarCapacidades) y una sola serializa el contrato (swe-directo.js leerSeleccion/armarTarea). Abrir una ventana MUEVE el nodo; no clona.
// Cada ventana solo aporta lo suyo: su lista de MODELO QUE RESPONDE (swe-directo.js opcionesModeloVentana), su nota de conexion y su titulo.
import { api } from "./api.js";
import { systemPromptOnCache, cargarSystemPromptOn, alternarSystemPromptOn } from "./swe-systemprompt.js";
import { camposFijos, modeloParaLista, modeloGuardado, SWE_LISTAS, MODELOS_SWE, MODELOS_WEB, MODOS_TRABAJO, AGENTES_SWE, WORKFLOWS_SWE, LIQUID_MIRROR, leerSeleccion, guardarSeleccion, requiereHarness, cargarCapacidades, olvidarCapacidades, normalizarCapacidades, estadoOpcion, idCatalogo, agruparOpciones, lineaNoInstalados, lineaSinVerificar, lineaOtros, opcionesModeloVentana, ETIQUETA_ESTADO, VENTANAS_CENTRAL } from "./swe-directo.js";
const K = "riu_swe_modelo";
const leer = () => { try { return JSON.parse(localStorage.getItem(K) || "{}") || {}; } catch (e) { return {}; } };
const refrescar = () => { try { window.RIU_SELECTORES && window.RIU_SELECTORES.refrescar(); } catch (e) {} };
const S = (window.RIU_SWE = window.RIU_SWE || {});
const guardado = leer();
for (const id of Object.keys(SWE_LISTAS)) S[id] = modeloGuardado(id, guardado[id]);  // lo guardado puede ser una entrada de la lista o el id del bridge elegido en el desplegable «Responde»
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
const ID_SELECTOR = { "swe-code": "swe-code", "swen-code-free": "swen-code-free", groq: "groq", nvidia: "nvidia-groq-team" };  // id del panel Selectores (chat-selectores.js)

// ---- Modelo que responde de cada ventana: SWE/SWEN en RIU_SWE; Groq en RIU_GROQ; NVIDIA en la ficha del chat. Siempre en id de catalogo (hf/x, groq/x, nvidia/x) o web-*. ----
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
      const c = chatActual(); if (c) c.ficha = cat;  // mismo id de extremo a extremo, sin elegir otro modelo
    }
  }
  else {
    const web = MODELOS_WEB.find((x) => x[0] === cat), m = web ? { model_id: cat, label: web[1] } : modeloParaLista(w, cat, S[w].model_id);
    if (m) elegirModeloSwe(w, m.model_id, m.label);
  }
  refrescar();
}
// catalogo del Router (fichas-externas.js) -> {id: false | "NO_CONFIGURADO" | "SIN_VERIFICAR"} para Groq/NVIDIA; vacio = sin informacion distinta del Harness
function mapaProveedor(w) {
  const prov = w === "groq" ? "groq" : w === "nvidia" ? "nvidia" : "";
  if (!prov) {
    // SWE CODE = locales; SWEN CODE free = locales + APIs. No depender del estado de agentes del Harness.
    if (w !== "swe-code" && w !== "swen-code-free") return {};
    const datos = [...(window.RIU_LOCAL?.lista || []), ...(w === "swen-code-free" ? [...G().lista, ...(window.RIU_CONFIG?.modelos || []).filter(m => String(m.id).startsWith("nvidia/"))] : [])];
    const o = {};
    for (const m of datos) o[m.id] = m.estado === "NO CONFIGURADO" ? "NO_CONFIGURADO"
      : m.disponible === true ? true : m.disponible === false ? false : "SIN_VERIFICAR";
    return o;
  }
  const lista = prov === "groq" ? G().lista || [] : (window.RIU_CONFIG && window.RIU_CONFIG.modelos || []).filter((m) => String(m.id).startsWith("nvidia/"));
  const aviso = prov === "groq" ? G().aviso || "" : (window.RIU_NVIDIA || {}).aviso || "";
  const o = {};
  if (lista.length) {
    for (const m of lista) o[m.id] = m.estado === "NO CONFIGURADO" ? "NO_CONFIGURADO"
      : m.disponible === false ? false : m.disponible === true ? true : "SIN_VERIFICAR";
    return o;
  }
  const est = /GROQ_API_KEY|NVIDIA_API_KEY|no tiene/i.test(aviso) ? "NO_CONFIGURADO" : "SIN_VERIFICAR";
  for (const m of MODELOS_SWE) if (m[0].startsWith(prov + "/")) o[m[0]] = est;
  return o;
}
function notaVentana(w) {
  if (w === "groq" || w === "nvidia") {
    const prov = w === "groq" ? "Groq" : "NVIDIA", lista = w === "groq" ? G().lista || [] : (window.RIU_CONFIG && window.RIU_CONFIG.modelos || []).filter((m) => String(m.id).startsWith("nvidia/"));
    const aviso = w === "groq" ? G().aviso || "" : (window.RIU_NVIDIA || {}).aviso || "";
    const confirmados = lista.filter(m => m.disponible === true).length;
    const desconocidos = lista.filter(m => m.disponible == null).length;
    return lista.length ? `${prov}: ${confirmados} de ${lista.length} modelos verificados disponibles${desconocidos ? "; " + desconocidos + " sin verificar" : ""}.` : `${prov}: ${aviso || "sin modelos cargados"}.`;
  }
  return w === "swe-code" ? "Modelos locales HF del Harness (el agente se elige abajo)." : "Cuentas web del bridge + modelos del catálogo. El modo de trabajo elige asesoría, revisión, solución…";
}

// ---- Disponibilidad: una sola consulta (cargarCapacidades); «Actualizar» la repite sin recargar el chat ----
let CAP = normalizarCapacidades(null), CAP_LISTA = false, CTL = null, VENTANA = "", ULTIMA = 0;
const ROTULOS = { agente_responde: "AGENTE QUE RESPONDE", modelo_responde: "MODELO QUE RESPONDE", agente_tool: "AGENTE QUE EJECUTA", modelo_tool: "MODELO PARA TOOL", workflow: "WORKFLOW", modo_trabajo: "MODO DE TRABAJO" };
const LISTAS = { agente_responde: [AGENTES_SWE, "agente"], agente_tool: [AGENTES_SWE, "agente"], modelo_responde: [MODELOS_SWE, "modelo"], modelo_tool: [MODELOS_SWE, "modelo"], workflow: [WORKFLOWS_SWE, "workflow"] };
function selector(k) { const s = el("select"); s.dataset.sweCtl = k; s.setAttribute("aria-label", ROTULOS[k]); return s; }
function controles() {
  const c = el("div", "swe-ctl"); c.setAttribute("role", "group"); c.setAttribute("aria-label", "Selector central: agentes, modelos, modo y workflow");
  const nota = el("p", "fila-desc swe-nota");
  const rej = el("div", "swe-rej");
  [["Responde", "agente_responde", "modelo_responde"], ["Ejecuta", "agente_tool", "modelo_tool"]].forEach(([t, a1, m1]) => {
    const caja = (micro, k) => { const w = el("span", "swe-sel"), m = el("span", "swe-micro", micro); m.setAttribute("aria-hidden", "true"); w.append(m, selector(k)); return w; };  // micro-etiqueta visible; el aria-label del select sigue siendo el rotulo completo
    const r = el("div", "swe-rej-fila"); r.append(el("span", "swe-rej-t", t), caja("Agente", a1), caja("Modelo", m1)); rej.append(r);
  });
  const lm = el("div", "swe-rej-fila swe-wf swe-bloque"); lm.append(el("span", "swe-rej-t", "Modo de trabajo"), selector("modo_trabajo"));
  const mo = el("div", "sel-salida swe-bloque"); mo.setAttribute("role", "group"); mo.setAttribute("aria-label", "Modo agéntico");
  const b = el("button", "pill salida-op"); b.type = "button"; b.dataset.sweAgentico = "1"; b.setAttribute("aria-label", "MODO AGÉNTICO");
  mo.append(el("span", "sel-salida-t", "Modo agéntico:"), b);
  // System prompt de la ficha del Router MVP: ON/OFF, aplica a TODOS los modelos (chat Yaiwes y OpenClaw, mismo bridge). Defecto ON.
  const sp = el("div", "sel-salida swe-bloque"); sp.setAttribute("role", "group"); sp.setAttribute("aria-label", "System prompt de la ficha");
  const spB = el("button", "pill salida-op"); spB.type = "button"; spB.dataset.sweSystemprompt = "1"; spB.setAttribute("aria-label", "SYSTEM PROMPT");
  sp.append(el("span", "sel-salida-t", "System prompt:"), spB);
  const fw = el("div", "swe-rej-fila swe-wf swe-bloque"); fw.append(el("span", "swe-rej-t", "Workflow"), selector("workflow"));
  const lq = el("div", "consil-diagrama lleno swe-liquid"); lq.hidden = true; lq.setAttribute("aria-label", "Liquid Mirror: dos participantes");
  const act = el("div", "swe-actualizar"), bt = el("button", "secondary swe-refrescar", "Actualizar disponibilidad"); bt.type = "button"; bt.setAttribute("aria-label", "Actualizar disponibilidad de agentes y modelos"); act.append(bt, el("span", "swe-hora"));
  c.append(nota, rej, lm, mo, sp, fw, lq, el("p", "fila-desc swe-fijo"), el("p", "fila-desc swe-estado-sel"), el("p", "fila-desc swe-noinst"), el("p", "fila-desc swe-estado"), act);
  cargarSystemPromptOn().then(pintarControles);  // estado real del bridge en segundo plano; el boton ya nace pintado en ON (defecto) mientras llega
  return c;
}
function llenar(s, items, actual) {  // disponibles arriba; lo no disponible, al final y deshabilitado, con su estado real; la eleccion actual se queda visible aunque no este disponible
  const op = (x, ok) => { const o = el("option", null, x.etq); o.value = x.id; o.selected = x.id === actual; o.disabled = !ok && !x.elegible; if (!ok) o.title = x.motivo; return o; }; // estado una sola vez: la agrupacion ya lo declara  // SIN VERIFICAR + intentable: se puede elegir con aviso
  s.replaceChildren(...items.ok.map((x) => op(x, true)));
  const grupos = [[items.sinVerificar, "Sin verificar"], [items.noInstalado, "No instalados"], [items.incompatible, "Incompatibles con este modelo"], [items.otros, "No configurados / no disponibles"]];
  grupos.forEach(([l, t]) => { if (!l.length) return; const og = el("optgroup"); og.label = t; og.append(...l.map((x) => op(x, false))); s.append(og); });
  s.value = actual;
}
function agrupar(k, sel, w) {
  const [lista, tipo] = LISTAS[k];
  if (k === "modelo_responde" || k === "modelo_tool") {
    const resp = k === "modelo_responde", ops = opcionesModeloVentana(resp ? w : "swen-code-free", CAP, mapaProveedor(resp ? w : "swen-code-free"), { web: resp && w === "swen-code-free" });
    // un modelo SIN VERIFICAR no bloquea el chat normal: se puede elegir, con su rotulo; lo no disponible va al final, deshabilitado y con su estado real
    const g = { ok: ops.filter((o) => o.ok).map((o) => ({ id: o.id, etq: o.estado === "DISPONIBLE" ? o.nombre : `${o.nombre} — ${ETIQUETA_ESTADO[o.estado]}`, estado: o.estado, motivo: o.motivo, elegible: o.elegible })), noInstalado: [], incompatible: [], sinVerificar: [], otros: ops.filter((o) => !o.ok).map((o) => ({ id: o.id, etq: o.nombre, estado: o.estado, motivo: o.motivo, elegible: o.elegible })) };
    return { g, ops };
  }
  const modelo = k === "agente_responde" ? sel.modelo_responde : k === "agente_tool" ? (sel.workflow === "liquid_mirror" ? "hf/lfm2.5-350m" : sel.modelo_tool) : undefined;
  return { g: agruparOpciones(CAP, tipo, lista, modelo), tipo };
}
function pintarControles() {
  const sel = leerSeleccion();
  document.querySelectorAll(".swe-ctl").forEach((c) => {
    const problemas = [];
    Object.keys(LISTAS).forEach((k) => {
      const s = c.querySelector(`select[data-swe-ctl="${k}"]`); if (!s) return;
      const [lista, tipo] = LISTAS[k];
      if (camposFijos(sel.workflow).has(k)) {  // el workflow ya fija este dato (workflows.py): el control no influye, asi que se rotula y no se puede tocar
        const o = el("option", null, "fijo por el workflow"); o.value = sel[k]; o.selected = true; s.replaceChildren(o);
        s.disabled = true; s.dataset.fijo = "1"; s.classList.remove("no-ok"); s.classList.add("fijo"); s.title = ROTULOS[k] + ": fijo por el workflow " + nombreDe(WORKFLOWS_SWE, sel.workflow) + " (este control no influye)";
        return;
      }
      delete s.dataset.fijo; s.classList.remove("fijo");
      const valor = k === "modelo_responde" ? (modeloVentana(VENTANA) || sel.modelo_responde) : sel[k];
      const { g, ops } = agrupar(k, sel, VENTANA);
      // la eleccion actual se queda SIEMPRE visible (con su estado), aunque no este en la lista de la ventana
      const ya = [...g.ok, ...g.sinVerificar, ...g.noInstalado, ...g.incompatible, ...g.otros].some((x) => x.id === valor);
      if (!ya && valor) { const st = k.startsWith("modelo") ? estadoOpcion(CAP, "modelo", valor) : estadoOpcion(CAP, tipo, valor); g.otros.push({ id: valor, etq: nombreDe(lista, valor) || nombreDe(MODELOS_WEB, valor), estado: st.ok ? "SIN_VERIFICAR" : st.estado, motivo: st.motivo || "no es un modelo de esta ventana" }); }
      llenar(s, g, valor);
      s.disabled = false;
      const st = k.startsWith("modelo") ? (ops || []).find((o) => o.id === valor) || estadoOpcion(CAP, "modelo", valor) : estadoOpcion(CAP, tipo, valor, k === "agente_responde" ? sel.modelo_responde : sel.modelo_tool);
      const malo = !st.ok || st.estado === "SIN_VERIFICAR";
      s.classList.toggle("no-ok", !st.ok); s.title = malo ? ROTULOS[k] + ": " + ETIQUETA_ESTADO[st.estado] + (st.motivo ? " — " + st.motivo : "") : "";
      const importa = k === "modelo_responde" || (k === "modelo_tool" ? sel.modo_agentico : requiereHarness(sel));  // un agente/modelo de tool solo BLOQUEA si hay modo agentico o workflow; igual se muestra su error
      if (!st.ok) problemas.push(ROTULOS[k] + " " + (nombreDe(lista, valor) || nombreDe(MODELOS_WEB, valor)) + ": " + ETIQUETA_ESTADO[st.estado] + (st.motivo ? " — " + String(st.motivo).replace(/\s*\(([^()]*)\)/g, ": $1") : "") + (importa ? "" : " (no bloquea: modo agéntico OFF)"));
    });
    const sm = c.querySelector('select[data-swe-ctl="modo_trabajo"]');
    if (sm) { sm.replaceChildren(...[["", "Sin modo (conversación normal)"], ...MODOS_TRABAJO].map(([v, t]) => { const o = el("option", null, t); o.value = v; return o; })); sm.value = sel.modo_trabajo; sm.title = VENTANA === "groq" || VENTANA === "nvidia" ? "El modo de trabajo se envía en los chats por el bridge (SWE CODE / SWEN CODE free); Groq y NVIDIA por el Router no lo usan todavía." : ""; }
    const b = c.querySelector("[data-swe-agentico]"); if (b) { b.textContent = sel.modo_agentico ? "ON" : "OFF"; b.setAttribute("aria-pressed", String(sel.modo_agentico)); b.classList.toggle("on", sel.modo_agentico); }
    const spB = c.querySelector("[data-swe-systemprompt]"); if (spB) { const on = systemPromptOnCache(); spB.textContent = on ? "ON" : "OFF"; spB.setAttribute("aria-pressed", String(on)); spB.classList.toggle("on", on); }
    const lq = c.querySelector(".swe-liquid"); lq.hidden = sel.workflow !== "liquid_mirror";
    if (!lq.hidden) {
      const lm = estadoOpcion(CAP, "workflow", "liquid_mirror"); lq.replaceChildren();
      LIQUID_MIRROR.forEach((p, i) => {
        if (i) lq.append(el("span", "dg-flecha", "→ handoff →"));
        lq.append(el("span", "dg-paso", `${p.etiqueta} · ${p.servidor} · ${p.modelo.replace("hf/", "")}` + (lm.ok ? "" : " · " + ETIQUETA_ESTADO[lm.estado])));
      });
    }
    c.querySelector(".swe-nota").textContent = notaVentana(VENTANA) + (VENTANA === "groq" || VENTANA === "nvidia" ? " El modo de trabajo solo se aplica en los envíos por el bridge." : "");
    const ni = c.querySelector(".swe-noinst"), ga = agruparOpciones(CAP, "agente", AGENTES_SWE);
    ni.textContent = CAP_LISTA ? [lineaNoInstalados(ga), lineaSinVerificar(ga), lineaOtros(ga)].filter(Boolean).join(" · ") : "Consultando qué agentes están conectados…"; ni.hidden = !ni.textContent;
    const fj = c.querySelector(".swe-fijo"); if (fj) { const f = camposFijos(sel.workflow); fj.hidden = !f.size; fj.textContent = f.size ? `Fijo por el workflow ${nombreDe(WORKFLOWS_SWE, sel.workflow)}: agente y modelo que responden, y modelo de Ejecuta (no influyen; cada paso usa su modelo).` : ""; }
    const es = c.querySelector(".swe-estado-sel"); es.textContent = problemas.join(" · "); es.hidden = !problemas.length;
    const e = c.querySelector(".swe-estado");
    e.textContent = requiereHarness(sel)
      ? (CAP_LISTA ? (CAP.harness === "ok" ? "Se envía como tarea al Harness (task_id y checkpoint); lo no disponible no se puede ejecutar y el envío se bloquea." : "SIN VERIFICAR: el Harness no respondió o no reporta agentes; no se afirma que haya agentes instalados.") : "Consultando al Harness qué agentes están conectados…")
      : "Individual con modo agéntico OFF: responde el modelo elegido, como siempre (los agentes no se activan).";
    const h = c.querySelector(".swe-hora"); if (h) h.textContent = ULTIMA ? "Comprobado " + new Date(ULTIMA).toLocaleTimeString() : "";
  });
}
async function refrescarCapacidades(forzar, conFichas = false) {
  if (forzar) olvidarCapacidades();
  const bt = document.querySelector(".swe-refrescar"); if (bt) bt.disabled = true;
  try { if (conFichas && window.RIU_FICHAS && window.RIU_FICHAS.recargar) await window.RIU_FICHAS.recargar(); } catch (e) {}  // catalogos Groq/NVIDIA del Router, sin recargar el chat
  CAP = await cargarCapacidades(api); CAP_LISTA = true; ULTIMA = Date.now(); pintarControles();
  if (bt) bt.disabled = false;
}

// ---- Eventos: registrados UNA vez (delegados en document); abrir una ventana no vuelve a registrar nada ----
document.addEventListener("click", (e) => {
  const b = e.target.closest && e.target.closest("[data-swe-agentico]"); if (b) { guardarSeleccion({ modo_agentico: !leerSeleccion().modo_agentico }); pintarControles(); return; }
  const spB = e.target.closest && e.target.closest("[data-swe-systemprompt]"); if (spB) { alternarSystemPromptOn().then(pintarControles); return; }
  if (e.target.closest && e.target.closest(".swe-refrescar")) refrescarCapacidades(true, true);
});
document.addEventListener("change", (e) => {
  const s = e.target.closest && e.target.closest("select[data-swe-ctl]"); if (!s) return;
  const k = s.dataset.sweCtl;
  guardarSeleccion({ [k]: s.value });
  if (k === "modelo_responde" && VENTANA) {  // el desplegable ES la lista de modelos de la ventana: lo mostrado es lo que se envia
    fijarModeloVentana(VENTANA, s.value);
    try { window.RIU_SELECTORES && window.RIU_SELECTORES.encender(ID_SELECTOR[VENTANA]); } catch (err) {}  // elegir un modelo enciende ESE selector: el mensaje sale a este modelo y no a otra ficha activa
    const otra = document.getElementById("sh-selectores"); if (otra) otra.hidden = true; debajo = "";
  }
  pintarControles();
});
// el contrato siempre lleva el modelo de la ventana abierta (modelo_tool, agentes y workflow no se tocan)
function sincronizar(w) { const m = modeloVentana(w); if (m) guardarSeleccion({ modelo_responde: m }); }

// ---- Una sola ventana modal activa: abrir una ventana cierra las demas; al cerrar vuelve la de debajo (Selector de modelos) ----
let opener = null, openerId = "", debajo = "";
const enfocables = (s) => [...s.querySelectorAll("button, select, summary, input, textarea, a[href], [tabindex]")].filter((n) => !n.disabled && n.tabIndex >= 0 && n.getClientRects().length > 0);
function cerrarHoja(s) {
  if (s.hidden) return;
  s.hidden = true; VENTANA = "";
  const vuelve = debajo && document.getElementById(debajo); debajo = "";
  if (vuelve) vuelve.hidden = false;
  const o = opener && opener.isConnected ? opener : document.getElementById(openerId);  // el pill puede haberse vuelto a pintar al elegir modelo
  opener = null; if (o && typeof o.focus === "function") o.focus();
}
function iconoX() {
  const NS = "http://www.w3.org/2000/svg", svg = document.createElementNS(NS, "svg"), d = document.createElementNS(NS, "path");
  svg.setAttribute("viewBox", "0 0 24 24"); svg.setAttribute("width", "22"); svg.setAttribute("height", "22"); svg.setAttribute("aria-hidden", "true"); svg.setAttribute("focusable", "false");
  d.setAttribute("d", "M6 6l12 12M18 6L6 18"); d.setAttribute("fill", "none"); d.setAttribute("stroke", "currentColor"); d.setAttribute("stroke-width", "2.4"); d.setAttribute("stroke-linecap", "round");
  svg.append(d); return svg;
}
function hoja(id, desde) {
  const v = VENTANAS[id];
  let s = document.getElementById("sh-" + id);
  if (!s) {
    s = el("div", "sheet swe-hoja"); s.id = "sh-" + id; s.hidden = true; s.setAttribute("role", "dialog"); s.setAttribute("aria-modal", "true"); s.setAttribute("aria-label", v.titulo);
    const caja = el("div", "va-caja");
    const cab = el("div", "row va-head swe-cab");  // pegajosa: titulo + X siempre a la vista
    const x = el("button", "secondary sh-cerrar"); x.type = "button"; x.setAttribute("aria-label", "Cerrar"); x.title = "Cerrar"; x.append(iconoX());  // icono SVG propio: no depende de que la fuente del sistema tenga el glifo ✕
    cab.append(el("strong", null, v.titulo), x);
    const cuerpo = el("div", "swe-cuerpo"); cuerpo.dataset.host = id;
    caja.append(cab, cuerpo); s.append(caja);
    s.addEventListener("click", (e) => { if (e.target === s || e.target.closest(".sh-cerrar")) cerrarHoja(s); });
    document.addEventListener("keydown", (e) => {  // en captura: con la hoja abierta es la de arriba; Escape la cierra a ella sola y el foco vuelve a su boton
      if (s.hidden) return;
      if (e.key === "Escape") { e.stopPropagation(); cerrarHoja(s); return; }
      if (e.key !== "Tab") return;  // trampa de foco simple: Tab / Mays+Tab dan la vuelta dentro de la hoja
      const f = enfocables(s); if (!f.length) return;
      const i = f.indexOf(document.activeElement);
      if (e.shiftKey && i <= 0) { e.preventDefault(); f[f.length - 1].focus(); }
      else if (!e.shiftKey && (i < 0 || i === f.length - 1)) { e.preventDefault(); f[0].focus(); }
    }, true);
    document.body.append(s);
  }
  const abiertas = [...document.querySelectorAll(".sheet:not([hidden])")].filter((x) => x !== s);
  debajo = (abiertas.find((x) => x.id === "sh-selectores") || {}).id || ""; abiertas.forEach((x) => { x.hidden = true; });  // una sola modal activa
  if (!CTL) CTL = controles();
  s.querySelector(".swe-cuerpo").append(CTL);  // el unico juego de controles pasa a esta hoja (sale de la otra): el MISMO nodo
  VENTANA = id; sincronizar(id);
  pintarControles();
  opener = desde || null; openerId = desde && desde.id ? desde.id : "";
  s.hidden = false; s.querySelector(".swe-cuerpo").scrollTop = 0; refrescarCapacidades(true);  // al abrir se vuelve a preguntar al Harness: un "no disponible" viejo no se queda pegado
  const x = s.querySelector(".sh-cerrar"); if (x) x.focus();
}
// capturar: estas 4 pastillas abren SOLO esta ventana (las hojas viejas de Groq y NVIDIA ya no existen: su lista de modelos era el duplicado)
document.addEventListener("click", (e) => { const p = e.target.closest && e.target.closest("#sel-swe, #sel-swen, #sel-groq, #sel-ngt"); if (p) { e.stopImmediatePropagation(); e.preventDefault(); hoja(PILLS[p.id], p); } }, true);
window.addEventListener("riu:fichas", () => { if (VENTANA) { sincronizar(VENTANA); pintarControles(); } });  // llegan los catalogos de Groq/NVIDIA

// Gancho para el resto del frontend (enviar-mensaje.js): estado de la eleccion de una ventana, sin segundo selector
window.RIU_SWE_CENTRAL = {
  ventanas: VENTANAS_CENTRAL,
  get ventana() { return VENTANA; },
  get nodo() { return CTL; },
  modeloVentana,
  // texto del bloqueo si la eleccion de esa ventana NO esta disponible (se queda visible con su error); "" si se puede enviar. Con modo agentico/workflow lo valida enviarTareaSwe.
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
