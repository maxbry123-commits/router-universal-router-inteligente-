// tools-ventana.js — Staff de tools: ventana 🧰 en el chat y bloque en Configuración.
// Recursos LLM enlazables sin programar (Ficha 4 por Harness/HTTP, tool NVIDIA de código, Groq) y agentes del staff (máx. 20):
// listar, añadir, quitar y elegir con un selector qué recurso usa cada agente. La LLM del chat hace lo mismo con las tools
// agente_enlazar / recurso_llm / nvidia_codigo. Backend: puente_chat tools_estado, groq_agentes, agente_enlazar, recurso_probar.
import { accion } from "./api.js";
const el = (t, c, x) => { const e = document.createElement(t); if (c) e.className = c; if (x != null) e.textContent = x; return e; };
const btn = (txt, cls, fn) => { const b = el("button", cls || "secondary", txt); b.type = "button"; if (fn) b.onclick = fn; return b; };
let estado = null;
const cargar = async () => { estado = await accion("tools_estado", { rapido: true }); return estado; };
const CSS = `#ventana-tools .va-caja{overflow:auto;max-height:88vh}.tv-sec{margin:10px 0 4px;font-weight:600}.tv-sub{font-size:12px;opacity:.7;margin:6px 0 2px}
.tv-fila{display:flex;gap:6px;align-items:center;flex-wrap:wrap;padding:6px 8px;border-radius:8px;background:rgba(127,127,127,.08);margin:3px 0}
.tv-fila .tv-n{flex:1 1 140px;min-width:0;overflow:hidden;text-overflow:ellipsis}.tv-fila small{opacity:.65;display:block}
.tv-fila select{max-width:100%;flex:1 1 160px}.tv-res{font-size:12px;white-space:pre-wrap;opacity:.85;width:100%}
.tv-form{display:flex;flex-wrap:wrap;gap:6px}.tv-form input,.tv-form select{flex:1 1 140px;min-width:0}`;

function selectorRecurso(recursos, actual) {
  const s = el("select", "tv-rec");
  const grupos = {};
  recursos.forEach((r) => { (grupos[r.grupo] = grupos[r.grupo] || []).push(r); });
  Object.entries(grupos).forEach(([g, rs]) => { const og = document.createElement("optgroup"); og.label = g; rs.forEach((r) => og.append(new Option(r.nombre + (r.rol ? " · " + r.rol : ""), r.id))); s.append(og); });
  if (actual) s.value = actual;
  return s;
}

async function probar(salida, payload) {
  salida.textContent = "Probando…"; const t0 = performance.now();
  try { const r = await accion("recurso_probar", Object.assign({ mensaje: "Responde en una línea: ¿qué modelo eres?" }, payload)); salida.textContent = (r.ok ? "✅ " : "⚠️ ") + (r.ms / 1000).toFixed(1) + " s · " + String(r.respuesta || "").slice(0, 240); salida.dataset.ok = r.ok ? "1" : "0"; }
  catch (x) { salida.textContent = "⚠️ " + x.message + " (" + ((performance.now() - t0) / 1000).toFixed(1) + " s)"; salida.dataset.ok = "0"; }
}

async function pintarVentana(caja) {
  caja.replaceChildren(el("div", "muted", "Cargando…"));
  let e; try { e = await cargar(); } catch (x) { caja.replaceChildren(el("div", "muted", "Sin conexión con el Router: " + x.message)); return; }
  const recursos = e.recursos || [];
  const nombreRec = (id) => (recursos.find((r) => r.id === id) || {}).nombre || id;
  const guardar = async (lista) => { try { const r = await accion("groq_agentes", { agentes: lista }); if (r.error) { alert(r.error); return; } } catch (x) { alert(x.message); return; } pintarVentana(caja); };
  // 1) agentes del staff: cada uno con su selector de recurso LLM
  const lista = el("div", "list tv-lista");
  e.agentes.forEach((a) => {
    const f = el("div", "tv-fila tv-ag"); f.dataset.agente = a.nombre;
    const n = el("div", "tv-n"); n.append(el("strong", "", a.nombre), el("small", "", "usa: " + (a.recurso ? nombreRec(a.recurso) : "Groq " + a.modelo)));
    const sel = selectorRecurso(recursos, a.recurso || ("groq:" + a.modelo)); sel.title = "Modelo que usa este agente";
    const res = el("div", "tv-res");
    sel.onchange = async () => { res.textContent = "Enlazando…"; try { const r = await accion("agente_enlazar", { nombre: a.nombre, recurso: sel.value }); if (r.error) { res.textContent = "⚠️ " + r.error; return; } pintarVentana(caja); } catch (x) { res.textContent = "⚠️ " + x.message; } };
    f.append(n, sel, btn("Probar", "secondary tv-probar", () => probar(res, { agente: a.nombre })), btn("Quitar", "secondary", () => guardar(e.agentes.filter((x) => x.nombre !== a.nombre))), res);
    lista.append(f);
  });
  const form = el("form", "tv-form");
  const nom = el("input"); nom.placeholder = "nombre del agente"; nom.required = true; nom.id = "tv-nombre";
  const rec = selectorRecurso(recursos, recursos[0] && recursos[0].id); rec.id = "tv-recurso";
  const sis = el("input"); sis.placeholder = "instrucciones (system prompt corto)"; sis.id = "tv-sistema";
  const add = el("button", "action", "Añadir agente"); add.id = "tv-anadir";
  form.append(nom, rec, sis, add);
  form.onsubmit = async (ev) => { ev.preventDefault(); if (e.agentes.length >= (e.max || 20)) { alert("Máximo " + (e.max || 20) + " agentes"); return; }
    try { const r = await accion("agente_enlazar", { nombre: nom.value, recurso: rec.value, sistema: sis.value }); if (r.error) { alert(r.error); return; } } catch (x) { alert(x.message); return; } pintarVentana(caja); };
  // 2) recursos LLM disponibles (staff), agrupados, con Probar
  const recs = el("div", "list tv-recursos");
  let g0 = "";
  recursos.forEach((r) => {
    if (r.grupo !== g0) { g0 = r.grupo; recs.append(el("div", "tv-sub", r.grupo + " · " + r.via)); }
    const f = el("div", "tv-fila tv-recurso"); f.dataset.recurso = r.id;
    const n = el("div", "tv-n"); n.append(el("span", "", r.nombre), el("small", "", r.rol || r.id));
    const res = el("div", "tv-res");
    f.append(n, btn("Probar", "secondary tv-probar", () => probar(res, { recurso: r.id })), res); recs.append(f);
  });
  const fichas = (e.fichas || []).map((f) => f.nombre).join(" · ");
  caja.replaceChildren(
    el("div", "tv-sec", "Agentes del staff (" + e.agentes.length + "/" + (e.max || 20) + ")"),
    el("div", "muted", "Elige en el selector qué modelo usa cada agente. La LLM del chat lo hace con agente_enlazar y lo usa con groq_agente."),
    lista, form,
    el("div", "tv-sec", "Recursos LLM enlazables"), recs,
    el("div", "tv-sec", "Ficha NVIDIA del chat"), el("div", "muted", fichas || "—"),
    el("div", "tv-sec", "Tools de la LLM del chat"), el("div", "muted", e.tools.join(", ")));
}

function instalarChat() {
  const bar = document.querySelector("#composer .composer-bar");
  if (!bar || document.querySelector("#btn-tools")) return;
  if (!document.querySelector("#tv-css")) { const st = el("style"); st.id = "tv-css"; st.textContent = CSS; document.head.append(st); }
  const b = el("button", "secondary", "🧰"); b.type = "button"; b.id = "btn-tools"; b.title = "Staff de tools y agentes"; b.setAttribute("aria-label", "Tools y agentes");
  const s = el("div", "sheet"); s.id = "ventana-tools"; s.hidden = true;
  const c = el("div", "va-caja"), h = el("div", "row va-head"), x = el("button", "secondary", "✕"), cuerpo = el("div", "list"); cuerpo.id = "tv-cuerpo";
  x.type = "button"; x.onclick = () => { s.hidden = true; };
  s.onclick = (ev) => { if (ev.target === s) s.hidden = true; };
  h.append(el("strong", "", "🧰 Staff de tools"), x); c.append(h, cuerpo); s.append(c); document.body.append(s);
  b.onclick = () => { s.hidden = false; pintarVentana(cuerpo); };
  const env = bar.querySelector(".action"); bar.insertBefore(b, env || null);
}

async function instalarConfig() {
  const temas = document.querySelector("#ap-temas");
  if (!temas || document.querySelector("#cfg-tools")) return;
  const sec = el("section", "ap-sec"); sec.id = "cfg-tools";
  sec.append(el("h2", "", "Fichas, recursos LLM, tools y agentes"));
  const cuerpo = el("div", "list"); sec.append(cuerpo);
  temas.closest("section").before(sec);
  cuerpo.append(el("div", "muted", "Cargando…"));
  try {
    const e = await cargar();
    const k = e.claves || {};
    const porGrupo = {}; (e.recursos || []).forEach((r) => { porGrupo[r.grupo] = (porGrupo[r.grupo] || 0) + 1; });
    cuerpo.replaceChildren(
      ...e.fichas.map((f) => el("div", "item", "Ficha NVIDIA · " + f.nombre + " · " + f.modelo + " · espera " + f.timeout_s + " s")),
      el("div", "item", "Recursos LLM: " + Object.entries(porGrupo).map(([g, n]) => g + " " + n).join(" · ")),
      el("div", "item", "Tools: " + e.tools.join(", ")),
      el("div", "item", "Agentes del staff: " + e.agentes.length + "/" + (e.max || 20) + " — " + e.agentes.map((a) => a.nombre + (a.recurso ? " → " + a.recurso : "")).join(", ")),
      el("div", "item", "Claves · NVIDIA chat: " + (k.nvidia_chat || 0) + " · NVIDIA código: " + (k.nvidia_codigo || 0) + " · Groq: " + (k.groq || 0)));
  } catch (x) { cuerpo.replaceChildren(el("div", "muted", "Sin conexión con el Router: " + x.message)); }
}

const revisar = () => { try { instalarChat(); instalarConfig(); } catch (e) { console.warn("tools-ventana", e); } };
new MutationObserver(revisar).observe(document.body, { childList: true, subtree: true });
revisar();
