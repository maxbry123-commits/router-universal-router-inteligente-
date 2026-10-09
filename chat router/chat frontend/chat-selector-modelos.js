// chat-selector-modelos.js — "Selector Qwen": selector NUEVO, solo frontend, separado del selector de ficha "modelo ▾".
// NO llama al Router ni envía nada. Al elegir un modelo guarda la elección en el chat activo y emite el evento
// 'riu:selector-qwen' { modelo_id_slug, label, grupo, sesion }. La ficha/plugin (pendiente, ver SELECTOR-QWEN-PENDIENTES.md)
// rellenará window.RIU_SELECTOR_QWEN.enviar; mientras siga en null el chat funciona exactamente como antes.
import { node } from "./api.js";

window.RIU_SELECTOR_QWEN = window.RIU_SELECTOR_QWEN || {
  enviar: null,      // gancho para la ficha/plugin: async ({ modelo_id_slug, mensaje, sesion }) => respuesta. null = sin cablear
  seleccion: null,   // última elección { modelo_id_slug, label, grupo }
  modelos: [],       // catálogo visible (slugs de interfaz, NO son ids de proveedor)
};

const GRUPOS = [
  { titulo: "Qwen", modelos: [
    ["🧠", "Qwen 3.8 Max", "Código complejo"],
    ["⚡", "Qwen 3.8 Flash", "Código rápido"],
    ["🧠", "Qwen 3.7 Max", "Razonamiento"],
    ["⚡", "Qwen 3.7 Plus", "Código + visión"],
    ["🚀", "Qwen 3.6 Flash", "Rápido / económico"]] },
  { titulo: "DeepSeek", modelos: [
    ["🧠", "DeepSeek V4 Pro", "Código complejo"],
    ["🧠", "DeepSeek V4 Pro 0813", "Máxima profundidad"],
    ["⚡", "DeepSeek V4 Flash", "Código rápido"]] },
  { titulo: "GLM", modelos: [
    ["🧠", "GLM 5.2", "Código + agentes"]] },
  { titulo: "Imágenes", modelos: [
    ["🎨", "Qwen Image 3.0 Pro", "Imágenes"],
    ["🎨", "Wan 2.7 Image", "Imágenes"]] },
  { titulo: "Modo recepción", recepcion: true, modelos: [
    ["🔊", "Qwen TTS", "Texto a voz"],
    ["🎙️", "Qwen Realtime", "Voz en vivo"],
    ["📝", "Qwen ASR", "Voz a texto"]] },
];
const slug = (t) => t.toLowerCase().normalize("NFD").replace(/[\u0300-\u036f]/g, "").replace(/[^a-z0-9]+/g, "-").replace(/^-|-$/g, "");
window.RIU_SELECTOR_QWEN.modelos = GRUPOS.flatMap((g) => g.modelos.map((m) => ({ modelo_id_slug: slug(m[1]), label: m[1], grupo: g.titulo })));

export function conectarSelectorModelos(ctx) {
  const { q, chat, tell, guardar } = ctx;
  const pill = q("#sel-nuevo"), lista = q("#sh-modelos-lista");
  const pintarPill = () => {
    const s = chat().selectorQwen;
    pill.textContent = s ? s.icono + " " + s.label + " ⌄" : "✦ Selector Qwen ⌄";
    pill.classList.toggle("on", !!s);
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
        b.append(node("span", m[0], "mod-ico"), txt, node("span", sel ? "✓" : "", "mod-ck"));
        b.addEventListener("click", () => elegir(m, g));
        caja.append(b);
      }
      lista.append(caja);
    }
  };
  pill.addEventListener("click", () => { pill.setAttribute("aria-expanded", String(q("#sh-modelos").hidden)); pintar(); });
  new MutationObserver(pintarPill).observe(q("#chat-tabs"), { childList: true, subtree: true, attributes: true });
  pintarPill();
}
