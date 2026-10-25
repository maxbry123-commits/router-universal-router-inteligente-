// ventana-tareas.js — tareas programadas de este chat y los archivos reales de la sesión.
// Manual: la ventana. Tool: con IA o Agentes encendidos el modelo escribe [[TAREA:titulo|diario|08:00]]prompt[[/TAREA]].
// El mismo objeto se ofrece al plugin cuando exista: accion "tareas". Si el servidor no la tiene, queda en este chat.
import { el, btn, ventana } from "./ventanas-control.js";
import { leer, escribir, uid, hash } from "./almacen.js";
import { parsearBloquesTarea } from "./contexto.js";

const K = "riu_tareas_v1";
const CADA = [["una", "Una vez"], ["diario", "Cada día"], ["semanal", "Cada semana"]];
let vista = "tareas";
let q = "";
let avisoEl = null;
let pintar = () => {};

function caja() {
  const v = leer(K, { tareas: [], vistos: [] });
  v.tareas = Array.isArray(v.tareas) ? v.tareas : [];
  v.vistos = Array.isArray(v.vistos) ? v.vistos : [];
  return v;
}
function guardar(v) { escribir(K, v); marcar(); }
function sesion() { return sessionStorage.getItem("riu_sesion") || "web-general"; }
function proxima(cada, hora, desde) {
  const p = String(hora || "08:00").split(":");
  const c = new Date(desde || Date.now());
  c.setHours(parseInt(p[0], 10) || 0, parseInt(p[1], 10) || 0, 0, 0);
  if (c.getTime() <= (desde || Date.now())) c.setDate(c.getDate() + (cada === "semanal" ? 7 : 1));
  return c.getTime();
}
function crear(p) {
  const cada = CADA.some((x) => x[0] === p.cada) ? p.cada : "diario";
  const hora = /^([01]?\d|2[0-3]):[0-5]\d$/.test(p.hora || "") ? p.hora.padStart(5, "0") : "08:00";
  return {
    id: uid(), titulo: String(p.titulo || "Tarea").slice(0, 80), prompt: String(p.prompt || "").slice(0, 2000),
    cada, hora, nunca: cada !== "una" && p.nunca !== false, omitir: !!p.omitir, on: true,
    proxima: proxima(cada, hora, Date.now()), ultima: 0,
  };
}
function avanzar(t) {
  t.ultima = Date.now();
  if (t.cada === "una" || !t.nunca) { t.on = false; t.proxima = 0; }
  else t.proxima = proxima(t.cada, t.hora, Date.now());
}
function lista() { return caja().tareas.filter((t) => t && t.on); }
function marcar() {
  const b = document.querySelector("#btn-tareas");
  if (!b) return;
  const n = caja().tareas.filter((t) => t.on && t.proxima && t.proxima <= Date.now()).length;
  b.title = n ? n + " lista" : "Tareas";
  b.setAttribute("aria-label", n ? "Tareas, " + n + " lista" : "Tareas");
  const nom = b.querySelector(".mas-nom");
  if (nom) nom.textContent = b.getAttribute("aria-label");
}
async function avisarServidor(accion, extra) {
  if (!window.RIU_ACCION) return false;
  try { await window.RIU_ACCION("tareas", Object.assign({ accion, sesion: sesion() }, extra)); return true; }
  catch (e) { return false; }
}
function meter(p) {
  const t = crear(p);
  const v = caja();
  v.tareas.unshift(t);
  v.tareas = v.tareas.slice(0, 30);
  guardar(v);
  avisarServidor("guardar", { tarea: t });
  return t;
}
function lanzar(t) {
  if (window.RIU_CHAT && window.RIU_CHAT.ocupado()) return "el chat está trabajando";
  const m = document.querySelector("#message");
  const form = document.querySelector("#composer");
  if (!m || !form) return "no hay caja";
  if (m.value.trim()) return "la caja tiene texto";
  m.value = t.prompt;
  m.dispatchEvent(new Event("input", { bubbles: true }));
  if (!t.omitir) return "lista en la caja";
  form.requestSubmit();
  return "enviada";
}
function vencer() {
  const v = caja();
  let cambio = false;
  v.tareas.forEach((t) => {
    if (!t.on || !t.proxima || t.proxima > Date.now()) return;
    if (!t.omitir) return;
    const r = lanzar(t);
    if (r !== "enviada") return;
    avanzar(t);
    cambio = true;
  });
  if (cambio) { guardar(v); pintar(); }
  else marcar();
}

function pintarTareas(cuerpo) {
  const v = caja();
  const aviso = el("div", "cv-est");
  avisoEl = aviso;
  const buscar = el("input");
  buscar.type = "search"; buscar.placeholder = "Buscar"; buscar.value = q; buscar.setAttribute("aria-label", "Buscar tarea");
  buscar.oninput = () => { q = buscar.value; const pos = buscar.selectionStart; pintar(); const b2 = document.querySelector("#ventana-tareas input[type=search]"); if (b2) { b2.focus(); try { b2.setSelectionRange(pos, pos); } catch (e) {} } };
  const chips = el("div", "loop-partes");
  [["tareas", "Programadas"], ["archivos", "Artefactos"]].forEach(([id, nom]) => {
    const s = el("button", vista === id ? "on" : "", nom);
    s.type = "button";
    s.onclick = () => { vista = id; pintar(); };
    chips.append(s);
  });
  const listaEl = el("div", "cola-lista");
  const form = el("form", "cv-form");
  form.hidden = true;
  const titulo = el("input"); titulo.placeholder = "Título"; titulo.setAttribute("aria-label", "Título"); titulo.maxLength = 80;
  const prompt = el("textarea", "vn-ta"); prompt.rows = 2; prompt.placeholder = "Qué debe hacer el modelo"; prompt.setAttribute("aria-label", "Prompt");
  const cada = el("select"); cada.setAttribute("aria-label", "Repetir");
  CADA.forEach(([id, nom]) => { const o = el("option", "", nom); o.value = id; cada.append(o); });
  cada.value = "diario";
  const hora = el("input"); hora.type = "time"; hora.value = "08:00"; hora.setAttribute("aria-label", "Hora");
  const nunca = el("input"); nunca.type = "checkbox"; nunca.checked = true;
  const labN = el("label", "tarea-check"); labN.append(nunca, el("span", "", "Se repite"));
  const omitir = el("input"); omitir.type = "checkbox";
  const labO = el("label", "tarea-check"); labO.append(omitir, el("span", "", "Enviar sola"));
  const guardarBtn = btn("Guardar", "secondary", () => {});
  form.append(titulo, prompt, cada, hora, labN, labO, guardarBtn);
  form.onsubmit = (ev) => {
    ev.preventDefault();
    if (!prompt.value.trim()) { aviso.textContent = "falta el prompt"; return; }
    meter({ titulo: titulo.value.trim() || "Tarea", prompt: prompt.value.trim(), cada: cada.value, hora: hora.value, nunca: nunca.checked, omitir: omitir.checked });
    titulo.value = ""; prompt.value = ""; form.hidden = true;
    aviso.textContent = "guardada en este chat";
    pintar();
  };
  const nueva = btn("Nueva", "secondary", () => { form.hidden = !form.hidden; if (!form.hidden) titulo.focus(); });
  const qAhora = q;
  const filtra = (t) => !qAhora || (t.titulo + " " + t.prompt).toLowerCase().includes(qAhora.toLowerCase());
  nueva.hidden = vista === "archivos";
  if (vista === "tareas") {
    const ts = v.tareas.filter(filtra);
    if (!ts.length) listaEl.append(el("div", "fila-desc", "Sin tareas. Nueva, o el modelo con [[TAREA:titulo|diario|08:00]]prompt[[/TAREA]] si IA está encendida."));
    ts.forEach((t) => {
      const listaYa = t.on && t.proxima && t.proxima <= Date.now();
      const fila = el("div", "cola-fila" + (t.on ? "" : " hecha"));
      const nombre = el("span", "", t.titulo);
      nombre.title = t.prompt;
      const cuando = el("div", "fila-desc", (CADA.find((x) => x[0] === t.cada) || CADA[1])[1] + " · " + t.hora + (t.omitir ? " · sola" : "") + (listaYa ? " · lista" : "") + (t.on ? "" : " · hecha"));
      const acc = el("div", "cv-form");
      if (t.on) acc.append(btn(listaYa ? "Lanzar" : "Ahora", "secondary", () => {
        const r = lanzar(t);
        aviso.textContent = r;
        if (r === "enviada") {
          const e = caja();
          const x = e.tareas.find((y) => y.id === t.id);
          if (x) avanzar(x);
          guardar(e);
        }
        pintar();
      }));
      acc.append(btn("Quitar", "secondary", () => {
        const e = caja(); e.tareas = e.tareas.filter((x) => x.id !== t.id); guardar(e); avisarServidor("quitar", { id: t.id }); pintar();
      }));
      fila.append(nombre, cuando, acc);
      listaEl.append(fila);
    });
  }
  cuerpo.replaceChildren(chips, buscar, nueva, form, listaEl, aviso);
  if (vista === "archivos") pintarArchivos(listaEl, q, aviso);
  marcar();
}
async function pintarArchivos(listaEl, q, aviso) {
  listaEl.replaceChildren(el("div", "fila-desc", "Cargando archivos de este chat"));
  let nombres = [];
  try {
    const r = await window.RIU_ACCION("archivos", { sesion: sesion() });
    nombres = (r.archivos || []).map(String);
    aviso.textContent = nombres.length + " en este chat";
  } catch (e) {
    aviso.textContent = "el servidor no dio archivos";
    listaEl.replaceChildren(el("div", "fila-desc", "No hay lista. El almacén responde cuando el chat está conectado."));
    return;
  }
  const f = nombres.filter((n) => !q || n.toLowerCase().includes(q.toLowerCase()));
  listaEl.replaceChildren();
  if (!f.length) listaEl.append(el("div", "fila-desc", nombres.length ? "Ningún archivo con ese texto" : "Este chat no tiene archivos"));
  f.slice(0, 40).forEach((n) => {
    const fila = el("button", "tarea-archivo", n);
    fila.type = "button";
    fila.title = "Poner el nombre en la caja";
    fila.onclick = () => {
      const m = document.querySelector("#message");
      if (!m) return;
      m.value = (m.value.trim() ? m.value.replace(/\s*$/, "") + "\n" : "") + n;
      m.dispatchEvent(new Event("input", { bubbles: true }));
      m.focus();
      aviso.textContent = "nombre en la caja";
    };
    listaEl.append(fila);
  });
}

function instalarTool() {
  const hist = document.querySelector("#histories");
  if (!hist || hist.dataset.tareas) return;
  hist.dataset.tareas = "1";
  let p = 0;
  const revisar = () => {
    p = 0;
    const v = caja();
    let cambio = false;
    hist.querySelectorAll(".message:not(.user):not(.pending) .txt").forEach((sp) => parsearBloquesTarea(sp.textContent).forEach((b) => {
      const h = hash(b.titulo + b.cada + b.hora + b.prompt);
      if (v.vistos.includes(h)) return;
      v.vistos.push(h);
      if (v.vistos.length > 200) v.vistos.shift();
      v.tareas.unshift(crear(b));
      v.tareas = v.tareas.slice(0, 30);
      cambio = true;
    }));
    if (cambio) { guardar(v); avisarServidor("guardar", { tareas: v.tareas }); pintar(); }
  };
  new MutationObserver(() => { if (!p) p = requestAnimationFrame(revisar); }).observe(hist, { childList: true, subtree: true, characterData: true });
  document.addEventListener("submit", (ev) => {
    if (!ev.target || ev.target.id !== "composer") return;
    const m = document.querySelector("#message");
    if (!m) return;
    const x = /^\/tarea(?:\s+([\s\S]*))?$/i.exec(m.value.trim());
    if (!x) return;
    ev.preventDefault();
    ev.stopPropagation();
    const resto = (x[1] || "").trim();
    if (!resto) { const b = document.querySelector("#btn-tareas"); if (b) b.click(); return; }
    const partes = resto.split("|").map((s) => s.trim());
    if (!partes[0] || !partes[3]) { if (avisoEl) avisoEl.textContent = "Uso: /tarea título | diario | 08:00 | prompt"; return; }
    meter({ titulo: partes[0], cada: partes[1], hora: partes[2], prompt: partes.slice(3).join(" | "), nunca: partes[1] !== "una", omitir: false });
    m.value = "";
    m.dispatchEvent(new Event("input", { bubbles: true }));
    pintar();
  }, true);
}

window.RIU_TAREAS = {
  listar: () => caja().tareas.map((t) => Object.assign({}, t)),
  guardar: (p) => meter(p),
  quitar: (id) => { const v = caja(); v.tareas = v.tareas.filter((t) => t.id !== id); guardar(v); return true; },
};

const montar = () => {
  ventana("tareas", "Tareas", (cuerpo) => { pintar = () => pintarTareas(cuerpo); pintar(); });
  instalarTool();
  marcar();
};
new MutationObserver(montar).observe(document.body, { childList: true, subtree: true });
montar();
setInterval(vencer, 30000);
vencer();
