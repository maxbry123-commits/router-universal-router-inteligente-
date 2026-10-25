// ventana-sesion.js — memoria de este chat, tope de ese texto y notas de revisión.
// El permiso de tools es el mismo del selector de modo. Nada de esto llama a otra organización.
import { el, btn, ventana } from "./ventanas-control.js";
import { leer, escribir, hash } from "./almacen.js";
import { parsearBloquesMemoria, parsearBloquesRevision, parsearModo } from "./contexto.js";

const K = "riu_sesion_v1";
const TIPOS = ["error", "seguridad", "aviso", "nota"];
export function estadoSesion() {
  const v = leer(K, {});
  const tope = Math.min(4000, Math.max(200, Number(v.tope) || 800));
  const revisiones = Array.isArray(v.revisiones) ? v.revisiones.filter((r) => r && TIPOS.includes(r.tipo) && r.texto).slice(0, 12) : [];
  return { memoria: v.memoria !== false, nota: String(v.nota || "").slice(0, 4000), tope, revisiones };
}
function guardar(p) { const a = estadoSesion(); escribir(K, { ...a, ...p }); }
function permiso() {
  const m = window.RIU_MODE;
  return m && m.getApproval ? m.getApproval() : "manual";
}
function ponerEnvio(agente) {
  const s = document.querySelector("#agent");
  if (!s) return "el selector de agente no está";
  if (!agente) { s.value = ""; s.dispatchEvent(new Event("change", { bubbles: true })); return "preguntar"; }
  const op = [...s.options].find((o) => o.value);
  if (!op) return "el router no tiene agentes";
  s.value = op.value;
  s.dispatchEvent(new Event("change", { bubbles: true }));
  return "agente";
}

function pintar(cuerpo) {
  const e = estadoSesion();
  const aviso = el("div", "cv-est");
  const mem = el("button", "toggle" + (e.memoria ? " on" : ""), e.memoria ? "ON" : "OFF");
  mem.type = "button"; mem.setAttribute("role", "switch"); mem.setAttribute("aria-checked", String(e.memoria)); mem.setAttribute("aria-label", "Memoria");
  mem.addEventListener("click", () => { guardar({ memoria: !e.memoria }); pintar(cuerpo); });
  const cab = el("div", "ses-fila"); cab.append(el("strong", "", "Memoria"), mem);
  const nota = el("textarea", "vn-ta"); nota.rows = 3; nota.maxLength = 4000; nota.value = e.nota; nota.placeholder = "Lo que este chat debe recordar"; nota.setAttribute("aria-label", "Nota de memoria");
  nota.addEventListener("change", () => { guardar({ nota: nota.value }); aviso.textContent = "memoria guardada"; });
  const tope = el("input"); tope.type = "number"; tope.min = "200"; tope.max = "4000"; tope.value = String(e.tope); tope.setAttribute("aria-label", "Tope de caracteres");
  tope.addEventListener("change", () => { guardar({ tope: tope.value }); aviso.textContent = "tope " + estadoSesion().tope; });
  const tf = el("div", "ses-fila"); tf.append(el("span", "", "Tope"), tope);
  const auto = permiso() === "auto";
  const per = el("button", "toggle" + (auto ? " on" : ""), auto ? "Automático" : "Manual");
  per.type = "button"; per.setAttribute("aria-pressed", String(auto)); per.title = "El mismo permiso del selector de modo";
  per.addEventListener("click", () => {
    const m = window.RIU_MODE;
    if (!m || !m.setApproval) { aviso.textContent = "el selector de modo no está listo"; return; }
    m.setApproval(permiso() === "auto" ? "manual" : "auto");
    pintar(cuerpo);
  });
  const pf = el("div", "ses-fila"); pf.append(el("span", "", "Tools"), per);
  const ag = !!(document.querySelector("#agent") || {}).value;
  const preguntar = el("button", "toggle" + (ag ? "" : " on"), "Preguntar"); preguntar.type = "button"; preguntar.setAttribute("aria-pressed", String(!ag));
  const agente = el("button", "toggle" + (ag ? " on" : ""), "Agente"); agente.type = "button"; agente.setAttribute("aria-pressed", String(ag));
  preguntar.addEventListener("click", () => { aviso.textContent = ponerEnvio(false); pintar(cuerpo); const n = cuerpo.querySelector(".cv-est"); if (n) n.textContent = "preguntar"; });
  agente.addEventListener("click", () => { const t = ponerEnvio(true); pintar(cuerpo); const n = cuerpo.querySelector(".cv-est"); if (n) n.textContent = t; });
  const ef = el("div", "ses-fila"); ef.append(preguntar, agente);
  const tipo = el("select"); tipo.setAttribute("aria-label", "Tipo de revisión");
  TIPOS.forEach((t) => tipo.append(el("option", "", t)));
  const texto = el("input"); texto.placeholder = "Qué hay que corregir"; texto.setAttribute("aria-label", "Texto de la revisión");
  const form = el("form", "ses-fila");
  form.append(tipo, texto, btn("Añadir", "secondary", () => {}));
  form.onsubmit = (ev) => {
    ev.preventDefault();
    const t = texto.value.trim();
    if (!t) return;
    const revisiones = [{ id: hash(tipo.value + t + Date.now()), tipo: tipo.value, texto: t.slice(0, 240) }, ...estadoSesion().revisiones].slice(0, 12);
    guardar({ revisiones });
    pintar(cuerpo);
  };
  const lista = el("div", "cola-lista");
  if (!e.revisiones.length) lista.append(el("div", "fila-desc", "Sin revisiones. Se envían con el siguiente mensaje."));
  e.revisiones.forEach((r) => {
    const fila = el("div", "cola-fila");
    fila.append(el("strong", "", r.tipo), el("div", "fila-desc", r.texto));
    fila.append(btn("Quitar", "secondary", () => { guardar({ revisiones: estadoSesion().revisiones.filter((x) => x.id !== r.id) }); pintar(cuerpo); }));
    lista.append(fila);
  });
  cuerpo.replaceChildren(el("div", "fila-desc", "La memoria viaja solo si está ON. El tope la recorta."), cab, nota, tf, pf, ef, el("div", "mod-grupo-t", "Revisión"), form, lista, aviso);
}

function instalar() {
  const hist = document.querySelector("#histories");
  if (hist && !hist.dataset.sesionNotas) {
    hist.dataset.sesionNotas = "1";
    let p = 0;
    const vistos = leer("riu_sesion_vistos_v1", []);
    const revisar = () => {
      p = 0;
      let cambio = false;
      hist.querySelectorAll(".message:not(.user):not(.pending) .txt").forEach((sp) => {
        parsearBloquesMemoria(sp.textContent).forEach((b) => {
          const h = hash("m" + b);
          if (vistos.includes(h)) return;
          vistos.push(h); cambio = true;
          guardar({ memoria: true, nota: b });
        });
        const modo = parsearModo(sp.textContent);
        if (modo) {
          const h = hash("modo" + modo);
          if (!vistos.includes(h)) { vistos.push(h); ponerEnvio(modo === "agente"); cambio = true; }
        }
        parsearBloquesRevision(sp.textContent).forEach((b) => {
          const h = hash(b.tipo + b.texto);
          if (vistos.includes(h)) return;
          vistos.push(h); cambio = true;
          const revisiones = [{ id: h, tipo: b.tipo, texto: b.texto }, ...estadoSesion().revisiones.filter((x) => x.id !== h)].slice(0, 12);
          guardar({ revisiones });
        });
      });
      if (cambio) { if (vistos.length > 200) vistos.splice(0, vistos.length - 200); escribir("riu_sesion_vistos_v1", vistos); }
    };
    new MutationObserver(() => { if (!p) p = requestAnimationFrame(revisar); }).observe(hist, { childList: true, subtree: true, characterData: true });
  }
}
window.addEventListener("mode:approval", () => { const c = document.querySelector("#ventana-sesion .vn-cuerpo"); if (c && !document.querySelector("#ventana-sesion").hidden) pintar(c); });

const montar = () => { ventana("sesion", "Sesión", pintar); instalar(); };
new MutationObserver(montar).observe(document.body, { childList: true, subtree: true });
montar();
