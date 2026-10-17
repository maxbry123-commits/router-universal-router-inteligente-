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
import { montarRoom } from "./room-conferencias.js";
import { montarTamano } from "./texto-tamano.js";
import { crearCola, devolverACaja, antesDeCola } from "./cola-envio.js";

const MODOS = { fast: "rápido", balanced: "equilibrado", think: "pensar" };
const MAX_CHAT = 10;
const CLAVE_CHATS = "riu_chats_v1";  // sesiones/anclas/ficha de cada pestaña: sobreviven a recargas en esta pestaña
const etiquetaCorta = (a) => a.startsWith("handoff:") ? a.slice(8) : a.startsWith("enlace:") ? a.slice(7, 40) : a.startsWith("raiz:") ? "raíz " + a.slice(5, 40) : a;

export async function mount(root, { api, tell }) {
  const q = (s) => root.querySelector(s);
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
  const medirCtl = () => { const s = document.querySelector(".topbar") || document.querySelector(".sidebar") || document.querySelector("#navigation"); const b = s ? Math.round(s.getBoundingClientRect().bottom) : 0; if (b > 0 && b < window.innerHeight * 0.8) document.documentElement.style.setProperty("--ctl-top", b + "px"); };  // la barra se pega justo debajo de la tira superior (.topbar en escritorio; .sidebar solo es la tira en movil)
  medirCtl(); window.addEventListener("resize", medirCtl);
  const previo = (c, message) => { const h = A.cargarHistorial(c.sesion).filter((m) => m.rol === "user" || m.rol === "bot"); if (h.length && h[h.length - 1].rol === "user" && h[h.length - 1].texto === message) h.pop(); return h.slice(-20).map((m) => ({ role: m.rol === "user" ? "user" : "assistant", content: m.texto })); };  // historial de ESTA sesion, aparte del input actual
  const previoTodo = (c, message) => { const h = A.cargarHistorial(c.sesion).filter((m) => m.rol === "user" || m.rol === "bot"); if (h.length && h[h.length - 1].rol === "user" && h[h.length - 1].texto === message) h.pop(); const out = []; let tam = 0; for (const m of h.slice(-20).reverse()) { const t = String(m.texto || ""); if (tam + t.length > 30000) break; tam += t.length; out.unshift({ role: m.rol === "user" ? "user" : "assistant", content: t }); } return out; };  // Team 5 MVP: ultimos 20 mensajes / ~30 KB: TODO el historial de ESTA sesion, con roles
  const chats = [];
  let activo = 0;
  const chat = () => chats[activo];
  const colaDe = (c) => c.cola || (c.cola = crearCola({ ocupado: () => !!c.ocupado, enviar: (x) => { enviar(c, x.texto, x.el); } }));  // una cola por chat (cada chat tiene su sesion)
  const chatA = () => (window.RIU_OBJETIVO_ANCLA ? window.RIU_OBJETIVO_ANCLA() : chat());  // objetivo del anclaje: el chat (por defecto) u otro (constitución, workflow, agentes, proyecto, sandbox)
  const guardar = () => {
    try {
      localStorage.setItem("riu_chat_activo", String(activo)); localStorage.setItem(CLAVE_CHATS, JSON.stringify(
        chats.map((c) => ({ sesion: c.sesion, ficha: c.ficha, anclados: [...c.anclados], instrucciones: c.instrucciones || "", selectorQwen: c.selectorQwen || null, fastReply: !!c.fastReply, motor: !!c.motor, project_id: c.project_id || null }))));
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
      const b = node("button", "Chat " + (i + 1) + (c.ocupado ? " …" : "") + (c.cola && c.cola.length ? " +" + c.cola.length : ""), "chip" + (i === activo ? " on" : ""));
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
    try { if (window.RIU_ROOM) window.RIU_ROOM.pintar(); } catch (e) {}  // ROOM CONFERENCIAS: su pestaña y su vista (si está activa, oculta el chat)
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
    }).finally(() => { c.ocupado = false; pintarTabs(); abajo(c); colaDe(c).siguiente(); });  // lo escrito mientras se retomaba sale ahora, en orden
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
  window.RIU_CHAT = { chat, ocupado: () => chats.some((x) => x.ocupado || (x.cola && x.cola.length)), tokens: () => [...chat().anclados], pintar: () => { pintarAnclados(); guardar(); } };  // ganchos para las ventanas de workflows / constitución / claves
  try { montarRoom({ q, tell }); } catch (e) { try { console.warn("room", e); } catch (x) {} }  // ROOM CONFERENCIAS junto a Chat 1/2/3
  try { montarTamano({ q, tell }); } catch (e) {}  // A− / A+ tamaño del texto del chat
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

  // ---- pildora de ficha: hoja con todas las fichas (por chat) ----
  const pintarFichas = () => {
    const lista = q("#sh-ficha-lista");
    lista.replaceChildren();
    for (const m of window.RIU_CONFIG?.modelos || []) {
      lista.append(fila(m.etiqueta.replace(/[\p{Extended_Pictographic}\uFE0F\u200D]/gu, "").trim(), "", m.id === chat().ficha, () => {
        chat().ficha = m.id;
        pintarFichaPill();
        pintarFichas();
        cerrarHojas();
        guardar();
      }));
    }
  };
  pintarFichas();

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

  // ---- selector de ancla: handoffs con boton de encender + pegar enlace/handoff propio ----
  const ANCLAS = [
    ["chat-router", "chat router/", "handoff del proyecto workflow Loops code Yaiwes"],
    ["skill", "SKILL.md", "handoff del skill maestro Maxbry UI FROMTED"],
    ["preview", "Preview Vercel", "handoff del panel-chat de prueba"],
  ];
  const pintarAnclas = () => {
    const lista = q("#sh-ancla-lista");
    lista.replaceChildren();
    for (const [k, t, d] of ANCLAS) {
      lista.append(filaEncender(t, d, "handoff:" + k, async (enc) => {
        if (!enc || window.RIU_OBJETIVO_ANCLA) return;
        try {  // muestra en el chat lo que quedo anclado
          const r = await window.RIU_ACCION("handoff", { fuente: k, sesion: chat().sesion });
          const c = chat();
          c.hist.append(burbuja("ANCLADO " + k + ":\n" + JSON.stringify(r.handoff || r, null, 1)));
          abajo(c);
        } catch (err) { tell(err.message); }
      }));
    }
    lista.append(fila("Auditor de code del repo", "ubica los archivos de code del proyecto", false, async (ev) => {
      ev.currentTarget.disabled = true;
      try {
        const r = await window.RIU_ACCION("auditor_code", { sesion: chat().sesion });
        cerrarHojas();
        const c = chat();
        c.hist.append(burbuja("AUDITOR CODE — " + r.total + " archivos:\n" + (r.carpetas || []).join("\n")));
        abajo(c);
      } catch (err) { tell(err.message); }
    }));
  };
  // mi handoff: texto propio guardado en memoria, editable; va interno con cada mensaje
  const cargarMiHandoff = async () => {
    try {
      const r = await window.RIU_ACCION("handoff_texto", { sesion: chatA().sesion });
      q("#mi-handoff").value = r.texto || "";
      q("#mh-estado").textContent = r.encendido ? "encendido" : "apagado";
    } catch (err) { q("#mh-estado").textContent = err.message; }
  };
  q("#mh-guardar").addEventListener("click", async () => {
    try {
      const texto = q("#mi-handoff").value;
      const r = await window.RIU_ACCION("handoff_texto", { sesion: chatA().sesion, texto });
      q("#mh-estado").textContent = r.encendido ? "encendido" : "apagado";
      if (r.encendido) {
        const c = chat();
        c.hist.append(burbuja("MI HANDOFF anclado:\n" + texto));
        abajo(c);
      }
      tell("Mi handoff " + (r.encendido ? "guardado y encendido" : "apagado"));
    } catch (err) { tell(err.message); }
  });
  q("#mh-apagar").addEventListener("click", async () => {
    try {
      await window.RIU_ACCION("handoff_texto", { sesion: chatA().sesion, texto: "" });
      q("#mh-estado").textContent = "apagado";
      tell("Mi handoff apagado");
    } catch (err) { tell(err.message); }
  });
  q("#ancla-enlace-on").addEventListener("click", () => {
    const v = (q("#ancla-enlace").value || "").trim();
    if (!v) { tell("Pega primero un enlace o handoff"); return; }
    chatA().anclados.add("enlace:" + v);
    q("#ancla-enlace").value = "";
    pintarAnclados(); guardar();
    tell("Enlace anclado al chat");
  });

  // ---- adjuntar y ventana de archivos (boton encender = anclar al chat + x-ray) ----
  let anclarAlSubir = false;  // true solo cuando se sube desde la ventana ⚓
  const subir = async (file) => {
    const buf = await file.arrayBuffer();
    if (buf.byteLength > 2_000_000) { tell("Archivo muy grande (máx ~2 MB)"); return; }
    let bin = ""; const bytes = new Uint8Array(buf);
    for (let i = 0; i < bytes.length; i += 8192) bin += String.fromCharCode.apply(null, bytes.subarray(i, i + 8192));
    const _dest = window.RIU_DESTINO_ARCHIVOS || (() => ({}));  // destinoArchivos(): unica autoridad de a donde van los archivos (chat / constitucion / proyecto seleccionado)
    const r = await window.RIU_ACCION("subir", { nombre: file.name, tipo: file.type || "texto", datos_b64: btoa(bin), sesion: chat().sesion, ..._dest() });
    if (anclarAlSubir) { chatA().anclados.add(r.nombre || file.name); pintarAnclados(); guardar(); tell("Subido y anclado: " + (r.nombre || file.name)); }
    else tell("Subido (sin anclar): " + (r.nombre || file.name));
  };
  const subirVarios = async (files) => {
    for (const f of files) { try { await subir(f); } catch (err) { tell(f.name + ": " + err.message); } }
    if (!q("#ventana-ancla").hidden) cargarArchivos("#anc-lista");
  };
  q("#btn-adjunto").addEventListener("click", () => { anclarAlSubir = false; q("#adjunto").click(); });
  q("#adjunto").addEventListener("change", async (e) => {
    const fs = [...e.target.files]; e.target.value = "";
    if (fs.length) await subirVarios(fs);
    anclarAlSubir = false;
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
    let algo = false; const enCola = [];
    for (const c of chats) {
      if (c.cola && c.cola.length) { enCola.push(...c.cola.vaciar().map((x) => x.texto)); algo = true; }  // la cola no sigue tras Detener: sus textos vuelven a la caja
      c.detenerFlag = true;
      if (c.detenerFn) { try { c.detenerFn(); } catch (e) {} algo = true; }
      if (c.hist) c.hist.querySelectorAll(".pending").forEach((p) => { p.remove(); algo = true; });
      if (c.ocupado) { algo = true; c.ocupado = false; pintarTabs(); }
      if (window.RIU_CANCELAR) { try { window.RIU_CANCELAR(c.sesion); } catch (e) {} }
    }
    devolverACaja(q("#message"), enCola); if (enCola.length) pintarTabs();
    tell(algo ? "Detenido" + (enCola.length ? " · " + enCola.length + " en cola devuelto(s) a la caja" : "") : "No hay proceso en marcha");
  });

  // ---- ventana del motor: descarga/extraccion/copiar/mover entre repos ----
  const extraerUrls = (t) => { const s = new Set(); (String(t || "").match(/https?:\/\/[^\s"'<>)\]]+/g) || []).forEach((u) => s.add(u.replace(/[.,;:!?]+$/g, ""))); return [...s]; };
  const motorConfirma = (t) => { chat().hist.append(node("div", t, "item message meta")); abajo(chat()); };
  const mm = q("#motor-mover"), mc = q("#motor-copiar");
  mm.addEventListener("change", () => { if (mm.checked) mc.checked = false; else if (!mc.checked) mm.checked = true; });
  mc.addEventListener("change", () => { if (mc.checked) mm.checked = false; else if (!mm.checked) mc.checked = true; });
  const motorEjecutar = async (origen, destino, op) => {
    if (!origen || !destino) { tell("Falta el enlace de origen o de destino"); return null; }
    try {
      const r = await window.RIU_ACCION("mover_raiz", { op, origen, destino, sesion: chat().sesion });
      if (r.error) { motorConfirma("motor: GAP " + r.error + " — " + (r.detalle || "")); return r; }
      motorConfirma(r.op + " ✓ " + r.archivos + " archivo(s) · " + r.estado + " · " + r.registro + (r.fallos && r.fallos.length ? " · fallos: " + r.fallos.join(", ") : ""));
      return r;
    } catch (e) { motorConfirma("motor: GAP " + e.message); return null; }
  };
  q("#motor-ejecutar").addEventListener("click", async () => {
    await motorEjecutar(q("#motor-origen").value.trim(), q("#motor-destino").value.trim(), mm.checked ? "mover" : "copiar");
  });
  q("#motor-archivo-btn").addEventListener("click", () => q("#motor-archivo").click());
  q("#motor-archivo").addEventListener("change", async (e) => {
    const f = e.target.files[0]; e.target.value = "";
    if (!f) return;
    const txt = await f.text();
    const urls = extraerUrls(txt);
    const viejo = q("#motor-urls").value.trim();
    q("#motor-urls").value = (viejo ? viejo + "\n" : "") + urls.join("\n");
    motorConfirma("archivo " + f.name + ": " + urls.length + " URL(s) visibles extraídas");
  });
  q("#motor-activar").addEventListener("click", async () => {
    const urls = extraerUrls(q("#motor-urls").value);
    const dest = q("#motor-destino2").value.trim() || q("#motor-destino").value.trim();
    if (!urls.length || !dest) { tell("Pega las URLs y el enlace destino"); return; }
    q("#motor-cola").textContent = "cola: " + urls.length + " descarga(s)";
    for (let i = 0; i < urls.length; i++) {
      q("#motor-cola").textContent = "cola: " + (i + 1) + "/" + urls.length + " → " + urls[i].slice(0, 60);
      await motorEjecutar(urls[i], dest, "copiar");
    }
    q("#motor-cola").textContent = "cola terminada: " + urls.length + "/" + urls.length;
  });
  q("#motor-auditar").addEventListener("click", async () => {
    const lista = q("#motor-hist");
    lista.replaceChildren(node("div", "Cargando…", "muted"));
    try {
      const r = await window.RIU_ACCION("descargas", { op: "lista", sesion: chat().sesion });
      lista.replaceChildren();
      const items = (r.lista || []).slice().reverse();
      if (!items.length) { lista.append(node("div", "Sin descargas en la bitácora", "muted")); return; }
      items.forEach((d) => {
        const b = node("button", "", "fila");
        b.type = "button";
        b.append(node("span", (d.estado === "procesando" ? "… " : d.estado === "completado" ? "✓ " : "! ") + d.op + " " + (d.archivos || 0) + " archivos · " + d.id, "fila-nom"));
        b.addEventListener("click", async () => {
          const v = await window.RIU_ACCION("descargas", { op: "ver", id: d.id, sesion: chat().sesion });
          q("#motor-detalle").textContent = JSON.stringify(v, null, 1).slice(0, 4000);
        });
        lista.append(b);
      });
    } catch (e) { lista.replaceChildren(node("div", "GAP " + e.message, "muted")); }
  });
  const cargarArchivos = async (destino = "#va-lista") => {
    const lista = q(destino);
    lista.replaceChildren(node("div", "Cargando…", "muted"));
    try {
      const r = await window.RIU_ACCION("archivos", { sesion: chat().sesion, ...window.RIU_DESTINO_ARCHIVOS() });  // lista del objetivo actual (chat/constitucion/proyecto seleccionado), no siempre del chat
      lista.replaceChildren();
      for (const nombre of r.archivos || []) {
        const fil = node("div", "", "va-item");
        const t = node("button", "", "toggle" + (chatA().anclados.has(nombre) ? " on" : ""));
        t.type = "button"; t.title = "Encender = anclar al chat, apagar = quitar";
        t.addEventListener("click", () => {
          const enc = !chatA().anclados.has(nombre);
          enc ? chatA().anclados.add(nombre) : chatA().anclados.delete(nombre);
          t.classList.toggle("on", enc);
          pintarAnclados(); guardar();
        });
        const nom = node("span", nombre, "fila-nom");
        const xr = node("button", "X-Ray", "mini");
        xr.type = "button"; xr.title = "Auditoría forense del archivo";
        xr.addEventListener("click", async () => {
          xr.disabled = true;
          try {
            const r2 = await window.RIU_ACCION("xray", { nombre, sesion: chat().sesion });
            cerrarHojas();
            const c = chat();
            c.hist.append(burbuja("X-RAY " + (r2.nombre || nombre) + "\n" + (r2.estructura || "") +
              "\nURLs: " + (r2.urls || []).join(", ") + "\nMAPA:\n" + (r2.mapa_mental || "") +
              "\nFLUJO: " + (r2.microflujo || "") + "\n" + (r2.resumen_goals || "")));
            abajo(c);
          } catch (err) { tell(err.message); }
        });
        fil.append(nom, t, xr);
        lista.append(fil);
      }
      if (!(r.archivos || []).length) lista.append(node("div", "No hay archivos subidos en este chat", "muted"));
    } catch (err) { lista.replaceChildren(node("div", err.message, "item message error")); }
  };

  // ---- sandbox: system prompt de code anclado a esta sesion ----
  const cargarSandbox = async () => {
    try {
      const r = await window.RIU_ACCION("sandbox", { sesion: chat().sesion });
      q("#sandbox-texto").value = r.sandbox || "";
      q("#sb-estado").textContent = r.sandbox ? "encendido" : "apagado";
    } catch (err) { q("#sb-estado").textContent = err.message; }
  };
  q("#sb-guardar").addEventListener("click", async () => {
    try {
      const r = await window.RIU_ACCION("sandbox", { sesion: chat().sesion, texto: q("#sandbox-texto").value });
      q("#sb-estado").textContent = r.encendido ? "encendido" : "apagado";
      tell("Sandbox " + (r.encendido ? "encendido y anclado" : "apagado"));
    } catch (err) { tell(err.message); }
  });
  q("#sb-apagar").addEventListener("click", async () => {
    try {
      await window.RIU_ACCION("sandbox", { sesion: chat().sesion, texto: "" });
      q("#sb-estado").textContent = "apagado";
      tell("Sandbox apagado");
    } catch (err) { tell(err.message); }
  });

  // ---- selects secundarios (dentro de más) ----
  const select = (id, options, value, label) => {
    const target = q(id);
    for (const item of options) {
      const option = node("option", item[label]);
      option.value = item[value];
      target.append(option);
    }
  };
  try {
    const providers = await api("/chat/providers");
    select("#provider", (providers.providers || []).filter(item => item.id !== "auto"), "id", "label");
    select("#agent", (await api("/chat/agents")).agents || [], "id", "name");
    const accounts = await api("/chat/github/accounts");
    select("#github", accounts.accounts || [], "account", "account");
  } catch (error) { tell(error.message); }
  q("#provider").addEventListener("change", async event => {
    const model = q("#model");
    model.replaceChildren(node("option", "Router elige"));
    if (event.target.value === "auto") return;
    try { select("#model", (await api(`/chat/providers/${encodeURIComponent(event.target.value)}/models`)).models || [], "model_id", "label"); }
    catch (error) { tell(error.message); }
  });

  // ---- enviar: cada chat corre su tarea en paralelo con su sesion, su ficha y sus anclas ----
  if (window.__riuFastH) window.removeEventListener("riu:fast-reply-toggle", window.__riuFastH);
  window.__riuFastH = (ev) => { chat().fastReply = (ev && ev.detail && ev.detail.forzar) ? true : !chat().fastReply; pintarFastReply(); guardar(); tell(chat().fastReply ? "Respuesta rápida activada" : "Respuesta rápida desactivada"); };
  const pintarMotor = () => { const b = q("#btn-motor-on"); if (b) { b.classList.toggle("sel-on", !!chat().motor); b.setAttribute("aria-pressed", String(!!chat().motor)); } };
  const bmo = q("#btn-motor-on"); if (bmo) bmo.addEventListener("click", () => { chat().motor = !chat().motor; pintarMotor(); guardar(); tell(chat().motor ? "⚙ Motor ON: el modelo puede descargar, extraer, copiar y mover" : "⚙ Motor OFF"); });
  pintarMotor();
  const bpr = q("#btn-proyectos"); if (bpr) bpr.addEventListener("click", () => { if (window.RIU_ANCLA_ABRIR) window.RIU_ANCLA_ABRIR("proyecto"); });  // misma ventana-ancla, objetivo Proyecto
  window.addEventListener("riu:fast-reply-toggle", window.__riuFastH);
  q("#composer").addEventListener("submit", async event => {
    chat().hist.__sigue = true;  // al enviar vuelves al final
    event.preventDefault();
    const c = chat();
    const input = q("#message");
    const message = input.value.trim();
    if (!message) return;
    if (message === "/ayuda") { tell("Elige modelo en la píldora, enciende anclas/archivos y envía. /ayuda no ejecuta modelos."); return; }
    if (c.ocupado || colaDe(c).length) {  // escribir sin esperar: la caja sigue libre; el mensaje queda "en cola" en el hilo y sale al terminar la respuesta actual
      const ub = burbuja(message, "user"); c.hist.append(ub); input.value = "";
      colaDe(c).poner({ texto: message, el: ub }); pintarTabs(); abajo(c); input.focus(); return;  // el foco vuelve a la caja: sigues escribiendo
    }
    await enviar(c, message, null);
  });
  const enviar = async (c, message, ubCola) => { try { await enviar0(c, message, ubCola); } finally { colaDe(c).siguiente(); } };  // al terminar (bien, error o Detener) sale el siguiente en cola
  const enviar0 = async (c, message, ubCola) => {
    const input = q("#message");
    const noSale = (t) => { if (ubCola) { ubCola.remove(); devolverACaja(input, [message]); } c.hist.append(node("div", t, "item message meta")); abajo(c); };  // un mensaje en cola que no puede salir vuelve a la caja
    const selAct = window.RIU_SELECTORES?.activo;  // solo "Nvidia groq team" tiene modelos reales en el Router hoy
    const fichaQwen = selAct === "team-qwen" && c.selectorQwen ? "qw-" + c.selectorQwen.modelo_id_slug : null;  // Team qwen: su ficha, mismo camino que Nvidia
    const fichaMvp = selAct === "team-5-mvp";  // Team 5 MVP: ruta propia -> fichas_qwen ficha_qwen=5 (1 modelo elegido, historial completo y tools)
    if (fichaMvp && !c.selectorQwen) {
      noSale("Team 5 MVP: elige primero un modelo en la hoja Team 5 MVP ⌄ (el mismo catalogo de la Ficha 1 / Team qwen). No se envio a otro modelo.");
      return;
    }
    const CONSIL_LISTO = /^(ask-consil-code-qwen-team|ask-consil-fromtend-qwen-team|ask-consil-nvidia-groq)$/;  // Ask Consil cableados al Router; nvidia-groq va como CONSULTA a la ficha ask-consil-factory
    if (selAct && selAct !== "nvidia-groq-team" && !fichaQwen && !CONSIL_LISTO.test(selAct) && !fichaMvp) {
      const nomSel = (window.RIU_SELECTORES.selectores.find((x) => x.id === selAct) || {}).nombre || selAct;
      const det = selAct === "team-qwen" ? (c.selectorQwen ? " · " + c.selectorQwen.label : " · sin modelo elegido") : "";
      noSale(nomSel + det + ": sin IA conectada en el Router (no hay proveedor ni clave para estos modelos). No se envió a otro modelo. Enciende Nvidia groq team o apaga el selector.");
      return;
    }
    if (ubCola) antesDeCola(c.hist, ubCola); else { c.hist.append(burbuja(message, "user")); input.value = ""; }  // el de la cola ya esta pintado: solo baja al final
    A.registrar(c.sesion, "user", message);
    c.ocupado = true; pintarTabs();
    const pending = node("div", "Enviando…", "item message pending");  // Enviando hasta que el Router confirma proceso_id; luego riu-progreso pone Pensando/tools
    antesDeCola(c.hist, pending);  // lo que sigue en cola queda debajo
    const alProgreso = (e) => {
      if (!pending.isConnected) { window.removeEventListener('riu-progreso', alProgreso); return; }  // listener fuera solo si la burbuja desaparecio (o en finally)
      const d = e.detail;
      if (!d || d.sesion !== c.sesion) return;  // evento de otro chat: ignorar, no quitarse
      const v = window.RIU_PENDIENTE && window.RIU_PENDIENTE(c.sesion);  // progreso aislado: solo mi sesion y, si hay PID guardado, solo mi proceso
      if (v && v.pid && d.proceso_id && d.proceso_id !== v.pid) return;
      if (d.parcial) { const ya = pending.classList.contains('parcial') ? pending.textContent : ''; if (ya && d.parcial.startsWith(ya)) { if (d.parcial.length > ya.length) pending.append(d.parcial.slice(ya.length)); } else pending.textContent = d.parcial; pending.classList.add('parcial'); try { abajo(c); } catch (x) {} return; }  // render incremental: solo se anade el trozo nuevo  // texto parcial en stream dentro de la burbuja; la final la reemplaza (pending.remove)
      if (pending.classList.contains('parcial')) return;  // ya hay texto parcial: no volver a 'Pensando…'
      pending.textContent = d.texto !== undefined ? d.texto : d;
    };
    window.addEventListener('riu-progreso', alProgreso);
    try { abajo(c); } catch (e) {}
    const agent = (q("#agent") || {}).value || "";
    const provider = (q("#provider") || {}).value || "";
    const model = (q("#model") || {}).value || "";
    const max_tokens = { fast: 512, balanced: 1024, think: 2048 }[modo];
    try {
      const selAct = window.RIU_SELECTORES?.activo;  // selectores Qwen -> plugin fichas_qwen (fichas 1, 2, 3 y 5 = Team 5 MVP)
      const fq = selAct === "team-qwen" ? "1" : selAct === "ask-consil-code-qwen-team" ? "2" : selAct === "ask-consil-fromtend-qwen-team" ? "3" : null;
      const mvp = selAct === "team-5-mvp" ? { plugin: "fichas_qwen", ficha_qwen: "5", modelo: c.selectorQwen ? c.selectorQwen.label : "", instrucciones_fijas: c.instrucciones || "" } : null;  // Team 5 MVP: fichas_qwen ficha_qwen=5, sin N4, sin fallback
      const body = { message: mvp ? message : A.envolver(message, c.instrucciones), ficha: fichaQwen || (selAct === "ask-consil-nvidia-groq" ? "ask-consil-factory" : c.ficha), provider, model, mode: agent ? "agent" : "direct", agent_id: agent || null, max_tokens: mvp ? 0 : max_tokens, fast_reply: !!c.fastReply && FAST_SEL(), motor: !!c.motor, project_id: c.project_id || null, ...(fq ? { plugin: "fichas_qwen", ficha_qwen: fq, modelo: fq === "1" && c.selectorQwen ? c.selectorQwen.label : "", task_type: "chat" } : {}), ...(mvp || {}) };  // MVP: input literal + instrucciones_fijas aparte, max_tokens lo decide la ficha
      // con harnessUrl el mensaje va al harness DeepSeek (y este a la memoria por su plugin); si no, al Router como hoy
      c.detenerFlag = false;
      const raceDetener = new Promise((_, rej) => { c.detenerFn = () => rej(new Error("PROCESO_DETENIDO")); });  // Detener ya vale desde aqui: tambien mientras se restaura el historial o se arma el contexto
      const ctxPrev = selAct === "ask-consil-code-qwen-team" ? previo(c, message) : undefined;  // Team 5 MVP: SIN contexto_previo -> contexto_explicito=false -> el Harness lee memoria_yaiwes; consil-code: ultimos 20
      const answer = window.RIU_CONFIG?.harnessUrl
        ? await Promise.race([window.RIU_HARNESS({ model: fichaQwen || (selAct === "ask-consil-nvidia-groq" ? "ask-consil-factory" : c.ficha), message: mvp ? message : A.envolver(message, c.instrucciones), max_tokens: mvp ? 0 : max_tokens, fast_reply: !!c.fastReply && FAST_SEL(), motor: !!c.motor, project_id: c.project_id || null, contexto_previo: ctxPrev, anclados: [...c.anclados], sesion: c.sesion, qwen: fq ? { plugin: "fichas_qwen", ficha_qwen: fq, modelo: fq === "1" && c.selectorQwen ? c.selectorQwen.label : "", task_type: "chat" } : (mvp || null), avisar: (t) => c.hist.append(node('div', t, 'item message')) }), raceDetener])
        : await Promise.race([api("/chat/send", { method: "POST", body }), raceDetener]);
      c.detenerFn = null;
      if (c.detenerFlag) throw new Error("PROCESO_DETENIDO");  // detenido mientras la respuesta llegaba: no pintar respuesta tardia
      pending.remove();
      c.hist.append(burbuja(answer.reply || "Sin respuesta"));
      A.registrar(c.sesion, "bot", answer.reply || "Sin respuesta");
      if (answer.execution_path === "FAST_QA") c.hist.append(node("div", "⚡ respuesta rápida · " + answer.ms + " ms", "item meta"));
      else if (answer.execution_path === "FAST_CONSULT") c.hist.append(node("div", "⚡ cónsil rápido · " + answer.ms + " ms", "item meta"));
      else if (c.fastReply && FAST_SEL() && answer.execution_path === "HEAVY") c.hist.append(node("div", "Respuesta rápida omitida: la tarea requiere flujo completo", "item meta"));
      if (answer.tools && answer.tools.length) { const meta = node("div", "Herramientas usadas: ", "item message meta"); answer.tools.forEach((t, i) => { const ok = typeof t === "string" || t.ok; const s = document.createElement("span"); s.textContent = (typeof t === "string" ? t : t.nombre) + (ok ? "" : " (fallo)"); if (!ok) s.className = "tool-fail"; if (i) meta.append(", "); meta.append(s); }); c.hist.append(meta); }
      if (answer.job_id) { window.__riuJob = answer.job_id; const ar = q('#apagar-respaldo'); if (ar) ar.hidden = false; }
      abajo(c);
    } catch (error) {
      pending.remove();
      A.registrar(c.sesion, "err", (c.detenerFlag || /PROCESO_DETENIDO/.test(String(error && error.message))) ? "proceso detenido por el usuario" : "GAP: " + error.message);
      c.hist.append(node("div", (c.detenerFlag || /PROCESO_DETENIDO/.test(String(error && error.message))) ? "proceso detenido por el usuario" : `GAP: ${error.message}`, "item message" + (c.detenerFlag || /PROCESO_DETENIDO/.test(String(error && error.message)) ? " meta" : " error")));
      abajo(c);
      if (!(c.detenerFlag || /PROCESO_DETENIDO/.test(String(error && error.message))) && !input.value) { input.value = message; input.dispatchEvent(new Event("input", { bubbles: true })); }  // si falla, el mensaje vuelve a la caja
    } finally {
      window.removeEventListener('riu-progreso', alProgreso);  // listener fuera al terminar/error/cancelar
      c.detenerFn = null; c.ocupado = false; pintarTabs(); colaDe(c).siguiente();  // en el mismo paso que pinta la respuesta: la cola baja debajo de ella
      if (window.matchMedia("(pointer: fine)").matches) input.focus();
    }
  };
  q("#message").addEventListener("keydown", event => {
    if (event.key === "Enter" && !event.shiftKey && window.matchMedia("(pointer: fine)").matches) {
      event.preventDefault();
      q("#composer").requestSubmit();
    }
  });


}
