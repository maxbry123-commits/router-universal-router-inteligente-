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

const GRUPOS = [
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
    ["imagen", "Qwen Image 3.0 Pro", "Imágenes"],
    ["imagen", "Wan 2.7 Image", "Imágenes"]] },
  { titulo: "Modo recepción", recepcion: true, modelos: [
    ["voz", "Qwen TTS", "Texto a voz"],
    ["micro", "Qwen Realtime", "Voz en vivo"],
    ["texto", "Qwen ASR", "Voz a texto"]] },
];
const ICO = {  // iconos de línea monocromos (currentColor), skill Maxbry UI: sin emojis de color
  pensar: '<path d="M9 18h6M10 21h4M12 3a6 6 0 0 0-4 10.5c.7.7 1 1.5 1 2.5h6c0-1 .3-1.8 1-2.5A6 6 0 0 0 12 3z"/>', rayo: '<path d="M13 2L4 14h7l-1 8 9-12h-7z"/>',
  rapido: '<path d="M4 6l7 6-7 6zM13 6l7 6-7 6z"/>', imagen: '<rect x="3" y="4" width="18" height="16" rx="2"/><circle cx="9" cy="10" r="2"/><path d="M21 16l-5-5-9 9"/>',
  voz: '<path d="M4 9v6h4l5 4V5L8 9zM16 9a4 4 0 0 1 0 6M18.5 6.5a8 8 0 0 1 0 11"/>', micro: '<rect x="9" y="3" width="6" height="11" rx="3"/><path d="M5 11a7 7 0 0 0 14 0M12 18v3"/>', texto: '<path d="M4 6h16M4 12h16M4 18h10"/>' };
const slug = (t) => t.toLowerCase().normalize("NFD").replace(/[\u0300-\u036f]/g, "").replace(/[^a-z0-9]+/g, "-").replace(/^-|-$/g, "");
window.RIU_SELECTOR_QWEN.modelos = GRUPOS.flatMap((g) => g.modelos.map((m) => ({ modelo_id_slug: slug(m[1]), label: m[1], grupo: g.titulo })));

export function conectarSelectorModelos(ctx) {
  const { q, chat, tell, guardar } = ctx;
  const pill = q("#sel-nuevo"), lista = q("#sh-modelos-lista");
  const pillMvp = q("#sel-mvp"), mia = q("#modelo-ia");  // Team 5 MVP: la hoja solo se abre desde #modelo-ia (debajo del textarea)
  const pintarPill = () => {
    const s = chat().selectorQwen;
    pill.textContent = "Team qwen"; if (!pill.classList.contains("bloq")) pill.title = s ? "Team qwen · " + s.label : "Team qwen";  // el modelo elegido va en el tooltip
    if (pillMvp) { if (!pillMvp.classList.contains("bloq")) pillMvp.title = s ? "Team 5 MVP · " + s.label : "Team 5 MVP"; }
    if (mia) { mia.textContent = s ? "Modelo IA: " + s.label + " ⌄" : "Modelo IA: elegir ⌄"; mia.title = s ? "Modelo IA · " + s.label : "Elegir modelo"; mia.classList.toggle("on", !!s); }
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
    pintarPill(); pintar(); guardar();  // elegir modelo solo guarda chat().selectorQwen: NO enciende ni apaga el sistema
    q("#sh-modelos").hidden = true;
  };
  const pintar = () => {
    const s = chat().selectorQwen;
    lista.replaceChildren();
    for (const g of GRUPOS) {
      lista.append(node("h4", g.titulo, "mod-grupo-t"));
      const caja = node("div", "", "mod-grupo");
      const noTexto = g.titulo === "Imágenes" || g.recepcion;  // imagen/voz: visibles siempre; con Team 5 encendido quedan disabled (solo hay ejecutor texto)
      const mvpOn = (window.RIU_SELECTORES && window.RIU_SELECTORES.activo) === "team-5-mvp";
      for (const m of g.modelos) {
        const sel = !!(s && s.label === m[1]);
        const off = noTexto && mvpOn;
        const b = node("button", "", "mod-fila" + (sel ? " sel" : "") + (off ? " mod-off" : ""));
        b.type = "button"; b.setAttribute("aria-pressed", String(sel));
        if (off) { b.disabled = true; b.title = "no disponible en Team 5 MVP"; }
        const txt = node("span", "", "mod-txt");
        txt.append(node("b", m[1]), node("small", off ? "no disponible en Team 5 MVP" : m[2]));
        const ico = node("span", "", "mod-ico"); ico.innerHTML = '<svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">' + (ICO[m[0]] || "") + "</svg>";
        b.append(ico, txt, node("span", sel ? "✓" : "", "mod-ck"));
        if (!off) b.addEventListener("click", () => elegir(m, g));
        caja.append(b);
      }
      lista.append(caja);
    }
  };
  const conmutar = (id) => { const S = window.RIU_SELECTORES; if (!S) return; if (S.activo === id) S.apagar(); else S.encender(id); };  // pills de sistema: solo ON/OFF; la hoja de modelos la abre #modelo-ia
  pill.addEventListener("click", () => conmutar("team-qwen"));
  if (pillMvp) pillMvp.addEventListener("click", () => conmutar("team-5-mvp"));
  if (mia) mia.addEventListener("click", () => pintar());  // al abrir la hoja se repinta (check ✓ y disabled de Team 5 al dia)
  window.addEventListener("riu:selector-activo", pintar);  // encender Team 5 deshabilita imagen/voz al momento
  new MutationObserver(pintarPill).observe(q("#chat-tabs"), { childList: true, subtree: true, attributes: true });
  pintarPill();
  conectarSelectores(ctx);
}
