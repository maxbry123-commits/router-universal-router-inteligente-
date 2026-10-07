import { node } from "./api.js";

const MODOS = { fast: "⚡ rápido", balanced: "⚖ equilibrado", think: "🧠 pensar" };
const MAX_CHAT = 5;
const CLAVE_CHATS = "riu_chats_v1";  // sesiones/anclas/ficha de cada pestaña: sobreviven a recargas en esta pestaña
const etiquetaCorta = (a) => a.startsWith("handoff:") ? "⚓" + a.slice(8) : a.startsWith("enlace:") ? "🔗" + a.slice(7, 40) : "📎" + a;

export async function mount(root, { api, tell }) {
  const q = (s) => root.querySelector(s);
  const ejecutar = (accion, payload) => {
    if (typeof window.YAIWES_PLUGIN_BRIDGE?.execute !== "function") throw new Error("BRIDGE_MISSING");
    return window.YAIWES_PLUGIN_BRIDGE.execute(accion, payload);
  };
  const copiarTexto = async t => {
    try { await navigator.clipboard.writeText(t); tell("Copiado"); }
    catch { tell("No se pudo copiar al portapapeles"); }
  };
  const defecto = window.RIU_CONFIG?.defecto || "";
  let fichas = [];
  const fichaEt = id => fichas.find(m => m.id === id);

  // ---- multi-chat: hasta 5 estancias, cada una con su sesion, su ficha, sus anclas y su historial ----
  const tabsEl = q("#chat-tabs"), histEl = q("#histories");
  const chats = [];
  let activo = 0;
  const chat = () => chats[activo];
  const limiteAnclas = c => {
    if (c.anclados.size < 8) return true;
    tell("Máximo 8 anclas por tarea (límite del plugin)");
    return false;
  };
  const input = q("#message");
  let modo = "balanced";
  const capturar = () => {
    const c = chat();
    if (!c) return;
    c.borrador = input.value;
    c.modo = modo;
  };
  const restaurar = () => {
    const c = chat();
    input.value = c.borrador || "";
    modo = c.modo || "balanced";
    q("#modo").textContent = MODOS[modo] + " ▾";
  };
  const recordar = (c, text, cls) => {
    const entrada = { texto: text.slice(0, 4000), clase: cls || "" };
    c.hist.append(burbuja(text, cls, texto => { entrada.texto = texto.slice(0, 4000); guardar(); }));
    c.mensajes.push(entrada);
    c.mensajes = c.mensajes.slice(-50);
    guardar();
  };
  const guardar = () => {
    try {
      sessionStorage.setItem(CLAVE_CHATS, JSON.stringify(
        chats.map((c) => ({ sesion: c.sesion, ficha: c.ficha, anclados: [...c.anclados],
          borrador: c.borrador, modo: c.modo, mensajes: c.mensajes }))));
    } catch (e) {}
  };
  const pintarAnclados = () => {
    const caja = q("#anclados");
    caja.innerHTML = "";
    chat().anclados.forEach((a) => caja.append(node("span", "⚓ " + etiquetaCorta(a), "anclado-item")));
  };
  const pintarFichaPill = () => {
    const et = fichaEt(chat().ficha);
    q("#ficha").textContent = (et ? et.etiqueta : "modelo").slice(0, 24) + " ▾";
  };
  const pintarTabs = () => {
    tabsEl.replaceChildren();
    chats.forEach((c, i) => {
      const b = node("button", "💬 " + (i + 1) + (c.ocupado ? " ⏳" : ""), "chip" + (i === activo ? " on" : ""));
      b.type = "button"; b.title = "Chat " + (i + 1) + " — sesión " + c.sesion;
      b.addEventListener("click", () => {
        if (i === activo) return;
        capturar();
        activo = i;
        restaurar();
        pintarTabs();
      });
      tabsEl.append(b);
    });
    if (chats.length < MAX_CHAT) {
      const mas = node("button", "＋", "chip");
      mas.type = "button"; mas.title = "Nuevo chat — tareas en paralelo o en cola";
      mas.addEventListener("click", nuevoChat);
      tabsEl.append(mas);
    }
    chats.forEach((c, i) => { c.hist.hidden = i !== activo; });
    pintarAnclados();
    pintarFichaPill();
    guardar();
  };
  const nuevoChat = (restaurado) => {
    if (chats.length) capturar();
    const h = node("div", "", "chat-history");
    h.hidden = true; h.setAttribute("role", "log");
    histEl.append(h);
    const sesion = restaurado?.sesion || "web-" + crypto.randomUUID();
    const c = {
      sesion,
      ficha: restaurado?.ficha || defecto,
      hist: h,
      anclados: new Set(restaurado?.anclados || []),
      borrador: restaurado?.borrador || "",
      modo: restaurado?.modo || "balanced",
      mensajes: Array.isArray(restaurado?.mensajes) ? restaurado.mensajes.slice(-50) : [],
      ocupado: false,
    };
    c.mensajes.forEach(m => h.append(burbuja(m.texto, m.clase, texto => { m.texto = texto.slice(0, 4000); guardar(); })));
    chats.push(c);
    activo = chats.length - 1;
    restaurar();
    pintarTabs();
  };
  try {
    const previos = JSON.parse(sessionStorage.getItem(CLAVE_CHATS) || "[]");
    if (Array.isArray(previos) && previos.length) {
      previos.slice(0, MAX_CHAT).forEach((p) => nuevoChat(p));
      activo = 0; restaurar(); pintarTabs();
    } else nuevoChat();
  } catch (e) { nuevoChat(); }
  input.addEventListener("input", () => { chat().borrador = input.value; guardar(); });

  function burbuja(texto, cls, onEdit) {
    const d = node("div", "", "item message" + (cls ? " " + cls : ""));
    const span = node("span", texto, "txt");
    d.append(span);
    const b = node("button", "⧉", "copiar");
    b.type = "button"; b.title = "Copiar esta salida";
    b.addEventListener("click", () => copiarTexto(span.textContent));
    d.append(b);
    if (!cls || !/\b(user|meta|pending|error)\b/.test(cls)) {
      const e = node("button", "✏️", "editar");
      e.type = "button"; e.title = "Editar esta salida";
      let editando = false;
      e.addEventListener("click", () => {
        editando = !editando;
        span.contentEditable = editando ? "true" : "false";
        e.textContent = editando ? "✔" : "✏️";
        e.title = editando ? "Guardar edición" : "Editar esta salida";
        if (!editando) onEdit?.(span.textContent);
        if (editando) span.focus();
      });
      d.append(e);
    }
    return d;
  }

  // ---- hojas (sheets): cada pildora abre la suya ----
  const cerrarHojas = () => root.querySelectorAll(".sheet").forEach((s) => { s.hidden = true; });
  root.querySelectorAll("[data-sheet]").forEach((b) => b.addEventListener("click", async () => {
    const sh = q("#" + b.dataset.sheet);
    const abierto = !sh.hidden;
    cerrarHojas();
    sh.hidden = abierto;
    if (!abierto && b.dataset.sheet === "ventana-archivos") cargarArchivos();
    if (!abierto && b.dataset.sheet === "ventana-sandbox") cargarSandbox();
    if (!abierto && b.dataset.sheet === "sh-ancla") { pintarAnclas(); cargarMiHandoff(); }
  }));
  root.querySelectorAll(".sh-cerrar").forEach((b) => b.addEventListener("click", cerrarHojas));

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
    const t = node("button", chat().anclados.has(clave) ? "Apagar" : "Encender", "toggle" + (chat().anclados.has(clave) ? " on" : ""));
    t.type = "button"; t.title = "Encender = anclar, apagar = quitar";
    t.setAttribute("aria-label", titulo + ": anclar al chat");
    t.setAttribute("aria-pressed", String(chat().anclados.has(clave)));
    t.addEventListener("click", () => {
      const enc = !chat().anclados.has(clave);
      if (enc && !limiteAnclas(chat())) return;
      enc ? chat().anclados.add(clave) : chat().anclados.delete(clave);
      t.classList.toggle("on", enc);
      t.textContent = enc ? "Apagar" : "Encender";
      t.setAttribute("aria-pressed", String(enc));
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
    if (!fichas.length) lista.append(node("div", "Fichas sin verificar: Router no disponible", "muted"));
    for (const m of fichas) {
      lista.append(fila(m.etiqueta, "", m.id === chat().ficha, () => {
        chat().ficha = m.id;
        pintarFichaPill();
        pintarFichas();
        cerrarHojas();
        guardar();
      }));
    }
  };
  pintarFichas();
  void (async () => { try {
    const r = await ejecutar("modelos", { sesion: chat().sesion });
    if (!Array.isArray(r.modelos)) throw new Error("FICHAS_INVALIDAS");
    fichas = r.modelos.filter(m => m.id && !/deepseek/i.test(m.id)).map(m => ({
      id: m.id, etiqueta: (window.RIU_CONFIG?.modelos || []).find(x => x.id === m.id)?.etiqueta || m.nombre || m.id
    }));
    pintarFichas();
    pintarFichaPill();
  } catch (error) { tell("Fichas no verificadas: " + error.message); } })();

  // ---- pildora de modo ----
  const pintarModos = () => {
    const lista = q("#sh-modo-lista");
    lista.replaceChildren();
    for (const [k, et] of [["fast", "Rápido — 512 tok"], ["balanced", "Equilibrado — 1024 tok"], ["think", "Pensar — 2048 tok"]]) {
      lista.append(fila(MODOS[k], et, k === modo, () => {
        modo = k;
        chat().modo = k;
        q("#modo").textContent = MODOS[k] + " ▾";
        pintarModos();
        cerrarHojas();
        guardar();
      }));
    }
  };
  pintarModos();

  // ---- selector de ancla: handoffs con boton de encender + pegar enlace/handoff propio ----
  const ANCLAS = [
    ["chat-router", "📂 chat router/", "handoff del proyecto workflow Loops code Yaiwes"],
    ["skill", "😄 SKILL.md", "handoff del skill maestro Maxbry UI FROMTED"],
    ["preview", "🔗 Preview Vercel", "handoff del panel-chat de prueba"],
  ];
  const pintarAnclas = () => {
    const lista = q("#sh-ancla-lista");
    lista.replaceChildren();
    for (const [k, t, d] of ANCLAS) {
      lista.append(filaEncender(t, d, "handoff:" + k, async (enc) => {
        if (!enc) return;
        const c = chat();
        try {
          const r = await ejecutar("handoff", { fuente: k, sesion: c.sesion });
          if (!r.handoff) throw new Error("HANDOFF_SIN_CONFIRMACION");
          recordar(c, "⚓ ANCLADO " + k + ":\n" + JSON.stringify(r.handoff, null, 1));
          c.hist.scrollTop = c.hist.scrollHeight;
        } catch (err) {
          c.anclados.delete("handoff:" + k);
          if (chat() === c) pintarAnclas();
          guardar();
          tell(err.message);
        }
      }));
    }
    lista.append(fila("🔬 Auditor de code del repo", "ubica los archivos de code del proyecto", false, async () => {
      const c = chat();
      try {
        const r = await ejecutar("auditor_code", { sesion: c.sesion });
        cerrarHojas();
        recordar(c, "🔎 AUDITOR CODE — " + r.total + " archivos:\n" + (r.carpetas || []).join("\n"));
        c.hist.scrollTop = c.hist.scrollHeight;
      } catch (err) { tell(err.message); }
    }));
  };
  // mi handoff: texto propio guardado en memoria, editable; va interno con cada mensaje
  const cargarMiHandoff = async () => {
    const c = chat();
    try {
      const r = await ejecutar("handoff_texto", { sesion: c.sesion });
      if (chat() !== c) return;
      q("#mi-handoff").value = r.texto || "";
      q("#mh-estado").textContent = r.encendido ? "encendido" : "apagado";
    } catch (err) { if (chat() === c) q("#mh-estado").textContent = err.message; }
  };
  q("#mh-guardar").addEventListener("click", async () => {
    const c = chat();
    try {
      const texto = q("#mi-handoff").value;
      const r = await ejecutar("handoff_texto", { sesion: c.sesion, texto });
      if (chat() === c) q("#mh-estado").textContent = r.encendido ? "encendido" : "apagado";
      if (r.encendido) {
        recordar(c, "⚓ MI HANDOFF anclado:\n" + texto);
        c.hist.scrollTop = c.hist.scrollHeight;
      }
      tell("Mi handoff " + (r.encendido ? "guardado y encendido" : "apagado"));
    } catch (err) { tell(err.message); }
  });
  q("#mh-apagar").addEventListener("click", async () => {
    const c = chat();
    try {
      await ejecutar("handoff_texto", { sesion: c.sesion, texto: "" });
      if (chat() === c) q("#mh-estado").textContent = "apagado";
      tell("Mi handoff apagado");
    } catch (err) { tell(err.message); }
  });
  q("#ancla-enlace-on").addEventListener("click", () => {
    const v = (q("#ancla-enlace").value || "").trim();
    if (!v) { tell("Pega primero un enlace o handoff"); return; }
    if (!/^https:\/\/[^\s]+$/.test(v)) { tell("Solo enlaces HTTPS válidos"); return; }
    if (!chat().anclados.has("enlace:" + v) && !limiteAnclas(chat())) return;
    chat().anclados.add("enlace:" + v);
    q("#ancla-enlace").value = "";
    pintarAnclados(); guardar();
    tell("Enlace anclado al chat");
  });

  // ---- adjuntar y ventana de archivos (boton encender = anclar al chat + x-ray) ----
  const subir = async (file) => {
    const c = chat();
    const buf = await file.arrayBuffer();
    if (buf.byteLength > 2_000_000) { tell("Archivo muy grande (máx ~2 MB)"); return; }
    let bin = ""; const bytes = new Uint8Array(buf);
    for (let i = 0; i < bytes.length; i += 8192) bin += String.fromCharCode.apply(null, bytes.subarray(i, i + 8192));
    const r = await ejecutar("subir", { nombre: file.name, tipo: file.type || "texto", datos_b64: btoa(bin), sesion: c.sesion });
    if (!r.ok || !r.nombre) throw new Error("SUBIR_SIN_CONFIRMACION");
    if (c.anclados.has(r.nombre) || limiteAnclas(c)) c.anclados.add(r.nombre);
    if (chat() === c) pintarAnclados();
    guardar();
    tell("Subido" + (c.anclados.has(r.nombre) ? " y anclado" : " sin anclar (límite 8)") + ": " + file.name);
  };
  q("#btn-adjunto").addEventListener("click", () => q("#adjunto").click());
  q("#adjunto").addEventListener("change", async (e) => {
    const f = e.target.files[0]; e.target.value = "";
    if (f) { try { await subir(f); } catch (err) { tell(err.message); } }
  });
  q("#btn-copiar-input").addEventListener("click", () => copiarTexto(q("#message").value));
  q("#btn-detener").addEventListener("click", () => {
    const c = chat();
    if (!c.ocupado) { tell("No hay una tarea activa en este chat"); return; }
    c.detenerFlag = true;
    c.detenerFn?.();
  });

  // ---- ventana del motor: descarga/extraccion/copiar/mover entre repos ----
  const extraerUrls = (t) => { const s = new Set(); (String(t || "").match(/https?:\/\/[^\s"'<>)\]]+/g) || []).forEach((u) => s.add(u.replace(/[.,;:!?]+$/g, ""))); return [...s]; };
  const motorConfirma = (t, c = chat()) => { recordar(c, t, "meta"); c.hist.scrollTop = c.hist.scrollHeight; };
  const mm = q("#motor-mover"), mc = q("#motor-copiar");
  mm.addEventListener("change", () => { if (mm.checked) mc.checked = false; else if (!mc.checked) mm.checked = true; });
  mc.addEventListener("change", () => { if (mc.checked) mm.checked = false; else if (!mm.checked) mc.checked = true; });
  const motorEjecutar = async (origen, destino, op, c = chat()) => {
    if (!origen || !destino) { tell("Falta el enlace de origen o de destino"); return null; }
    try {
      const r = await ejecutar("mover_raiz", { op, origen, destino, sesion: c.sesion });
      if (r.error || r.estado !== "completado" || (r.fallos || []).length) {
        motorConfirma("⬇ motor: GAP " + (r.error || r.estado || "SIN_CONFIRMACION") + " · " + (r.fallos || []).join(", "), c);
        return null;
      }
      motorConfirma("⬇ " + r.op + " ✓ " + r.archivos + " archivo(s) · " + r.estado + " · " + r.registro, c);
      return r;
    } catch (e) { motorConfirma("⬇ motor: GAP " + e.message, c); return null; }
  };
  q("#motor-ejecutar").addEventListener("click", async () => {
    await motorEjecutar(q("#motor-origen").value.trim(), q("#motor-destino").value.trim(), mm.checked ? "mover" : "copiar");
  });
  q("#motor-archivo-btn").addEventListener("click", () => q("#motor-archivo").click());
  q("#motor-archivo").addEventListener("change", async (e) => {
    const c = chat();
    const f = e.target.files[0]; e.target.value = "";
    if (!f) return;
    const txt = await f.text();
    if (chat() !== c) { motorConfirma("Archivo leído en otra pestaña; vuelve a ese chat para pegar las URLs", c); return; }
    const urls = extraerUrls(txt);
    const viejo = q("#motor-urls").value.trim();
    q("#motor-urls").value = (viejo ? viejo + "\n" : "") + urls.join("\n");
    motorConfirma("⬇ archivo " + f.name + ": " + urls.length + " URL(s) visibles extraídas");
  });
  q("#motor-activar").addEventListener("click", async () => {
    const c = chat();
    const urls = extraerUrls(q("#motor-urls").value);
    const dest = q("#motor-destino2").value.trim() || q("#motor-destino").value.trim();
    if (!urls.length || !dest) { tell("Pega las URLs y el enlace destino"); return; }
    q("#motor-cola").textContent = "cola: " + urls.length + " descarga(s)";
    let hechas = 0;
    for (let i = 0; i < urls.length; i++) {
      q("#motor-cola").textContent = "cola: " + (i + 1) + "/" + urls.length + " → " + urls[i].slice(0, 60);
      if (await motorEjecutar(urls[i], dest, "copiar", c)) hechas++;
    }
    q("#motor-cola").textContent = "cola verificada: " + hechas + "/" + urls.length;
  });
  q("#motor-auditar").addEventListener("click", async () => {
    const c = chat();
    const lista = q("#motor-hist");
    lista.replaceChildren(node("div", "Cargando…", "muted"));
    try {
      const r = await ejecutar("descargas", { op: "lista", sesion: c.sesion });
      if (chat() !== c) return;
      lista.replaceChildren();
      const items = (r.lista || []).slice().reverse();
      if (!items.length) { lista.append(node("div", "Sin descargas en la bitácora", "muted")); return; }
      items.forEach((d) => {
        const b = node("button", "", "fila");
        b.type = "button";
        b.append(node("span", (d.estado === "procesando" ? "⏳ " : d.estado === "completado" ? "✅ " : "⚠️ ") + d.op + " " + (d.archivos || 0) + " archivos · " + d.id, "fila-nom"));
        b.addEventListener("click", async () => {
          const v = await ejecutar("descargas", { op: "ver", id: d.id, sesion: c.sesion });
          if (chat() === c) q("#motor-detalle").textContent = JSON.stringify(v, null, 1).slice(0, 4000);
        });
        lista.append(b);
      });
    } catch (e) { if (chat() === c) lista.replaceChildren(node("div", "GAP " + e.message, "muted")); }
  });
  const cargarArchivos = async () => {
    const c = chat();
    const lista = q("#va-lista");
    lista.replaceChildren(node("div", "Cargando…", "muted"));
    try {
      const r = await ejecutar("archivos", { sesion: c.sesion });
      if (chat() !== c) return;
      lista.replaceChildren();
      for (const nombre of r.archivos || []) {
        const fil = node("div", "", "va-item");
        const t = node("button", c.anclados.has(nombre) ? "Apagar" : "Encender", "toggle" + (c.anclados.has(nombre) ? " on" : ""));
        t.type = "button"; t.title = "Encender = anclar al chat, apagar = quitar";
        t.setAttribute("aria-label", nombre + ": anclar al chat");
        t.setAttribute("aria-pressed", String(c.anclados.has(nombre)));
        t.addEventListener("click", () => {
          const enc = !c.anclados.has(nombre);
          if (enc && !limiteAnclas(c)) return;
          enc ? c.anclados.add(nombre) : c.anclados.delete(nombre);
          t.classList.toggle("on", enc);
          t.textContent = enc ? "Apagar" : "Encender";
          t.setAttribute("aria-pressed", String(enc));
          pintarAnclados(); guardar();
        });
        const nom = node("span", nombre, "fila-nom");
        const xr = node("button", "X-Ray", "mini");
        xr.type = "button"; xr.title = "Auditoría forense del archivo";
        xr.addEventListener("click", async () => {
          xr.disabled = true;
          try {
            const r2 = await ejecutar("xray", { nombre, sesion: c.sesion });
            cerrarHojas();
            recordar(c, "🔬 X-RAY " + (r2.nombre || nombre) + "\n" + (r2.estructura || "") +
              "\nURLs: " + (r2.urls || []).join(", ") + "\nMAPA:\n" + (r2.mapa_mental || "") +
              "\nFLUJO: " + (r2.microflujo || "") + "\n" + (r2.resumen_goals || ""));
            c.hist.scrollTop = c.hist.scrollHeight;
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
    const c = chat();
    try {
      const r = await ejecutar("sandbox", { sesion: c.sesion });
      if (chat() !== c) return;
      q("#sandbox-texto").value = r.sandbox || "";
      q("#sb-estado").textContent = r.sandbox ? "encendido" : "apagado";
    } catch (err) { if (chat() === c) q("#sb-estado").textContent = err.message; }
  };
  q("#sb-guardar").addEventListener("click", async () => {
    const c = chat();
    try {
      const r = await ejecutar("sandbox", { sesion: c.sesion, texto: q("#sandbox-texto").value });
      if (chat() === c) q("#sb-estado").textContent = r.encendido ? "encendido" : "apagado";
      tell("Sandbox " + (r.encendido ? "encendido y anclado" : "apagado"));
    } catch (err) { tell(err.message); }
  });
  q("#sb-apagar").addEventListener("click", async () => {
    const c = chat();
    try {
      await ejecutar("sandbox", { sesion: c.sesion, texto: "" });
      if (chat() === c) q("#sb-estado").textContent = "apagado";
      tell("Sandbox apagado");
    } catch (err) { tell(err.message); }
  });

  // ---- enviar: cada chat corre su tarea en paralelo con su sesion, su ficha y sus anclas ----
  q("#composer").addEventListener("submit", async event => {
    event.preventDefault();
    const c = chat();
    if (c.ocupado) { tell("Este chat ya está ejecutando una tarea; usa otra pestaña o espera"); return; }
    const message = input.value.trim();
    if (!message) return;
    if (message === "/ayuda") { tell("Elige modelo en la píldora, enciende anclas/archivos y envía. /ayuda no ejecuta modelos."); return; }
    if (!fichas.some(m => m.id === c.ficha)) { tell("Ficha no confirmada por el Router; no se enviará la tarea"); return; }
    if (typeof window.YAIWES_PLUGIN_BRIDGE?.execute !== "function" || !window.RIU_CONFIG?.harnessUrl) {
      tell("BRIDGE_MISSING"); return;
    }
    capturar();
    recordar(c, message, "user");
    input.value = "";
    c.borrador = "";
    c.ocupado = true; pintarTabs();
    const pending = node("div", "Pensando…", "item message pending");
    c.hist.append(pending);
    c.hist.scrollTop = c.hist.scrollHeight;
    const max_tokens = { fast: 512, balanced: 1024, think: 2048 }[c.modo] || 1024;
    const controller = new AbortController();
    try {
      c.detenerFlag = false;
      const raceDetener = new Promise((_, rej) => { c.detenerFn = () => { controller.abort(); rej(new Error("PROCESO_DETENIDO")); }; });
      const answer = await Promise.race([ejecutar("chat.send", { model: c.ficha, message, max_tokens, anclados: [...c.anclados], sesion: c.sesion, signal: controller.signal, avisar: t => recordar(c, t, "meta") }), raceDetener]);
      if (!answer.reply?.trim()) throw new Error("RESPUESTA_VACIA");
      pending.remove();
      recordar(c, answer.reply);
      if (answer.tools && answer.tools.length) { const meta = node("div", "Herramientas usadas: ", "item message meta"); answer.tools.forEach((t, i) => { const ok = typeof t === "string" || t.ok; const s = document.createElement("span"); s.textContent = (typeof t === "string" ? t : t.nombre) + (ok ? "" : " (fallo)"); if (!ok) s.className = "tool-fail"; if (i) meta.append(", "); meta.append(s); }); c.hist.append(meta); }
      if (answer.job_id) { window.__riuJob = answer.job_id; q('#apagar-respaldo').hidden = false; }
      c.hist.scrollTop = c.hist.scrollHeight;
    } catch (error) {
      pending.remove();
      recordar(c, c.detenerFlag ? "⏹ espera local detenida; la tarea remota puede continuar (sin cancelación confirmada)" : `GAP: ${error.message}`, c.detenerFlag ? "meta" : "error");
      if (!c.detenerFlag) {
        c.borrador = message;
        if (chat() === c) input.value = message;
        guardar();
      }
      c.hist.scrollTop = c.hist.scrollHeight;
    } finally {
      c.detenerFn = null;
      c.ocupado = false; pintarTabs();
      if (chat() === c && window.matchMedia("(pointer: fine)").matches) input.focus();
    }
  });
  q("#message").addEventListener("keydown", event => {
    if (event.key === "Enter" && !event.shiftKey && window.matchMedia("(pointer: fine)").matches) {
      event.preventDefault();
      q("#composer").requestSubmit();
    }
  });

  // ---- control: toggles de encender/apagar ----
  const llamarControl = async (accion) => { try { await api(`/control/${accion}`, { method: "POST" }); tell(accion + ": ejecutado"); return true; } catch (error) { tell(error.message); return false; } };
  q("#tg-agentes").addEventListener("click", async (e) => {
    const b = e.currentTarget;
    if (await llamarControl(b.classList.contains("on") ? "pause-agents" : "resume-agents")) b.classList.toggle("on");
  });
  q("#tg-router").addEventListener("click", async (e) => {
    const b = e.currentTarget;
    if (await llamarControl(b.classList.contains("on") ? "emergency-stop" : "resume-router")) b.classList.toggle("on");
  });
  root.querySelectorAll("[data-control]").forEach(button => button.addEventListener("click", async () => {
    await llamarControl(button.dataset.control);
  }));
  q('#apagar-respaldo').addEventListener('click', async (e) => {
    const b = e.currentTarget;
    if (b.classList.contains("on")) { b.classList.remove("on"); tell("El respaldo se enciende al elegir un modelo HF"); return; }
    // el boton siempre apaga todos los servidores de respaldo, haya o no uno encendido desde esta pantalla
    try {
      const r = await window.RIU_APAGAR();
      tell(r.ok ? 'Respaldo apagado (' + ((r.p && r.p.apagados) || 0) + ' servidor(es) apagados)' : 'No se pudo apagar (HTTP ' + r.status + ')');
      if (r.ok) { window.__riuJob = null; }
    } catch (error) { tell(error.message); }
  });
}
