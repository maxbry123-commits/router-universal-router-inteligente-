// ventana-cola.js — cola de trabajo. Lee el checklist del harness; si no responde, se queda en este chat.
import { accion } from "./api.js";
import { el, btn, ventana } from "./ventanas-control.js";

const K = "riu_cola";
const MAX = 50;
let tareas = [];
let origen = "chat";

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
  tareas = (r.pendientes || []).filter((p) => p && p.id).map((p) => ({ id: p.id, texto: String(p.texto || "") }));
  origen = r.persistente === false ? "memoria" : "servidor";
}
async function refrescar() {
  const r = await accion("checklist", {});
  tomar(r);
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
  texto.rows = 2;
  texto.placeholder = "Tarea para la cola";
  texto.setAttribute("aria-label", "Tarea para la cola");
  const lista = el("div", "cola-lista");
  let ocupado = false;
  const ver = () => {
    estado.textContent = tareas.length + "/" + MAX + " · " + donde();
    lista.replaceChildren();
    tareas.forEach((t, i) => {
      const fila = el("div", "cola-fila");
      fila.append(el("span", "", (i + 1) + ". " + t.texto));
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
  const mover = async (i, d) => {
    const j = i + d;
    if (j < 0 || j >= tareas.length || ocupado) return;
    if (origen === "chat") {
      const a = tareas[j]; tareas[j] = tareas[i]; tareas[i] = a; guardarLocal(); ver(); return;
    }
    ocupado = true; ver();
    const ids = tareas.map((t) => t.id);
    const a = ids[j]; ids[j] = ids[i]; ids[i] = a;
    try { tomar(await accion("checklist", { accion: "ordenar", ids })); aviso.textContent = ""; }
    catch (e) { fallar(e); }
    ocupado = false; ver();
  };
  const sacar = async (i) => {
    if (ocupado) return;
    if (origen === "chat") { tareas.splice(i, 1); guardarLocal(); ver(); return; }
    ocupado = true; ver();
    try { tomar(await accion("checklist", { accion: "quitar", id: tareas[i].id })); aviso.textContent = ""; }
    catch (e) { fallar(e); }
    ocupado = false; ver();
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
      tomar(await accion("checklist", { accion: "agregar", texto: v.slice(0, 200) }));
      texto.value = ""; aviso.textContent = "";
    } catch (e) { fallar(e); }
    add.disabled = false; ver();
  });
  cuerpo.replaceChildren(estado, texto, add, lista, aviso);
  estado.textContent = "cargando";
  refrescar().then(() => { aviso.textContent = ""; ver(); }).catch(() => {
    origen = "chat";
    tareas = locales().map((t) => ({ id: "", texto: t }));
    aviso.textContent = "el servidor no respondió";
    ver();
  });
}

const montar = () => ventana("cola", "Cola", pintar);
new MutationObserver(montar).observe(document.body, { childList: true, subtree: true });
montar();
