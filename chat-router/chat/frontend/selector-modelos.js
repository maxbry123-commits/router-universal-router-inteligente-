// selector-modelos.js — un solo selector guarda TODOS los selectores de modelo (NVIDIA, Groq, Team qwen, Team 5 MVP, Ask cónsil…) en una ventana.
// Fuera queda el indicador con el selector encendido y el modelo que responde (texto de .sel-resp-global, lo escribe chat-selectores.js).
// No cambia el cableado: los botones ON/OFF, ⓘ y las hojas de cada selector siguen siendo los mismos nodos, solo se mudan a la ventana.
import { api } from "./api.js";
const ICONO = '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><rect x="7" y="7" width="10" height="10" rx="2"/><path d="M10 3v4M14 3v4M10 17v4M14 17v4M3 10h4M3 14h4M17 10h4M17 14h4"/></svg>';
let hoja, btn, obs, pintar = () => {};
let modelosApi = [], catalogoCargando = false;
async function cargarModelosApi() {
  if (catalogoCargando) return;
  catalogoCargando = true;
  try {
    const res = await api("/web/v1/modelos/disponibilidad");
    if (!res?.ok || !Array.isArray(res.modelos)) return;
    modelosApi = res.modelos.filter(m => m && /^(deepseek|openai|minimax)\//.test(m.id));
    pintarCatalogo();
  } catch { /* sin catalogo: quedan como SIN VERIFICAR; no fingir DISPONIBLE */ }
  finally { catalogoCargando = false; }
}
// Catálogo unificado de MODELOS (no de agentes). Lee los estados del mismo bridge que responde.
function modelosDisponibles() {
  const f = [
    ...((window.RIU_LOCAL || {}).lista || []),
    ...((window.RIU_GROQ || {}).lista || []),
    ...((window.RIU_CONFIG || {}).modelos || []).filter(m => String(m.id || "").startsWith("nvidia/")),
    ...modelosApi,
  ];
  // Si aun no existe catalogo accesible, conservar las fichas solicitadas como SIN VERIFICAR.
  const esperados = [
    ["hf/lfm2.5-350m", "Liquid LFM2.5 350M"], ["hf/qwen2.5-coder-1.5b", "Qwen2.5 Coder 1.5B"],
    ["hf/qwen3.5-0.8b", "Qwen3.5 0.8B"], ["hf/qwen3-0.6b", "Qwen3 0.6B"],
    ["groq/qwen/qwen3.8-27b", "Qwen 3.8 Groq"],
    ["nvidia/minimaxai/minimax-m3.1-flash", "MiniMax M3.1 Flash"],
    ["nvidia/meta/muse-glimmer-30b", "Muse Glimmer 30B"],
    ["nvidia/nvidia/nemotron-3-ultra-550b-a55b", "Nemotron 3 Ultra"],
    ["nvidia/z-ai/glm-5.3", "GLM 5.3"],
    ["deepseek/deepseek-v4-pro", "DeepSeek V4 Pro"],
    ["deepseek/deepseek-flash", "DeepSeek Flash"],
    ["minimax/MiniMax-M3", "MiniMax M3"],
    ["minimax/MiniMax-M2.7", "MiniMax M2.7"],
    ["openai/gpt-5.6", "OpenAI GPT-5.6"],
    ["openai/gpt-5.5", "OpenAI GPT-5.5"],
  ];
  const vistos = new Set();
  return [...f, ...esperados.map(([id, etiqueta]) => ({ id, etiqueta, disponible: null }))]
    .filter(m => m && /^(hf\/|groq\/|nvidia\/|deepseek\/|minimax\/|openai\/)/.test(m.id) && !vistos.has(m.id) && vistos.add(m.id));
}
function pintarCatalogo() {
  if (!hoja) return;
  const select = hoja.querySelector("#modelo-unificado");
  if (!select || document.activeElement === select) return;
  const lista = modelosDisponibles();
  const opciones = lista.map(m => {
    const op = document.createElement("option");
    op.value = m.id;
    op.textContent = String(m.etiqueta || m.nombre || m.id).replace(/\s+—\s+(SIN VERIFICAR|NO CONFIGURADO|NO DISPONIBLE)$/i, "") +
      (m.disponible === false ? " · No disponible" : m.disponible === true ? "" : " · Sin verificar");
    op.disabled = m.disponible === false;
    return op;
  });
  select.replaceChildren(...opciones);
  const activo = window.RIU_SELECTORES?.activo || "";
  const elegido = activo === "groq" ? window.RIU_GROQ?.modelo
    : activo === "nvidia-groq-team" ? window.RIU_NVIDIA?.modelo
    : activo === "swe-code" ? ("hf/" + (window.RIU_SWE?.["swe-code"]?.model_id || ""))
    : activo === "swen-code-free" ? window.RIU_SWE?.["swen-code-free"]?.model_id : "";
  if (opciones.some(x => x.value === elegido)) select.value = elegido;
  else select.selectedIndex = -1; // no asumir un modelo por defecto que el Director no eligio
}
function elegirUnificado(id) {
  if (!id || !modelosDisponibles().some(m => m.id === id && m.disponible !== false)) return false;
  const selec = window.RIU_SELECTORES;
  if (id.startsWith("groq/")) {
    if (!window.RIU_GROQ?.elegir?.(id)) return false;
    selec?.encender?.("groq");
  } else if (id.startsWith("nvidia/")) {
    const c = window.RIU_CHAT?.chat?.();
    window.RIU_NVIDIA = { ...(window.RIU_NVIDIA || {}), modelo: id };
    try { localStorage.setItem("riu_nvidia_modelo", id); } catch {}
    if (c) c.ficha = id;
    selec?.encender?.("nvidia-groq-team");
  } else if (/^(deepseek|openai|minimax)\//.test(id)) {
    const s = window.RIU_SWE || (window.RIU_SWE = {});
    s["swen-code-free"] = { model_id: id, label: modelosDisponibles().find(m => m.id === id)?.nombre || id };
    try { const g = JSON.parse(localStorage.getItem("riu_swe_modelo") || "{}") || {};
      g["swen-code-free"] = id; localStorage.setItem("riu_swe_modelo", JSON.stringify(g)); } catch {}
    selec?.encender?.("swen-code-free"); // misma ruta de chat, sin activar agentes
  } else if (id.startsWith("hf/")) {
    const previo = window.RIU_SWE || (window.RIU_SWE = {});
    const real = id.slice(3), label = modelosDisponibles().find(m => m.id === id)?.etiqueta || real;
    previo["swe-code"] = { model_id: real, label };
    try {
      const v = JSON.parse(localStorage.getItem("riu_swe_modelo") || "{}") || {};
      v["swe-code"] = real; localStorage.setItem("riu_swe_modelo", JSON.stringify(v));
    } catch {}
    selec?.encender?.("swe-code");
  } else return false;
  hoja.hidden = true;
  if (btn) btn.setAttribute("aria-expanded", "false");
  pintar();
  return true;
}

function asegurarHoja() {
  if (hoja && document.body.contains(hoja)) return hoja;
  hoja = document.createElement("div");
  hoja.id = "sh-selectores"; hoja.className = "sheet"; hoja.hidden = true; hoja.setAttribute("role", "dialog"); hoja.setAttribute("aria-modal", "true"); hoja.setAttribute("aria-label", "Selector de modelos");
  hoja.innerHTML = '<div class="va-caja"><div class="row va-head"><strong>Selector de modelos</strong><button type="button" class="secondary sh-cerrar" aria-label="Cerrar">✕</button></div></div>';
  document.body.append(hoja);
  // Una sola entrada directa para locales HF, Groq y todos los NVIDIA; no altera los selectores de agentes.
  const panel = document.createElement("div"); panel.className = "api-modelos-rapido";
  const fila = document.createElement("div"); fila.className = "api-modelos-fila";
  const model = document.createElement("select"); model.id = "modelo-unificado"; model.setAttribute("aria-label", "Elegir modelo de HF, Groq o NVIDIA");
  model.addEventListener("change", () => elegirUnificado(model.value));
  const plus = document.createElement("button"); plus.type = "button"; plus.id = "anadir-api-sdk";
  plus.className = "secondary"; plus.textContent = "+ API / SDK"; plus.setAttribute("aria-label", "Añadir API key o SDK al banco cifrado");
  plus.addEventListener("click", () => {
    const b = window.RIU_BANCO_CLAVES;
    if (b?.abrir) { hoja.hidden = true; b.abrir(); }
    else {
      // El panel de configuracion carga la ventana de claves: no duplicar formularios ni guardar en el navegador.
      const pill = document.getElementById("pill-claves");
      if (pill) { hoja.hidden = true; pill.click(); }
      else { const e = document.getElementById("api-modelos-nota"); if (e) e.textContent = "Abre Configuración → Banco de claves para añadir una API / SDK."; }
    }
  });
  const texto = document.createElement("label"); texto.setAttribute("for", "modelo-unificado"); texto.textContent = "Modelo que responde · HF / Groq / NVIDIA";
  const info = document.createElement("div"); info.id = "api-modelos-nota"; info.className = "fila-desc";
  info.textContent = "Una selección, sin cambiar de proveedor automáticamente. Los agentes no intervienen.";
  fila.append(model, plus); panel.append(texto, fila, info);
  hoja.querySelector(".va-caja").append(panel);
  const cerrar = () => { if (hoja.hidden) return; hoja.hidden = true; if (btn) { btn.setAttribute("aria-expanded", "false"); btn.focus(); } };
  hoja.addEventListener("click", (e) => {
    if (e.target === hoja || e.target.closest(".sh-cerrar")) { cerrar(); return; }
    const pill = e.target.closest(".sel-pill");
    if (pill && (pill.dataset.sheet || pill.id === "sel-groq")) { hoja.hidden = true; if (btn) btn.setAttribute("aria-expanded", "false"); }
  });
  document.addEventListener("keydown", (e) => { if (e.key === "Escape") cerrar(); });
  window.RIU_SELECTOR_MODELOS = { abrir: () => btn && btn.click(), cerrar, pintar: () => pintar(), get modelosApi() { return modelosApi; } };
  return hoja;
}
function montar() {
  const sec = document.getElementById("selectores"), composer = document.getElementById("composer");
  if (!sec || !composer) return false;
  if (btn && composer.contains(btn) && sec.parentNode && sec.parentNode.classList.contains("va-caja") && sec.parentNode.parentNode && sec.parentNode.parentNode.id === "sh-selectores") return true; // evitar MutationObserver -> replaceChildren -> MutationObserver infinito
  const caja = asegurarHoja().querySelector(".va-caja");
  [...caja.querySelectorAll("#selectores")].forEach((n) => { if (n !== sec) n.remove(); });
  if (sec.parentNode !== caja) caja.append(sec);
  if (!btn || !composer.contains(btn)) {
    btn = document.createElement("button");
    btn.type = "button"; btn.id = "btn-selector-modelos"; btn.className = "pill sel-indicador"; btn.setAttribute("aria-haspopup", "dialog"); btn.setAttribute("aria-controls", "sh-selectores");
    btn.innerHTML = ICONO + '<span class="sel-ind-txt"></span><span class="sel-ind-flecha" aria-hidden="true">⌄</span>';
    composer.prepend(btn);
    btn.addEventListener("click", () => { pintarCatalogo(); cargarModelosApi(); hoja.hidden = false; btn.setAttribute("aria-expanded", "true"); const f = hoja.querySelector(".sel-on, button"); if (f) f.focus(); });
  }
  const txt = btn.querySelector(".sel-ind-txt");
  pintar = () => {
    const g = sec.querySelector(".sel-resp-global"), t = (g && g.textContent.trim()) || "Selector de modelos";
    const m = t.match(/^Ningún selector encendido: responde (.+?)(?: \(por defecto[^)]*\))?$/), r = t.match(/^Responde: (.+)$/);
    txt.textContent = m ? "Modelo: " + m[1] + " · por defecto" : r ? r[1] : t; btn.title = t + " — tocar para cambiar"; btn.setAttribute("aria-label", "Selector de modelos: " + t);
    btn.classList.toggle("on", !!(g && g.classList.contains("on")));
  };
  if (obs) obs.disconnect();
  obs = new MutationObserver(pintar);
  obs.observe(sec, { subtree: true, childList: true, characterData: true, attributes: true, attributeFilter: ["class"] });
  pintar();
  return true;
}
let intentos = 0;
const esperar = () => { if (montar() || ++intentos > 100) return; setTimeout(esperar, 100); };
if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", esperar); else esperar();
new MutationObserver(() => { montar(); }).observe(document.body, { childList: true, subtree: true });
window.addEventListener("riu:selector-activo", () => pintar());
window.addEventListener("riu:fichas", () => { pintarCatalogo(); pintar(); });
window.addEventListener("riu:selector-activo", () => pintarCatalogo());
