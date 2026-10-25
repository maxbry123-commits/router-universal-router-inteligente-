// ventana-cola.js — cola de trabajo del chat. No envía las tareas al modelo.
import { el, btn, ventana } from "./ventanas-control.js";

const K = "riu_cola";
const MAX = 50;
let tareas = [];
try {
  const g = JSON.parse(sessionStorage.getItem(K) || "[]");
  if (Array.isArray(g)) tareas = g.filter((t) => typeof t === "string" && t.trim()).slice(0, MAX);
} catch (e) {}

function guardar() { try { sessionStorage.setItem(K, JSON.stringify(tareas)); } catch (e) {} }

function pintar(cuerpo) {
  const aviso = el("div", "cv-est");
  const estado = el("div", "wd-estado");
  const texto = el("textarea", "vn-ta");
  texto.rows = 2;
  texto.placeholder = "Tarea para la cola";
  texto.setAttribute("aria-label", "Tarea para la cola");
  const lista = el("div", "cola-lista");
  const ver = () => {
    estado.textContent = tareas.length + "/" + MAX + " · en este chat · no se envía al modelo";
    lista.replaceChildren();
    tareas.forEach((t, i) => {
      const fila = el("div", "cola-fila");
      fila.append(el("span", "", (i + 1) + ". " + t));
      const acc = el("div", "cv-form");
      const up = btn("Subir", "secondary", () => { if (!i) return; const a = tareas[i - 1]; tareas[i - 1] = tareas[i]; tareas[i] = a; guardar(); ver(); });
      const down = btn("Bajar", "secondary", () => { if (i === tareas.length - 1) return; const a = tareas[i + 1]; tareas[i + 1] = tareas[i]; tareas[i] = a; guardar(); ver(); });
      const quitar = btn("Quitar", "secondary", () => { tareas.splice(i, 1); guardar(); ver(); });
      up.disabled = i === 0;
      down.disabled = i === tareas.length - 1;
      acc.append(up, down, quitar);
      fila.append(acc);
      lista.append(fila);
    });
  };
  const add = btn("Añadir", "secondary", () => {
    const v = texto.value.trim();
    if (!v) { aviso.textContent = "escribe la tarea"; return; }
    if (tareas.length >= MAX) { aviso.textContent = "la cola admite 50 tareas"; return; }
    tareas.push(v.slice(0, 200));
    texto.value = "";
    aviso.textContent = "";
    guardar();
    ver();
  });
  cuerpo.replaceChildren(estado, texto, add, lista, aviso);
  ver();
}

const montar = () => ventana("cola", "Cola", pintar);
new MutationObserver(montar).observe(document.body, { childList: true, subtree: true });
montar();
