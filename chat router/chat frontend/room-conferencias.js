// room-conferencias.js — sección ROOM CONFERENCIAS junto a Chat 1/2/3: varias LLM y el usuario debaten en una sala.
// Eliges participantes (los mismos selectores: Team qwen/DeepSeek/GLM = ficha 1, Ask cónsil code = 2, Ask consil frontend = 3, NVIDIA)
// y el número de rondas; en cada ronda los modelos hablan EN ORDEN y cada uno ve la transcripción de los demás.
// Ruta: la misma del chat -> window.RIU_HARNESS -> plugin puente_chat por HTTP (chat_async + /resultado). No toca fichas.
// Historial: la misma memoria del chat (chat-ancla: IndexedDB + cache localStorage) con su propia sesión room-*; el Router la guarda por sesión.
import { node } from "./api.js";
import * as A from "./chat-ancla.js";

const CLAVE = "riu_room_v1";
const MAX_RONDAS = 5;  // participantes: sin tope, pueden entrar todos los selectores ("Todos")
const leer = () => { try { return JSON.parse(localStorage.getItem(CLAVE) || "{}") || {}; } catch (e) { return {}; } };
const PREF = /^\[\[([^\]\n]{1,60})\]\]\n?/;  // "[[Nombre]]\ntexto": quién habló, guardado dentro del mismo historial

function participantes() {
  const cat = ((window.RIU_SELECTOR_QWEN || {}).modelos || []).filter((m) => /^(Qwen|DeepSeek|GLM)$/.test(m.grupo));
  const def = (window.RIU_CONFIG || {}).defecto || "nv-muse-glimmer";
  return [
    ...cat.map((m) => ({ id: "f1:" + m.modelo_id_slug, nombre: m.label, model: "qw-" + m.modelo_id_slug, qwen: { plugin: "fichas_qwen", ficha_qwen: "1", modelo: m.label, task_type: "chat" } })),
    { id: "f2", nombre: "Ask cónsil code", model: def, qwen: { plugin: "fichas_qwen", ficha_qwen: "2", modelo: "", task_type: "chat" } },
    { id: "f3", nombre: "Ask consil frontend", model: def, qwen: { plugin: "fichas_qwen", ficha_qwen: "3", modelo: "", task_type: "chat" } },
    { id: "nv", nombre: "NVIDIA Glimmer", model: def, qwen: null },
  ];
}

export function montarRoom({ q, tell }) {
  const tabsEl = q("#chat-tabs"), histEl = q("#histories"), composer = q("#composer");
  if (!tabsEl || !histEl || !composer) return null;
  const st = Object.assign({ activo: false, sesion: "room-" + Math.random().toString(36).slice(2, 10), part: ["f1:qwen-3-8-flash", "f1:deepseek-v4-flash"], rondas: 1 }, leer());
  const guardar = () => { try { localStorage.setItem(CLAVE, JSON.stringify({ activo: st.activo, sesion: st.sesion, part: st.part, rondas: st.rondas })); } catch (e) {} };
  let ocupado = false, parar = false, cortar = null;  // cortar: Detener no espera a que el Router termine el turno en curso
  let tema = "", interv = "";  // tema: mensaje que abrió el debate; interv: lo último que dijo el Usuario EN MEDIO del debate

  // ---- vista ----
  const vista = node("div", "", "room-view"); vista.hidden = true;
  const cfg = node("div", "", "room-cfg");
  const lista = node("div", "", "room-part"); lista.setAttribute("role", "group"); lista.setAttribute("aria-label", "Participantes");
  const rond = node("div", "", "room-rondas");
  const menos = node("button", "−", "chip"), mas = node("button", "+", "chip"), nR = node("span", "", "room-n");
  [menos, mas].forEach((b) => { b.type = "button"; });
  menos.setAttribute("aria-label", "Menos rondas"); mas.setAttribute("aria-label", "Más rondas");
  rond.append(node("span", "Rondas", "muted"), menos, nR, mas);
  const limpiar = node("button", "Nueva sala", "chip room-nueva"); limpiar.type = "button"; limpiar.title = "Empieza una sala vacía (la anterior queda guardada en la memoria)";
  rond.append(limpiar);
  cfg.append(lista, rond);
  const hist = node("div", "", "chat-history room-hist"); hist.setAttribute("role", "log"); hist.hidden = true;
  hist.addEventListener("scroll", () => { hist.__sigue = hist.scrollHeight - hist.scrollTop - hist.clientHeight < 90; }, { passive: true });
  const form = node("form", "", "room-form");
  const caja = document.createElement("textarea"); caja.id = "room-msg"; caja.placeholder = "Tema o mensaje para la sala…"; caja.setAttribute("aria-label", "Mensaje para la sala"); caja.autocomplete = "off";
  const bStop = node("button", "Detener", "secondary room-stop"); bStop.type = "button"; bStop.hidden = true;
  const bEnv = node("button", "Debatir", "action room-enviar"); bEnv.type = "submit";
  const barra = node("div", "", "row room-barra"); barra.append(node("span", "", "room-estado muted"), bStop, bEnv);
  form.append(caja, barra);
  vista.append(cfg, hist, form);
  histEl.append(vista);
  const estado = barra.querySelector(".room-estado");
  const abajo = () => { if (hist.__sigue !== false) hist.scrollTop = hist.scrollHeight; };

  const pintarCfg = () => {
    const P = participantes(); lista.replaceChildren();
    st.part = st.part.filter((id) => P.some((p) => p.id === id));
    const todos = st.part.length === P.length;  // "Todos": un toque añade TODOS los selectores; otro toque los quita
    const bT = node("button", "Todos", "chip room-p room-todos" + (todos ? " on" : "")); bT.type = "button"; bT.setAttribute("aria-pressed", String(todos));
    bT.title = todos ? "Quitar a todos" : "Añadir a todos los modelos como participantes";
    bT.addEventListener("click", () => { if (ocupado) return; st.part = todos ? [] : [...st.part, ...P.map((p) => p.id).filter((id) => !st.part.includes(id))]; guardar(); pintarCfg(); });
    lista.append(bT);
    P.forEach((p) => {
      const on = st.part.includes(p.id), orden = st.part.indexOf(p.id) + 1;
      const b = node("button", (on ? orden + "· " : "") + p.nombre, "chip room-p" + (on ? " on" : ""));
      b.type = "button"; b.dataset.id = p.id; b.setAttribute("aria-pressed", String(on));
      b.addEventListener("click", () => {
        if (ocupado) return;
        if (st.part.includes(p.id)) st.part = st.part.filter((x) => x !== p.id);
        else st.part.push(p.id);
        guardar(); pintarCfg();
      });
      lista.append(b);
    });
    nR.textContent = String(st.rondas);
    menos.disabled = ocupado || st.rondas <= 1; mas.disabled = ocupado || st.rondas >= MAX_RONDAS;
  };
  menos.addEventListener("click", () => { st.rondas = Math.max(1, st.rondas - 1); guardar(); pintarCfg(); });
  mas.addEventListener("click", () => { st.rondas = Math.min(MAX_RONDAS, st.rondas + 1); guardar(); pintarCfg(); });

  const burbuja = (texto, cls) => {
    let quien = "", t = String(texto == null ? "" : texto);
    const m = !cls && t.match(PREF); if (m) { quien = m[1]; t = t.slice(m[0].length); }
    const d = node("div", "", "item message room-msg" + (cls ? " " + cls : ""));
    if (quien) d.append(node("div", quien, "room-quien"));
    const span = node("span", t, "txt"); d.append(span);
    const b = node("button", "⧉", "copiar"); b.type = "button"; b.title = "Copiar esta salida";
    b.addEventListener("click", () => { try { navigator.clipboard.writeText(span.textContent); } catch (e) {} });
    d.append(b);
    return d;
  };
  const listo = A.restaurar({ sesion: st.sesion, hist }, burbuja);
  limpiar.addEventListener("click", () => {
    if (ocupado) return;
    st.sesion = "room-" + Math.random().toString(36).slice(2, 10); guardar();
    hist.replaceChildren(); tell("Sala nueva");
  });

  // ---- debate ----
  const turnos = () => {  // ultimos turnos de la sala (~9 KB): [{ quien, texto, user }]
    const h = A.cargarHistorial(st.sesion).filter((x) => x.rol === "user" || x.rol === "bot");
    const out = []; let tam = 0;
    for (const x of h.slice(-24).reverse()) {
      const m = x.rol === "bot" && String(x.texto).match(PREF);
      const t = { quien: x.rol === "user" ? "Usuario" : m ? m[1] : "Modelo", texto: m ? String(x.texto).slice(m[0].length) : String(x.texto), user: x.rol === "user" };
      if (tam + t.texto.length > 9000) break; tam += t.texto.length; out.unshift(t);
    }
    return out;
  };
  const orden = (p, nombres, r, R) => "SALA DE CONFERENCIAS. Participan: Usuario, " + nombres.join(", ") + ". Ronda " + r + " de " + R + ". " +
    "Eres «" + p.nombre + "». Responde SOLO con tu propia intervención como «" + p.nombre + "»: aporta tu postura, coincide o rebate a los demás citando su nombre, sin repetir lo ya dicho y sin copiar la conversación. Máximo 120 palabras, en español.";
  // fichas Qwen: la conversación va en contexto_previo (historial aparte) y el input es solo la orden + el tema del Usuario,
  // así la puerta de capacidades del Router mira lo que pidió el Usuario y no las palabras que escribieron los otros modelos.
  // NVIDIA (puente_chat directo, sin contexto_previo): la conversación va dentro del mensaje.
  const armar = (p, nombres, r, R) => {
    const T = turnos(), ult = [...T].reverse().find((t) => t.user), t0 = tema || (ult && ult.texto);
    const usr = interv ? "\n\nEl Usuario intervino en el debate: «" + interv + "». Respóndele a él directamente (llámalo Usuario) además de a los demás." : "";
    if (p.qwen) return { message: orden(p, nombres, r, R) + (t0 ? "\n\nTema del Usuario: " + t0 : "") + usr, contexto_previo: T.map((t) => ({ role: t.user ? "user" : "assistant", content: "[" + t.quien + "]: " + t.texto })) };
    return { message: "Conversación de la sala:\n" + T.map((t) => "[" + t.quien + "]: " + t.texto).join("\n\n") + "\n\n" + orden(p, nombres, r, R) + usr };
  };
  const limpia = (p, t) => String(t || "").replace(new RegExp("^\\s*(\\*\\*)?\\[?«?" + p.nombre.replace(/[.*+?^${}()|[\]\\]/g, "\\$&") + "»?\\]?(\\*\\*)?\\s*:\\s*(\\*\\*)?\\s*", "i"), "").trim();  // quita el "**Nombre**:" que algunos modelos anteponen
  const turno = async (p, nombres, r, R) => {
    const pend = node("div", p.nombre + " · pensando…", "item message pending room-pend"); hist.append(pend); abajo();
    const alProg = (e) => { const d = e.detail; if (!d || d.sesion !== st.sesion) return; if (d.parcial) { pend.textContent = p.nombre + ": " + d.parcial; abajo(); } else if (d.texto && !d.parcial) pend.textContent = p.nombre + " · " + d.texto; };
    window.addEventListener("riu-progreso", alProg);
    const t0 = performance.now();
    try {
      const corte = new Promise((_, rej) => { cortar = () => rej(new Error("PROCESO_DETENIDO")); });
      const ans = await Promise.race([window.RIU_HARNESS({ model: p.model, ...armar(p, nombres, r, R), max_tokens: 700, sesion: st.sesion, qwen: p.qwen, avisar: (t) => { pend.textContent = p.nombre + " · " + t; } }), corte]);
      let txt = String((ans && ans.reply) || ""), via = "";
      const hc = txt.match(/^\s*ASK CONSIL(?: FRONTEND)?\s*\n+([^\n:]{1,40}):[ \t]*\n/);  // cabecera de Ask cónsil ("ASK CONSIL / DeepSeek V4 Pro:"): el modelo real pasa a la etiqueta
      if (hc) { via = " · " + hc[1].trim(); txt = txt.slice(hc[0].length); }
      txt = limpia(p, txt) || "Sin respuesta";
      const ms = Math.round(performance.now() - t0);
      pend.remove();
      const b = burbuja("[[" + p.nombre + via + "]]\n" + txt); b.dataset.ms = String(ms); hist.append(b);
      A.registrar(st.sesion, "bot", "[[" + p.nombre + via + "]]\n" + txt);
      hist.append(node("div", p.nombre + " · " + Math.floor(ms / 1000) + " s " + String(ms % 1000).padStart(3, "0") + " ms", "item meta room-ms"));
    } catch (err) {
      pend.remove();
      const msg = parar ? "proceso detenido por el usuario" : "GAP " + p.nombre + ": " + ((err && err.message) || err);
      hist.append(burbuja(msg, parar ? "meta" : "error")); A.registrar(st.sesion, "err", msg);
    } finally { cortar = null; window.removeEventListener("riu-progreso", alProg); abajo(); }
  };
  form.addEventListener("submit", async (ev) => {
    ev.preventDefault();
    const texto = caja.value.trim();
    if (!texto) return;
    if (ocupado) {  // el Usuario también participa: su mensaje entra en la sala y los siguientes turnos lo ven y le responden
      caja.value = ""; hist.__sigue = true;
      hist.append(burbuja(texto, "user")); A.registrar(st.sesion, "user", texto); interv = texto; abajo(); return;
    }
    const P = participantes(), sel = st.part.map((id) => P.find((p) => p.id === id)).filter(Boolean);
    if (!sel.length) { tell("Elige al menos un participante"); return; }
    if (!window.RIU_HARNESS || !(window.RIU_CONFIG || {}).harnessUrl) { tell("Router aún sin conectar: espera un momento"); return; }
    await listo;
    ocupado = true; parar = false; bStop.hidden = false; bEnv.textContent = "Intervenir"; caja.placeholder = "Intervén en el debate…"; pintarCfg(); window.RIU_ROOM.pintar();
    hist.__sigue = true; caja.value = "";
    hist.append(burbuja(texto, "user")); A.registrar(st.sesion, "user", texto); abajo();
    tema = texto; interv = "";
    const nombres = sel.map((p) => p.nombre), R = st.rondas;
    try {
      for (let r = 1; r <= R && !parar; r++) {
        if (R > 1) hist.append(node("div", "Ronda " + r + " de " + R, "item meta room-ronda"));
        for (const p of sel) { if (parar) break; estado.textContent = "Ronda " + r + "/" + R + " · " + p.nombre; await turno(p, nombres, r, R); }
      }
    } finally {
      ocupado = false; estado.textContent = ""; bStop.hidden = true; bEnv.textContent = "Debatir"; caja.placeholder = "Tema o mensaje para la sala…"; interv = ""; pintarCfg(); window.RIU_ROOM.pintar();
    }
  });
  bStop.addEventListener("click", () => { parar = true; if (cortar) { try { cortar(); } catch (e) {} } if (window.RIU_CANCELAR) { try { window.RIU_CANCELAR(st.sesion); } catch (e) {} } tell("Deteniendo la sala…"); });
  caja.addEventListener("keydown", (e) => { if (e.key === "Enter" && !e.shiftKey && window.matchMedia("(pointer: fine)").matches) { e.preventDefault(); form.requestSubmit(); } });

  // ---- pestaña ROOM CONFERENCIAS en la tira de chats (pintarTabs la vuelve a pintar) ----
  tabsEl.addEventListener("click", (e) => {  // captura: cualquier otra pestaña (Chat N o ＋) sale de la sala antes de su propio handler
    const b = e.target.closest("button"); if (!b || b.classList.contains("room-tab")) return;
    if (st.activo) { st.activo = false; guardar(); }
  }, true);
  const pintar = () => {
    let tab = tabsEl.querySelector(".room-tab");
    if (!tab) {
      tab = node("button", "", "chip room-tab"); tab.type = "button"; tab.title = "ROOM CONFERENCIAS — varias LLM debaten";
      tab.addEventListener("click", () => { st.activo = true; guardar(); pintar(); setTimeout(abajo, 30); });
    }
    tab.textContent = "ROOM CONFERENCIAS" + (ocupado ? " …" : "");
    tabsEl.append(tab);
    tab.classList.toggle("on", st.activo);
    vista.hidden = !st.activo; hist.hidden = !st.activo;
    composer.classList.toggle("room-oculto", st.activo);
    if (st.activo) {
      histEl.querySelectorAll(".chat-history:not(.room-hist)").forEach((h) => { h.hidden = true; });
      tabsEl.querySelectorAll(".chip.on:not(.room-tab)").forEach((c) => c.classList.remove("on"));
    }
  };
  pintarCfg();
  window.RIU_ROOM = { pintar, estado: () => ({ activo: st.activo, sesion: st.sesion, part: [...st.part], rondas: st.rondas, ocupado }) };
  pintar();
  return window.RIU_ROOM;
}
