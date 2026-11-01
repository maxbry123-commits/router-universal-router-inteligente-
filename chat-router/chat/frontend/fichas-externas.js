// fichas-externas.js — modelos REALES de Groq y NVIDIA del Router (/chat/providers/{groq,nvidia}/models; solo si el Space tiene su clave).
//  · selector NVIDIA: la hoja de fichas lista los modelos NVIDIA (id «nvidia/<modelo>»).
//  · selector Groq: hoja propia (#sel-groq) con los modelos Groq; el elegido queda en window.RIU_GROQ.modelo («groq/<modelo>»).
// Sin clave o sin conexión no se inventa nada: RIU_GROQ.aviso y la etiqueta lo dicen.
// Solo se ofrecen los modelos elegidos por el Director (MODELOS_SELECCIONADOS) y solo si el proveedor los publica en su catálogo real;
// uno elegido que el catálogo no trae se muestra «NO DISPONIBLE» y nunca se sustituye por otro en silencio (el backend tampoco).
import { api } from "./api.js";
const CACHE = "riu_fichas_ext_v3", KG = "riu_groq_modelo", VIEJAS = /^nv-/;
export const MODELOS_SELECCIONADOS = new Set(["groq/qwen/qwen3.8-27b", "nvidia/minimaxai/minimax-m3.1-flash", "nvidia/meta/muse-glimmer-30b", "nvidia/nvidia/nemotron-3-ultra-550b-a55b", "nvidia/z-ai/glm-5.3"]);
const NOMBRES = { "groq/qwen/qwen3.8-27b": "Qwen 3.8 27B", "nvidia/minimaxai/minimax-m3.1-flash": "MiniMax M3.1 Flash", "nvidia/meta/muse-glimmer-30b": "Muse Glimmer 30B", "nvidia/nvidia/nemotron-3-ultra-550b-a55b": "Nemotron 3 Ultra 550B", "nvidia/z-ai/glm-5.3": "GLM 5.3" };
const MARCA = { groq: "Groq · ", nvidia: "NVIDIA · " };
// catálogo real del proveedor (ids «<prov>/…») -> [{id, etiqueta, disponible}]: los elegidos presentes primero y, después, los ausentes como NO DISPONIBLE
export function seleccionar(prov, catalogo) {
  const real = new Set((catalogo || []).map((m) => (typeof m === "string" ? m : m && m.model_id)).filter(Boolean));
  const mios = [...MODELOS_SELECCIONADOS].filter((id) => id.startsWith(prov + "/"));
  const fila = (id, disponible) => ({ id, disponible, etiqueta: MARCA[prov] + NOMBRES[id] + (disponible ? "" : " — NO DISPONIBLE") });
  return [...mios.filter((id) => real.has(id)).map((id) => fila(id, true)), ...mios.filter((id) => !real.has(id)).map((id) => fila(id, false))];
}
const leer = (k, d) => { try { return JSON.parse(localStorage.getItem(k) || "null") || d; } catch (e) { return d; } };
const cfg = () => (window.RIU_CONFIG = window.RIU_CONFIG || {});
const G = (window.RIU_GROQ = window.RIU_GROQ || { lista: [], modelo: "", aviso: "cargando modelos de Groq…" });
const refrescar = () => { try { window.RIU_SELECTORES && window.RIU_SELECTORES.refrescar(); } catch (e) {} };
export function aplicar(d) {  // d: {groq:[{id,etiqueta,disponible}], nvidia:[…], locales:[…], avisoGroq, avisoNvidia}
  window.RIU_LOCAL = { lista: d.locales || [] }; // modelos HF por el MISMO bridge; sin afirmar disponible por solo tener URL
  G.lista = d.groq || [];
  const buenos = G.lista.filter((m) => m.disponible !== false), guardado = localStorage.getItem(KG) || "";
  const perdido = G.lista.find((m) => m.disponible === false && m.id === guardado);  // lo que el usuario tenía elegido y ya no existe: se dice, no se cambia
  G.modelo = buenos.some((m) => m.id === guardado) ? guardado : perdido ? "" : (buenos[0] || {}).id || "";
  G.aviso = G.modelo ? "" : (perdido || G.lista[0]) ? (perdido || G.lista[0]).etiqueta.replace(/^Groq · /, "") : (d.avisoGroq || "el Router no tiene GROQ_API_KEY");
  if ((d.nvidia || []).length) {
    const buenosNv = d.nvidia.filter((m) => m.disponible !== false), previoNv = (window.RIU_NVIDIA || {}).modelo || "";
    cfg().modelos = d.nvidia;
    cfg().defecto = buenosNv[0]?.id || "";
    const actualNv = buenosNv.some(m => m.id === previoNv) ? previoNv : cfg().defecto;
    window.RIU_NVIDIA = { aviso: actualNv ? "" : (d.avisoNvidia || "elige un modelo NVIDIA configurado"), lista: d.nvidia, modelo: actualNv };
    try { const c = window.RIU_CHAT && window.RIU_CHAT.chat(); if (c && (VIEJAS.test(c.ficha || "") || !c.ficha)) c.ficha = actualNv || c.ficha; } catch (e) {}
  } else {
    window.RIU_NVIDIA = { ...(window.RIU_NVIDIA || {}), aviso: d.avisoNvidia || "sin modelos NVIDIA verificados", lista: [], modelo: "" };
  }
  window.dispatchEvent(new CustomEvent("riu:fichas", { detail: { groq: G.lista.length, nvidia: (d.nvidia || []).length } }));
  refrescar();
}
aplicar(leer(CACHE, { groq: [], nvidia: [], avisoGroq: "cargando modelos de Groq…" }));  // antes de montar el chat: lo último conocido
export async function cargar() {
  const d = { groq: [], nvidia: [], locales: [] };
  // Fuente primaria: MISMO bridge y banco cifrado que hacen la inferencia de YAIWES y OpenClaw.
  // Si se consulta solo /chat/providers del Router MVP, faltan las claves guardadas en el bridge y aparecen falsos NO CONFIGURADO.
  try {
    const [pub, banco] = await Promise.all([api("/web/v1/modelos/disponibilidad"), api("/web/v1/claves")]);
    if (!pub?.ok || !Array.isArray(pub.modelos) || !banco?.ok) throw new Error("BRIDGE_CATALOGO_INVALIDO");
    d.locales = (Array.isArray(pub.locales) ? pub.locales : []).filter(m => m && /^hf\/[a-z0-9._-]+$/i.test(m.id)).map(m => ({
      id: m.id, disponible: null, estado: m.estado === "NO CONFIGURADO" ? "NO CONFIGURADO" : "SIN VERIFICAR",
      etiqueta: m.id.slice(3) + (m.estado === "NO CONFIGURADO" ? " — NO CONFIGURADO" : " — SIN VERIFICAR"),
    }));
    for (const p of ["groq", "nvidia"]) {
      const disponibles = pub.modelos.filter(m => m && m.proveedor === p && MODELOS_SELECCIONADOS.has(m.id));
      d[p] = disponibles.map(m => {
        const tieneClave = Number(banco[p]) > 0;
        const estado = !tieneClave ? "NO CONFIGURADO" : m.disponible === true ? "DISPONIBLE" : m.disponible === false ? "NO DISPONIBLE" : "SIN VERIFICAR";
        return { id: m.id, estado, disponible: !tieneClave || m.disponible === false ? false : m.disponible === true ? true : null,
          etiqueta: MARCA[p] + NOMBRES[m.id] + (estado === "DISPONIBLE" ? "" : " — " + estado) };
      });
      if (!Number(banco[p])) d["aviso" + (p === "groq" ? "Groq" : "Nvidia")] = "sin claves " + p.toUpperCase() + " en el banco del bridge";
    }
    try { localStorage.setItem(CACHE, JSON.stringify(d)); } catch (e) {}
    aplicar(d); return;
  } catch (e) { /* bridge anterior o inaccesible: comprobar Router sin afirmar falso NO DISPONIBLE */ }
  try {
    const provs = ((await api("/chat/providers")).providers || []).map((p) => p.id);
    for (const p of ["groq", "nvidia"]) {
      if (!provs.includes(p)) { d["aviso" + (p === "groq" ? "Groq" : "Nvidia")] = "no configurado o sin conexión al bridge; revisa banco de claves"; continue; }
      try { d[p] = seleccionar(p, ((await api("/chat/providers/" + p + "/models")).models || []).map((m) => m.model_id)); }
      catch (e) { d["aviso" + (p === "groq" ? "Groq" : "Nvidia")] = p + ": " + e.message.slice(0, 80); }
    }
    try { localStorage.setItem(CACHE, JSON.stringify(d)); } catch (e) {}
  } catch (e) { d.avisoGroq = d.avisoNvidia = "sin conexión con el Router ni el bridge"; }
  aplicar(d);
}
setTimeout(cargar, 800);
// El selector Groq ya no tiene hoja propia con lista de modelos (era el duplicado): su ventana es el SELECTOR CENTRAL unico (swe-selectores.js), cuyo
// MODELO QUE RESPONDE lista estos mismos modelos. Aqui solo queda el estado y los ganchos que ese selector usa.
G.elegir = (id) => { const m = G.lista.find((x) => x.id === id); if (!m || m.disponible === false) return false; G.modelo = id; G.aviso = ""; try { localStorage.setItem(KG, id); } catch (e) {} refrescar(); return true; };  // un modelo que el proveedor no publica no se elige
window.RIU_FICHAS = { recargar: cargar };  // «Actualizar disponibilidad» vuelve a pedir los catalogos sin recargar el chat
