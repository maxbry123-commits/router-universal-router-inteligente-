// fichas-externas.js — modelos REALES de Groq y NVIDIA del Router (/chat/providers/{groq,nvidia}/models; solo si el Space tiene su clave).
//  · selector NVIDIA: la hoja de fichas lista los modelos NVIDIA (id «nvidia/<modelo>»).
//  · selector Groq: hoja propia (#sel-groq) con los modelos Groq; el elegido queda en window.RIU_GROQ.modelo («groq/<modelo>»).
// Sin clave o sin conexión no se inventa nada: RIU_GROQ.aviso y la etiqueta lo dicen.
import { api } from "./api.js";
const CACHE = "riu_fichas_ext_v2", KG = "riu_groq_modelo", VIEJAS = /^nv-/;
const leer = (k, d) => { try { return JSON.parse(localStorage.getItem(k) || "null") || d; } catch (e) { return d; } };
const cfg = () => (window.RIU_CONFIG = window.RIU_CONFIG || {});
const G = (window.RIU_GROQ = window.RIU_GROQ || { lista: [], modelo: "", aviso: "cargando modelos de Groq…" });
const refrescar = () => { try { window.RIU_SELECTORES && window.RIU_SELECTORES.refrescar(); } catch (e) {} };
function aplicar(d) {  // d: {groq:[{id,etiqueta}], nvidia:[…], avisoGroq, avisoNvidia}
  G.lista = d.groq || []; G.aviso = G.lista.length ? "" : (d.avisoGroq || "el Router no tiene GROQ_API_KEY");
  const guardado = localStorage.getItem(KG) || ""; G.modelo = G.lista.some((m) => m.id === guardado) ? guardado : (G.lista[0] || {}).id || "";
  if ((d.nvidia || []).length) {
    cfg().modelos = d.nvidia; cfg().defecto = d.nvidia[0].id;
    try { const c = window.RIU_CHAT && window.RIU_CHAT.chat(); if (c && VIEJAS.test(c.ficha || "")) c.ficha = d.nvidia[0].id; } catch (e) {}
  } else (cfg().modelos || []).forEach((m) => { if (VIEJAS.test(m.id) && !/responde Qwen/.test(m.etiqueta)) m.etiqueta += " (" + (d.avisoNvidia || "sin NVIDIA en el Router") + ": responde Qwen)"; });
  window.dispatchEvent(new CustomEvent("riu:fichas", { detail: { groq: G.lista.length, nvidia: (d.nvidia || []).length } }));
  refrescar();
}
aplicar(leer(CACHE, { groq: [], nvidia: [], avisoGroq: "cargando modelos de Groq…" }));  // antes de montar el chat: lo último conocido
async function cargar() {
  const d = { groq: [], nvidia: [] };
  try {
    const provs = ((await api("/chat/providers")).providers || []).map((p) => p.id);
    for (const p of ["groq", "nvidia"]) {
      if (!provs.includes(p)) { d["aviso" + (p === "groq" ? "Groq" : "Nvidia")] = "el Router no tiene " + p.toUpperCase() + "_API_KEY"; continue; }
      try { d[p] = ((await api("/chat/providers/" + p + "/models")).models || []).map((m) => ({ id: m.model_id, etiqueta: (p === "groq" ? "Groq · " : "NVIDIA · ") + m.label })); }
      catch (e) { d["aviso" + (p === "groq" ? "Groq" : "Nvidia")] = p + ": " + e.message.slice(0, 80); }
    }
    try { localStorage.setItem(CACHE, JSON.stringify(d)); } catch (e) {}
  } catch (e) { d.avisoGroq = d.avisoNvidia = "sin conexión con el Router"; }
  aplicar(d);
}
setTimeout(cargar, 800);
// hoja del selector Groq
function hojaGroq() {
  let s = document.getElementById("sh-groq");
  if (!s) {
    s = document.createElement("div"); s.id = "sh-groq"; s.className = "sheet"; s.hidden = true; s.setAttribute("role", "dialog"); s.setAttribute("aria-label", "Modelos de Groq");
    s.innerHTML = '<div class="va-caja"><div class="row va-head"><strong>Groq · modelos</strong><button type="button" class="secondary sh-cerrar" aria-label="Cerrar">✕</button></div><div class="list" id="sh-groq-lista"></div></div>';
    s.addEventListener("click", (e) => { if (e.target === s || e.target.closest(".sh-cerrar")) s.hidden = true; });
    document.addEventListener("keydown", (e) => { if (e.key === "Escape") s.hidden = true; });
    document.body.append(s);
  }
  const l = s.querySelector("#sh-groq-lista"); l.replaceChildren();
  if (!G.lista.length) { const p = document.createElement("p"); p.className = "muted"; p.textContent = "Groq: " + G.aviso + ". Pide al Director que ponga GROQ_API_KEY en el Space."; l.append(p); }
  G.lista.forEach((m) => {
    const b = document.createElement("button"); b.type = "button"; b.className = "fila" + (m.id === G.modelo ? " on" : ""); b.setAttribute("aria-pressed", String(m.id === G.modelo));
    b.textContent = m.etiqueta + (m.id === G.modelo ? "  ✓" : "");
    b.onclick = () => { G.modelo = m.id; try { localStorage.setItem(KG, m.id); } catch (e) {} s.hidden = true; refrescar(); };
    l.append(b);
  });
  s.hidden = false;
}
document.addEventListener("click", (e) => { if (e.target.closest("#sel-groq")) hojaGroq(); });
