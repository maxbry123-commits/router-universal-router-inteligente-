// ventana-cola.js — cola de trabajo. El contrato está en LOOP-wachdog-cola.json.
// Solo habla con el plugin puente_chat del harness. No toca el router.
import { accion } from "./api.js";
import { el, btn, ventana, vivo, SIN_BACKEND } from "./ventanas-control.js";

const K = "riu_cola";
let MAX = 50;
const cable = { lista: "checklist", tool: "tools_lock", nombre: "pendientes", acciones: ["listar", "agregar", "marcar", "ordenar", "quitar"] };
let tareas = [];
let origen = "chat";
let agenteVe = null;

function locales() {
  try {
    const g = JSON.parse(sessionStorage.getItem(K) || "[]");
    if (Array.isArray(g)) {  // antes se guardaban solo los textos; ahora {texto, hecho}
      return g.map((t) => (typeof t === "string" ? { texto: t, hecho: false } : t && typeof t.texto === "string" ? { texto: t.texto, hecho: !!t.hecho } : null))
        .filter((t) => t && t.texto.trim()).slice(0, MAX);
    }
  } catch (e) {}
  return [];
}
function guardarLocal() {
  try { sessionStorage.setItem(K, JSON.stringify(tareas.map((t) => ({ texto: t.texto, hecho: !!t.hecho })))); } catch (e) {}
}
function tomar(r) {
  tareas = (r.pendientes || []).filter((p) => p && p.id).map((p) => ({ id: p.id, texto: String(p.texto || ""), hecho: !!p.hecho }));
  origen = r.persistente === false ? "memoria" : "servidor";
}
async function refrescar() {
  const r = await accion(cable.lista, { accion: cable.acciones[0] });
  tomar(r);
}
async function leerAgente() {
  const r = await accion(cable.tool, {});
  const t = (r.tools || []).find((x) => x.nombre === cable.nombre);
  agenteVe = !!(t && !t.locked);
}
function donde() {
  if (origen === "servidor") return "en el servidor";
  if (origen === "memoria") return "no se guarda al reiniciar";
  return "en este chat · no se envía al modelo";
}

function pintar(cuerpo) {
  const aviso = vivo(el("div", "cv-est"));
  const estado = vivo(el("div", "wd-estado"));
  const texto = el("textarea", "vn-ta");
  texto.rows = 1;
  texto.placeholder = "Tarea. Enter para añadir.";
  texto.setAttribute("aria-label", "Tarea para la cola");
  const lista = el("div", "cola-lista");
  lista.setAttribute("role", "list"); lista.setAttribute("aria-label", "Tareas de la cola");
  let ocupado = false;
  const ver = () => {
    const hechas = tareas.filter((t) => t.hecho).length;
    const f = window.RIU_CHAT_TOOL_FLAGS || {};
    const recibe = !agenteVe ? "" : (f.tools || f.agente_tool || f.llm_tool ? " · modelo" : " · falta IA");
    const sitio = origen === "servidor" ? "servidor" : donde();
    estado.textContent = tareas.length + "/" + MAX + " · " + hechas + " hechas · " + sitio + recibe;
    pintarAgente();
    lista.replaceChildren();
    tareas.forEach((t, i) => {
      const fila = el("div", "cola-fila" + (t.hecho ? " hecha" : "")); fila.setAttribute("role", "listitem");
      const hecho = el("input");
      hecho.type = "checkbox";
      hecho.checked = t.hecho;
      hecho.disabled = ocupado;
      hecho.setAttribute("aria-label", (t.hecho ? "Pasar a pendiente: " : "Marcar hecha: ") + t.texto);
      hecho.onchange = () => marcar(i);
      const caja = el("label", "cola-check");
      caja.append(hecho);
      const nombre = el("span", "", (i + 1) + ". " + t.texto);
      nombre.title = t.texto;
      fila.append(caja, nombre);
      const acc = el("div", "cv-form");
      const up = btn("Subir", "secondary", () => mover(i, -1));
      const down = btn("Bajar", "secondary", () => mover(i, 1));
      const quitar = btn("Quitar", "secondary", () => sacar(i));
      up.disabled = i === 0 || ocupado;
      down.disabled = i === tareas.length - 1 || ocupado;
      quitar.disabled = ocupado;
      acc.append(up, down, quitar);
      fila.append(acc);
      lista.append(fila);
    });
  };
  const fallar = (e) => { aviso.textContent = e.message || "el servidor no respondió"; };
  const marcar = async (i) => {
    if (ocupado || !tareas[i]) return;
    if (origen === "chat") { tareas[i].hecho = !tareas[i].hecho; guardarLocal(); ver(); return; }
    ocupado = true; ver();
    try { tomar(await accion(cable.lista, { accion: cable.acciones[2], id: tareas[i].id, hecho: !tareas[i].hecho })); aviso.textContent = ""; }
    catch (e) { fallar(e); }
    ocupado = false; ver();
  };
  const mover = async (i, d) => {
    const j = i + d;
    if (j < 0 || j >= tareas.length || ocupado) return;
    if (origen === "chat") {
      const a = tareas[j]; tareas[j] = tareas[i]; tareas[i] = a; guardarLocal(); ver(); return;
    }
    ocupado = true; ver();
    const ids = tareas.map((t) => t.id);
    const a = ids[j]; ids[j] = ids[i]; ids[i] = a;
    try { tomar(await accion(cable.lista, { accion: cable.acciones[3], ids })); aviso.textContent = ""; }
    catch (e) { fallar(e); }
    ocupado = false; ver();
  };
  const sacar = async (i) => {
    if (ocupado) return;
    if (origen === "chat") { tareas.splice(i, 1); guardarLocal(); ver(); return; }
    ocupado = true; ver();
    try { tomar(await accion(cable.lista, { accion: cable.acciones[4], id: tareas[i].id })); aviso.textContent = ""; }
    catch (e) { fallar(e); }
    ocupado = false; ver();
  };
  const agente = btn("Tool", "secondary", async () => {
    if (agenteVe === null) { aviso.textContent = SIN_BACKEND + ": no se puede cambiar la tool; el servidor no respondió"; return; }
    agente.disabled = true;
    try { await accion(cable.tool, { tool: cable.nombre, locked: !!agenteVe }); await leerAgente(); aviso.textContent = ""; }
    catch (e) { fallar(e); }
    agente.disabled = false;
    pintarAgente();
  });
  agente.title = "Tool pendientes. Con IA o Agentes encendidos, el modelo la recibe en el mensaje.";
  agente.classList.add("cola-tool");
  const pintarAgente = () => {
    agente.textContent = agenteVe ? "Tool ON" : "Tool OFF";
    agente.setAttribute("aria-pressed", agenteVe ? "true" : "false");
  };
  const add = btn("Añadir", "secondary", async () => {
    const v = texto.value.trim();
    if (!v) { aviso.textContent = "escribe la tarea"; return; }
    if (tareas.length >= MAX) { aviso.textContent = "la cola admite 50 tareas"; return; }
    if (origen === "chat") {
      tareas.push({ id: "", texto: v.slice(0, 200), hecho: false });
      texto.value = ""; aviso.textContent = ""; guardarLocal(); ver(); return;
    }
    add.disabled = true;
    try {
      tomar(await accion(cable.lista, { accion: cable.acciones[1], texto: v.slice(0, 200) }));
      texto.value = ""; aviso.textContent = "";
    } catch (e) { fallar(e); }
    add.disabled = false; ver();
  });
  texto.onkeydown = (ev) => { if (ev.key === "Enter" && !ev.shiftKey) { ev.preventDefault(); add.click(); } };
  const titulo = el("input"); titulo.placeholder = "Título de la cola"; titulo.setAttribute("aria-label", "Título de la cola");
  const tipo = el("select"); tipo.setAttribute("aria-label", "Tipo de tarea");
  ["model", "validation", "ricardo", "handoff", "delay"].forEach((v) => tipo.append(new Option(v, v)));
  const prompt = el("textarea", "vn-ta"); prompt.rows = 2; prompt.placeholder = "Prompt de t1"; prompt.setAttribute("aria-label", "Prompt de la tarea");
  const contiene = el("input"); contiene.placeholder = "acceptance contains"; contiene.setAttribute("aria-label", "Texto que debe contener");
  const qidIn = el("input"); qidIn.placeholder = "qid cit_…"; qidIn.setAttribute("aria-label", "Id de la cola");
  const plug = vivo(el("div", "cv-est"));
  const decir = (r) => { plug.textContent = typeof r === "string" ? r : JSON.stringify(r).slice(0, 220); };
  const llamar = async (action, body) => { try { decir(await window.RIU_PLUGIN("cola50", action, body)); } catch (e) { plug.textContent = e.message; } };
  const crearQ = btn("Crear", "action", () => llamar("crear", { title: titulo.value.trim() || "cola", tasks: [{ id: "t1", title: titulo.value.trim() || "t1", type: tipo.value, prompt: prompt.value, depends_on: [], acceptance: contiene.value.trim() ? { contains: contiene.value.trim() } : {} }] }));
  const verQ = btn("Listar", "secondary", () => llamar("listar", {}));
  const estQ = btn("Estado", "secondary", () => llamar("estado", { qid: qidIn.value.trim() }));
  const evQ = btn("Eventos", "secondary", () => llamar("eventos", { qid: qidIn.value.trim() }));
  const ctrl = (sub) => btn(sub, "secondary", () => llamar("accion", { qid: qidIn.value.trim(), sub }));
  const aprobar = btn("Aprobar", "secondary", () => llamar("aprobar", { qid: qidIn.value.trim(), task_id: "t1" }));
  const worker = (sub) => btn("worker " + sub, "secondary", () => llamar("worker", { sub }));
  const qFila = el("div", "cv-form");
  qFila.append(crearQ, verQ, estQ, evQ, ctrl("start"), ctrl("pause"), ctrl("resume"), ctrl("cancel"), aprobar, worker("start"), worker("stop"), worker("estado"));
  const cabeza = el("div", "cola-cabeza");
  cabeza.append(estado, agente);
  cuerpo.replaceChildren(el("div", "cv-sec", "cola50"), titulo, tipo, prompt, contiene, qidIn, qFila, plug, cabeza, texto, add, lista, aviso);
  estado.textContent = "cargando";
  refrescar().then(async () => {
    try { await leerAgente(); } catch (e) { agenteVe = null; aviso.textContent = "el agente no respondió"; }
    pintarAgente();
    ver();
  }).catch(() => {
    origen = "chat";
    tareas = locales().map((t) => ({ id: "", texto: t.texto, hecho: t.hecho }));
    aviso.textContent = SIN_BACKEND + ": el servidor no respondió; las tareas quedan en este chat";
    ver();
  });
}

fetch("/chat/ui/LOOP-wachdog-cola.json").then((r) => r.json()).then((j) => {
  const c = j && j.cola_trabajo;
  if (!c || c.plugin !== "puente_chat") return;
  if (c.max) MAX = c.max;
  if (c.lista) cable.lista = c.lista;
  if (c.tool) cable.tool = c.tool;
  if (c.nombre_tool) cable.nombre = c.nombre_tool;
  if (Array.isArray(c.acciones) && c.acciones.length === 5) cable.acciones = c.acciones;
}).catch(() => {});

const montar = () => ventana("cola", "Cola", pintar);
new MutationObserver(montar).observe(document.body, { childList: true, subtree: true });
montar();
