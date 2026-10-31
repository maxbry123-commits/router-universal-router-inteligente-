// swe-claves.js — claves de Groq y NVIDIA para los modelos SWE. Se guardan SOLO en este navegador (localStorage 'riu_swe_claves'),
// viajan unicamente en el cuerpo de las peticiones SWE al bridge (campo `claves`) y nunca se muestran ni se escriben en el chat.
export const CLAVE_LS = "riu_swe_claves";
const PROVEEDORES = ["groq", "nvidia"];
const ETIQUETA = { groq: "Groq", nvidia: "NVIDIA" };

const limpia = (v) => {
  if (typeof v === "string") return v.trim();
  if (Array.isArray(v)) return v.filter((x) => typeof x === "string").map((x) => x.trim()).filter(Boolean);
  return "";
};
const leerCrudo = () => { try { const o = JSON.parse(localStorage.getItem(CLAVE_LS)); return o && typeof o === "object" && !Array.isArray(o) ? o : {}; } catch (e) { return {}; } };

export function leerClaves() {
  const o = leerCrudo(), r = {};
  for (const p of PROVEEDORES) { const v = limpia(o[p]); if (v && v.length) r[p] = v; }
  return r;
}
export function guardarClave(proveedor, valor) {
  if (!PROVEEDORES.includes(proveedor)) return;
  const v = limpia(valor); if (!v) return;
  try { localStorage.setItem(CLAVE_LS, JSON.stringify({ ...leerClaves(), [proveedor]: v })); } catch (e) {}
}
export function borrarClaves() { try { localStorage.removeItem(CLAVE_LS); } catch (e) {} }

// ---- cableado de la seccion de Configuracion (el panel se monta despues: delegacion en document + MutationObserver) ----
function pintarEstado() {
  const est = document.getElementById("ap-clave-estado"); if (!est) return;
  const c = leerClaves();
  est.textContent = PROVEEDORES.filter((p) => c[p]).map((p) => ETIQUETA[p] + ": guardada").join(" · ");
}
function alClic(ev) {
  const t = ev.target && ev.target.closest ? ev.target.closest("#ap-clave-guardar, #ap-clave-borrar") : null;
  if (!t) return;
  const est = document.getElementById("ap-clave-estado");
  if (t.id === "ap-clave-guardar") {
    for (const p of PROVEEDORES) { const i = document.getElementById("ap-clave-" + p); if (i) { guardarClave(p, i.value); i.value = ""; } }
    pintarEstado();
    if (est && !est.textContent) est.textContent = "Nada que guardar";
  } else {
    borrarClaves();
    for (const p of PROVEEDORES) { const i = document.getElementById("ap-clave-" + p); if (i) i.value = ""; }
    if (est) est.textContent = "Claves borradas";
  }
}
if (typeof document !== "undefined" && document.addEventListener) {
  document.addEventListener("click", alClic);
  if (typeof MutationObserver !== "undefined") {
    let visto = false;
    new MutationObserver(() => { const hay = !!document.getElementById("ap-clave-estado"); if (hay && !visto) pintarEstado(); visto = hay; }).observe(document.documentElement, { childList: true, subtree: true });
  }
}
