// chat-selector-modelos.js — "Selector Qwen": selector NUEVO, solo frontend, separado del selector de ficha "modelo ▾".
// NO llama al Router ni envía nada. Al elegir un modelo guarda la elección en el chat activo y emite el evento
// 'riu:selector-qwen' { modelo_id_slug, label, grupo, sesion }. La ficha/plugin (pendiente, ver SELECTOR-QWEN-PENDIENTES.md)
// rellenará window.RIU_SELECTOR_QWEN.enviar; mientras siga en null el chat funciona exactamente como antes.
import { node } from "./api.js";
import { conectarSelectores } from "./chat-selectores.js";  // interruptor ⏻ de los 5 selectores (solo frontend)

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
  const pintarPill = () => {
    const s = chat().selectorQwen;
    pill.textContent = "Team qwen" + (s ? " · " + s.label : "") + " ⌄";
    pill.classList.toggle("on", !!s);
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
        const b = node("button", "", "mod-fila" + (sel ? " sel" : ""));
        b.type = "button"; b.setAttribute("aria-pressed", String(sel));
        const txt = node("span", "", "mod-txt");
        txt.append(node("b", m[1]), node("small", m[2]));
        const ico = node("span", "", "mod-ico"); ico.innerHTML = '<svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">' + (ICO[m[0]] || "") + "</svg>";
        b.append(ico, txt, node("span", sel ? "✓" : "", "mod-ck"));
        b.addEventListener("click", () => elegir(m, g));
        caja.append(b);
      }
      lista.append(caja);
    }
  };
  pill.addEventListener("click", () => { pill.setAttribute("aria-expanded", String(q("#sh-modelos").hidden)); pintar(); });
  new MutationObserver(pintarPill).observe(q("#chat-tabs"), { childList: true, subtree: true, attributes: true });
  pintarPill();
  conectarSelectores(ctx);
}
