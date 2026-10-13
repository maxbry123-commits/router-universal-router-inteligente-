// chat-selector-modelos.js — "Selector Qwen": selector NUEVO, solo frontend, separado del selector de ficha "modelo ▾".
// NO llama al Router ni envía nada. Al elegir un modelo guarda la elección en el chat activo y emite el evento
// 'riu:selector-qwen' { modelo_id_slug, label, grupo, sesion }. La ficha/plugin (pendiente, ver SELECTOR-QWEN-PENDIENTES.md)
// rellenará window.RIU_SELECTOR_QWEN.enviar; mientras siga en null el chat funciona exactamente como antes.
import { node } from "./api.js";
import { conectarSelectores } from "./chat-selectores.js";  // interruptor ON/OFF de los 5 selectores (solo frontend)

window.RIU_SELECTOR_QWEN = window.RIU_SELECTOR_QWEN || {
  enviar: null,      // gancho para la ficha/plugin: async ({ modelo_id_slug, mensaje, sesion }) => respuesta. null = sin cablear
  seleccion: null,   // última elección { modelo_id_slug, label, grupo }
  modelos: [],       // catálogo visible (slugs de interfaz, NO son ids de proveedor)
};

let GRUPOS = [
  { titulo: "Qwen", modelos: [
    ["pensar", "Qwen 3.8 Max", "Código complejo"],
    ["rayo", "Qwen 3.8 Flash", "Código rápido"],
    ["pensar", "Qwen 3.7 Max", "Razonamiento"],
    ["rayo", "Qwen 3.7 Plus", "Código + visión"],
    ["rapido", "Qwen 3.6 Flash", "Rápido / económico"]] },
  { titulo: "DeepSeek", modelos: [
    ["pensar", "DeepSeek V4 Pro", "Código complejo"],
    ["pensar", "DeepSeek V4 Pro 0813", "Máxima profundidad"],
    ["rayo", "DeepSeek V4 Flash", "Código rápido"]] },
  { titulo: "GLM", modelos: [
    ["pensar", "GLM 5.2", "Código + agentes"]] },
  { titulo: "Imágenes", modelos: [
    ["imagen", "Qwen Image 3.0 Pro", "Imágenes", "imagen"],
    ["imagen", "Wan 2.7 Image", "Imágenes", "imagen"]] },
  { titulo: "Modo recepción", recepcion: true, modelos: [
    ["voz", "Qwen TTS", "Texto a voz", "voz"],
    ["micro", "Qwen Realtime", "Voz en vivo", "voz"],
    ["texto", "Qwen ASR", "Voz a texto", "voz"]] },
];
const ICO = {  // iconos de línea monocromos (currentColor), skill Maxbry UI: sin emojis de color
  pensar: '<path d="M9 18h6M10 21h4M12 3a6 6 0 0 0-4 10.5c.7.7 1 1.5 1 2.5h6c0-1 .3-1.8 1-2.5A6 6 0 0 0 12 3z"/>', rayo: '<path d="M13 2L4 14h7l-1 8 9-12h-7z"/>',
  rapido: '<path d="M4 6l7 6-7 6zM13 6l7 6-7 6z"/>', imagen: '<rect x="3" y="4" width="18" height="16" rx="2"/><circle cx="9" cy="10" r="2"/><path d="M21 16l-5-5-9 9"/>',
  voz: '<path d="M4 9v6h4l5 4V5L8 9zM16 9a4 4 0 0 1 0 6M18.5 6.5a8 8 0 0 1 0 11"/>', micro: '<rect x="9" y="3" width="6" height="11" rx="3"/><path d="M5 11a7 7 0 0 0 14 0M12 18v3"/>', texto: '<path d="M4 6h16M4 12h16M4 18h10"/>' };
const slug = (t) => t.toLowerCase().normalize("NFD").replace(/[\u0300-\u036f]/g, "").replace(/[^a-z0-9]+/g, "-").replace(/^-|-$/g, "");
window.RIU_SELECTOR_QWEN.modelos = GRUPOS.flatMap((g) => g.modelos.map((m) => ({ modelo_id_slug: slug(m[1]), label: m[1], grupo: g.titulo })));

// fuente unica del catalogo: el selector de la Ficha 1 (ficha1-modelos.json) expuesto por fichas_qwen; si falla, queda la copia local
const cargarCatalogoF1 = async () => {
  try {
    const r = await fetch("/plugins/fichas_qwen/call/", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ action: "selector" }) });
    const d = await r.json();
    const sel = d && d.selector;
    if (!Array.isArray(sel) || !sel.length) return false;
    const ico = (m) => m.tipo === "imagen" ? "imagen" : m.tipo === "voz" ? (/realtime/i.test(m.nombre) ? "micro" : /asr/i.test(m.nombre) ? "texto" : "voz") : (/flash|plus/i.test(m.nombre) ? "rayo" : /3\.6/i.test(m.nombre) ? "rapido" : "pensar");
    const grp = (m) => m.tipo === "imagen" ? "Imágenes" : m.tipo === "voz" ? "Modo recepción" : m.nombre.split(" ")[0];
    const gs = {};
    for (const m of sel) { const t = grp(m); (gs[t] = gs[t] || []).push([ico(m), m.nombre, m.rol + (m.tipo !== "texto" ? " · " + m.tipo : ""), m.tipo]); }
    GRUPOS = Object.entries(gs).map(([titulo, modelos]) => ({ titulo, modelos }));
    window.RIU_SELECTOR_QWEN.modelos = GRUPOS.flatMap((g) => g.modelos.map((m) => ({ modelo_id_slug: slug(m[1]), label: m[1], grupo: g.titulo })));
    return true;
  } catch (e) { return false; }
};

export function conectarSelectorModelos(ctx) {
  const { q, chat, tell, guardar } = ctx;
  const pill = q("#sel-nuevo"), lista = q("#sh-modelos-lista");
  const pillMvp = q("#sel-mvp");  // Team 5 MVP: misma hoja y mismo catalogo; la ruta de envio es otra (ficha_qwen=5)
  let hojaOrigen = "team-qwen";  // quien abrio la hoja de modelos: al elegir, se enciende ESE selector y no el otro
  const pintarPill = () => {
    const s = chat().selectorQwen;
    pill.textContent = "Team qwen ⌄"; if (!pill.classList.contains("bloq")) pill.title = s ? "Team qwen · " + s.label : "Team qwen";  // el modelo elegido va en el tooltip
    pill.classList.toggle("on", !!s);
    if (pillMvp) { if (!pillMvp.classList.contains("bloq")) pillMvp.title = s ? "Team 5 MVP · " + s.label : "Team 5 MVP"; pillMvp.classList.toggle("on", !!s); }
    if (window.RIU_SELECTORES && window.RIU_SELECTORES.refrescar) window.RIU_SELECTORES.refrescar();
    window.RIU_SELECTOR_QWEN.seleccion = s ? { modelo_id_slug: s.modelo_id_slug, label: s.label, grupo: s.grupo, sesion: chat().sesion } : null;
  };
  const elegir = (m, g) => {
    const c = chat();
    const ya = c.selectorQwen && c.selectorQwen.label === m[1];
    c.selectorQwen = ya ? null : { icono: m[0], modelo_id_slug: slug(m[1]), label: m[1], grupo: g.titulo };
    const det = c.selectorQwen ? { modelo_id_slug: c.selectorQwen.modelo_id_slug, label: m[1], grupo: g.titulo, sesion: c.sesion } : null;
    window.RIU_SELECTOR_QWEN.seleccion = det;
    window.dispatchEvent(new CustomEvent("riu:selector-qwen", { detail: det }));
    pintarPill(); pintar(); guardar();
    const dest = hojaOrigen === "team-5-mvp" ? "team-5-mvp" : "team-qwen";
    const SEL = window.RIU_SELECTORES; if (SEL && SEL.encender) { if (c.selectorQwen) SEL.encender(dest); else if (SEL.activo === dest) SEL.apagar(); }  // elegir un modelo = el selector que abrio la hoja responde
    q("#sh-modelos").hidden = true;
  };
  const pintar = () => {
    const s = chat().selectorQwen;
    lista.replaceChildren();
    for (const g of GRUPOS) {
      lista.append(node("h4", g.titulo, "mod-grupo-t"));
      const caja = node("div", "", "mod-grupo");
      for (const m of g.modelos) {
        const sel = !!(s && s.label === m[1]);
        const noMvp = hojaOrigen === "team-5-mvp" && m[3] && m[3] !== "texto";  // Team 5 solo ejecuta texto hoy: el resto se muestra marcado, nunca se envia a otro modelo
        const b = node("button", "", "mod-fila" + (sel ? " sel" : "") + (noMvp ? " no-mvp" : ""));
        b.type = "button"; b.setAttribute("aria-pressed", String(sel));
        if (noMvp) { b.disabled = true; b.title = m[1] + " es " + m[3] + ": no disponible en MVP"; }
        const txt = node("span", "", "mod-txt");
        txt.append(node("b", m[1]), node("small", m[2] + (noMvp ? " — no disponible en MVP" : "")));
        const ico = node("span", "", "mod-ico"); ico.innerHTML = '<svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">' + (ICO[m[0]] || "") + "</svg>";
        b.append(ico, txt, node("span", sel ? "✓" : "", "mod-ck"));
        if (!noMvp) b.addEventListener("click", () => elegir(m, g));
        caja.append(b);
      }
      lista.append(caja);
    }
  };
  const SEL_GLOBAL = () => window.RIU_SELECTORES;
  pill.addEventListener("click", () => { const R = SEL_GLOBAL(); if (R && R.encender && R.activo !== "team-qwen") R.encender("team-qwen"); });
  if (pillMvp) pillMvp.addEventListener("click", () => { const R = SEL_GLOBAL(); if (R && R.encender && R.activo !== "team-5-mvp") R.encender("team-5-mvp"); });
  // #modelo-ia: unico punto de entrada al catalogo (#sh-modelos / mismo GRUPOS / selectorQwen); va debajo del input
  const pillMIA = q("#modelo-ia");
  const actualizarMIA = () => {
    if (!pillMIA) return;
    const R = SEL_GLOBAL(), act = R && R.activo, s = chat().selectorQwen;
    const consil = act === "ask-consil-code-qwen-team" || act === "ask-consil-fromtend-qwen-team";
    const nvidia = act === "nvidia-groq-team" || act === "ask-consil-nvidia-groq";
    if (consil) { pillMIA.textContent = "Modelos definidos por la ficha"; pillMIA.disabled = true; pillMIA.removeAttribute("data-sheet"); }
    else if (nvidia) { pillMIA.textContent = "Modelo IA: " + (q("#ficha") && q("#ficha").dataset.ficha ? q("#ficha").dataset.ficha : "Nvidia groq team") + " v"; pillMIA.disabled = false; pillMIA.dataset.sheet = "sh-ficha"; }
    else { pillMIA.textContent = "Modelo IA: " + (s ? s.label : "elegir") + " v"; pillMIA.disabled = false; pillMIA.dataset.sheet = "sh-modelos"; }
  };
  if (pillMIA) {
    pillMIA.addEventListener("click", () => {
      const R = SEL_GLOBAL();
      hojaOrigen = R && R.activo === "team-5-mvp" ? "team-5-mvp" : "team-qwen";  // el modelo elegido enciende el sistema activo, nunca el otro
      const sh = q("#" + (pillMIA.dataset.sheet || "sh-modelos"));
      if (sh) pillMIA.setAttribute("aria-expanded", String(sh.hidden));
      pintar();
    });
  }
  window.addEventListener("riu:selector-activo", actualizarMIA);
  new MutationObserver(actualizarMIA).observe(q("#chat-tabs"), { childList: true, subtree: true, attributes: true });
  actualizarMIA();
  cargarCatalogoF1().then((ok) => { if (ok) { pintarPill(); pintar(); } });  // el catalogo real de la Ficha 1 sustituye la copia local
  new MutationObserver(pintarPill).observe(q("#chat-tabs"), { childList: true, subtree: true, attributes: true });
  pintarPill();
  conectarSelectores(ctx);
}
