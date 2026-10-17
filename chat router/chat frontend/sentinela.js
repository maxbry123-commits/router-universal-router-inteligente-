// sentinela.js — Constitución sentinela (contrato verificable), system prompt (simple, sin validación) y «Anclar archivo real».
// Lógica + secciones de la ventana Constitución (el system prompt tiene su propia ventana: ventana-system-prompt.js). El backend (fichas_qwen/sentinela_contrato.py) valida la salida y corrige con 1 reintento.
import { el, boton } from "./ventanas-comun.js";
const K_SP = "riu_system_prompts_v1", K_AR = "riu_ancla_real_v1", K_CON = "riu_constitucion_v1";
const leerJ = (k, d) => { try { return Object.assign(d, JSON.parse(localStorage.getItem(k) || "null") || {}); } catch (e) { return d; } };
const guardarJ = (k, v) => { try { localStorage.setItem(k, JSON.stringify(v)); } catch (e) {} };
export const dameSP = () => { const v = leerJ(K_SP, { lista: [], activo: null }); if (!Array.isArray(v.lista)) v.lista = []; return v; };
export const dameAR = () => { const v = leerJ(K_AR, { on: false, archivos: [] }); if (!Array.isArray(v.archivos)) v.archivos = []; return v; };
const dameC = () => leerJ(K_CON, { encendida: false, texto: "" });
export const PLANTILLA = "Responde en español y sigue el sistema de diseño YAIWES.\nTERMINA CON: SENTINELA7\nPROHIBIDO: lorem ipsum\nMAX_LINEAS: 40\n# Otras reglas verificables: DEBE: <texto> · EMPIEZA CON: <texto> · FORMATO: json · ESQUEMA: {json schema} · CODIGO: python · MAX_CARACTERES: 4000";
export function datosSentinela() {  // lo que viaja con cada mensaje (solo lo encendido)
  const out = {}, c = dameC();
  if (c.encendida) out.sentinela = { on: true, contrato: String(c.texto || "").slice(0, 12000) };
  const sp = dameSP(), a = sp.lista.find((x) => x.id === sp.activo);
  if (a && String(a.texto || "").trim()) out.system_prompt = { nombre: a.nombre, texto: String(a.texto).slice(0, 6000) };
  const ar = dameAR();
  if (ar.on && ar.archivos.length) out.ancla_real = { on: true, archivos: ar.archivos.slice(0, 8) };
  return out;
}
export function textoSentinela(s) {  // línea visible en el chat bajo la respuesta
  if (!s) return "";
  const p = [];
  if (s.on) {
    const e = s.estado || "SIN_VALIDAR";
    p.push(e === "PASO" ? "📜✅ Constitución: pasó el contrato (" + (s.reglas_verificables || 0) + " reglas)" :
      e === "CORREGIDA" ? "📜🛠️ Constitución: salida corregida (" + (s.violaciones || []).join("; ") + ") · " + (s.via === "arreglo_determinista" ? "arreglo sin LLM" : "juez " + (s.ms_juez || 0) + " ms") :
      e === "NO_CUMPLE" ? "📜⚠️ Constitución: NO cumple tras 1 reintento (" + (s.violaciones_finales || s.violaciones || []).join("; ") + ")" : "📜 Constitución: " + e);
  }
  if (s.system_prompt) p.push("🧾 System prompt: " + s.system_prompt);
  (s.archivos || []).forEach((a) => p.push("📎 " + a.nombre + " viajó (" + a.chars + " car.)" + (a.sintaxis ? " · " + (a.sintaxis_ok ? "✅ " : "❌ ") + a.sintaxis : "") + (a.ejecucion && a.ejecucion.ejecutado ? " · ejecutado rc=" + a.ejecucion.rc + (a.ejecucion.salida ? " → " + String(a.ejecucion.salida).trim().slice(0, 80) : "") : "")));
  return p.join("\n");
}
window.RIU_SENTINELA_TXT = textoSentinela;
export async function llamarSentinela(accion, payload) {  // Componente -> Harness (puente_chat) -> HTTP -> fichas_qwen -> grafo (Graphiti · Graphify · SQLite)
  const f = window.RIU_ACCION; if (typeof f !== "function") throw new Error("Harness no disponible todavía");
  const r = await f(accion, payload); if (r && r.error) throw new Error(r.error + (r.detalle ? ": " + r.detalle : "")); return r || {};
}
function payloadGrafo() {
  const c = dameC(), sp = dameSP(), a = sp.lista.find((x) => x.id === sp.activo), ar = dameAR();
  return { sesion: "director", contrato: c.encendida ? String(c.texto || "") : "", system_prompt: a ? { nombre: a.nombre, texto: a.texto } : "", archivos: ar.on ? ar.archivos : [] };
}
let tSync = 0;
export function sincronizarGrafo(tell, ya) {  // lo anclado se escribe en el grafo (SQLite-grafo + Graphiti en 2º plano + Graphify para código)
  clearTimeout(tSync);
  const go = async () => { const p = payloadGrafo(); if (!p.contrato && !p.system_prompt && !p.archivos.length) return null;
    try { const r = await llamarSentinela("sentinela_anclar", p); window.__riuSentinelaGrafo = r; window.dispatchEvent(new CustomEvent("riu:sentinela-grafo", { detail: r })); return r; } catch (e) { if (tell) tell("Grafo: " + e.message); return null; } };
  if (ya) return go();
  tSync = setTimeout(go, 1200); return null;
}
const resumenGrafo = (r) => !r ? "Aún no anclado al grafo." : "Grafo SQLite: " + r.graph_sqlite + " · Graphiti: " + r.graphiti + " · Graphify: " + (typeof r.graphify === "object" ? r.graphify.status + (r.graphify.nodos ? " (" + r.graphify.nodos + " nodos)" : "") : r.graphify) + " · " + (r.escritos || []).length + " anclas";
export function seccionSystemPrompt(cuerpo, tell, alCambiar) {  // ventana aparte: simple, NO funciona como la Constitución (sin validación)
  const box = el("div", "sent-sp"); box.dataset.sent = "sp";
  const pintarSP = () => {
    box.replaceChildren(); const sp = dameSP();
    box.append(el("div", "vn-t", "System prompt (simple, sin validación)"), el("div", "vn-estado", "Se añade al inicio del mensaje del modelo. No se verifica ni corrige: eso solo lo hace la Constitución."));
    const sel = el("select", "vn-in"); sel.setAttribute("aria-label", "System prompt activo"); sel.dataset.sent = "sp-sel";
    const o0 = el("option", "", "Ninguno"); o0.value = ""; sel.append(o0);
    sp.lista.forEach((x) => { const o = el("option", "", x.nombre); o.value = x.id; sel.append(o); }); sel.value = sp.activo || "";
    const nom = el("input", "vn-in"); nom.placeholder = "Nombre del system prompt"; nom.setAttribute("aria-label", "Nombre del system prompt"); nom.dataset.sent = "sp-nombre";
    const ta = el("textarea", "vn-ta"); ta.placeholder = "Escribe aquí el system prompt…"; ta.setAttribute("aria-label", "Texto del system prompt"); ta.dataset.sent = "sp-texto";
    const act = sp.lista.find((x) => x.id === sp.activo); if (act) { nom.value = act.nombre; ta.value = act.texto; }
    sel.addEventListener("change", () => { const v = dameSP(); v.activo = sel.value || null; guardarJ(K_SP, v); pintarSP(); if (alCambiar) alCambiar(); sincronizarGrafo(tell); tell(sel.value ? "System prompt activo: " + sel.selectedOptions[0].textContent : "Sin system prompt"); });
    const g = boton("Guardar", "mini", () => { const v = dameSP(), n = nom.value.trim() || "Prompt " + (v.lista.length + 1), t = ta.value.slice(0, 6000); if (!t.trim()) { tell("Escribe el system prompt"); return; }
      let x = v.lista.find((y) => y.id === v.activo && y.nombre === n) || v.lista.find((y) => y.nombre === n); if (!x) { x = { id: "sp-" + Date.now().toString(36), nombre: n, texto: t }; v.lista.push(x); } else x.texto = t;
      v.activo = x.id; guardarJ(K_SP, v); pintarSP(); if (alCambiar) alCambiar(); sincronizarGrafo(tell); tell("System prompt guardado y activo: " + n); }); g.dataset.sent = "sp-guardar";
    const nv = boton("Nuevo", "mini", () => { const v = dameSP(); v.activo = null; guardarJ(K_SP, v); pintarSP(); if (alCambiar) alCambiar(); });
    const br = boton("Borrar", "mini", () => { const v = dameSP(); if (!v.activo) return; v.lista = v.lista.filter((y) => y.id !== v.activo); v.activo = null; guardarJ(K_SP, v); pintarSP(); if (alCambiar) alCambiar(); tell("System prompt borrado"); });
    const fila = el("div", "vn-fila"); fila.append(g, nv, br);
    box.append(sel, nom, ta, fila);
  };
  pintarSP();
  cuerpo.append(box);
  return { pintar: pintarSP };
}
export function montarSecciones(cuerpo, tell) {
  // 1) Contrato verificable (el mismo texto de «Mi constitución sentinela»)
  const ayuda = el("div", "vn-estado", "Contrato: cada línea CLAVE: valor se verifica en la salida (TERMINA CON, EMPIEZA CON, DEBE, PROHIBIDO, FORMATO: json, ESQUEMA, CODIGO: python, MAX_LINEAS, MAX_CARACTERES; también «termina con PALABRA» / «empieza con PALABRA»). El resto de líneas viaja como regla. Si falla: 1 corrección automática.");
  const pl = boton("Insertar plantilla de contrato", "mini", () => { const ta = cuerpo.querySelector("textarea[aria-label='Mi constitución']"); if (!ta) return; ta.value = (ta.value.trim() ? ta.value.trim() + "\n" : "") + PLANTILLA; ta.dispatchEvent(new Event("input", { bubbles: true })); sincronizarGrafo(tell); tell("Plantilla insertada"); });
  pl.dataset.sent = "plantilla";
  const ta0 = cuerpo.querySelector("textarea[aria-label='Mi constitución']"); if (ta0) { ta0.after(ayuda, pl); ta0.addEventListener("input", () => sincronizarGrafo()); } else cuerpo.append(ayuda, pl);
  // 2) System prompt: ventana aparte (ventana-system-prompt.js); aquí solo el acceso
  const irSP = boton("System prompt: ventana aparte", "mini", () => { const b = document.querySelector("#pill-system-prompt"); if (b) b.click(); else tell("La ventana del system prompt no está disponible"); }); irSP.dataset.sent = "sp-abrir";
  // 3) Anclar archivo real: el contenido viaja en el contexto; el código se valida (y se ejecuta en sandbox si el Router lo permite)
  const ab = el("div", "sent-ar"); ab.dataset.sent = "ar";
  const pintarAR = () => {
    ab.replaceChildren(); const ar = dameAR();
    const t = boton("Anclar archivo real: " + (ar.on ? "ON" : "OFF"), "toggle" + (ar.on ? " on" : ""), () => { const v = dameAR(); v.on = !v.on; guardarJ(K_AR, v); pintarAR(); sincronizarGrafo(tell); tell("Anclar archivo real: " + (v.on ? "ON · el contenido viaja con cada mensaje" : "OFF")); });
    t.setAttribute("aria-pressed", String(!!ar.on)); t.dataset.sent = "ar-toggle";
    const fi = el("input"); fi.type = "file"; fi.multiple = true; fi.dataset.sent = "ar-file"; fi.setAttribute("aria-label", "Archivos a anclar");
    fi.addEventListener("change", async () => { const v = dameAR();
      for (const f of [...fi.files].slice(0, 8)) { if (f.size > 200000) { tell(f.name + ": demasiado grande (máx. 200 KB)"); continue; } const txt = (await f.text()).slice(0, 20000); v.archivos = v.archivos.filter((x) => x.nombre !== f.name); v.archivos.push({ nombre: f.name, contenido: txt }); }
      v.archivos = v.archivos.slice(-8); guardarJ(K_AR, v); fi.value = ""; pintarAR(); validar(); sincronizarGrafo(tell); });
    ab.append(el("div", "vn-t", "Anclar archivo real"), el("div", "vn-estado", "ON: el contenido completo de cada archivo viaja con el mensaje. El código se valida (Python, JavaScript, JSON) y su resultado va al modelo."), t, fi);
    const lst = el("div", "sent-lista"); lst.dataset.sent = "ar-lista";
    ar.archivos.forEach((a) => { const f = el("div", "vn-fila"); const n = el("span", "vn-estado", "📎 " + a.nombre + " · " + String(a.contenido || "").length + " car." + (a._val ? " · " + a._val : "")); n.dataset.archivo = a.nombre;
      f.append(n, boton("Quitar", "mini", () => { const v = dameAR(); v.archivos = v.archivos.filter((x) => x.nombre !== a.nombre); guardarJ(K_AR, v); pintarAR(); sincronizarGrafo(tell); })); lst.append(f); });
    ab.append(lst);
  };
  async function validar() {
    const ar = dameAR(); if (!ar.archivos.length) return;
    try { const r = await llamarSentinela("sentinela_validar", { archivos: ar.archivos.map((a) => ({ nombre: a.nombre, contenido: a.contenido })) });
      const v = dameAR(); (r.archivos || []).forEach((x) => { const a = v.archivos.find((y) => y.nombre === x.nombre); if (a) a._val = (x.sintaxis ? (x.sintaxis_ok ? "✅ " : "❌ ") + x.sintaxis : x.lenguaje) + (x.ejecucion && x.ejecucion.ejecutado ? " · rc=" + x.ejecucion.rc : ""); });
      guardarJ(K_AR, v); pintarAR(); } catch (e) { tell("Validación: " + e.message); }
  }
  pintarAR();
  // 4) Grafo: Graphiti + Graphify + grafo SQLite (consultable)
  const gb = el("div", "sent-grafo"); gb.dataset.sent = "grafo";
  const est = el("div", "vn-estado", resumenGrafo(window.__riuSentinelaGrafo)); est.dataset.sent = "grafo-estado";
  const pre = el("pre", "con-pre"); pre.hidden = true; pre.dataset.sent = "grafo-res";
  gb.append(el("div", "vn-t", "Grafo (Graphiti · Graphify)"), est,
    boton("Anclar al grafo ahora", "mini", async () => { est.textContent = "Anclando…"; const r = await sincronizarGrafo(tell, true); est.textContent = resumenGrafo(r); }),
    boton("Consultar el grafo", "mini", async () => { try { const r = await llamarSentinela("sentinela_grafo", { sesion: "director", consulta: "" }); pre.hidden = false;
      const g = Array.isArray(r.graph_sqlite) ? r.graph_sqlite : [], gf = Array.isArray(r.graphify) ? r.graphify : [];
      pre.textContent = "Grafo SQLite: " + g.length + " nodos\n" + g.slice(0, 6).map((x) => "· " + (x.key || x.id || "") + " " + JSON.stringify(x.data || x).slice(0, 90)).join("\n") +
        "\nGraphiti: " + (Array.isArray(r.graphiti) ? r.graphiti.length + " resultados" : r.graphiti) + " · escrituras " + JSON.stringify(r.graphiti_escrituras || {}) +
        "\nGraphify: " + (Array.isArray(r.graphify) ? gf.length + " nodos\n" + gf.slice(0, 8).map((x) => "· " + x.label + " (" + x.file + ")").join("\n") : r.graphify); } catch (e) { tell("Grafo: " + e.message); } }), pre);
  window.addEventListener("riu:sentinela-grafo", (e) => { if (est.isConnected) est.textContent = resumenGrafo(e.detail); });
  cuerpo.append(irSP, ab, gb);
}
