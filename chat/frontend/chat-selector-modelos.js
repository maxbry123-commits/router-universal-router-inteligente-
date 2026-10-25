// chat-selector-modelos.js — "Selector Qwen": selector NUEVO, solo frontend, separado del selector de ficha "modelo ▾".
// NO llama al Router ni envía nada. Al elegir un modelo guarda la elección en el chat activo y emite el evento
// 'riu:selector-qwen' { modelo_id_slug, label, grupo, sesion }. La ficha/plugin (pendiente, ver SELECTOR-QWEN-PENDIENTES.md)
// rellenará window.RIU_SELECTOR_QWEN.enviar; mientras siga en null el chat funciona exactamente como antes.
import { node, api } from "./api.js";
import { conectarSelectores } from "./chat-selectores.js";  // interruptor ON/OFF de los 5 selectores (solo frontend)

window.RIU_SELECTOR_QWEN = window.RIU_SELECTOR_QWEN || {
  enviar: null,      // gancho para la ficha/plugin: async ({ modelo_id_slug, mensaje, sesion }) => respuesta. null = sin cablear
  seleccion: null,   // última elección { modelo_id_slug, label, grupo }
  modelos: [],       // catálogo visible (slugs de interfaz, NO son ids de proveedor)
};

const GRUPOS = [
  { titulo: "Qwen", modelos: [
    ["pensar", "Qwen 3.8 Max", "Código complejo", "qwen3.8-max"],
    ["rayo", "Qwen 3.8 Flash", "Código rápido", "qwen3.8-flash"],
    ["pensar", "Qwen 3.7 Max", "Razonamiento", "qwen3.7-max"],
    ["rayo", "Qwen 3.7 Plus", "Código + visión", "qwen3.7-plus"],
    ["rapido", "Qwen 3.6 Flash", "Rápido / económico", "qwen3.6-flash"]] },
  { titulo: "DeepSeek", modelos: [
    ["pensar", "DeepSeek V4 Pro", "Código complejo", "deepseek-v4-pro"],
    ["pensar", "DeepSeek V4 Pro 0813", "Máxima profundidad", "deepseek-v4-pro-0813"],
    ["rayo", "DeepSeek V4 Flash", "Código rápido", "deepseek-v4-flash-0731"]] },
  { titulo: "GLM", modelos: [
    ["pensar", "GLM 5.2", "Código + agentes", "glm-5.2"]] },
  { titulo: "Imágenes", modelos: [
    ["imagen", "Qwen Image 3.0 Pro", "Imágenes", "qwen-image-3.0-pro"],
    ["imagen", "Wan 2.7 Image", "Imágenes", "wan2.7-image"]] },
  { titulo: "Modo recepción", modelos: [
    ["voz", "Qwen TTS", "Texto a voz", "qwen-audio-3.0-tts-plus"],
    ["micro", "Qwen Realtime", "Voz en vivo", "qwen-audio-3.0-realtime-plus"],
    ["texto", "Qwen ASR", "Voz a texto", "qwen-audio-3.0-asr-flash"]] },
];
const CATALOGO_CLAVE = "riu_catalogo_qwen";  // ultima lista que dio el Router (localStorage)
const CATALOGO_RESPALDO = ["qwen3.8-max", "qwen3.8-flash", "qwen3.7-max", "qwen3.7-plus", "qwen3.6-flash", "glm-5.3", "glm-5.2", "deepseek-v4-pro", "deepseek-v4-pro-0813", "deepseek-v4-flash-0731", "deepseek-v4.1-flash", "deepseek-v4.1-flash-1017", "qwen-image-3.0-pro", "wan2.7-image", "wan2.7-image-pro", "qwen-audio-3.0-tts-plus", "qwen-audio-3.0-realtime-plus", "qwen-audio-3.0-asr-flash", "wan3.0-video", "happyhorse-1.1-t2v", "happyhorse-1.1-i2v", "happyhorse-1.1-r2v"];  // plan Personal (mvp/modelos.json, p=1)

const ICO = {  // iconos de línea monocromos (currentColor), skill Maxbry UI: sin emojis de color
  pensar: '<path d="M9 18h6M10 21h4M12 3a6 6 0 0 0-4 10.5c.7.7 1 1.5 1 2.5h6c0-1 .3-1.8 1-2.5A6 6 0 0 0 12 3z"/>', rayo: '<path d="M13 2L4 14h7l-1 8 9-12h-7z"/>',
  rapido: '<path d="M4 6l7 6-7 6zM13 6l7 6-7 6z"/>', imagen: '<rect x="3" y="4" width="18" height="16" rx="2"/><circle cx="9" cy="10" r="2"/><path d="M21 16l-5-5-9 9"/>',
  voz: '<path d="M4 9v6h4l5 4V5L8 9zM16 9a4 4 0 0 1 0 6M18.5 6.5a8 8 0 0 1 0 11"/>', micro: '<rect x="9" y="3" width="6" height="11" rx="3"/><path d="M5 11a7 7 0 0 0 14 0M12 18v3"/>', texto: '<path d="M4 6h16M4 12h16M4 18h10"/>' };
const slug = (t) => t.toLowerCase().normalize("NFD").replace(/[\u0300-\u036f]/g, "").replace(/[^a-z0-9]+/g, "-").replace(/^-|-$/g, "");
window.RIU_SELECTOR_QWEN.modelos = GRUPOS.flatMap((g) => g.modelos.map((m) => ({ model_id: m[3], modelo_id_slug: slug(m[1]), label: m[1], grupo: g.titulo })));

export function conectarSelectorModelos(ctx) {
  const { q, chat, tell, guardar } = ctx;
  let cargando = false;
  // La lista cableada de GRUPOS no se sustituye por ids crudos. El Router solo se consulta; si no responde, la lista sigue.
  const cargarCatalogo = (intento = 1) => {
    if (cargando) return;
    cargando = true;
    api('/chat/providers/qwen/models').then((r) => {
      if (!Array.isArray(r.models) || !r.models.length) throw new Error('Catalogo vacio');
      const ids = r.models.map((m) => m.model_id);
      try { localStorage.setItem(CATALOGO_CLAVE, JSON.stringify(ids)); } catch (e) {}
      pintar();
    }).catch(() => {
      cargando = false;
      if (intento < 3) { setTimeout(() => cargarCatalogo(intento + 1), 4000); return; }
      pintar(); lista.append(node('p', 'El Router no respondió: esta es la lista guardada. Puedes elegir igual; se actualiza al volver a abrir.', 'fila-desc'));
    }).finally(() => { cargando = false; });
  };

  const pill = q("#sel-nuevo"), lista = q("#sh-modelos-lista");
  if (!pill || !lista || !q("#sh-modelos")) return;
  const pillMvp = q("#sel-mvp");  // Team 5 MVP: misma hoja y mismo catalogo; la ruta de envio es otra (ficha_qwen=5)
  let hojaOrigen = "team-qwen";  // quien abrio la hoja de modelos: al elegir, se enciende ESE selector y no el otro
  const pintarPill = () => {
    const s = chat().selectorQwen;
    pill.textContent = "Team qwen ⌄"; if (!pill.classList.contains("bloq")) pill.title = s ? "Team qwen · " + s.label : "Team qwen";  // el modelo elegido va en el tooltip
    pill.classList.toggle("on", !!s || !!((chat().selectorQwenMulti || []).length));
    if (pillMvp) { if (!pillMvp.classList.contains("bloq")) pillMvp.title = s ? "Team 5 MVP · " + s.label : "Team 5 MVP"; pillMvp.classList.toggle("on", !!s); }
    if (window.RIU_SELECTORES && window.RIU_SELECTORES.refrescar) window.RIU_SELECTORES.refrescar();
    window.RIU_SELECTOR_QWEN.seleccion = s ? { modelo_id_slug: s.modelo_id_slug, label: s.label, grupo: s.grupo, sesion: chat().sesion } : null;
  };
  const elegir = (m, g) => {
    const c = chat();
    if (c.paralelo) {  // >>> MODOS <<< T6: modo paralelo = multi-seleccion (max 6) sin cerrar la hoja
      c.selectorQwenMulti = c.selectorQwenMulti || [];
      const i = c.selectorQwenMulti.findIndex((x) => x.label === m[1]);
      if (i >= 0) c.selectorQwenMulti.splice(i, 1);
      else if (c.selectorQwenMulti.length < 6) c.selectorQwenMulti.push({ model_id: m[3], modelo_id_slug: slug(m[1]), label: m[1], grupo: g.titulo });
      else { tell("Paralelo: máximo 6 modelos"); return; }
      pintarPill(); pintar(); guardar();
      const SEL = window.RIU_SELECTORES; if (SEL && SEL.encender && c.selectorQwenMulti.length) SEL.encender("team-qwen");
      return;
    }
    const ya = c.selectorQwen && c.selectorQwen.label === m[1];
    c.selectorQwen = ya ? null : { icono: m[0], model_id: m[3], modelo_id_slug: slug(m[1]), label: m[1], grupo: g.titulo };
    const det = c.selectorQwen ? { modelo_id_slug: c.selectorQwen.modelo_id_slug, label: m[1], grupo: g.titulo, sesion: c.sesion } : null;
    window.RIU_SELECTOR_QWEN.seleccion = det;
    window.dispatchEvent(new CustomEvent("riu:selector-qwen", { detail: det }));
    pintarPill(); pintar(); guardar(); if (typeof actualizarMIA === "function") actualizarMIA();  // la pildora de abajo refleja el modelo elegido
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
        const sel = !!(s && s.label === m[1]) || !!((chat().selectorQwenMulti || []).find((x) => x.label === m[1]));
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
  const SEL_GLOBAL = () => window.RIU_SELECTORES;
  pill.addEventListener("click", () => { hojaOrigen = "team-qwen"; pill.setAttribute("aria-expanded", String(q("#sh-modelos").hidden)); pintar(); cargarCatalogo(); });
  if (pillMvp) pillMvp.addEventListener("click", () => { hojaOrigen = "team-5-mvp"; pillMvp.setAttribute("aria-expanded", String(q("#sh-modelos").hidden)); pintar(); });
  new MutationObserver(pintarPill).observe(q("#chat-tabs"), { childList: true, subtree: true, attributes: true });
  pintarPill();
  conectarSelectores(ctx);
  cargarCatalogo();
}
