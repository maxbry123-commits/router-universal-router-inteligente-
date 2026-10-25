import { node } from "./api.js";
import * as A from "./chat-ancla.js";
import { conectarSelectorModelos } from "./chat-selector-modelos.js";
import { conectarMicrofono } from "./chat-microfono.js";
import { conectarVentanas } from "./chat-ventanas.js";
import { conectarRiu } from "./chat-riu.js";
import { conectarRiu2 } from "./chat-riu2.js";
import { conectarVentanasNuevas } from "./ventanas-nuevas.js";
import { proyId } from "./objetivos-ancla.js";
import { montarProyectos } from "./ventana-proyectos.js";
// >>> MODOS BEGIN
import { initModeSelector } from "./mode_selector.js";
import { montarBuzon } from "./buzon-proceso.js";
import { montarSelectsSecundarios } from "./selects-secundarios.js";
import { montarSandboxChat } from "./ventana-sandbox-chat.js";
import { montarMotor } from "./ventana-motor.js";
import { montarSelectorAncla } from "./selector-ancla.js";
import { montarControlesChat } from "./controles-chat.js";
import { montarEnviar } from "./enviar-mensaje.js";
import { montarPildoraFicha } from "./pildora-ficha.js";
// <<< MODOS END

const MODOS = { fast: "rápido", balanced: "equilibrado", think: "pensar" };
const MAX_CHAT = 10;
const CLAVE_CHATS = "riu_chats_v1";  // sesiones/anclas/ficha de cada pestaña: sobreviven a recargas en esta pestaña
const etiquetaCorta = (a) => a.startsWith("handoff:") ? a.slice(8) : a.startsWith("enlace:") ? a.slice(7, 40) : a.startsWith("raiz:") ? "raíz " + a.slice(5, 40) : a;

export async function mount(root, { api, tell }) {
  const q = (s) => root.querySelector(s) || document.querySelector(s);  // en móvil shell.js lleva los controles (.ctl-int) a #movil-panel, fuera de root
  const editor = q("#message");
  const ajustarAlturaEditor = () => {
    editor.style.height = "auto";
    const limite = parseFloat(getComputedStyle(editor).maxHeight) || 128;
    editor.style.height = Math.min(editor.scrollHeight, limite) + "px";
  };
  editor.addEventListener("input", ajustarAlturaEditor);
  window.addEventListener("resize", ajustarAlturaEditor);
  ajustarAlturaEditor();
  const copiarTexto = (t) => { try { navigator.clipboard.writeText(t); } catch (e) {} };
  const defecto = window.RIU_CONFIG?.defecto || "";
  const fichaEt = (id) => (window.RIU_CONFIG?.modelos || []).find((m) => m.id === id);

  // ---- multi-chat: hasta 5 estancias, cada una con su sesion, su ficha, sus anclas y su historial ----
  const tabsEl = q("#chat-tabs"), histEl = q("#histories");
  const abajo = (c) => {  // sigue las respuestas solo si estas cerca del final; si subiste, aparece "↓ nuevo"
    if (c.hist.__sigue !== false) { c.hist.scrollTop = c.hist.scrollHeight; if (c.hist.__nuevo) c.hist.__nuevo.hidden = true; return; }
    let b = c.hist.__nuevo;
    if (!b) {
      b = c.hist.__nuevo = document.createElement("button"); b.type = "button"; b.className = "btn-nuevo-abajo"; b.textContent = "↓ nuevo";
      b.style.cssText = "position:sticky;bottom:8px;left:50%;transform:translateX(-50%);display:block;margin:0 auto;z-index:5;padding:4px 12px;border-radius:14px;font-size:13px";
      b.addEventListener("click", () => { c.hist.__sigue = true; c.hist.scrollTop = c.hist.scrollHeight; b.hidden = true; });
      c.hist.addEventListener("scroll", () => { if (c.hist.__sigue) b.hidden = true; }, { passive: true });
    }
    c.hist.append(b); b.hidden = false;
  };  // sigue las respuestas solo si estas cerca del final; el historial tiene su propio scroll
  const mmMovil = window.matchMedia("(max-width: 720px)");
  const reacomodoMovil = () => {
    const h1 = document.querySelector("#h1-slot h1, #h1-slot-int h1");
    if (h1) (mmMovil.matches ? q("#h1-slot-int") : q("#h1-slot")).appendChild(h1);
  };
  reacomodoMovil(); mmMovil.addEventListener("change", reacomodoMovil);
  const ctlB = q("#ctl-barra"), ctlP = q("#ctl-panel");  // barra Controles: desliza hacia abajo y se recoge; son los mismos botones de siempre (no se clonan ni cambian de nodo)
  if (ctlB && ctlP) ctlB.addEventListener("click", () => { const ab = ctlP.classList.toggle("abierto"); ctlB.setAttribute("aria-expanded", String(ab)); ctlB.textContent = ab ? "Controles ▴" : "Controles ▾"; });
  const medirCtl = () => { const s = document.querySelector(".topbar") || document.querySelector(".sidebar") || document.querySelector("#navigation"); const b = s ? Math.round(s.getBoundingClientRect().bottom) : 0; if (b > 0 && b < window.innerHeight * 0.8) document.documentElement.style.setProperty("--ctl-top", b + "px"); const sec = q("#histories") && q("#histories").parentElement; if (sec) document.documentElement.style.setProperty("--chat-top", Math.round(sec.getBoundingClientRect().top + window.scrollY) + "px"); };  // --chat-top: dónde empieza de verdad el chat (escritorio: Enviar siempre a la vista)  // la barra se pega justo debajo de la tira superior (.topbar en escritorio; .sidebar solo es la tira en movil)
  medirCtl(); window.addEventListener("resize", medirCtl); [300, 1200].forEach((ms) => setTimeout(medirCtl, ms));  // otra vez cuando terminan de montarse los controles de arriba
  const previo = (c, message) => { const h = A.cargarHistorial(c.sesion).filter((m) => m.rol === "user" || m.rol === "bot"); if (h.length && h[h.length - 1].rol === "user" && h[h.length - 1].texto === message) h.pop(); return h.map((m) => ({ role: m.rol === "user" ? "user" : "assistant", content: m.texto })); };  // historial completo de ESTA sesion, aparte del input actual
  const previoTodo = (c, message) => { const h = A.cargarHistorial(c.sesion).filter((m) => m.rol === "user" || m.rol === "bot"); if (h.length && h[h.length - 1].rol === "user" && h[h.length - 1].texto === message) h.pop(); const out = []; let tam = 0; for (const m of h.slice(-20).reverse()) { const t = String(m.texto || ""); if (tam + t.length > 30000) break; tam += t.length; out.unshift({ role: m.rol === "user" ? "user" : "assistant", content: t }); } return out; };  // Team 5 MVP: ultimos 20 mensajes / ~30 KB: TODO el historial de ESTA sesion, con roles
  const chats = [];
  const chatTools = window.RIU_CHAT_TOOL_FLAGS = { tools: false, agente_tool: false, llm_tool: false };
  let activo = 0;
  const chat = () => chats[activo];
  const releerAnclas = (c) => {
    try {
      const guardado = JSON.parse(localStorage.getItem(CLAVE_CHATS) || "[]").find((x) => x.sesion === c.sesion);
      if (Array.isArray(guardado?.anclados)) {
        c.anclados.clear(); guardado.anclados.forEach((a) => c.anclados.add(a));
      }
    } catch (e) {}
    return [...c.anclados];
  };
  const chatA = () => (window.RIU_OBJETIVO_ANCLA ? window.RIU_OBJETIVO_ANCLA() : chat());  // objetivo del anclaje: el chat (por defecto) u otro (constitución, workflow, agentes, proyecto, sandbox)
  const guardar = () => {
    try {
      localStorage.setItem("riu_chat_activo", String(activo)); localStorage.setItem(CLAVE_CHATS, JSON.stringify(
        chats.map((c) => ({ sesion: c.sesion, ficha: c.ficha, anclados: [...c.anclados], instrucciones: c.instrucciones || "", selectorQwen: c.selectorQwen || null, selectorQwenMulti: [...(c.selectorQwenMulti || [])], paralelo: !!c.paralelo, fastReply: !!c.fastReply, motor: !!c.motor, project_id: c.project_id || null }))));
    } catch (e) {}
    try { A.respaldarPestanas(JSON.parse(localStorage.getItem(CLAVE_CHATS) || "[]")); } catch (e) {}  // respaldo de pestañas en el Router (nombre y orden)
  };
  const pintarAnclados = () => {
    const caja = q("#anclados");
    caja.innerHTML = "";
    const todos = [...chat().anclados];
    const ba = q("#btn-ancla"); if (ba) ba.dataset.n = String(todos.length);  // RUI 19: contador del boton ancla
    if ((chat().instrucciones || "").trim()) caja.append(node("span", "📌 instrucciones fijas", "anclado-item"));
    todos.slice(0, 3).forEach((a) => caja.append(node("span", etiquetaCorta(a), "anclado-item")));
    if (todos.length > 3) caja.append(node("span", "+" + (todos.length - 3) + " más ⚓", "anclado-item"));
  };
  const pintarFichaPill = () => {
    const et = fichaEt(chat().ficha);
    const t = (et ? et.etiqueta : "modelo").replace(/[\p{Extended_Pictographic}\uFE0F\u200D]/gu, "").trim(); const fp = q("#ficha"); if (!fp) return;  // vista movil: la pildora puede no existir -> no romper el envio
    fp.textContent = "NVIDIA ⌄"; fp.title = "NVIDIA · " + t; fp.dataset.ficha = t;  // selector 1 (sin emojis de color)
  };
  const FAST_SEL = () => /^(team-qwen|ask-consil-code-qwen-team|ask-consil-fromtend-qwen-team)$/.test((window.RIU_SELECTORES && window.RIU_SELECTORES.activo) || "");  // ⚡ solo cuenta con un selector de ficha encendido
  const pintarFastReply = () => {  // ⚡ Respuesta rápida: el estado es de cada chat; los botones viven junto a cada selector de ficha
    if (!chat()) return;
    window.dispatchEvent(new CustomEvent("riu:fast-reply", { detail: { on: !!chat().fastReply } }));
  };
  const pintarTabs = () => { try { pintarTabs0(); } catch (e) { try { console.error("pintarTabs", e); } catch (x) {} } };  // un fallo de UI (layout movil) nunca bloquea el envio
  const pintarTabs0 = () => {
    tabsEl.replaceChildren();
    pintarFastReply();
    chats.forEach((c, i) => {
      const b = node("button", "Chat " + (i + 1) + (c.ocupado ? " …" : ""), "chip" + (i === activo ? " on" : ""));
      b.type = "button"; b.title = "Chat " + (i + 1) + " — sesión " + c.sesion;
      b.addEventListener("click", () => { activo = i; pintarTabs(); });
      tabsEl.append(b);
    });
    if (chats.length < MAX_CHAT) {
      const mas = node("button", "＋", "chip");
      mas.type = "button"; mas.title = "Nuevo chat — tareas en paralelo o en cola";
      mas.addEventListener("click", nuevoChat);
      tabsEl.append(mas);
    }
    const rec = node("button", "↺", "mini btn-recuperar-hist"); rec.type = "button"; rec.id = "btn-recuperar-hist"; rec.title = "Recuperar historial y contexto de este chat"; rec.setAttribute("aria-label", "Recuperar historial"); rec.style.borderRadius = "999px";  // sin clase chip: no recibe la X de borrar
    rec.addEventListener("click", recuperarHist); tabsEl.append(rec);
    chats.forEach((c, i) => { c.hist.hidden = i !== activo; });
    pintarAnclados();
    try { pintarFichaPill(); } catch (e) {}
    { const bd = q("#btn-detener"); if (bd) bd.hidden = false; }  // Detener SIEMPRE visible (restaurado por orden de Antonio)
    guardar();
  };
  const recuperarHist = async () => {  // ↺: une copia local + respaldo del Router; reabre (en su orden) los chats cuya pestaña se perdió; los borrados no vuelven
    let c = chat(); if (c.ocupado) { tell("Ese chat está trabajando: espera o pulsa Detener"); return; }
    tell("Recuperando historial…"); let pest = 0;
    try {
      let r = { total: 0, router: 0, routerOk: true }, total0 = 0;
      for (const x of chats) if (!x.ocupado) { const y = await A.recuperar(x, burbuja, api); total0 += y.total; if (x === c) r = y; }  // todos los chats abiertos, no solo el visible
      const vacio = chats.length === 1 && !total0;  // navegador borrado: la pestaña nueva y vacía se cambia por las recuperadas
      for (const p of await A.pestanasPerdidas(chats.map((x) => x.sesion))) { if (chats.length >= MAX_CHAT) break; const prev = activo; nuevoChat(p); const y = await A.recuperar(chat(), burbuja, api); r = { total: r.total + y.total, router: r.router + y.router, routerOk: r.routerOk && y.routerOk }; activo = prev; pest++; }
      if (vacio && pest) { const v = chats[0]; v.hist.remove(); chats.splice(0, 1); A.olvidar(v.sesion); activo = 0; c = chat(); }
      pintarTabs(); c.hist.__sigue = true; abajo(c);
      tell(r.total ? "Historial recuperado: " + r.total + " mensajes" + (r.router ? " (" + r.router + " desde el Router)" : "") + (pest ? " · " + pest + " chat(s) reabiertos" : "") : (r.routerOk ? "No hay historial guardado para este chat" : "Sin conexión con el Router: solo se revisó la copia local"));
    } catch (e) { tell("No se pudo recuperar el historial"); }
  };
  const nuevoChat = (restaurado) => {
    const h = node("div", "", "chat-history");
    h.addEventListener("scroll", () => { h.__sigue = h.scrollHeight - h.scrollTop - h.clientHeight < 90; }, { passive: true });  // si subes, deja de seguir; al volver cerca del fondo sigue otra vez
    h.hidden = true; h.setAttribute("role", "log");
    histEl.append(h);
    chats.push({
      sesion: restaurado?.sesion || "web-" + Math.random().toString(36).slice(2, 10),
      ficha: fichaEt(restaurado?.ficha) ? restaurado.ficha : defecto,  // fichas NVIDIA viejas guardadas -> Glimmer
      hist: h,
      anclados: new Set(restaurado?.anclados || []),
      selectorQwen: restaurado?.selectorQwen || null,
      selectorQwenMulti: restaurado?.selectorQwenMulti || [],
      paralelo: !!restaurado?.paralelo,  // >>> MODOS <<< T6
      fastReply: !!(restaurado && restaurado.fastReply),
      motor: !!(restaurado && restaurado.motor),
      project_id: (restaurado && restaurado.project_id) || null,
      instrucciones: restaurado?.instrucciones || "",
      ocupado: false,
    });
    activo = chats.length - 1;
    pintarTabs();
  };
  try {
    const previos = JSON.parse(localStorage.getItem(CLAVE_CHATS) || sessionStorage.getItem(CLAVE_CHATS) || "[]");
    if (Array.isArray(previos) && previos.length) {
      const act = Number(localStorage.getItem("riu_chat_activo")) || 0; previos.slice(0, MAX_CHAT).forEach((p) => nuevoChat(p));
      activo = Math.min(Math.max(act, 0), chats.length - 1); pintarTabs();
    } else nuevoChat();
  } catch (e) { nuevoChat(); }

  const burbuja = (texto, cls) => {
    const d = node("div", "", "item message" + (cls ? " " + cls : ""));
    const span = node("span", texto, "txt");
    d.append(span);
    const b = node("button", "⧉", "copiar");
    b.type = "button"; b.title = "Copiar esta salida";
    b.addEventListener("click", () => copiarTexto(span.textContent));
    d.append(b);
    if (!cls || !/\b(user|meta|pending|error)\b/.test(cls)) {
      const e = node("button", "", "editar"); e.innerHTML = '<svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M4 20h4L19 9l-4-4L4 16zM13.5 6.5l4 4"/></svg>'; e.setAttribute("aria-label", "Editar");
      e.type = "button"; e.title = "Editar esta salida";
      let editando = false; span.dataset.orig = texto;
      e.addEventListener("click", () => {
        editando = !editando;
        if (!editando) { const nuevo = span.textContent; if (nuevo !== span.dataset.orig) { A.reemplazar(chat().sesion, span.dataset.orig, nuevo); span.dataset.orig = nuevo; } }  // la edicion sustituye al texto guardado
        span.contentEditable = editando ? "true" : "false";
        if (editando) e.textContent = "✓"; else e.innerHTML = '<svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M4 20h4L19 9l-4-4L4 16zM13.5 6.5l4 4"/></svg>';
        e.title = editando ? "Guardar edición" : "Editar esta salida";
        if (editando) span.focus();
      });
      d.append(e);
    }
    return d;
  };

  A.conectarRespaldo(api);  // cada mensaje y la lista de pestañas también quedan en /memoria del Router
  const ancla = A.montarAncla({ q, chat: chatA, tell, guardar, pintarAnclados });
  chats.forEach((c) => { c.historialListo = A.restaurar(c, burbuja); c.historialListo.then(() => {  // historial guardado: vuelve al recargar; una tarea que seguia corriendo se retoma por su proceso_id (NO se relanza)
    if (!window.RIU_PENDIENTE || !window.RIU_PENDIENTE(c.sesion)) return;
    c.ocupado = true; pintarTabs();
    const aviso = node("div", "Recuperando la respuesta de la tarea que seguía corriendo…", "item message meta"); c.hist.append(aviso); abajo(c);
    window.RIU_RETOMAR(c.sesion).then((p) => {
      aviso.remove();
      if (p && p.error === 'PROCESO_DETENIDO') { c.hist.append(node("div", "proceso detenido por el usuario", "item message meta")); abajo(c); return; }
      const t = p && ((p.choices && p.choices[0] && p.choices[0].message && p.choices[0].message.content) || p.reply);
      if (t) { c.hist.append(burbuja(t)); A.registrar(c.sesion, "bot", t); } else c.hist.append(burbuja(p && p.error === "PROCESO_NO_EXISTE" ? "La tarea ya no está en el Router (se reinició). Reenvía tu mensaje." : "Sin respuesta de la tarea recuperada: " + ((p && (p.error || p.detalle)) || "vacía"), "error"));
    }).finally(() => { c.ocupado = false; pintarTabs(); abajo(c); });
  }); });
  conectarSelectorModelos({ q, chat, tell, guardar });  // Selector Qwen: solo frontend
  conectarMicrofono({ q, tell });  // micrófono: dictado por voz al input
  // ---- hojas (sheets): cada pildora abre la suya ----
  const cerrarHojas = () => root.querySelectorAll(".sheet").forEach((s) => { s.hidden = true; });
  root.querySelectorAll("[data-sheet]").forEach((b) => b.addEventListener("click", async () => {
    const sh = q("#" + b.dataset.sheet);
    const abierto = !sh.hidden;
    cerrarHojas();
    sh.hidden = abierto;
    if (!abierto && b.dataset.sheet === "ventana-archivos") cargarArchivos();
    if (!abierto && b.dataset.sheet === "ventana-ancla") { cargarArchivos("#anc-lista"); ancla.refrescar(); }
    if (!abierto && b.dataset.sheet === "ventana-sandbox") cargarSandbox();
    if (!abierto && b.dataset.sheet === "sh-ancla") { pintarAnclas(); cargarMiHandoff(); }
  }));
  root.querySelectorAll(".sh-cerrar").forEach((b) => b.addEventListener("click", cerrarHojas));
  conectarVentanas({ root, q });
  conectarRiu({ q });  // RUI: bloques de codigo con copiar, barra de lectura y boton bajar
  const cerrarChat = async (i) => {  // borrar un chat (la X de su pestana); si es el unico, se vacia y queda uno nuevo
    if (!chats[i]) return;
    if (chats[i].ocupado) { tell("Ese chat está trabajando: espera o pulsa Detener"); return; }
    if (chats[i].project_id && window.RIU_ACCION) {  // unlink ANTES de borrar, FAIL CLOSED: si el backend no confirma, el chat NO se borra
      try { await window.RIU_ACCION("proyecto", { op: "unlink_chat", project_id: chats[i].project_id, sesion: chats[i].sesion }); }
      catch (e) { tell("No se pudo quitar el chat del proyecto"); return; }
    }
    const ses = chats[i].sesion; A.olvidar(ses);
    try { for (const k of ["riu_hist_v1", "riu_proy_v1"]) { const t = JSON.parse(localStorage.getItem(k) || "{}"); if (t && t[ses] !== undefined) { delete t[ses]; localStorage.setItem(k, JSON.stringify(t)); } } } catch (e) {}
    if (chats.length < 2) { nuevoChat(); i = 0; }
    chats[i].hist.remove(); chats.splice(i, 1); activo = Math.max(0, Math.min(activo > i ? activo - 1 : activo, chats.length - 1));
    pintarTabs(); guardar(); tell("Chat borrado");
  };
  try { montarProyectos(root, { tell: (t) => { try { const e = document.createElement("div"); e.className = "item message meta"; e.textContent = t; chat().hist.append(e); } catch (x) {} } }); } catch (e) {}  // ventana Proyectos disponible desde el arranque
  window.RIU_CHAT = { chat, ocupado: () => chats.some((x) => x.ocupado), tokens: () => [...chat().anclados], sincronizarAnclas: () => { chats.forEach(releerAnclas); pintarAnclados(); }, pintar: () => { pintarAnclados(); guardar(); } };  // ganchos para las ventanas de workflows / constitución / claves
  window.RIU_DESTINO_ARCHIVOS = () => {  // destinoArchivos(): UNICA autoridad de a donde van los archivos segun el objetivo de la ventana-ancla
    const o = window.RIU_OBJETIVO_ANCLA ? window.RIU_OBJETIVO_ANCLA() : null;
    if (o && o.tipo === "constitucion") return { destino: "constitucion" };
    if (o && o.tipo === "proyecto") { return { destino: "proyecto", project_id: o.project_id || proyId(o.id) || chat().project_id || "" }; }  // project_id persistido del objetivo, nunca slug recalculado
    return {};
  };
  window.RIU_ANCLA_REFRESCAR = () => { cargarArchivos("#anc-lista"); ancla.refrescar(); pintarAnclas(); cargarMiHandoff(); };  // refresca la ventana de anclaje al cambiar de objetivo
  root.addEventListener("riu:cerrar-chat", (e) => cerrarChat(e.detail));
  conectarRiu2({ root, q, tell });  // RUI 12-21 + mejoras de flujo (ventanas, borrador, avisos)
  conectarVentanasNuevas({ root, q, tell });  // workflows, constitución sentinela, banco de claves y destinos del anclaje (cada uno en su archivo)

  const fila = (titulo, desc, marcada, alClick) => {
    const r = node("button", "", "fila" + (marcada ? " on" : ""));
    r.type = "button";
    const nom = node("span", titulo, "fila-nom");
    if (desc) nom.append(node("span", desc, "fila-desc"));
    r.append(nom, node("span", marcada ? "✓" : "", "fila-ck"));
    r.addEventListener("click", alClick);
    return r;
  };

  // boton de encender/apagar para anclas y archivos: encendido = va anclado con cada mensaje
  const filaEncender = (titulo, desc, clave, onOff) => {
    const r = node("div", "", "fila");
    const nom = node("span", titulo, "fila-nom");
    if (desc) nom.append(node("span", desc, "fila-desc"));
    const t = node("button", "", "toggle" + (chatA().anclados.has(clave) ? " on" : ""));
    t.type = "button"; t.title = "Encender = anclar, apagar = quitar";
    t.addEventListener("click", () => {
      const enc = !chatA().anclados.has(clave);
      enc ? chatA().anclados.add(clave) : chatA().anclados.delete(clave);
      t.classList.toggle("on", enc);
      pintarAnclados(); guardar();
      if (onOff) onOff(enc);
    });
    r.append(nom, t);
    return r;
  };

  montarPildoraFicha({ q, fila, chat, pintarFichaPill, cerrarHojas, guardar, root });  // píldora de ficha: hoja con todas las fichas (por chat) → pildora-ficha.js

  // ---- pildora de modo ----
  let modo = "balanced";
  const pintarModos = () => {
    const lista = q("#sh-modo-lista");
    lista.replaceChildren();
    for (const [k, et] of [["fast", "Rápido — 512 tok"], ["balanced", "Equilibrado — 1024 tok"], ["think", "Pensar — 2048 tok"]]) {
      lista.append(fila(MODOS[k], et, k === modo, () => {
        modo = k;
        q("#modo").textContent = MODOS[k] + " ⌄";
        pintarModos();
        cerrarHojas();
      }));
    }
  };
  pintarModos();

  const { pintarAnclas, cargarMiHandoff } = montarSelectorAncla({ q, filaEncender, chat, burbuja, abajo, fila, cerrarHojas, chatA, pintarAnclados, guardar, tell });  // selector de ancla: handoffs con botón de encender + pegar enlace/handoff propio → selector-ancla.js
  // ---- adjuntar y ventana de archivos (boton encender = anclar al chat + x-ray) ----
  let anclarAlSubir = false;  // true solo cuando se sube desde la ventana ⚓
  const subir = async (file) => {
    const buf = await file.arrayBuffer();
    if (buf.byteLength > 2_000_000) throw new Error('ARCHIVO_MUY_GRANDE: límite vigente de 2 MB por archivo');
    let bin = ""; const bytes = new Uint8Array(buf);
    for (let i = 0; i < bytes.length; i += 8192) bin += String.fromCharCode.apply(null, bytes.subarray(i, i + 8192));
    const _dest = window.RIU_DESTINO_ARCHIVOS || (() => ({}));  // destinoArchivos(): unica autoridad de a donde van los archivos (chat / constitucion / proyecto seleccionado)
    const destinoExplicito = _dest();
    const projectId = String(q('#adjunto')?.dataset.riuUploadProject || '');
    const destinoCarga = projectId ? { destino: 'proyecto', project_id: projectId } : destinoExplicito;
    const r = await window.RIU_ACCION("subir", { nombre: file.name, tipo: file.type || "texto", datos_b64: btoa(bin), sesion: chat().sesion, ...destinoCarga });
    if (!r || r.error || r.ok !== true) {
      throw new Error('GAP_SUBIR: ' + String((r && (r.error || r.detalle)) || 'SIN_CONFIRMACION'));
    }
    // solo DESPUES se permite decir "Subido" y/o cambiar el Set de anclas
    if (anclarAlSubir) { chatA().anclados.add(r.nombre || file.name); pintarAnclados(); guardar(); tell("Subido y anclado: " + (r.nombre || file.name)); }
    else tell("Subido (sin anclar): " + (r.nombre || file.name));
  };
  const subirVarios = async (files) => {
    const lote = [...files]; let correctos = 0, fallidos = 0;
    for (const [i, f] of lote.entries()) {
      try { await subir(f); correctos++; }
      catch (err) { fallidos++; tell(f.name + ': ' + err.message); }
      if ((i + 1) % 10 === 0 || i + 1 === lote.length)
        tell('Subidas: ' + (i + 1) + '/' + lote.length + ' · PASS ' + correctos + ' · GAP ' + fallidos);
    }
    if (!q("#ventana-ancla").hidden) cargarArchivos("#anc-lista");
  };
  q("#btn-adjunto").addEventListener("click", () => { anclarAlSubir = false; delete q("#adjunto").dataset.riuUploadProject; q("#adjunto").click(); });
  q("#adjunto").addEventListener("change", async (e) => {
    try {
      const fs = [...e.target.files]; e.target.value = "";
      if (fs.length) await subirVarios(fs);
      anclarAlSubir = false;
    } finally { delete e.target.dataset.riuUploadProject; }
  });
  q("#anc-subir").addEventListener("click", () => { anclarAlSubir = true; q("#adjunto").click(); });
  const anclarTodos = async (encender) => {
    const r = await window.RIU_ACCION("archivos", { sesion: chat().sesion, ...window.RIU_DESTINO_ARCHIVOS() });  // misma autoridad que cargarArchivos/subir: chat/constitucion/proyecto
    for (const n of r.archivos || []) encender ? chatA().anclados.add(n) : chatA().anclados.delete(n);
    pintarAnclados(); guardar(); cargarArchivos("#anc-lista");
  };
  q("#anc-todos").addEventListener("click", () => anclarTodos(true).catch((err) => tell(err.message)));
  q("#anc-ninguno").addEventListener("click", () => anclarTodos(false).catch((err) => tell(err.message)));
  q("#btn-copiar-input").addEventListener("click", () => copiarTexto(q("#message").value));
  q("#btn-detener").addEventListener("click", () => {  // parar duro en TODOS los chats: detenerFn corta el envio en curso, RIU_CANCELAR corta el polling/retomado y avisa al Router, y si la promesa se perdio (tab suspendida/registro borrado) igual se limpia ocupado + pending para que el cubo no siga girando
    let algo = false;
    for (const c of chats) {
      c.detenerFlag = true;
      if (c.detenerFn) { try { c.detenerFn(); } catch (e) {} algo = true; }
      if (c.hist) c.hist.querySelectorAll(".pending").forEach((p) => { p.remove(); algo = true; });
      if (c.ocupado) { algo = true; c.ocupado = false; pintarTabs(); }
      if (window.RIU_CANCELAR) { try { window.RIU_CANCELAR(c.sesion); } catch (e) {} }
    }
    tell(algo ? "Detenido" : "No hay proceso en marcha");
  });

  const { cargarArchivos } = montarMotor({ chat, abajo, q, chatA, pintarAnclados, guardar, cerrarHojas, burbuja, tell });  // ventana del motor: descarga/extracción/copiar/mover entre repos → ventana-motor.js
  const { cargarSandbox } = await montarSandboxChat({ chat, q, api, tell });  // sandbox: system prompt de code anclado a esta sesión → ventana-sandbox-chat.js
  await montarSelectsSecundarios({ q, api, tell });  // selects secundarios (dentro de «más»): proveedor, modelo, agente, grupo, cuenta GitHub → selects-secundarios.js

  // ---- enviar: cada chat corre su tarea en paralelo con su sesion, su ficha y sus anclas ----
  if (window.__riuFastH) window.removeEventListener("riu:fast-reply-toggle", window.__riuFastH);
  window.__riuFastH = (ev) => { chat().fastReply = (ev && ev.detail && ev.detail.forzar) ? true : !chat().fastReply; pintarFastReply(); guardar(); tell(chat().fastReply ? "Respuesta rápida activada" : "Respuesta rápida desactivada"); };
  const pintarMotor = () => { const b = q("#btn-motor-on"); if (b) { b.classList.toggle("sel-on", !!chat().motor); b.setAttribute("aria-pressed", String(!!chat().motor)); } };
  const bmo = q("#btn-motor-on"); if (bmo) bmo.addEventListener("click", () => { chat().motor = !chat().motor; pintarMotor(); guardar(); tell(chat().motor ? "⚙ Motor ON: el modelo puede descargar, extraer, copiar y mover" : "⚙ Motor OFF"); });
  montarControlesChat({ q, chat, guardar, chatTools, pintarMotor, tell });  // botones del chat: paralelo, Agente tool, LLM tool y Proyectos → controles-chat.js
  // >>> MODOS BEGIN  (punto A: boton selector de modos junto a los del compositor; el backend es la autoridad)
  let modeUI = null;
  try {
    modeUI = await initModeSelector({
      mountEl: q("#mode-selector-mount"),
      registryUrl: "/chat/ui/modes_registry.json",
      conversationId: "panel",
      composerEl: q("#message"),
      thinkingToggleEl: q("#modo"),   // punto C: en modos autonomos el selector de thinking queda deshabilitado
    });
    window.RIU_MODE = modeUI;
  } catch (e) { try { console.warn("mode_selector no cargo:", e); } catch (_) {} }  // si el registro no responde, el chat sigue sin modos
  // <<< MODOS END
  montarEnviar({ q, chat, abajo, burbuja, ajustarAlturaEditor, pintarTabs, getModeUI: () => modeUI, releerAnclas, chatTools, FAST_SEL, getModo: () => modo, previo, api, tell });  // envío del mensaje: cada chat corre su tarea con su sesión, ficha, anclas, modos y herramientas → enviar-mensaje.js
  q("#message").addEventListener("keydown", event => {
    if (event.key === "Enter" && !event.shiftKey && window.matchMedia("(pointer: fine)").matches) {
      event.preventDefault();
      q("#composer").requestSubmit();
    }
  });

  montarBuzon({ q, chat, abajo, ajustarAlturaEditor, burbuja });  // buzón en vivo (Director → proceso) y cola de pendientes (modelo → Director) → buzon-proceso.js

}
