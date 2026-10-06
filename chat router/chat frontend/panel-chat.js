import { node } from "./api.js";

export async function mount(root, { api, tell }) {
  const anclados = new Set();
  const copiarTexto = (t) => { try { navigator.clipboard.writeText(t); } catch (e) {} };
  const burbuja = (texto, cls) => {
    const d = node("div", texto, "item message" + (cls ? " " + cls : ""));
    const b = node("button", "⧉", "copiar");
    b.type = "button"; b.title = "Copiar";
    b.addEventListener("click", () => copiarTexto(texto));
    d.append(b);
    return d;
  };
  const pintarAnclados = () => {
    const s = root.querySelector("#anclados");
    s.textContent = anclados.size ? "📎 " + [...anclados].join(", ") : "";
  };
  const subir = async (file) => {
    const buf = await file.arrayBuffer();
    if (buf.byteLength > 2_000_000) { tell("Archivo muy grande (máx ~2 MB)"); return; }
    let bin = ""; const bytes = new Uint8Array(buf);
    for (let i = 0; i < bytes.length; i += 8192) bin += String.fromCharCode.apply(null, bytes.subarray(i, i + 8192));
    const r = await window.RIU_ACCION("subir", { nombre: file.name, tipo: file.type || "texto", datos_b64: btoa(bin) });
    anclados.add(r.nombre || file.name); pintarAnclados();
    tell("Subido y anclado: " + file.name);
  };
  root.querySelector("#btn-adjunto").addEventListener("click", () => root.querySelector("#adjunto").click());
  root.querySelector("#adjunto").addEventListener("change", async (e) => {
    const f = e.target.files[0]; e.target.value = "";
    if (f) { try { await subir(f); } catch (err) { tell(err.message); } }
  });
  root.querySelector("#btn-copiar-input").addEventListener("click", () => copiarTexto(root.querySelector("#message").value));
  const ventana = root.querySelector("#ventana-archivos");
  root.querySelector("#btn-archivos").addEventListener("click", async () => {
    ventana.hidden = !ventana.hidden;
    if (ventana.hidden) return;
    const lista = root.querySelector("#va-lista");
    lista.replaceChildren(node("div", "Cargando…", "muted"));
    try {
      const r = await window.RIU_ACCION("archivos", {});
      lista.replaceChildren();
      for (const nombre of r.archivos || []) {
        const lab = node("label", "", "item va-item");
        const cb = node("input", ""); cb.type = "checkbox"; cb.checked = anclados.has(nombre);
        cb.addEventListener("change", () => { cb.checked ? anclados.add(nombre) : anclados.delete(nombre); pintarAnclados(); });
        lab.append(cb, document.createTextNode(nombre));
        lista.append(lab);
      }
      if (!(r.archivos || []).length) lista.append(node("div", "No hay archivos subidos", "muted"));
    } catch (err) { lista.replaceChildren(node("div", err.message, "item message error")); }
  });
  root.querySelector("#va-cerrar").addEventListener("click", () => { ventana.hidden = true; });
  const select = (id, options, value, label) => {
    const target = root.querySelector(id);
    for (const item of options) {
      const option = node("option", item[label]);
      option.value = item[value];
      target.append(option);
    }
  };
  const fichas = window.RIU_CONFIG?.modelos || [];
  for (const m of fichas) { const o = node('option', m.etiqueta); o.value = m.id; root.querySelector('#ficha').append(o); }
  if (window.RIU_CONFIG?.defecto) root.querySelector('#ficha').value = window.RIU_CONFIG.defecto;
  try {
    const providers = await api("/chat/providers");
    select("#provider", (providers.providers || []).filter(item => item.id !== "auto"), "id", "label");
    select("#agent", (await api("/chat/agents")).agents || [], "id", "name");
    const accounts = await api("/chat/github/accounts");
    select("#github", accounts.accounts || [], "account", "account");
  } catch (error) { tell(error.message); }
  root.querySelector("#provider").addEventListener("change", async event => {
    const model = root.querySelector("#model");
    model.replaceChildren(node("option", "Router elige"));
    if (event.target.value === "auto") return;
    try { select("#model", (await api(`/chat/providers/${encodeURIComponent(event.target.value)}/models`)).models || [], "model_id", "label"); }
    catch (error) { tell(error.message); }
  });
  root.querySelector("#composer").addEventListener("submit", async event => {
    event.preventDefault();
    const input = root.querySelector("#message");
    const message = input.value.trim();
    if (!message) return;
    if (message === "/ayuda") { tell("Usa el selector de agente y envía tu mensaje. /ayuda no ejecuta modelos."); return; }
    const history = root.querySelector("#history");
    history.append(node("div", message, "item message user"));
    input.value = "";
    const sendBtn = root.querySelector("#composer button.action");
    sendBtn.disabled = true;
    const pending = node("div", "Pensando…", "item message pending");
    history.append(pending);
    history.scrollTop = history.scrollHeight;
    const agent = root.querySelector("#agent").value;
    const provider = root.querySelector("#provider").value;
    const model = root.querySelector("#model").value;
    const max_tokens = { fast: 512, balanced: 1024, think: 2048 }[root.querySelector("#mode").value];
    try {
      const body = { message, ficha: root.querySelector('#ficha').value, provider, model, mode: agent ? "agent" : "direct", agent_id: agent || null, max_tokens };
      // con harnessUrl el mensaje va al harness DeepSeek (y este a la memoria por su plugin); si no, al Router como hoy
      const answer = window.RIU_CONFIG?.harnessUrl ? await window.RIU_HARNESS({ model: body.ficha, message, max_tokens, anclados: [...anclados], avisar: (t) => history.append(node('div', t, 'item message')) }) : await api("/chat/send", { method: "POST", body });
      pending.remove();
      history.append(burbuja(answer.reply || "Sin respuesta"));
      if (answer.tools && answer.tools.length) { const meta = node("div", "Herramientas usadas: ", "item message meta"); answer.tools.forEach((t, i) => { const ok = typeof t === "string" || t.ok; const s = document.createElement("span"); s.textContent = (typeof t === "string" ? t : t.nombre) + (ok ? "" : " (fallo)"); if (!ok) s.className = "tool-fail"; if (i) meta.append(", "); meta.append(s); }); history.append(meta); }
      if (answer.job_id) { window.__riuJob = answer.job_id; root.querySelector('#apagar-respaldo').hidden = false; }
      history.scrollTop = history.scrollHeight;
    } catch (error) {
      pending.remove();
      history.append(node("div", `GAP: ${error.message}`, "item message error"));
      history.scrollTop = history.scrollHeight;
    } finally {
      sendBtn.disabled = false;
      if (window.matchMedia("(pointer: fine)").matches) input.focus();
    }
  });
  root.querySelector("#message").addEventListener("keydown", event => {
    if (event.key === "Enter" && !event.shiftKey && window.matchMedia("(pointer: fine)").matches) {
      event.preventDefault();
      root.querySelector("#composer").requestSubmit();
    }
  });
  root.querySelectorAll("[data-control]").forEach(button => button.addEventListener("click", async () => {
    try { await api(`/control/${button.dataset.control}`, { method: "POST" }); tell(`${button.textContent}: ejecutado`); }
    catch (error) { tell(error.message); }
  }));
  const stop = root.querySelector('#apagar-respaldo');
  stop.addEventListener('click', async () => {
    const cfg = window.RIU_CONFIG || {};
    // el boton siempre apaga todos los servidores de respaldo, haya o no uno encendido desde esta pantalla
    try {
      const r = await window.RIU_APAGAR();
      tell(r.ok ? 'Respaldo apagado (' + ((r.p && r.p.apagados) || 0) + ' servidor(es) apagados)' : 'No se pudo apagar (HTTP ' + r.status + ')');
      if (r.ok) { window.__riuJob = null; }
    } catch (error) { tell(error.message); }
  });
}
