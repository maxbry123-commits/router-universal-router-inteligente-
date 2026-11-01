// swe-claves.js — claves de Groq y NVIDIA. Se guardan SOLO en el BANCO CIFRADO DEL SERVIDOR (POST/GET/DELETE {BASE}/web/v1/claves con la clave del chat en X-API-Key);
// las usan SWE CODE, SWEN CODE y los selectores Groq/NVIDIA. R1 (auditoria 3): el navegador NO guarda claves (ni respaldo en localStorage) ni las reenvia en las
// peticiones de inferencia: si el banco no responde solo se informa el estado y no se guarda nada. Los valores jamas se muestran ni se escriben en el chat.
// CLAVE_LS es la entrada VIEJA de versiones anteriores: purgarLocal() la borra al cargar.
export const CLAVE_LS = "riu_swe_claves";
const PROVEEDORES = ["groq", "nvidia"];
const ETIQUETA = { groq: "Groq", nvidia: "NVIDIA" };

export const MAX_CLAVES = 20;  // por proveedor (el banco del bridge admite GROQ_API_KEY_1..20)
// Varias claves por proveedor: texto separado por coma, punto y coma, espacios o saltos de linea, o un array. Sin vacias ni repetidas; tope 20.
export function separarClaves(v) {
  const trozos = typeof v === "string" ? [v] : Array.isArray(v) ? v.filter((x) => typeof x === "string") : [];
  return [...new Set(trozos.flatMap((t) => t.split(/[\s,;]+/)).filter(Boolean))].slice(0, MAX_CLAVES);
}
const limpia = (v) => { const l = separarClaves(v); return l.length > 1 ? l : l[0] || ""; };  // una sola -> texto (como siempre); varias -> array
const cuantas = (v) => (Array.isArray(v) ? v.length : v ? 1 : 0);
export function purgarLocal() { try { localStorage.removeItem(CLAVE_LS); } catch (e) {} }
purgarLocal();  // una clave que quedo en el navegador por versiones anteriores se borra

// ---- banco del servidor ----
const RUTA = "/web/v1/claves";
const TOPE_MS = 20000;
const cfg = () => (typeof window !== "undefined" && window.RIU_CONFIG) || {};
const valida = (u) => /^https:\/\/[a-z0-9-]+\.hf\.space$/.test(u || "");

// BASE = el mismo origen que usa api.js; si aun no se resolvio, se le pide a api.js que lo resuelva
async function resolverBase() {
  const c = cfg(); if (c.apiBase) return c.apiBase;
  try { const l = localStorage.getItem("riu_live_url"); if (valida(l)) return l; } catch (e) {}
  try { const m = await import("./api.js"); await m.api("/health").catch(() => {}); } catch (e) {}
  return cfg().apiBase || cfg().proxyDestino || "";
}
async function llamar(metodo, cuerpo) {
  const base = await resolverBase(), c = cfg(), h = {};
  let k = ""; try { k = sessionStorage.getItem("riu_clave") || ""; } catch (e) {}
  h[c.authHeader || "X-API-Key"] = k;
  if (cuerpo !== undefined) h["Content-Type"] = "application/json";
  const ac = typeof AbortController === "function" ? new AbortController() : null;
  const t = ac ? setTimeout(() => ac.abort(), TOPE_MS) : null;
  let r;
  try {
    r = await fetch(String(base).replace(/\/$/, "") + RUTA, { method: metodo, headers: h, credentials: base ? "omit" : "same-origin", body: cuerpo === undefined ? undefined : JSON.stringify(cuerpo), signal: ac ? ac.signal : undefined });
  } catch (e) { throw { status: 0, code: "RED" }; } finally { if (t) clearTimeout(t); }
  let p = {}; try { p = await r.json(); } catch (e) {}
  if (!r.ok || p.ok === false || ((metodo === "POST" || metodo === "DELETE") && p.local !== true)) {
    throw { status: r.ok ? 503 : r.status, code: (p && p.error && p.error.code) || "BANCO_NO_GUARDADO" };
  }
  return { groq: Number(p.groq) || 0, nvidia: Number(p.nvidia) || 0,
    ...(metodo === "POST" || metodo === "DELETE" ? { local: p.local, persistido: p.persistido === true } : {}) };
}
export const estadoBanco = () => llamar("GET");
export const borrarBanco = () => llamar("DELETE");
export const guardarEnBanco = (valores) => llamar("POST", valores);

export function textoConteos(n) {
  const t = PROVEEDORES.filter((p) => n[p] > 0).map((p) => ETIQUETA[p] + ": " + n[p] + (n[p] === 1 ? " guardada" : " guardadas")).join(" · ");
  return t || "Sin claves guardadas en el servidor";
}
export function textoError(e) {
  if (e && e.code === "BANCO_NO_GUARDADO") return "No se guardó nada: falló el banco cifrado del servidor";
  if (e && e.code === "BANCO_NO_BORRADO") return "No se borraron las claves: falló el banco cifrado del servidor";
  if (e && e.status === 401) return "Clave del chat incorrecta: no se guardó nada";
  if (e && e.status === 400) return "Clave con formato inválido (8–300 caracteres, sin espacios; separa varias con coma o salto de línea): no se guardó nada";
  if (e && e.status === 503) return "El servidor no tiene clave de acceso configurada: no se guardó nada";
  return "";
}
const sinBanco = (e) => !e || e.status === 0 || e.status === 404 || e.status >= 500 && e.status !== 503;

const SIN_SERVIDOR = "el servidor no respondió; el banco del servidor es la única fuente y las claves no se guardan en este navegador";
// Guardar: SOLO al banco del servidor. Devuelve {ok, texto}: ok = quedo guardada en el banco; nunca incluye valores.
export async function guardarConEstado(valores) {
  const v = {}; for (const p of PROVEEDORES) { const x = limpia(valores && valores[p]); if (x && x.length) v[p] = x; }
  if (!Object.keys(v).length) return { ok: false, texto: "Nada que guardar" };
  try {
    const n = await guardarEnBanco(v);
    return { ok: true, texto: textoConteos(n) + (n.persistido ? " · respaldo cifrado publicado" : " · solo banco local; respaldo externo no confirmado") };
  } catch (e) {
    if (!sinBanco(e)) return { ok: false, texto: textoError(e) || "No se pudo guardar" };
    return { ok: false, texto: "No se guardó nada: " + SIN_SERVIDOR };
  }
}
export const guardar = async (valores) => (await guardarConEstado(valores)).texto;
export async function borrar() {
  try {
    const n = await borrarBanco();
    return n.persistido ? "Claves borradas del servidor y del respaldo cifrado" : "Claves borradas del banco local; respaldo externo no confirmado";
  } catch (e) { return textoError(e) || (sinBanco(e) ? "No se borró nada: " + SIN_SERVIDOR : "No se pudo borrar en el servidor"); }
}
export async function estado() {  // sin banco solo se informa el estado
  try { return textoConteos(await estadoBanco()); } catch (e) {
    const err = textoError(e);
    return e && e.status === 401 ? err.replace(": no se guardó nada", "") : "Sin verificar: " + SIN_SERVIDOR;
  }
}

// ---- cableado de la seccion de Configuracion (el panel se monta despues: delegacion en document + MutationObserver) ----
const poner = async (promesa) => { const est = document.getElementById("ap-clave-estado"); if (est) est.textContent = "…"; const t = await promesa; const e2 = document.getElementById("ap-clave-estado"); if (e2) e2.textContent = t; };
function alClic(ev) {
  const t = ev.target && ev.target.closest ? ev.target.closest("#ap-clave-guardar, #ap-clave-borrar") : null;
  if (!t) return;
  const vaciar = () => { for (const p of PROVEEDORES) { const i = document.getElementById("ap-clave-" + p); if (i) i.value = ""; } };
  if (t.id === "ap-clave-guardar") {
    const v = {}; for (const p of PROVEEDORES) { const i = document.getElementById("ap-clave-" + p); if (i) v[p] = i.value; }
    const est = document.getElementById("ap-clave-estado"); if (est) est.textContent = "…";
    guardarConEstado(v).then((r) => { if (r.ok) vaciar(); /* solo tras exito: si falla (401/400) el usuario no pierde lo que escribio */ const e2 = document.getElementById("ap-clave-estado"); if (e2) e2.textContent = r.texto; });
  } else {
    const seguro = typeof window !== "undefined" && typeof window.confirm === "function" ? window.confirm("¿Borrar las claves de Groq y NVIDIA guardadas? Esta acción no se puede deshacer.") : true;
    if (!seguro) return;
    vaciar(); poner(borrar());
  }
}
if (typeof document !== "undefined" && document.addEventListener) {
  document.addEventListener("click", alClic);
  if (typeof MutationObserver !== "undefined") {
    let visto = false;
    new MutationObserver(() => { const hay = !!document.getElementById("ap-clave-estado"); if (hay && !visto) poner(estado()); visto = hay; }).observe(document.documentElement, { childList: true, subtree: true });
  }
}
