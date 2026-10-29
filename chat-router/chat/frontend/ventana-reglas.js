// ventana-reglas.js — idioma de la respuesta, reglas que viajan con el mensaje y tope de lo que escribes.
// No revisa pull requests ni cobra: solo recorta el envío si pasa el tope.
import { el, btn, ventana } from "./ventanas-control.js";
import { leer, escribir, hash, cuadernoTraer } from "./almacen.js";
import { parsearIdioma, parsearBloquesRegla } from "./contexto.js";

const K = "riu_reglas_v1";
const IDIOMAS = [["", "El del mensaje"], ["es", "Español"], ["en", "Inglés"], ["pt", "Portugués"]];
export function estadoReglas() {
  const v = leer(K, {});
  const idioma = IDIOMAS.some((x) => x[0] === v.idioma) ? v.idioma : "";
  const topeMsg = Math.min(20000, Math.max(0, Number(v.topeMsg) || 0));
  const reglas = Array.isArray(v.reglas) ? v.reglas.filter((r) => r && r.texto).slice(0, 8) : [];
  return { idioma, topeMsg, reglas };
}
function guardar(p) { escribir(K, { ...estadoReglas(), ...p }); }

function pintar(cuerpo) {
  const e = estadoReglas();
  const aviso = el("div", "cv-est");
  const idioma = el("select"); idioma.setAttribute("aria-label", "Idioma de la respuesta");
  IDIOMAS.forEach(([v, n]) => { const o = el("option", "", n); o.value = v; if (v === e.idioma) o.selected = true; idioma.append(o); });
  idioma.addEventListener("change", () => { guardar({ idioma: idioma.value }); aviso.textContent = "idioma guardado"; });
  const tope = el("input"); tope.type = "number"; tope.min = "0"; tope.max = "20000"; tope.value = String(e.topeMsg); tope.setAttribute("aria-label", "Tope del mensaje");
  tope.addEventListener("change", () => { guardar({ topeMsg: tope.value }); aviso.textContent = Number(tope.value) > 0 ? "tope " + estadoReglas().topeMsg : "sin tope"; });
  const fila = el("div", "ses-fila"); fila.append(idioma, tope);
  const texto = el("input"); texto.placeholder = "Regla para el modelo"; texto.setAttribute("aria-label", "Nueva regla");
  const form = el("form", "ses-fila");
  form.append(texto, btn("Añadir", "secondary", () => {}));
  form.onsubmit = (ev) => {
    ev.preventDefault();
    const t = texto.value.trim();
    if (!t) return;
    guardar({ reglas: [{ id: hash(t + Date.now()), texto: t.slice(0, 240), on: true }, ...estadoReglas().reglas].slice(0, 8) });
    pintar(cuerpo);
  };
  const lista = el("div", "cola-lista");
  if (!e.reglas.length) lista.append(el("div", "fila-desc", "Sin reglas. Las encendidas viajan con cada mensaje."));
  e.reglas.forEach((r) => {
    const sw = el("button", "toggle" + (r.on !== false ? " on" : ""), r.on !== false ? "ON" : "OFF");
    sw.type = "button"; sw.setAttribute("role", "switch"); sw.setAttribute("aria-checked", String(r.on !== false)); sw.setAttribute("aria-label", "Regla");
    sw.addEventListener("click", () => { guardar({ reglas: estadoReglas().reglas.map((x) => x.id === r.id ? { ...x, on: x.on === false } : x) }); pintar(cuerpo); });
    const f = el("div", "cola-fila");
    f.append(sw, el("div", "fila-desc", r.texto), btn("Quitar", "secondary", () => { guardar({ reglas: estadoReglas().reglas.filter((x) => x.id !== r.id) }); pintar(cuerpo); }));
    lista.append(f);
  });
  cuerpo.replaceChildren(el("div", "fila-desc", "Idioma y reglas van en el mensaje. 0 en el tope no corta lo que escribes."), fila, form, lista, aviso);
}

function instalar() {
  const hist = document.querySelector("#histories");
  if (hist && !hist.dataset.reglas) {
    hist.dataset.reglas = "1";
    cuadernoTraer(K, () => !estadoReglas().reglas.length && !estadoReglas().idioma && !estadoReglas().topeMsg);
    let p = 0;
    const vistos = leer("riu_reglas_vistos_v1", []);
    const revisar = () => {
      p = 0;
      let cambio = false;
      hist.querySelectorAll(".message:not(.user):not(.pending) .txt").forEach((sp) => {
        const idi = parsearIdioma(sp.textContent);
        if (idi) {
          const h = hash("i" + idi + sp.textContent.length);
          if (!vistos.includes(h)) { vistos.push(h); guardar({ idioma: idi }); cambio = true; }
        }
        parsearBloquesRegla(sp.textContent).forEach((t) => {
          const h = hash(t);
          if (vistos.includes(h)) return;
          vistos.push(h); cambio = true;
          const ya = estadoReglas().reglas;
          if (!ya.some((r) => r.texto === t)) guardar({ reglas: [{ id: h, texto: t, on: true }, ...ya].slice(0, 8) });
        });
      });
      if (cambio) { if (vistos.length > 200) vistos.splice(0, vistos.length - 200); escribir("riu_reglas_vistos_v1", vistos); }
    };
    new MutationObserver(() => { if (!p) p = requestAnimationFrame(revisar); }).observe(hist, { childList: true, subtree: true, characterData: true });
  }
  if (document.body.dataset.reglasTope) return;
  document.body.dataset.reglasTope = "1";
  document.addEventListener("submit", (ev) => {
    if (!ev.target || ev.target.id !== "composer") return;
    const m = document.querySelector("#message");
    const n = estadoReglas().topeMsg;
    if (!m || !n || m.value.trim().startsWith("/") || m.value.length <= n) return;
    ev.preventDefault();
    ev.stopPropagation();
    const a = document.querySelector("#notice");
    if (a) a.textContent = "El mensaje pasa el tope de " + n + " caracteres";
  }, true);
}

const montar = () => { ventana("reglas", "Reglas", pintar); instalar(); };
new MutationObserver(montar).observe(document.body, { childList: true, subtree: true });
montar();
