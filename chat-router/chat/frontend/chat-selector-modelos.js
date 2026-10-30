// Team qwen y Team 5 MVP comparten el catálogo del Router y guardan el id de proveedor en cada chat.
import { node, api } from "./api.js";
import { conectarSelectores } from "./chat-selectores.js";  // interruptor ON/OFF de los 5 selectores (solo frontend)

window.RIU_SELECTOR_QWEN = window.RIU_SELECTOR_QWEN || {
  enviar: null,      // gancho para la ficha/plugin: async ({ modelo_id_slug, mensaje, sesion }) => respuesta. null = sin cablear
  seleccion: null,   // última elección { modelo_id_slug, label, grupo }
  modelos: [],
};

// Regla (Antonio): el selector solo muestra modelos de SWE CODE y SWEN CODE free.
const SOLO_SWE = new Set([
  // SWE CODE (local, HF S1-S3)
  "hf-liquid-lfm25", "swe-codex-qwen25-15b", "swe-opencode-qwen35-08b", "swe-agent-lfm25", "swe-openhands-lfm25", "hf-qwen25-coder-15b",
  // SWEN CODE free (web via bridge + modos swecode)
  "web-qwen38max", "web-qwen37max", "web-dsv4-flash",
  "swecode-consulta", "swecode-revision", "swecode-solucion", "swecode-arquitectura", "swecode-archivos", "swecode-prompt_code", "swecode-despliega",
  // ids alias del bridge
  "lfm2.5-350m", "qwen2.5-coder-1.5b", "qwen3.5-0.8b", "qwen3-0.6b"]);
const GRUPOS = [
  { titulo: "SWEN CODE free (web)", modelos: [
    ["pensar", "Qwen 3.8 Max (web)", "Código complejo · via bridge", "web-qwen38max"],
    ["pensar", "Qwen 3.7 Max (web)", "Razonamiento · via bridge", "web-qwen37max"],
    ["rayo", "DeepSeek V4 Flash (web)", "Código rápido · via bridge", "web-dsv4-flash"],
    ["pensar", "Concilio", "los 3 web a la vez", "swecode-consulta"],
    ["pensar", "SWE · revision", "modo revision", "swecode-revision"],
    ["pensar", "SWE · solucion", "modo solucion", "swecode-solucion"],
    ["pensar", "SWE · arquitectura", "modo arquitectura", "swecode-arquitectura"],
    ["pensar", "SWE · archivos", "modo archivos", "swecode-archivos"],
    ["pensar", "SWE · prompt_code", "modo prompt_code", "swecode-prompt_code"],
    ["rayo", "SWE · despliega", "modo despliega", "swecode-despliega"]] },
  { titulo: "SWE CODE (local HF)", modelos: [
    ["rapido", "Liquid AI (HF)", "LFM2.5-350M · respondedor principal", "hf-liquid-lfm25"],
    ["pensar", "SWE · Codex escribe", "Qwen2.5-Coder-1.5B", "swe-codex-qwen25-15b"],
    ["pensar", "SWE · OpenCode revisa", "Qwen3.5-0.8B", "swe-opencode-qwen35-08b"],
    ["rayo", "SWE · Agent ejecuta", "LFM2.5-350M · tool/agentic", "swe-agent-lfm25"],
    ["rayo", "SWE · OpenHands verifica", "LFM2.5-350M", "swe-openhands-lfm25"],
    ["pensar", "Qwen Code (HF)", "Qwen2.5-Coder-1.5B local", "hf-qwen25-coder-15b"]] },
];
const CATALOGO_CLAVE = "riu_catalogo_qwen";  // ultima lista que dio el Router (localStorage)
const CATALOGO_RESPALDO = ["web-qwen38max", "web-qwen37max", "web-dsv4-flash", "swecode-consulta", "swecode-revision", "swecode-solucion", "swecode-arquitectura", "swecode-archivos", "swecode-prompt_code", "swecode-despliega", "swe-codex-qwen25-15b", "swe-opencode-qwen35-08b", "swe-agent-lfm25", "swe-openhands-lfm25", "hf-qwen25-coder-15b", "hf-liquid-lfm25"];  // solo SWE CODE + SWEN CODE free

const etiqueta = (id) => id.replace(/^(qwen|deepseek|glm|kimi|minimax|wan|happyhorse)/i, (s) => ({ qwen: "Qwen ", deepseek: "DeepSeek", glm: "GLM", kimi: "Kimi", minimax: "MiniMax", wan: "Wan ", happyhorse: "HappyHorse" })[s.toLowerCase()]).replace(/-/g, " ").replace(/\b(max|flash|plus|pro|image|video|code)\b/g, (s) => s[0].toUpperCase() + s.slice(1)).replace(/\b[vkm](?=\d)/g, (s) => s.toUpperCase());
export function gruposModelos(modelos) {
  const grupos = new Map(), vistos = new Set();
  for (const entrada of modelos) {
    const id = typeof entrada === "string" ? entrada : entrada?.model_id;
    if (typeof id !== "string" || !id || vistos.has(id) || !SOLO_SWE.has(id)) continue;  // solo SWE CODE + SWEN CODE free
    vistos.add(id);
    const conocido = GRUPOS.find((g) => g.modelos.some((m) => m[3] === id));
    const tipo = entrada?.tipo || (/audio/.test(id) ? "audio" : /video|[tir]2v$/.test(id) ? "video" : /image/.test(id) ? "imagen" : "texto");
    const familia = /^(qwen|deepseek|glm|kimi|minimax)/i.exec(id)?.[1];
    const titulo = conocido?.titulo || ({ imagen: "Imágenes", audio: "Modo recepción", video: "Video" })[tipo] || (familia ? etiqueta(familia).trim() : "Otros");
    const modelo = conocido?.modelos.find((m) => m[3] === id) || [tipo === "texto" ? "pensar" : tipo === "audio" ? "voz" : "imagen", etiqueta(id), tipo, id];
    if (!grupos.has(titulo)) grupos.set(titulo, { titulo, modelos: [] });
    grupos.get(titulo).modelos.push(modelo);
  }
  return [...grupos.values()];
}
let catalogo = CATALOGO_RESPALDO;
try { const guardado = JSON.parse(localStorage.getItem(CATALOGO_CLAVE)); if (Array.isArray(guardado) && guardado.length) catalogo = guardado; } catch (e) {}
let grupos = gruposModelos(catalogo);

const ICO = {  // iconos de línea monocromos (currentColor), skill Maxbry UI: sin emojis de color
  pensar: '<path d="M9 18h6M10 21h4M12 3a6 6 0 0 0-4 10.5c.7.7 1 1.5 1 2.5h6c0-1 .3-1.8 1-2.5A6 6 0 0 0 12 3z"/>', rayo: '<path d="M13 2L4 14h7l-1 8 9-12h-7z"/>',
  rapido: '<path d="M4 6l7 6-7 6zM13 6l7 6-7 6z"/>', imagen: '<rect x="3" y="4" width="18" height="16" rx="2"/><circle cx="9" cy="10" r="2"/><path d="M21 16l-5-5-9 9"/>',
  voz: '<path d="M4 9v6h4l5 4V5L8 9zM16 9a4 4 0 0 1 0 6M18.5 6.5a8 8 0 0 1 0 11"/>', micro: '<rect x="9" y="3" width="6" height="11" rx="3"/><path d="M5 11a7 7 0 0 0 14 0M12 18v3"/>', texto: '<path d="M4 6h16M4 12h16M4 18h10"/>' };
const slug = (t) => t.toLowerCase().normalize("NFD").replace(/[\u0300-\u036f]/g, "").replace(/[^a-z0-9]+/g, "-").replace(/^-|-$/g, "");
const publicarCatalogo = () => { window.RIU_SELECTOR_QWEN.modelos = grupos.flatMap((g) => g.modelos.map((m) => ({ model_id: m[3], modelo_id_slug: slug(m[1]), label: m[1], grupo: g.titulo }))); };
publicarCatalogo();

export function conectarSelectorModelos(ctx) {
  const { q, chat, tell, guardar } = ctx;
  let cargando = false;
  // El servidor decide el plan; si no responde se conserva su último catálogo.
  const cargarCatalogo = (intento = 1) => {
    if (cargando) return;
    if (!sessionStorage.getItem("riu_clave")) { pintar(); return; }
    cargando = true;
    api('/chat/providers/qwen/models').then((r) => {
      if (!Array.isArray(r.models) || !r.models.length) throw new Error('Catalogo vacio');
      const nuevos = gruposModelos(r.models);
      if (!nuevos.length) throw new Error('Catalogo vacio');
      grupos = nuevos; publicarCatalogo();
      try { localStorage.setItem(CATALOGO_CLAVE, JSON.stringify(r.models.filter((m) => SOLO_SWE.has(typeof m === "string" ? m : m?.model_id)))); } catch (e) {}
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
    window.RIU_SELECTOR_QWEN.seleccion = s ? { model_id: s.model_id, modelo_id_slug: s.modelo_id_slug, label: s.label, grupo: s.grupo, sesion: chat().sesion } : null;
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
    const dest0 = hojaOrigen === "team-5-mvp" ? "team-5-mvp" : "team-qwen";
    const SEL0 = window.RIU_SELECTORES;
    const ya = c.selectorQwen && c.selectorQwen.label === m[1];
    const delOtro = ya && SEL0 && SEL0.activo && SEL0.activo !== dest0;  // mismo modelo elegido por el otro selector: un clic lo mueve, no lo apaga
    c.selectorQwen = (ya && !delOtro) ? null : { icono: m[0], model_id: m[3], modelo_id_slug: slug(m[1]), label: m[1], grupo: g.titulo };
    const det = c.selectorQwen ? { model_id: c.selectorQwen.model_id, modelo_id_slug: c.selectorQwen.modelo_id_slug, label: m[1], grupo: g.titulo, sesion: c.sesion } : null;
    window.RIU_SELECTOR_QWEN.seleccion = det;
    window.dispatchEvent(new CustomEvent("riu:selector-qwen", { detail: det }));
    pintarPill(); pintar(); guardar(); if (typeof actualizarMIA === "function") actualizarMIA();  // la pildora de abajo refleja el modelo elegido
    const dest = dest0, SEL = SEL0;
    if (SEL && SEL.encender) { if (c.selectorQwen) SEL.encender(dest); else if (SEL.activo === dest) SEL.apagar(); }  // elegir un modelo = el selector que abrio la hoja responde
    q("#sh-modelos").hidden = true;
    pill.setAttribute("aria-expanded", "false"); if (pillMvp) pillMvp.setAttribute("aria-expanded", "false");  // UX: al elegir la hoja se cierra; el botón debe anunciar «colapsado»
  };
  const pintar = () => {
    const s = chat().selectorQwen;
    lista.replaceChildren();
    for (const g of grupos) {
      lista.append(node("h4", g.titulo, "mod-grupo-t"));
      const caja = node("div", "", "mod-grupo");
      for (const m of g.modelos) {
        const sel = !!(s && s.label === m[1]) || !!((chat().selectorQwenMulti || []).find((x) => x.label === m[1]));
        const b = node("button", "", "mod-fila" + (sel ? " sel" : ""));
        b.type = "button"; b.setAttribute("aria-pressed", String(sel));
        const txt = node("span", "", "mod-txt");
        txt.append(node("b", m[1]), node("small", m[2]));
        const ico = node("span", "", "mod-ico"); ico.innerHTML = '<svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">' + (ICO[m[0]] || '<circle cx="12" cy="12" r="10"/>') + "</svg>";
        b.append(ico, txt, node("span", sel ? "✓" : "", "mod-ck"));
        b.addEventListener("click", () => elegir(m, g));
        caja.append(b);
      }
      lista.append(caja);
    }
  };
  const SEL_GLOBAL = () => window.RIU_SELECTORES;
  const abrir = (origen, boton) => {
    hojaOrigen = origen;
    q("#sh-modelos .va-head strong").textContent = origen === "team-5-mvp" ? "Team 5 MVP" : "Team qwen";
    boton.setAttribute("aria-expanded", String(q("#sh-modelos").hidden)); pintar(); cargarCatalogo();
  };
  pill.addEventListener("click", () => abrir("team-qwen", pill));
  if (pillMvp) pillMvp.addEventListener("click", () => abrir("team-5-mvp", pillMvp));
  new MutationObserver(pintarPill).observe(q("#chat-tabs"), { childList: true, subtree: true, attributes: true });
  pintarPill();
  conectarSelectores(ctx);
  cargarCatalogo();
}