// orquestador.js — "Grok Bot mejorado": ventana orquestador de agentes dentro del chat.
// Cada agente es un icono de app; al tocarlo abre su seccion de chat (copia anclada al chat principal, hilo aislado).
// Backend: plugin orquestador (listar/crear/borrar/mirror/enviar/estado/aprobar/subir/archivos/chat_crear); LLM por el harness puente_chat.
import { accion } from "./api.js";
const el = (t, c, x) => { const e = document.createElement(t); if (c) e.className = c; if (x != null) e.textContent = x; return e; };
const btn = (txt, cls, fn, id) => { const b = el("button", cls || "secondary", txt); b.type = "button"; if (id) b.id = id; b.onclick = fn; return b; };
const ESTADO_TXT = { activo: "Activo", trabajando: "Trabajando", bloqueado: "Bloqueado", aprobacion: "Necesita aprobación", terminado: "Terminado", error: "Error" };
const fmt = (ms) => Math.floor(ms / 1000) + " s " + String(ms % 1000).padStart(3, "0") + " ms";
let MODELOS = [], AGENTES = [], SEL = null, cuerpo = null, timer = null;

async function orq(acc, payload) {
  let base = ""; try { base = localStorage.getItem("riu_orq_base") || ""; } catch (e) {}
  if (!base) { // mismo camino que el chat: harnessUrl de api.js con el plugin orquestador
    await accion("status", {}).catch(() => {});
    base = (window.RIU_CONFIG?.harnessUrl || "").replace(/\/plugins\/puente_chat\/call\/?$/, "");
  }
  const h = { "Content-Type": "application/json" }; const pw = sessionStorage.getItem("riu_clave"); if (pw) h["X-API-Key"] = pw;
  const ac = new AbortController(); const t = setTimeout(() => ac.abort(), acc === "chat_crear" ? 95000 : 20000);
  try {
    const r = await fetch(base.replace(/\/+$/, "") + "/plugins/orquestador/call/" + acc, { method: "POST", headers: h, body: JSON.stringify(payload || {}), signal: ac.signal });
    const env = await r.json().catch(() => ({}));
    if (!r.ok || env.status !== "ok") throw new Error(env.reason || env.detail || ("HTTP " + r.status));
    return env.result || {};
  } finally { clearTimeout(t); }
}
const sesionChat = () => sessionStorage.getItem("riu_sesion") || "web-general";
const selModelo = (val, id) => { const s = el("select"); if (id) s.id = id; MODELOS.forEach((m) => s.append(new Option(m.nombre, m.id))); if (val) s.value = val; return s; };

function leyenda() {
  const d = el("div", "orq-leyenda");
  Object.entries(ESTADO_TXT).forEach(([k, v]) => { const s = el("span"); s.append(el("i", "orq-sem " + k), document.createTextNode(v)); d.append(s); });
  return d;
}

function grilla() {
  const g = el("div", "orq-grid"); g.id = "orq-grid";
  AGENTES.forEach((a) => {
    const b = el("button", "orq-app" + (SEL === a.id ? " sel" : "")); b.type = "button"; b.dataset.id = a.id; b.title = a.nombre + " · " + ESTADO_TXT[a.estado];
    const i = el("span", "orq-ico", a.icono || "🤖"); const s = el("i", "orq-sem " + a.estado); s.dataset.estado = a.estado;
    b.append(i, s, el("small", "", a.nombre)); b.onclick = () => abrir(a.id); g.append(b);
  });
  const add = el("button", "orq-app orq-add"); add.type = "button"; add.id = "orq-nuevo"; add.append(el("span", "orq-ico", "+"), el("small", "", "Agente"));
  add.onclick = () => { SEL = "nuevo"; pintar(); }; g.append(add);
  return g;
}

function formNuevo() {
  const f = el("div", "orq-sec"); f.id = "orq-form-nuevo";
  const nom = el("input"); nom.placeholder = "Nombre del agente"; nom.id = "orq-n-nombre";
  const sis = el("textarea"); sis.rows = 2; sis.placeholder = "Instrucciones / system del agente"; sis.id = "orq-n-sistema";
  const mod = selModelo("ficha-qwen38flash", "orq-n-modelo");
  const crear = btn("Crear", "action", async () => { crear.disabled = true; try { const r = await orq("crear", { nombre: nom.value, sistema: sis.value, modelo: mod.value, chat_sesion: sesionChat() }); if (r.error) throw new Error(r.error); SEL = r.agente.id; await refrescar(); } catch (x) { alert(x.message); crear.disabled = false; } }, "orq-n-crear");
  const ped = el("input"); ped.placeholder = "Pídele a la LLM del chat que cree un agente…"; ped.id = "orq-llm-pedido";
  const llm = btn("🧠 Crear con LLM", "secondary", async () => { llm.disabled = true; llm.textContent = "🧠 pensando…"; try { const r = await orq("chat_crear", { pedido: ped.value, chat_sesion: sesionChat() }); if (r.error) throw new Error(r.error + " " + (r.detalle || "")); SEL = r.agente.id; await refrescar(); } catch (x) { alert(x.message); } llm.disabled = false; llm.textContent = "🧠 Crear con LLM"; }, "orq-llm-crear");
  const mirSel = el("select"); mirSel.id = "orq-mirror-de"; mirSel.append(new Option("Mirror del chat principal", "chat")); AGENTES.forEach((a) => mirSel.append(new Option("Mirror de " + a.nombre, a.id)));
  const mir = btn("🪞 Añadir mirror", "secondary", () => mirror(mirSel.value), "orq-mirror-crear");
  const r1 = el("div", "orq-row"); r1.append(ped, llm);
  const r2 = el("div", "orq-row"); r2.append(mirSel, mir);
  f.append(el("strong", "", "Nuevo agente"), nom, sis, el("div", "muted", "Modelo (ficha 4)"), mod, crear,
    el("strong", "", "La LLM del chat lo crea (tool crear_agente)"), r1, el("strong", "", "Mirror (copia que trabaja en paralelo)"), r2);
  return f;
}

async function mirror(de) {
  const p = { de, chat_sesion: sesionChat() };
  if (de === "chat") p.mensajes = [...document.querySelectorAll("#messages .msg, #messages .message")].slice(-12).map((m) => ({ role: /user|usuario/.test(m.className) ? "user" : "assistant", content: (m.innerText || "").slice(0, 3000) })).filter((m) => m.content);
  const r = await orq("mirror", p); if (r.error) { alert(r.error); return; } SEL = r.agente.id; await refrescar();
}

function seccion(a) {
  const s = el("div", "orq-sec"); s.id = "orq-sec"; s.dataset.id = a.id;
  const h = el("div", "orq-head");
  const sem = el("i", "orq-sem " + a.estado); sem.style.position = "static"; sem.id = "orq-sem";
  const mod = selModelo(a.modelo, "orq-modelo"); mod.title = "Modelo de la ficha 4 que usa este agente";
  mod.onchange = async () => { const r = await orq("configurar", { id: a.id, modelo: mod.value }); if (r.error) alert(r.error); refrescar(); };
  h.append(el("span", "", a.icono), el("strong", "", a.nombre), sem, el("span", "orq-badge", ESTADO_TXT[a.estado]), mod);
  const info = el("div", "muted", "Hace: " + (a.sistema || "agente general").slice(0, 140) + " · memoria " + a.memoria_id + " · " + (a.archivos || []).length + " archivos · creado por " + a.creado_por + (a.origen ? " · mirror de " + a.origen : "") + (a.latencia_ms ? " · última respuesta " + fmt(a.latencia_ms) : ""));
  info.id = "orq-info";
  const st = el("div", "orq-stream"); st.id = "orq-stream"; (a.stream || []).slice(-4).forEach((l) => st.append(el("div", "", l)));
  const hilo = el("div", "orq-hilo"); hilo.id = "orq-hilo";
  (a.mensajes || []).forEach((m) => { const d = el("div", "orq-msg " + m.role, m.content); if (m.ms) d.append(el("em", "", fmt(m.ms))); hilo.append(d); });
  const inp = el("input"); inp.placeholder = "Habla con " + a.nombre + "…"; inp.id = "orq-input";
  const enviar = async () => { const t = inp.value.trim(); if (!t) return; inp.value = ""; const r = await orq("enviar", { id: a.id, mensaje: t }); if (r.error) alert(r.error); await refrescar(); };
  inp.onkeydown = (e) => { if (e.key === "Enter") enviar(); };
  const plus = el("div", "orq-plus"); plus.hidden = true; plus.id = "orq-plus";
  const file = el("input"); file.type = "file"; file.id = "orq-file";
  file.onchange = async () => { const f = file.files[0]; if (!f) return; const b64 = await new Promise((ok) => { const r = new FileReader(); r.onload = () => ok(String(r.result).split(",")[1] || ""); r.readAsDataURL(f); }); const r = await orq("subir", { id: a.id, nombre: f.name, datos_b64: b64 }); if (r.error) alert(r.error); await refrescar(); };
  const ins = el("input"); ins.placeholder = "Instrucción extra para este agente"; ins.id = "orq-ins";
  plus.append(el("strong", "", "Añadir archivo o instrucción"), file, el("div", "orq-row"));
  plus.lastChild.append(ins, btn("Añadir", "secondary", async () => { if (!ins.value.trim()) return; await orq("subir", { id: a.id, instruccion: ins.value }); await refrescar(); }, "orq-ins-ok"));
  const hablar = btn("🎙", "secondary", () => { const SR = window.SpeechRecognition || window.webkitSpeechRecognition; if (!SR) { inp.focus(); return; } const r = new SR(); r.lang = "es-CO"; r.onresult = (e) => { inp.value = e.results[0][0].transcript; enviar(); }; r.start(); }, "orq-hablar");
  hablar.title = "Hablar con el agente que ejecuta la tarea";
  const fila = el("div", "orq-row"); fila.append(btn("+", "secondary", () => { plus.hidden = !plus.hidden; }, "orq-mas"), inp, hablar, btn("Enviar", "action", enviar, "orq-enviar"));
  const acc = el("div", "orq-row");
  if (a.estado === "aprobacion") acc.append(btn("✅ Aprobar", "action", async () => { await orq("aprobar", { id: a.id }); refrescar(); }, "orq-aprobar"));
  acc.append(btn("🪞 Mirror", "secondary", () => mirror(a.id), "orq-mirror"), btn("🗑 Borrar", "secondary", async () => { if (!confirm("¿Borrar " + a.nombre + " y su sandbox?")) return; await orq("borrar", { id: a.id }); SEL = null; refrescar(); }, "orq-borrar"));
  if ((a.archivos || []).length) acc.append(el("span", "muted", "📎 " + a.archivos.join(", ")));
  s.append(h, info, el("div", "muted", "Actividad"), st, hilo, plus, fila, acc);
  setTimeout(() => { hilo.scrollTop = hilo.scrollHeight; }, 0);
  return s;
}

async function pintar(full) {
  if (!cuerpo) return;
  let det = null;
  if (SEL && SEL !== "nuevo") { try { det = (await orq("estado", { id: SEL })).agente; } catch (x) { det = null; } if (det) AGENTES = AGENTES.map((a) => (a.id === det.id ? det : a)); }
  const foco = document.activeElement?.id, val = document.getElementById("orq-input")?.value, plusAbierto = document.getElementById("orq-plus")?.hidden === false;
  cuerpo.replaceChildren(grilla(), leyenda(), SEL === "nuevo" || !AGENTES.length ? formNuevo() : det ? seccion(det) : el("div", "muted", "Toca un agente para abrir su ventana."));
  if (val) document.getElementById("orq-input").value = val; if (plusAbierto && document.getElementById("orq-plus")) document.getElementById("orq-plus").hidden = false;
  if (foco && document.getElementById(foco) && foco !== "orq-file") document.getElementById(foco).focus();
  clearTimeout(timer);
  if (!document.getElementById("ventana-orq").hidden && AGENTES.some((a) => a.estado === "trabajando")) timer = setTimeout(refrescar, 1200);
}
async function abrir(id) { SEL = id; await pintar(); }
async function refrescar() {
  try { if (!MODELOS.length) MODELOS = (await orq("modelos", {})).modelos || []; AGENTES = (await orq("listar", {})).agentes || []; }
  catch (x) { cuerpo.replaceChildren(el("div", "muted", "Sin conexión con el orquestador: " + x.message)); return; }
  if (SEL && SEL !== "nuevo" && !AGENTES.some((a) => a.id === SEL)) SEL = null;
  if (!SEL && AGENTES.length) SEL = AGENTES[AGENTES.length - 1].id;
  await pintar();
}

function instalar() {
  const bar = document.querySelector("#composer .composer-bar");
  if (!bar || document.querySelector("#btn-orq")) return;
  const b = btn("🤖", "secondary", () => { s.hidden = false; refrescar(); }, "btn-orq"); b.title = "Orquestador de agentes"; b.setAttribute("aria-label", "Orquestador de agentes");
  const s = el("div", "sheet"); s.id = "ventana-orq"; s.hidden = true;
  const c = el("div", "va-caja"), h = el("div", "row va-head"); cuerpo = el("div"); cuerpo.id = "orq-cuerpo"; cuerpo.style.cssText = "display:flex;flex-direction:column;gap:10px";
  h.append(el("strong", "", "Orquestador · agentes"), btn("✕", "secondary", () => { s.hidden = true; clearTimeout(timer); }, "orq-cerrar"));
  s.onclick = (ev) => { if (ev.target === s) { s.hidden = true; clearTimeout(timer); } };
  c.append(h, cuerpo); s.append(c); document.body.append(s);
  bar.insertBefore(b, bar.querySelector(".action") || null);
}
window.RIU_ORQ = { orq, refrescar };
new MutationObserver(() => { try { instalar(); } catch (e) { console.warn("orquestador", e); } }).observe(document.body, { childList: true, subtree: true });
try { instalar(); } catch (e) {}
