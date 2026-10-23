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

const GRUPOS = [];  // Catalogo servido por el Router para el plan activo.

const ICO = {  // iconos de línea monocromos (currentColor), skill Maxbry UI: sin emojis de color
  pensar: '<path d="M9 18h6M10 21h4M12 3a6 6 0 0 0-4 10.5c.7.7 1 1.5 1 2.5h6c0-1 .3-1.8 1-2.5A6 6 0 0 0 12 3z"/>', rayo: '<path d="M13 2L4 14h7l-1 8 9-12h-7z"/>',
  rapido: '<path d="M4 6l7 6-7 6zM13 6l7 6-7 6z"/>', imagen: '<rect x="3" y="4" width="18" height="16" rx="2"/><circle cx="9" cy="10" r="2"/><path d="M21 16l-5-5-9 9"/>',
  voz: '<path d="M4 9v6h4l5 4V5L8 9zM16 9a4 4 0 0 1 0 6M18.5 6.5a8 8 0 0 1 0 11"/>', micro: '<rect x="9" y="3" width="6" height="11" rx="3"/><path d="M5 11a7 7 0 0 0 14 0M12 18v3"/>', texto: '<path d="M4 6h16M4 12h16M4 18h10"/>' };
const slug = (t) => t.toLowerCase().normalize("NFD").replace(/[\u0300-\u036f]/g, "").replace(/[^a-z0-9]+/g, "-").replace(/^-|-$/g, "");
window.RIU_SELECTOR_QWEN.modelos = GRUPOS.flatMap((g) => g.modelos.map((m) => ({ model_id: m[3], modelo_id_slug: slug(m[1]), label: m[1], grupo: g.titulo })));

export function conectarSelectorModelos(ctx) {
  const { q, chat, tell, guardar } = ctx;
  api('/chat/providers/qwen/models').then((r) => {
    if (!Array.isArray(r.models) || !r.models.length) throw new Error('Catalogo vacio');
    GRUPOS.splice(0, GRUPOS.length, { titulo: 'Modelos del plan activo', modelos: r.models.map((m) => ['pensar', m.model_id, 'ID enviado al proveedor', m.model_id]) });
    window.RIU_SELECTOR_QWEN.modelos = r.models.map((m) => ({ model_id: m.model_id, modelo_id_slug: slug(m.model_id), label: m.model_id, grupo: 'Modelos del plan activo' }));
    pintar();
  }).catch(() => { GRUPOS.splice(0, GRUPOS.length); pintar(); tell('No se pudo cargar el catalogo del Router; no se sustituira el modelo elegido'); });

  const pill = q("#sel-nuevo"), lista = q("#sh-modelos-lista");
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
  pill.addEventListener("click", () => { hojaOrigen = "team-qwen"; pill.setAttribute("aria-expanded", String(q("#sh-modelos").hidden)); pintar(); });
  if (pillMvp) pillMvp.addEventListener("click", () => { hojaOrigen = "team-5-mvp"; pillMvp.setAttribute("aria-expanded", String(q("#sh-modelos").hidden)); pintar(); });
  new MutationObserver(pintarPill).observe(q("#chat-tabs"), { childList: true, subtree: true, attributes: true });
  pintarPill();
  conectarSelectores(ctx);
}
