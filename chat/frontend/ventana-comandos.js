// ventana-comandos.js — comandos del chat. A mano: la ventana o /comando nombre | texto.
// Tool: con IA o Agentes encendidos, [[COMANDO:nombre]]texto[[/COMANDO]]. Se llaman con /nombre.
import { el, btn, ventana } from "./ventanas-control.js";
import { leer, escribir, hash } from "./almacen.js";
import { parsearBloquesComando } from "./contexto.js";

const K = "riu_comandos_v1";
const NOMBRE = /^[a-z0-9-]{1,24}$/;
export function listaComandos() {
  const v = leer(K, []);
  return Array.isArray(v) ? v.filter((c) => c && NOMBRE.test(c.nombre) && c.texto) : [];
}
function guardarLista(v) { escribir(K, v.slice(0, 20)); }
function meter(nombre, texto) {
  const n = String(nombre || "").trim().toLowerCase();
  const t = String(texto || "").trim().slice(0, 500);
  if (!NOMBRE.test(n) || !t) return "el nombre va en minúsculas, sin espacios, y hace falta el texto";
  const v = listaComandos().filter((c) => c.nombre !== n);
  v.unshift({ nombre: n, texto: t });
  guardarLista(v);
  return "guardado /" + n;
}
function quitar(nombre) { guardarLista(listaComandos().filter((c) => c.nombre !== nombre)); }

function pintar(cuerpo) {
  const aviso = el("div", "cv-est");
  const nombre = el("input"); nombre.placeholder = "nombre"; nombre.setAttribute("aria-label", "Nombre del comando"); nombre.maxLength = 24;
  const texto = el("textarea", "vn-ta"); texto.rows = 2; texto.placeholder = "Texto que entra en la caja"; texto.setAttribute("aria-label", "Texto del comando");
  const form = el("form", "cv-form");
  form.append(nombre, texto, btn("Guardar", "secondary", () => {}));
  form.onsubmit = (ev) => {
    ev.preventDefault();
    aviso.textContent = meter(nombre.value, texto.value);
    if (aviso.textContent.startsWith("guardado")) { nombre.value = ""; texto.value = ""; }
    pintar(cuerpo);
    const a = cuerpo.querySelector(".cv-est"); if (a) a.textContent = aviso.textContent;
  };
  const lista = el("div", "cola-lista");
  const cs = listaComandos();
  if (!cs.length) lista.append(el("div", "fila-desc", "Sin comandos. Escribe / en la caja para ver los del chat."));
  cs.forEach((c) => {
    const fila = el("div", "cola-fila");
    fila.append(el("span", "", "/" + c.nombre), el("div", "fila-desc", c.texto));
    fila.append(btn("Quitar", "secondary", () => { quitar(c.nombre); pintar(cuerpo); }));
    lista.append(fila);
  });
  cuerpo.replaceChildren(el("div", "fila-desc", "Un comando pone su texto en la caja. No envía solo."), form, lista, aviso);
}

function instalar() {
  const hist = document.querySelector("#histories");
  if (hist && !hist.dataset.comandos) {
    hist.dataset.comandos = "1";
    let p = 0;
    const vistos = leer("riu_comandos_vistos_v1", []);
    const revisar = () => {
      p = 0;
      let cambio = false;
      hist.querySelectorAll(".message:not(.user):not(.pending) .txt").forEach((sp) => parsearBloquesComando(sp.textContent).forEach((b) => {
        const h = hash(b.nombre + b.texto);
        if (vistos.includes(h)) return;
        vistos.push(h);
        if (vistos.length > 200) vistos.shift();
        meter(b.nombre, b.texto);
        cambio = true;
      }));
      if (cambio) escribir("riu_comandos_vistos_v1", vistos);
    };
    new MutationObserver(() => { if (!p) p = requestAnimationFrame(revisar); }).observe(hist, { childList: true, subtree: true, characterData: true });
  }
  if (document.body.dataset.cmdSlash) return;
  document.body.dataset.cmdSlash = "1";
  document.addEventListener("submit", (ev) => {
    if (!ev.target || ev.target.id !== "composer") return;
    const m = document.querySelector("#message");
    if (!m) return;
    const x = /^\/comando(?:\s+([\s\S]*))?$/i.exec(m.value.trim());
    if (!x) return;
    ev.preventDefault();
    ev.stopPropagation();
    const resto = (x[1] || "").trim();
    if (!resto) { const b = document.querySelector("#btn-comandos"); if (b) b.click(); return; }
    const i = resto.indexOf("|");
    const nota = i < 0 ? "Uso: /comando nombre | texto" : meter(resto.slice(0, i), resto.slice(i + 1));
    m.value = "";
    m.dispatchEvent(new Event("input", { bubbles: true }));
    const a = document.querySelector("#ventana-comandos .cv-est");
    if (a) a.textContent = nota;
  }, true);
}

const montar = () => { ventana("comandos", "Comandos", pintar); instalar(); };
new MutationObserver(montar).observe(document.body, { childList: true, subtree: true });
montar();
