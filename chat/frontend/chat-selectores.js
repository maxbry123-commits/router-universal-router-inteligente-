// chat-selectores.js — panel "Selectores" (entre el chat y Control): 6 selectores, cada uno con su botón ON/OFF.
// Solo frontend: NO llama al Router ni envía nada. Solo 1 encendido a la vez: al encender uno, los demás quedan
// bloqueados (gris, deshabilitados) hasta apagarlo. Gancho para la ficha/plugin (Claude):
// window.RIU_SELECTORES { activo, selectores, consil, encender(id), apagar() } + evento 'riu:selector-activo' { activo, anterior, nombre }.
const CLAVE = "riu_selector_activo";  // sessionStorage: sobrevive a recargas en esta pestaña
const SELECTORES = [  // nombres exactos de Antonio
  { id: "nvidia-groq-team", nombre: "NVIDIA", pills: ["#sel-ngt", "#ficha"] },  // ficha NVIDIA: Glimmer / Nemotron 3 Super (Groq y NVIDIA codigo van como tools)
  { id: "groq", nombre: "Groq", pills: ["#sel-groq"] },  // modelos reales de Groq (fichas-externas.js); sin GROQ_API_KEY en el Space lo dice
  { id: "team-qwen", nombre: "Team qwen", pills: ["#sel-nuevo"] },  // los 14 modelos QwenCloud
  { id: "ask-consil-code-qwen-team", nombre: "Ask cónsil code qwen team", pills: ["#sel-cc"] },
  { id: "ask-consil-fromtend-qwen-team", nombre: "Ask consil fromtend qwen team", pills: ["#sel-cf"] },
  { id: "team-5-mvp", nombre: "Team 5 MVP", pills: ["#sel-mvp"] },  // Ficha 5: 1 modelo elegido del mismo selector que Team qwen
  { id: "mirror-ficha4-ficha5-nvidia-groq", nombre: "Mirror", pills: ["#sel-mirror"], mirror: true },  // Mirror: participa en room_debatir/chat_bots con origen room:<ficha_id>
];
const POWER = '<svg viewBox="0 0 24 24" width="15" height="15" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" aria-hidden="true"><path d="M12 3v9M6.3 6.3a8 8 0 1 0 11.4 0"/></svg>';
const DIAGRAMAS = {  // micro diagramas transversales horizontales; Ask consil Nvidia groq sigue pendiente de definición explícita
  "team-5-mvp": { sel: "#mvp-diagrama", texto: "INPUT + HISTORIAL SESIÓN + TOOLS → 1 MODELO ELEGIDO → TOOL CALL SI HACE FALTA → RESPUESTA" },
  "team-qwen": { sel: "#team-qwen-diagrama", texto: "SELECTOR 14 → 1 MODELO → EJECUTA → SALIDA → PROPONE AUDITORÍA FORENSE X-RAY (código fuente + input block verbatim) → «ok» → [Qwen 3.7 Flash | DeepSeek V4 Flash | Qwen 3.8 Flash] VERIFICACIÓN CRUZADA A LA VEZ: REVISAN, REFACTORIZAN, RESUELVEN GAPS → ↺ LOOP" },
  "ask-consil-code-qwen-team": { sel: "#consil-code-diagrama", texto: "12 GOALS ENTRADA → [DeepSeek V4 Pro | GLM 5.2 | Qwen 3.7 Max | Qwen 3.8 Max] ANALIZAN Y PROPONEN EN PARALELO → Qwen 3.8 Max DECIDE Y EJECUTA → [GLM 5.2 | Qwen v4 Max] REVISAN, AUDITAN Y REFACTORIZAN → 12 GOALS SALIDA → PROPONE AUDITORÍA FORENSE X-RAY (código fuente + input block verbatim) → «ok» → [Qwen 3.7 Flash | DeepSeek V4 Flash | Qwen 3.8 Flash] VERIFICACIÓN CRUZADA A LA VEZ: REVISAN, REFACTORIZAN, RESUELVEN GAPS → ↺ LOOP" },
  "ask-consil-fromtend-qwen-team": { sel: "#consil-frontend-diagrama", texto: "12 GOALS ENTRADA → [DeepSeek V4 Pro | GLM 5.2 | Qwen 3.7 Max | Qwen 3.8 Max] ANALIZAN Y PROPONEN EN PARALELO → Qwen 3.8 Max DECIDE Y EJECUTA → [GLM 5.2 | Qwen 3.8 Max] REVISAN, AUDITAN Y REFACTORIZAN → 12 GOALS SALIDA → PROPONE AUDITORÍA FORENSE X-RAY (código fuente + input block verbatim) → «ok» → [Qwen 3.7 Flash | DeepSeek V4 Flash | Qwen 3.8 Flash] VERIFICACIÓN CRUZADA A LA VEZ: REVISAN, REFACTORIZAN, RESUELVEN GAPS → ↺ LOOP" },
  "mirror-ficha4-ficha5-nvidia-groq": { sel: "#mirror-diagrama", texto: "MIRROR ORIGEN room:<ficha_id> → PARTICIPANTE POOL room_debatir/chat_bots → DEBATE/CHAT CON MODELOS FICHA4/FICHA5/NVIDIA/GROQ → SALIDA INTEGRADA" },
};
const CONSIL_MODELOS = {  // fichas 2 y 3: orden y papeles tal cual el input block del Director (2026-10-10)
  "ask-consil-code-qwen-team": [
    ["DeepSeek V4 Pro", "Arquitectura · analiza, propone y revisa · paralelo"],
    ["GLM 5.2", "Arquitectura · analiza, propone y revisa · paralelo · salida: revisa, audita y refactoriza"],
    ["Qwen 3.7 Max", "Arquitectura · analiza, propone y revisa · paralelo"],
    ["Qwen 3.8 Max", "Arquitectura · analiza, propone y revisa · paralelo · decide y ejecuta"],
  ],
  "ask-consil-fromtend-qwen-team": [
    ["DeepSeek V4 Pro", "Arquitectura · analiza, propone y revisa · paralelo"],
    ["GLM 5.2", "Arquitectura · analiza, propone y revisa · paralelo · salida: revisa, audita y refactoriza"],
    ["Qwen 3.7 Max", "Arquitectura · analiza, propone y revisa · paralelo"],
    ["Qwen 3.8 Max", "Arquitectura · analiza, propone y revisa · paralelo · decide y ejecuta"],
  ],
};
const MIRROR_FICHAS = {  // mirror: fichas que participan como origen room:<ficha_id>
  "mirror-ficha4-ficha5-nvidia-groq": [
    ["ficha4", "Ficha 4 · mirror participante · origen room:ficha4"],
    ["ficha5", "Ficha 5 · mirror participante · origen room:ficha5"],
    ["nvidia", "NVIDIA · mirror participante · origen room:nvidia"],
    ["groq", "Groq · mirror participante · origen room:groq"],
  ],
};
const INFO = '<svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" aria-hidden="true"><circle cx="12" cy="12" r="9"/><path d="M12 11v6M12 7.5v.5"/></svg>';
const pintarDiagrama = (caja, texto) => {  // pasos en línea, desplazable en horizontal; el texto queda exacto (" → " entre pasos)
  caja.replaceChildren(); caja.title = texto; caja.classList.add("lleno");
  const pista = () => caja.classList.toggle("mas", caja.scrollLeft + caja.clientWidth < caja.scrollWidth - 2);  // pista visual: hay más a la derecha
  if (!caja.dataset.pista) { caja.dataset.pista = "1"; caja.addEventListener("scroll", pista, { passive: true }); new ResizeObserver(pista).observe(caja); }
  texto.split(" → ").forEach((paso, i) => {
    if (i) { const f = document.createElement("span"); f.className = "dg-flecha"; f.textContent = " → "; caja.append(f); }
    const p = document.createElement("span"); p.className = "dg-paso"; p.textContent = paso; caja.append(p);
  });
};
const svg = (p) => '<svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">' + p + "</svg>";
const ICO_F = {  // iconos de línea para las hojas con el mismo diseño que Team qwen
  pensar: '<path d="M9 18h6M10 21h4M12 3a6 6 0 0 0-4 10.5c.7.7 1 1.5 1 2.5h6c0-1 .3-1.8 1-2.5A6 6 0 0 0 12 3z"/>',
  flecha: '<path d="M4 12h15M13 6l6 6-6 6"/>',
  lupa: '<circle cx="11" cy="11" r="6"/><path d="M20 20l-4.5-4.5"/>',
  chip: '<rect x="6" y="6" width="12" height="12" rx="2"/><path d="M9 2v4M15 2v4M9 18v4M15 18v4M2 9h4M2 15h4M18 9h4M18 15h4"/>',
  pendiente: '<circle cx="12" cy="12" r="9"/><path d="M12 7v5l3 2"/>',
  mirror: '<path d="M4 12h16M12 4v16M7 7l10 10M17 7L7 17"/>',
};
const icoFicha = (id) => id.startsWith("ask-consil") ? "pensar" : id === "motor-descarga" ? "flecha" : id.startsWith("motor-") ? "lupa" : id.startsWith("mirror") ? "mirror" : "chip";  // equivalente de línea del emoji original
const limpia = (t) => t.replace(/[\p{Extended_Pictographic}\uFE0F\u200D]/gu, "").trim();
const el = (tag, cls, txt) => { const e = document.createElement(tag); if (cls) e.className = cls; if (txt != null) e.textContent = txt; return e; };
const decorarFichas = (lista) => {  // Nvidia groq team: las MISMAS fichas reales de RIU_CONFIG, mismo orden; no inventa proveedores
  const filas = [...lista.children].filter((e) => e.matches("button.fila"));
  if (!filas.length) return;
  const mods = window.RIU_CONFIG?.modelos || [], caja = el("div", "mod-grupo");
  for (const r of filas) {
    const nom = r.querySelector(".fila-nom"), ck = r.querySelector(".fila-check");
    if (!nom || !ck) continue;
    const id = r.dataset.id || "";
    const mod = mods.find((m) => m.id === id);
    if (!mod) continue;
    const prov = mod.proveedor || "pipeline";
    const ico = el("span", "fila-ico");
    ico.innerHTML = svg(ICO_F[icoFicha(id)] || ICO_F.chip);
    nom.prepend(ico);
    const tag = el("span", "fila-tag", prov);
    nom.append(tag);
  }
};
const FAST = /^(team-qwen|ask-consil-code-qwen-team|ask-consil-fromtend-qwen-team)$/;
const filas = () => {  // panel Selectores del chat: ⓘ diagrama, ⚡ respuesta rápida, ON/OFF y «Modelo: …» en cada fila; solo uno encendido a la vez
  const lista = document.getElementById("sel-power");
  if (!lista || lista.dataset.riuFilas) return;
  lista.dataset.riuFilas = "1";
  const global = el("div", "sel-resp-global"), act = () => sessionStorage.getItem(CLAVE) || "";
  lista.before(global);
  const fichaEt = () => { try { const f = window.RIU_CHAT.chat().ficha, m = (window.RIU_CONFIG.modelos || []).find((x) => x.id === f); return m ? m.etiqueta : f || "NVIDIA"; } catch (e) { return "NVIDIA"; } };  // modelo Groq/NVIDIA elegido en la hoja de fichas
  const modelo = (s) => s.id === "groq" ? ((window.RIU_GROQ || {}).modelo || (window.RIU_GROQ || {}).aviso || "elige un modelo") : s.id === "nvidia-groq-team" ? fichaEt() : s.id === "team-qwen" || s.id === "team-5-mvp" ? ((window.RIU_SELECTOR_QWEN || {}).seleccion || {}).label || "Qwen 3.8 Max" : (CONSIL_MODELOS[s.id] || []).map((m) => m[0]).join(" · ") || s.nombre;
  const fila = (s) => lista.querySelector('.sel-fila[data-selector="' + s.id + '"]');
  const refrescar = () => {
    SELECTORES.forEach((s) => {
      const f = fila(s); if (!f) return;
      const on = act() === s.id, b = f.querySelector(".sel-on");
      f.classList.toggle("activa", on); b.classList.toggle("on", on); b.disabled = false; b.title = on ? "Apagar " + s.nombre : "Encender " + s.nombre + " (apaga el que esté encendido)"; b.setAttribute("aria-pressed", String(on));
      b.lastChild.textContent = on ? "ON" : "OFF"; f.querySelector(".sel-resp").textContent = "Modelo: " + modelo(s);
    });
    const a = SELECTORES.find((s) => s.id === act());
    global.textContent = a ? "Responde: " + a.nombre + " · " + modelo(a) : "Ningún selector encendido: responde " + (/^nv-/.test(((window.RIU_CHAT && window.RIU_CHAT.chat()) || {}).ficha || "nv-") ? "Qwen 3.8 Max (por defecto del Router)" : fichaEt()); global.classList.toggle("on", !!a);
    window.dispatchEvent(new CustomEvent("riu:selector-activo", { detail: { activo: act(), anterior: "", nombre: a ? a.nombre : "" } }));
  };
  SELECTORES.filter((s) => !s.mirror).forEach((s) => {
    const f = fila(s); if (!f) return;
    if (DIAGRAMAS[s.id]) {
      const i = el("button", "sel-info"), d = el("div", "sel-diagrama consil-diagrama"); i.type = "button"; i.setAttribute("aria-label", "Cómo funciona " + s.nombre); i.innerHTML = svg('<circle cx="12" cy="12" r="9"/><path d="M12 11v5M12 8h.01"/>'); d.hidden = true;
      pintarDiagrama(d, DIAGRAMAS[s.id].texto); i.onclick = () => { d.hidden = !d.hidden; i.classList.toggle("abierto", !d.hidden); }; f.append(i); f.append(d);
    }
    if (FAST.test(s.id)) {
      const z = el("button", "sel-fast"); z.type = "button"; z.setAttribute("aria-label", "Respuesta rápida"); z.dataset.selector = s.id; z.innerHTML = svg('<path d="M13 2L4 14h7l-1 8 9-12h-7z"/>');
      z.onclick = () => { if (window.__riuFastH) window.__riuFastH(); }; f.append(z);
    }
    const b = el("button", "sel-on"); b.type = "button"; b.setAttribute("aria-label", "ON/OFF " + s.nombre); b.innerHTML = POWER + "<span>OFF</span>";
    b.onclick = () => { if (act() === s.id) sessionStorage.removeItem(CLAVE); else sessionStorage.setItem(CLAVE, s.id); refrescar(); };
    f.append(b, el("p", "sel-resp"));
  });
  window.addEventListener("riu:fast-reply", (e) => lista.querySelectorAll(".sel-fast").forEach((z) => { z.classList.toggle("on", !!e.detail.on); z.setAttribute("aria-pressed", String(!!e.detail.on)); }));
  window.RIU_SELECTORES = { get activo() { return act(); }, selectores: SELECTORES, consil: CONSIL_MODELOS, mirror: MIRROR_FICHAS, refrescar,
    encender(id) { sessionStorage.setItem(CLAVE, id); refrescar(); }, apagar() { sessionStorage.removeItem(CLAVE); refrescar(); } };
  refrescar();
};
const init = () => {
  if (!document.getElementById("selectores-panel")) return filas();
  const panel = document.getElementById("selectores-panel");
  if (!panel || panel.dataset.riuSelectoresInit) return;
  panel.dataset.riuSelectoresInit = "1";
  const activo = sessionStorage.getItem(CLAVE) || "";
  const botones = [];
  SELECTORES.forEach((s) => {
    const btn = el("button", "sel-btn", "");
    btn.dataset.id = s.id;
    btn.title = s.nombre;
    const ico = el("span", "sel-ico");
    ico.innerHTML = POWER;
    btn.append(ico);
    const lbl = el("span", "sel-nom", s.nombre);
    btn.append(lbl);
    if (s.mirror) {
      const badge = el("span", "sel-badge", "MIRROR");
      btn.append(badge);
    }
    btn.addEventListener("click", () => toggle(s.id));
    panel.append(btn);
    botones.push(btn);
  });
  const actualizar = () => {
    const act = sessionStorage.getItem(CLAVE) || "";
    botones.forEach((b) => {
      const on = b.dataset.id === act;
      b.classList.toggle("on", on);
      b.disabled = false;  // tocar otro selector lo enciende y apaga el anterior (solo uno a la vez)
      b.setAttribute("aria-pressed", String(on));
    });
    const diagBox = document.getElementById("selector-diagrama");
    if (diagBox) {
      const d = DIAGRAMAS[act];
      if (d) {
        const caja = document.querySelector(d.sel);
        if (caja) pintarDiagrama(caja, d.texto);
      }
    }
    window.dispatchEvent(new CustomEvent("riu:selector-activo", { detail: { activo: act, anterior: "", nombre: SELECTORES.find((s) => s.id === act)?.nombre || "" } }));
  };
  window.RIU_SELECTORES = {
    get activo() { return sessionStorage.getItem(CLAVE) || ""; },
    selectores: SELECTORES,
    consil: CONSIL_MODELOS,
    mirror: MIRROR_FICHAS,
    encender(id) { sessionStorage.setItem(CLAVE, id); actualizar(); },
    apagar() { sessionStorage.removeItem(CLAVE); actualizar(); },
  };
  if (activo) sessionStorage.setItem(CLAVE, activo);
  actualizar();
};
export const conectarSelectores = init;
const toggle = (id) => {
  const actual = sessionStorage.getItem(CLAVE) || "";
  if (actual === id) {
    sessionStorage.removeItem(CLAVE);
  } else {
    sessionStorage.setItem(CLAVE, id);
  }
  const act = sessionStorage.getItem(CLAVE) || "";
  const botones = document.querySelectorAll(".sel-btn");
  botones.forEach((b) => {
    const on = b.dataset.id === act;
    b.classList.toggle("on", on);
    b.disabled = false;
    b.setAttribute("aria-pressed", String(on));
  });
  const diagBox = document.getElementById("selector-diagrama");
  if (diagBox) {
    const d = DIAGRAMAS[act];
    if (d) {
      const caja = document.querySelector(d.sel);
      if (caja) pintarDiagrama(caja, d.texto);
    }
  }
  window.dispatchEvent(new CustomEvent("riu:selector-activo", { detail: { activo: act, anterior: actual, nombre: SELECTORES.find((s) => s.id === act)?.nombre || "" } }));
};
if (document.readyState === "loading") {
  document.addEventListener("DOMContentLoaded", init);
} else {
  init();
}
