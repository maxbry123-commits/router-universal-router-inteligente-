import { node } from "./api.js";

const MODOS = { fast: "⚡ rápido", balanced: "⚖ equilibrado", think: "🧠 pensar" };
const MAX_CHAT = 5;
const CLAVE_CHATS = "riu_chats_v1";  // sesiones/anclas/ficha de cada pestaña: sobreviven a recargas en esta pestaña
const etiquetaCorta = (a) => a.startsWith("handoff:") ? "⚓" + a.slice(8) : a.startsWith("enlace:") ? "🔗" + a.slice(7, 40) : "📎" + a;

export async function mount(root, { api, tell }) {
  const q = (s) => root.querySelector(s);
  const copiarTexto = (t) => { try { navigator.clipboard.writeText(t); } catch (e) {} };
  const defecto = window.RIU_CONFIG?.defecto || "";
  const fichaEt = (id) => (window.RIU_CONFIG?.modelos || []).find((m) => m.id === id);

  // ---- multi-chat: hasta 5 estancias, cada una con su sesion, su ficha, sus anclas y su historial ----
  const tabsEl = q("#chat-tabs"), histEl = q("#histories");
  const chats = [];
  let activo = 0;
  const chat = () => chats[activo];
  const guardar = () => {
    try {
      sessionStorage.setItem(CLAVE_CHATS, JSON.stringify(
        chats.map((c) => ({ sesion: c.sesion, ficha: c.ficha, anclados: [...c.anclados] }))));
    } catch (e) {}
  };
  const pintarAnclados = () => {
    q("#anclados").textContent = chat().anclados.size ? [...chat().anclados].map(etiquetaCorta).join("  ") : "";
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
      b.addEventListener("click", () => { activo = i; pintarTabs(); });
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
    const h = node("div", "", "chat-history");
    h.hidden = true; h.setAttribute("role", "log");
    histEl.append(h);
    chats.push({
      sesion: restaurado?.sesion || "web-" + Math.random().toString(36).slice(2, 10),
      ficha: restaurado?.ficha || defecto,
      hist: h,
      anclados: new Set(restaurado?.anclados || []),
      ocupado: false,
    });
    activo = chats.length - 1;
    pintarTabs();
  };
  try {
    const previos = JSON.parse(sessionStorage.getItem(CLAVE_CHATS) || "[]");
    if (Array.isArray(previos) && previos.length) {
      previos.slice(0, MAX_CHAT).forEach((p) => nuevoChat(p));
      activo = 0; pintarTabs();
    } else nuevoChat();
  } catch (e) { nuevoChat(); }

  const burbuja = (texto, cls) => {
    const d = node("div", texto, "item message" + (cls ? " " + cls : ""));
    const b = node("button", "⧉", "copiar");
    b.type = "button"; b.title = "Copiar esta salida";
    b.addEventListener("click", () => copiarTexto(texto));
    d.append(b);
    return d;
  };

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
    const t = node("button", "", "toggle" + (chat().anclados.has(clave) ? " on" : ""));
    t.type = "button"; t.title = "Encender = anclar, apagar = quitar";
    t.addEventListener("click", () => {
      const enc = !chat().anclados.has(clave);
      enc ? chat().anclados.add(clave) : chat().anclados.delete(clave);
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

  // ---- pildora de modo ----
  let modo = "balanced";
  const pintarModos = () => {
    const lista = q("#sh-modo-lista");
    lista.replaceChildren();
    for (const [k, et] of [["fast", "Rápido — 512 tok"], ["balanced", "Equilibrado — 1024 tok"], ["think", "Pensar — 2048 tok"]]) {
      lista.append(fila(MODOS[k], et, k === modo, () => {
        modo = k;
        q("#modo").textContent = MODOS[k] + " ▾";
        pintarModos();
        cerrarHojas();
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
        try {  // muestra en el chat lo que quedo anclado
          const r = await window.RIU_ACCION("handoff", { fuente: k, sesion: chat().sesion });
          const c = chat();
          c.hist.append(burbuja("⚓ ANCLADO " + k + ":\n" + JSON.stringify(r.handoff || r, null, 1)));
          c.hist.scrollTop = c.hist.scrollHeight;
        } catch (err) { tell(err.message); }
      }));
    }
    lista.append(fila("🔬 Auditor de code del repo", "ubica los archivos de code del proyecto", false, async (ev) => {
      ev.currentTarget.disabled = true;
      try {
        const r = await window.RIU_ACCION("auditor_code", { sesion: chat().sesion });
        cerrarHojas();
        const c = chat();
        c.hist.append(burbuja("🔎 AUDITOR CODE — " + r.total + " archivos:\n" + (r.carpetas || []).join("\n")));
        c.hist.scrollTop = c.hist.scrollHeight;
      } catch (err) { tell(err.message); }
    }));
  };
  // mi handoff: texto propio guardado en memoria, editable; va interno con cada mensaje
  const cargarMiHandoff = async () => {
    try {
      const r = await window.RIU_ACCION("handoff_texto", { sesion: chat().sesion });
      q("#mi-handoff").value = r.texto || "";
      q("#mh-estado").textContent = r.encendido ? "encendido" : "apagado";
    } catch (err) { q("#mh-estado").textContent = err.message; }
  };
  q("#mh-guardar").addEventListener("click", async () => {
    try {
      const texto = q("#mi-handoff").value;
      const r = await window.RIU_ACCION("handoff_texto", { sesion: chat().sesion, texto });
      q("#mh-estado").textContent = r.encendido ? "encendido" : "apagado";
      if (r.encendido) {
        const c = chat();
        c.hist.append(burbuja("⚓ MI HANDOFF anclado:\n" + texto));
        c.hist.scrollTop = c.hist.scrollHeight;
      }
      tell("Mi handoff " + (r.encendido ? "guardado y encendido" : "apagado"));
    } catch (err) { tell(err.message); }
  });
  q("#mh-apagar").addEventListener("click", async () => {
    try {
      await window.RIU_ACCION("handoff_texto", { sesion: chat().sesion, texto: "" });
      q("#mh-estado").textContent = "apagado";
      tell("Mi handoff apagado");
    } catch (err) { tell(err.message); }
  });
  q("#ancla-enlace-on").addEventListener("click", () => {
    const v = (q("#ancla-enlace").value || "").trim();
    if (!v) { tell("Pega primero un enlace o handoff"); return; }
    chat().anclados.add("enlace:" + v);
    q("#ancla-enlace").value = "";
    pintarAnclados(); guardar();
    tell("Enlace anclado al chat");
  });

  // ---- adjuntar y ventana de archivos (boton encender = anclar al chat + x-ray) ----
  const subir = async (file) => {
    const buf = await file.arrayBuffer();
    if (buf.byteLength > 2_000_000) { tell("Archivo muy grande (máx ~2 MB)"); return; }
    let bin = ""; const bytes = new Uint8Array(buf);
    for (let i = 0; i < bytes.length; i += 8192) bin += String.fromCharCode.apply(null, bytes.subarray(i, i + 8192));
    const r = await window.RIU_ACCION("subir", { nombre: file.name, tipo: file.type || "texto", datos_b64: btoa(bin), sesion: chat().sesion });
    chat().anclados.add(r.nombre || file.name); pintarAnclados(); guardar();
    tell("Subido y anclado: " + file.name);
  };
  q("#btn-adjunto").addEventListener("click", () => q("#adjunto").click());
  q("#adjunto").addEventListener("change", async (e) => {
    const f = e.target.files[0]; e.target.value = "";
    if (f) { try { await subir(f); } catch (err) { tell(err.message); } }
  });
  q("#btn-copiar-input").addEventListener("click", () => copiarTexto(q("#message").value));
  const cargarArchivos = async () => {
    const lista = q("#va-lista");
    lista.replaceChildren(node("div", "Cargando…", "muted"));
    try {
      const r = await window.RIU_ACCION("archivos", { sesion: chat().sesion });
      lista.replaceChildren();
      for (const nombre of r.archivos || []) {
        const fil = node("div", "", "va-item");
        const t = node("button", "", "toggle" + (chat().anclados.has(nombre) ? " on" : ""));
        t.type = "button"; t.title = "Encender = anclar al chat, apagar = quitar";
        t.addEventListener("click", () => {
          const enc = !chat().anclados.has(nombre);
          enc ? chat().anclados.add(nombre) : chat().anclados.delete(nombre);
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
            c.hist.append(burbuja("🔬 X-RAY " + (r2.nombre || nombre) + "\n" + (r2.estructura || "") +
              "\nURLs: " + (r2.urls || []).join(", ") + "\nMAPA:\n" + (r2.mapa_mental || "") +
              "\nFLUJO: " + (r2.microflujo || "") + "\n" + (r2.resumen_goals || "")));
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

  // ---- selects secundarios (dentro de ⚙ más) ----
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
  q("#composer").addEventListener("submit", async event => {
    event.preventDefault();
    const c = chat();
    const input = q("#message");
    const message = input.value.trim();
    if (!message) return;
    if (message === "/ayuda") { tell("Elige modelo en la píldora, enciende anclas/archivos y envía. /ayuda no ejecuta modelos."); return; }
    const ub = burbuja(message, "user");
    c.hist.append(ub);
    input.value = "";
    c.ocupado = true; pintarTabs();
    const pending = node("div", "Pensando…", "item message pending");
    c.hist.append(pending);
    c.hist.scrollTop = c.hist.scrollHeight;
    const agent = q("#agent").value;
    const provider = q("#provider").value;
    const model = q("#model").value;
    const max_tokens = { fast: 512, balanced: 1024, think: 2048 }[modo];
    try {
      const body = { message, ficha: c.ficha, provider, model, mode: agent ? "agent" : "direct", agent_id: agent || null, max_tokens };
      // con harnessUrl el mensaje va al harness DeepSeek (y este a la memoria por su plugin); si no, al Router como hoy
      const answer = window.RIU_CONFIG?.harnessUrl
        ? await window.RIU_HARNESS({ model: c.ficha, message, max_tokens, anclados: [...c.anclados], sesion: c.sesion, avisar: (t) => c.hist.append(node('div', t, 'item message')) })
        : await api("/chat/send", { method: "POST", body });
      pending.remove();
      c.hist.append(burbuja(answer.reply || "Sin respuesta"));
      if (answer.tools && answer.tools.length) { const meta = node("div", "Herramientas usadas: ", "item message meta"); answer.tools.forEach((t, i) => { const ok = typeof t === "string" || t.ok; const s = document.createElement("span"); s.textContent = (typeof t === "string" ? t : t.nombre) + (ok ? "" : " (fallo)"); if (!ok) s.className = "tool-fail"; if (i) meta.append(", "); meta.append(s); }); c.hist.append(meta); }
      if (answer.job_id) { window.__riuJob = answer.job_id; q('#apagar-respaldo').hidden = false; }
      c.hist.scrollTop = c.hist.scrollHeight;
    } catch (error) {
      pending.remove();
      c.hist.append(node("div", `GAP: ${error.message}`, "item message error"));
      c.hist.scrollTop = c.hist.scrollHeight;
    } finally {
      c.ocupado = false; pintarTabs();
      if (window.matchMedia("(pointer: fine)").matches) input.focus();
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
