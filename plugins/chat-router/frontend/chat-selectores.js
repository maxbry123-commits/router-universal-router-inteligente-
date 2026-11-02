// chat-selectores.js — panel "Selectores" (entre el chat y Control): 7 selectores, cada uno con su botón ON/OFF.
// Solo frontend: NO llama al Router ni envía nada. Solo 1 encendido a la vez: al encender uno, los demás quedan
// bloqueados (gris, deshabilitados) hasta apagarlo. Gancho para la ficha/plugin (Claude):
// window.RIU_SELECTORES { activo, selectores, consil, encender(id), apagar() } + evento 'riu:selector-activo' { activo, anterior, nombre }.
const CLAVE = "riu_selector_activo";  // sessionStorage: sobrevive a recargas en esta pestaña
const SELECTORES = [  // nombres exactos de Antonio
  { id: "nvidia-groq-team", nombre: "NVIDIA", pills: ["#sel-ngt", "#ficha"] },
  { id: "team-qwen", nombre: "Team qwen", pills: ["#sel-nuevo"] },
  { id: "ask-consil-code-qwen-team", nombre: "Ask cónsil code qwen team", pills: ["#sel-cc"] },
  { id: "ask-consil-fromtend-qwen-team", nombre: "Ask consil fromtend qwen team", pills: ["#sel-cf"] },
  { id: "team-5-mvp", nombre: "Team 5 MVP", pills: ["#sel-mvp"] },
  { id: "mirror-ficha4-ficha5-nvidia-groq", nombre: "Mirror", pills: ["#sel-mirror"], mirror: true },
  { id: "swe-code-free", nombre: "SWE CODE free", pills: ["#sel-swe"], swe: true },
];
const POWER = '<svg viewBox="0 0 24 24" width="15" height="15" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" aria-hidden="true"><path d="M12 3v9M6.3 6.3a8 8 0 1 0 11.4 0"/></svg>';
const DIAGRAMAS = {
  "team-5-mvp": { sel: "#mvp-diagrama", texto: "INPUT + HISTORIAL SESIÓN + TOOLS → 1 MODELO ELEGIDO → TOOL CALL SI HACE FALTA → RESPUESTA" },
  "team-qwen": { sel: "#team-qwen-diagrama", texto: "SELECTOR 14 → 1 MODELO → EJECUTA → SALIDA → PROPONE AUDITORÍA FORENSE X-RAY (código fuente + input block verbatim) → «ok» → [Qwen 3.7 Flash | DeepSeek V4 Flash | Qwen 3.8 Flash] VERIFICACIÓN CRUZADA A LA VEZ: REVISAN, REFACTORIZAN, RESUELVEN GAPS → ↺ LOOP" },
  "ask-consil-code-qwen-team": { sel: "#consil-code-diagrama", texto: "12 GOALS ENTRADA → [DeepSeek V4 Pro | GLM 5.2 | Qwen 3.7 Max | Qwen 3.8 Max] ANALIZAN Y PROPONEN EN PARALELO → Qwen 3.8 Max DECIDE Y EJECUTA → [GLM 5.2 | Qwen v4 Max] REVISAN, AUDITAN Y REFACTORIZAN → 12 GOALS SALIDA → PROPONE AUDITORÍA FORENSE X-RAY (código fuente + input block verbatim) → «ok» → [Qwen 3.7 Flash | DeepSeek V4 Flash | Qwen 3.8 Flash] VERIFICACIÓN CRUZADA A LA VEZ: REVISAN, REFACTORIZAN, RESUELVEN GAPS → ↺ LOOP" },
  "ask-consil-fromtend-qwen-team": { sel: "#consil-frontend-diagrama", texto: "12 GOALS ENTRADA → [DeepSeek V4 Pro | GLM 5.2 | Qwen 3.7 Max | Qwen 3.8 Max] ANALIZAN Y PROPONEN EN PARALELO → Qwen 3.8 Max DECIDE Y EJECUTA → [GLM 5.2 | Qwen 3.8 Max] REVISAN, AUDITAN Y REFACTORIZAN → 12 GOALS SALIDA → PROPONE AUDITORÍA FORENSE X-RAY (código fuente + input block verbatim) → «ok» → [Qwen 3.7 Flash | DeepSeek V4 Flash | Qwen 3.8 Flash] VERIFICACIÓN CRUZADA A LA VEZ: REVISAN, REFACTORIZAN, RESUELVEN GAPS → ↺ LOOP" },
  "mirror-ficha4-ficha5-nvidia-groq": { sel: "#mirror-diagrama", texto: "MIRROR ORIGEN room:<ficha_id> → PARTICIPANTE POOL room_debatir/chat_bots → DEBATE/CHAT CON MODELOS FICHA4/FICHA5/NVIDIA/GROQ → SALIDA INTEGRADA" },
  "swe-code-free": { sel: "#swe-diagrama", texto: "INPUT → SWE CODE free ON → OPENCLAW EJECUTA → SI FALLA: ANTICIPA (timeout/red/429/401) → REINTENTO 3x BACKOFF → SI SIGUE FALLANDO: AUTO-REPARAR (/health) → RESPUESTA O ALERTA" },
};
const CONSIL_MODELOS = {
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
const MIRROR_FICHAS = {
  "mirror-ficha4-ficha5-nvidia-groq": [
    ["ficha4", "Ficha 4 · mirror participante · origen room:ficha4"],
    ["ficha5", "Ficha 5 · mirror participante · origen room:ficha5"],
    ["nvidia", "NVIDIA · mirror participante · origen room:nvidia"],
    ["groq", "Groq · mirror participante · origen room:groq"],
  ],
};
const INFO = '<svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" aria-hidden="true"><circle cx="12" cy="12" r="9"/><path d="M12 11v6M12 7.5v.5"/></svg>';
const pintarDiagrama = (caja, texto) => {
  caja.replaceChildren(); caja.title = texto; caja.classList.add("lleno");
  const pista = () => caja.classList.toggle("mas", caja.scrollLeft + caja.clientWidth < caja.scrollWidth - 2);
  if (!caja.dataset.pista) { caja.dataset.pista = "1"; caja.addEventListener("scroll", pista, { passive: true }); new ResizeObserver(pista).observe(caja); }
  texto.split(" → ").forEach((paso, i) => {
    if (i) { const f = document.createElement("span"); f.className = "dg-flecha"; f.textContent = " → "; caja.append(f); }
    const p = document.createElement("span"); p.className = "dg-paso"; p.textContent = paso; caja.append(p);
  });
};
const svg = (p) => '<svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">' + p + "</svg>";
const ICO_F = {
  pensar: '<path d="M9 18h6M10 21h4M12 3a6 6 0 0 0-4 10.5c.7.7 1 1.5 1 2.5h6c0-1 .3-1.8 1-2.5A6 6 0 0 0 12 3z"/>',
  flecha: '<path d="M4 12h15M13 6l6 6-6 6"/>',
  lupa: '<circle cx="11" cy="11" r="6"/><path d="M20 20l-4.5-4.5"/>',
  chip: '<rect x="6" y="6" width="12" height="12" rx="2"/><path d="M9 2v4M15 2v4M9 18v4M15 18v4M2 9h4M2 15h4M18 9h4M18 15h4"/>',
  pendiente: '<circle cx="12" cy="12" r="9"/><path d="M12 7v5l3 2"/>',
  mirror: '<path d="M4 12h16M12 4v16M7 7l10 10M17 7L7 17"/>',
  swe: '<path d="M4 6h16M4 12h16M4 18h10"/>',
};
const icoFicha = (id) => id.startsWith("ask-consil") ? "pensar" : id === "motor-descarga" ? "flecha" : id.startsWith("motor-") ? "lupa" : id.startsWith("mirror") ? "mirror" : id === "swe-code-free" ? "swe" : "chip";
const limpia = (t) => t.replace(/[\p{Extended_Pictographic}\uFE0F\u200D]/gu, "").trim();
const el = (tag, cls, txt) => { const e = document.createElement(tag); if (cls) e.className = cls; if (txt != null) e.textContent = txt; return e; };
const decorarFichas = (lista) => {
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
const init = () => {
  const panel = document.getElementById("selectores-panel");
  if (!panel) return;
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
    if (s.swe) {
      const badge = el("span", "sel-badge", "SWE");
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
      b.disabled = act && !on;
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
    b.disabled = act && !on;
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
