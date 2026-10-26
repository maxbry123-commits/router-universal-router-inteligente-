// ventana-cola.js — cola de trabajo. El contrato está en LOOP-wachdog-cola.json.
// Solo habla con el plugin puente_chat del harness. No toca el router.
import { accion } from "./api.js";
import { el, btn, ventana } from "./ventanas-control.js";

const K = "riu_cola";
let MAX = 50;
const cable = { lista: "checklist", tool: "tools_lock", nombre: "pendientes", acciones: ["listar", "agregar", "marcar", "ordenar", "quitar"] };
let tareas = [];
let origen = "chat";
let agenteVe = null;

function locales() {
  try {
    const g = JSON.parse(sessionStorage.getItem(K) || "[]");
    if (Array.isArray(g)) return g.filter((t) => typeof t === "string" && t.trim()).slice(0, MAX);
  } catch (e) {}
  return [];
}
function guardarLocal() {
  try { sessionStorage.setItem(K, JSON.stringify(tareas.map((t) => t.texto))); } catch (e) {}
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
  const aviso = el("div", "cv-est");
  const estado = el("div", "wd-estado");
  const texto = el("textarea", "vn-ta");
  texto.rows = 1;
  texto.placeholder = "Tarea. Enter para añadir.";
  texto.setAttribute("aria-label", "Tarea para la cola");
  const lista = el("div", "cola-lista");
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
      const fila = el("div", "cola-fila" + (t.hecho ? " hecha" : ""));
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
    if (agenteVe === null) return;
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
      tareas.push({ id: "", texto: v.slice(0, 200) });
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
  const cabeza = el("div", "cola-cabeza");
  cabeza.append(estado, agente);
  cuerpo.replaceChildren(cabeza, texto, add, lista, aviso);
  estado.textContent = "cargando";
  refrescar().then(async () => {
    try { await leerAgente(); } catch (e) { agenteVe = null; aviso.textContent = "el agente no respondió"; }
    pintarAgente();
    ver();
  }).catch(() => {
    origen = "chat";
    tareas = locales().map((t) => ({ id: "", texto: t }));
    aviso.textContent = "el servidor no respondió";
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
