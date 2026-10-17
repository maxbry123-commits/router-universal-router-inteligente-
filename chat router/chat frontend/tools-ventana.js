// tools-ventana.js — MVP de tools: ventana en el chat (modelos, tools y pool de agentes Groq, max 20) y bloque en Configuración.
// Backend: puente_chat acciones groq_agentes (listar/guardar) y tools_estado. Sin frameworks: mismo estilo (.sheet/.va-caja).
import { accion } from "./api.js";
const el = (t, c, x) => { const e = document.createElement(t); if (c) e.className = c; if (x != null) e.textContent = x; return e; };
let estado = null;
const cargar = async () => { estado = await accion("tools_estado", {}); return estado; };

function filaAgente(a, quitar) {
  const f = el("div", "item tv-ag"); f.style.cssText = "display:flex;gap:8px;align-items:center;justify-content:space-between";
  const t = el("span", "", a.nombre + " · " + a.modelo); t.title = a.sistema || "";
  f.append(t);
  if (quitar) { const b = el("button", "secondary", "Quitar"); b.type = "button"; b.onclick = () => quitar(a.nombre); f.append(b); }
  return f;
}

async function pintarVentana(caja) {
  caja.replaceChildren(el("div", "muted", "Cargando…"));
  let e; try { e = await cargar(); } catch (x) { caja.replaceChildren(el("div", "muted", "Sin conexión con el Router: " + x.message)); return; }
  const mods = (window.RIU_CONFIG?.modelos || []).map((m) => m.etiqueta).join(" · ");
  const guardar = async (lista) => {
    const r = await accion("groq_agentes", { agentes: lista });
    if (r.error) { alert(r.error); return; }
    pintarVentana(caja);
  };
  const quitar = (n) => guardar(e.agentes.filter((a) => a.nombre !== n));
  const form = el("form", "row tv-form"); form.style.cssText = "flex-wrap:wrap;gap:6px";
  const nom = el("input"); nom.placeholder = "nombre"; nom.required = true; nom.id = "tv-nombre";
  const mod = el("select"); mod.id = "tv-modelo"; ["openai/gpt-oss-20b", "openai/gpt-oss-120b", "qwen/qwen3.8-27b"].forEach((m) => mod.append(new Option(m, m)));
  const sis = el("input"); sis.placeholder = "prompt de sistema corto"; sis.id = "tv-sistema";
  const add = el("button", "action", "Añadir"); add.id = "tv-anadir";
  form.append(nom, mod, sis, add);
  form.onsubmit = (ev) => { ev.preventDefault(); if (e.agentes.length >= 20) { alert("Máximo 20 agentes"); return; } guardar([...e.agentes, { nombre: nom.value, modelo: mod.value, sistema: sis.value }]); };
  const lista = el("div", "list tv-lista"); e.agentes.forEach((a) => lista.append(filaAgente(a, quitar)));
  caja.replaceChildren(
    el("strong", "", "Modelos en el chat"), el("div", "muted", "NVIDIA: " + mods),
    el("strong", "", "Tools"), el("div", "muted", e.tools.join(", ")),
    el("strong", "", "Agentes Groq (" + e.agentes.length + "/20) · tool groq_agente"), lista, form);
}

function instalarChat() {
  const bar = document.querySelector("#composer .composer-bar");
  if (!bar || document.querySelector("#btn-tools")) return;
  const b = el("button", "secondary", "🧰"); b.type = "button"; b.id = "btn-tools"; b.title = "Tools y agentes"; b.setAttribute("aria-label", "Tools y agentes");
  const s = el("div", "sheet"); s.id = "ventana-tools"; s.hidden = true;
  const c = el("div", "va-caja"), h = el("div", "row va-head"), x = el("button", "secondary", "✕"), cuerpo = el("div", "list"); cuerpo.id = "tv-cuerpo";
  x.type = "button"; x.onclick = () => { s.hidden = true; };
  s.onclick = (ev) => { if (ev.target === s) s.hidden = true; };
  c.style.overflow = "auto";
  h.append(el("strong", "", "Tools y agentes"), x); c.append(h, cuerpo); s.append(c); document.body.append(s);
  b.onclick = () => { s.hidden = false; pintarVentana(cuerpo); };
  const env = bar.querySelector(".action"); bar.insertBefore(b, env || null);
}

async function instalarConfig() {
  const temas = document.querySelector("#ap-temas");
  if (!temas || document.querySelector("#cfg-tools")) return;
  const sec = el("section", "ap-sec"); sec.id = "cfg-tools";
  sec.append(el("h2", "", "Fichas, modelos, tools y agentes"));
  const cuerpo = el("div", "list"); sec.append(cuerpo);
  temas.closest("section").before(sec);
  cuerpo.append(el("div", "muted", "Cargando…"));
  try {
    const e = await cargar();
    const k = e.claves || {};
    cuerpo.replaceChildren(
      ...e.fichas.map((f) => el("div", "item", "Ficha " + f.nombre + " · " + f.modelo + " · espera " + f.timeout_s + " s")),
      el("div", "item", "Tools: " + e.tools.join(", ")),
      el("div", "item", "Agentes Groq conectados: " + e.agentes.length + "/20 — " + e.agentes.map((a) => a.nombre).join(", ")),
      el("div", "item", "Estado claves · NVIDIA: " + (k.nvidia || 0) + " · Groq: " + (k.groq || 0) + " · GitHub: " + (k.github ? "ok" : "no") + " · HF: " + (k.hf ? "ok" : "no")));
  } catch (x) { cuerpo.replaceChildren(el("div", "muted", "Sin conexión con el Router: " + x.message)); }
}

const revisar = () => { try { instalarChat(); instalarConfig(); } catch (e) { console.warn("tools-ventana", e); } };
new MutationObserver(revisar).observe(document.body, { childList: true, subtree: true });
revisar();
