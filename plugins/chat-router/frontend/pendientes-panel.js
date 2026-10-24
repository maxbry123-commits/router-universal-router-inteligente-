// pendientes-panel.js — t175u: panel 📋 Pendientes del bloc de notas. Guarda cada input block VERBATIM 1:1 (inmutable, sha256),
// la LLM (Ficha 4 por el Harness del chat: puente_chat notas/pendientes) lo organiza en un DSL DAG con 5 estados,
// y Antonio edita aquí el prompt JSON / system prompt que usa el modelo organizador (se aplica en la siguiente organización).
import { accion } from "./api.js";
const el = (t, c, x) => { const e = document.createElement(t); if (c) e.className = c; if (x != null) e.textContent = x; return e; };
const btn = (txt, fn) => { const b = el("button", "secondary", txt); b.type = "button"; b.onclick = fn; return b; };
const CSS = `#ventana-pendientes .va-caja{overflow:auto;max-height:88vh}.pp-ta{width:100%;box-sizing:border-box;font-family:monospace;font-size:12px}
.pp-sec{margin:10px 0 4px;font-weight:600}.pp-n{padding:6px 8px;border-radius:8px;background:rgba(127,127,127,.08);margin:3px 0}
.pp-n small{opacity:.7;display:block;white-space:pre-wrap}.pp-est{font-size:12px;opacity:.85;white-space:pre-wrap}`;

// Checklist (agregar, marcar, ordenar): vive en el servidor; el modelo la consulta/actualiza con la herramienta «pendientes» si está encendida
function checklist() {
  const caja = el("div", "list"), est = el("div", "pp-est"), nuevo = el("input"), fila = el("div", "row");
  nuevo.placeholder = "Nuevo pendiente"; nuevo.setAttribute("aria-label", "Nuevo pendiente"); nuevo.style.flex = "1 1 160px"; nuevo.style.minWidth = "0";
  const pintarLista = (ps) => {
    caja.replaceChildren(...(ps.length ? ps : [{ vacio: true }]).map((p, i) => {
      if (p.vacio) return el("div", "muted", "Sin pendientes");
      const f = el("div", "pp-n row"), cb = el("input"), t = el("span", "", p.texto);
      cb.type = "checkbox"; cb.checked = p.hecho; cb.setAttribute("aria-label", "Hecho: " + p.texto); cb.onchange = () => llamar({ accion: "marcar", id: p.id, hecho: cb.checked });
      t.style.flex = "1 1 120px"; t.style.overflowWrap = "anywhere"; if (p.hecho) t.style.textDecoration = "line-through";
      const mover = (d) => { const ids = ps.map((x) => x.id); ids.splice(i + d, 0, ids.splice(i, 1)[0]); llamar({ accion: "ordenar", ids }); };
      f.append(cb, t);
      if (i > 0) f.append(btn("↑", () => mover(-1)));
      if (i < ps.length - 1) f.append(btn("↓", () => mover(1)));
      f.append(btn("✕", () => llamar({ accion: "quitar", id: p.id })));
      return f;
    }));
  };
  const llamar = async (c) => { try { const r = await accion("checklist", c); est.textContent = r.persistente === false ? "⚠️ No se guardará tras reiniciar (almacenamiento HF no disponible)" : ""; pintarLista(r.pendientes || []); return true; } catch (x) { est.textContent = "⚠️ " + x.message; return false; } };
  const agregar = btn("＋ Añadir", async () => { if (nuevo.value.trim() && await llamar({ accion: "agregar", texto: nuevo.value })) nuevo.value = ""; });
  nuevo.onkeydown = (ev) => { if (ev.key === "Enter") { ev.preventDefault(); agregar.click(); } };
  const org = btn("🧠 Organizar con IA", async () => { org.disabled = true; est.textContent = "Organizando…"; if (await llamar({ accion: "organizar" })) est.textContent = ""; org.disabled = false; });
  org.title = "Un modelo (qwen3.7 por defecto) ordena los pendientes por prioridad; no crea ni borra ninguno";
  fila.append(nuevo, agregar, org);
  llamar({});
  const todo = el("div", "list"); todo.append(fila, caja, est); return todo;
}

function pintarDag(caja, v) {
  caja.replaceChildren();
  const dag = (v && v.dag) || null;
  if (!dag || !Array.isArray(dag.nodos)) { caja.append(el("div", "muted", v && v.error ? "⚠️ " + v.error + " " + (v.detalle || "") : "Sin vista organizada todavía.")); return; }
  caja.append(el("div", "muted", "Modelo: " + (v.modelo || "—") + " · inputs: " + (v.inputs || 0) + " · " + (v.fecha || "")));
  const deps = {}; (dag.aristas || []).forEach((a) => { (deps[a.a] = deps[a.a] || []).push(a.de); });
  const grupos = {}; dag.nodos.forEach((n) => { (grupos[n.grupo || "General"] = grupos[n.grupo || "General"] || []).push(n); });
  Object.entries(grupos).forEach(([g, ns]) => {
    caja.append(el("div", "pp-sec", g));
    ns.forEach((n) => { const d = el("div", "pp-n"); d.append(el("div", "", (n.estado || "") + " · " + (n.id || "") + " · " + (n.titulo || "")));
      d.append(el("small", "", (n.cita ? "«" + n.cita + "»" : "") + (n.fuente ? "  [" + [].concat(n.fuente).join(", ") + "]" : "") + (deps[n.id] ? "  ← depende de " + deps[n.id].join(", ") : "") + (n.falta ? "  ⚪ falta: " + n.falta : ""))); caja.append(d); });
  });
}

let organizador = null;  // el organizador con LLM (notas + DAG) no existe en el Router MVP: se prueba una vez
async function pintar(cuerpo) {
  cuerpo.replaceChildren(el("div", "muted", "Cargando…"));
  if (organizador === null) { try { await accion("notas", { accion: "listar" }); organizador = true; } catch (x) { organizador = false; } }
  if (!organizador) { cuerpo.replaceChildren(el("div", "pp-sec", "Checklist"), checklist(), el("div", "muted", "El organizador con LLM (bloc de notas y DAG) no está disponible en este Router.")); return; }
  const inTa = el("textarea", "pp-ta"), prTa = el("textarea", "pp-ta"), est = el("div", "pp-est"), dag = el("div", "list"), lista = el("div", "muted");
  inTa.rows = 5; inTa.placeholder = "Pega aquí el input block tal cual (se guarda verbatim 1:1, no se edita después)"; prTa.rows = 10;
  const avisar = (t) => { est.textContent = t; };
  const cargarInputs = async () => { try { const r = await accion("notas", { accion: "listar" }); lista.textContent = (r.inputs || []).length + " input blocks guardados · " + (r.inputs || []).slice(-5).map((x) => x.id + " (" + x.chars + " c)").join(" · "); } catch (x) { lista.textContent = "⚠️ " + x.message; } };
  const cargarVista = async () => { try { pintarDag(dag, await accion("pendientes", { accion: "vista" })); } catch (x) { dag.replaceChildren(el("div", "muted", "⚠️ " + x.message)); } };
  const guardarIn = btn("Guardar input verbatim", async () => { if (!inTa.value.trim()) return; try { const r = await accion("notas", { accion: "guardar", texto: inTa.value }); avisar(r.error ? "⚠️ " + r.error : (r.repetido ? "Ya estaba guardado" : "Guardado " + r.id) + " · sha256 " + String(r.sha256 || "").slice(0, 12)); if (!r.error) inTa.value = ""; cargarInputs(); } catch (x) { avisar("⚠️ " + x.message); } });
  const guardarPr = btn("Guardar prompt JSON", async () => { try { const r = await accion("pendientes", { accion: "prompt_guardar", prompt: prTa.value }); avisar(r.error ? "⚠️ " + r.error : "Prompt guardado: se usa en la próxima organización"); } catch (x) { avisar("⚠️ " + x.message); } });
  const organizar = btn("🧠 Organizar con la LLM", async () => {
    avisar("Organizando… (Ficha 4 por el Harness)"); const t0 = performance.now();
    try { const r = await accion("pendientes", { accion: "organizar" }); const id = r.trabajo; if (!id) { pintarDag(dag, r); avisar(""); return; }
      for (let i = 0; i < 90; i++) { await new Promise((s) => setTimeout(s, 2000)); const t = await accion("pendientes", { accion: "trabajo", trabajo: id });
        if (t.estado === "procesando") { avisar("Organizando… " + ((performance.now() - t0) / 1000).toFixed(0) + " s"); continue; }
        pintarDag(dag, t.resultado || t); avisar((t.resultado && !t.resultado.error ? "✅ " : "⚠️ ") + ((performance.now() - t0) / 1000).toFixed(1) + " s"); return; }
      avisar("⚠️ Tiempo agotado; la vista se actualiza cuando termine");
    } catch (x) { avisar("⚠️ " + x.message); } });
  try { const p = await accion("pendientes", { accion: "prompt_leer" }); prTa.value = JSON.stringify(p.prompt || {}, null, 2); } catch (x) { prTa.value = ""; }
  cuerpo.replaceChildren(el("div", "pp-sec", "0) Checklist"), checklist(), el("div", "pp-sec", "1) Input block verbatim"), inTa, guardarIn, lista,
    el("div", "pp-sec", "2) Prompt JSON / system prompt del organizador (editable)"), prTa, guardarPr,
    el("div", "pp-sec", "3) Pendientes organizados (DSL DAG)"), organizar, est, dag);
  cargarInputs(); cargarVista();
}

function instalar() {
  const bar = document.querySelector("#composer .composer-bar");
  if (!bar || document.querySelector("#btn-pendientes")) return;
  if (!document.querySelector("#pp-css")) { const st = el("style"); st.id = "pp-css"; st.textContent = CSS; document.head.append(st); }
  const b = el("button", "secondary", "📋"); b.type = "button"; b.id = "btn-pendientes"; b.title = "Pendientes y bloc de notas"; b.setAttribute("aria-label", "Pendientes y bloc de notas");
  const s = el("div", "sheet"); s.id = "ventana-pendientes"; s.hidden = true;
  const c = el("div", "va-caja"), h = el("div", "row va-head"), x = el("button", "secondary", "✕"), cuerpo = el("div", "list");
  x.type = "button"; x.onclick = () => { s.hidden = true; }; s.onclick = (ev) => { if (ev.target === s) s.hidden = true; };
  h.append(el("strong", "", "Pendientes"), x); c.append(h, cuerpo); s.append(c); document.body.append(s);
  b.onclick = () => { s.hidden = false; pintar(cuerpo); };
  const env = bar.querySelector(".action"); bar.insertBefore(b, env || null);
}
const revisar = () => { try { instalar(); } catch (e) { console.warn("pendientes-panel", e); } };
new MutationObserver(revisar).observe(document.body, { childList: true, subtree: true });
revisar();
