// fichas-externas.js — modelos REALES de Groq y NVIDIA en la hoja de fichas del chat (selector NVIDIA/Groq).
// El Router los publica en /chat/providers/{groq,nvidia}/models (solo si tiene su clave); el id viaja tal cual: «groq/<modelo>», «nvidia/<modelo>».
// Las fichas viejas (nv-muse-glimmer, nv-nemotron-super) no existen en el Router MVP y respondían con Qwen: se sustituyen.
import { api } from "./api.js";
const CACHE = "riu_fichas_ext_v1", VIEJAS = /^nv-/;
const leer = () => { try { return JSON.parse(localStorage.getItem(CACHE) || "[]"); } catch (e) { return []; } };
const cfg = () => (window.RIU_CONFIG = window.RIU_CONFIG || {});
function aplicar(lista) {  // lista: [{id, etiqueta}]
  if (!Array.isArray(lista) || !lista.length) return false;
  cfg().modelos = lista; cfg().defecto = lista[0].id;
  try { const c = window.RIU_CHAT && window.RIU_CHAT.chat(); if (c && VIEJAS.test(c.ficha || "")) c.ficha = lista[0].id; } catch (e) {}
  window.dispatchEvent(new CustomEvent("riu:fichas", { detail: { n: lista.length } }));
  try { window.RIU_SELECTORES && window.RIU_SELECTORES.refrescar(); } catch (e) {}
  return true;
}
aplicar(leer());  // antes de montar el chat: una ficha groq/… guardada sigue siendo válida al recargar
async function cargar() {
  try {
    const provs = ((await api("/chat/providers")).providers || []).filter((p) => p.id === "groq" || p.id === "nvidia");
    const lista = [];
    for (const p of provs) {
      try { for (const m of (await api("/chat/providers/" + p.id + "/models")).models || []) lista.push({ id: m.model_id, etiqueta: p.label + " · " + m.label }); }
      catch (e) { console.warn("fichas-externas", p.id, e.message); }
    }
    if (aplicar(lista)) { try { localStorage.setItem(CACHE, JSON.stringify(lista)); } catch (e) {} }
  } catch (e) { console.warn("fichas-externas", e.message); }
}
setTimeout(cargar, 800);
