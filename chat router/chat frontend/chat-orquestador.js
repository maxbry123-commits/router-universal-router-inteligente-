// PUNTO 6 — Mini-orquestador MVP (no un "superorquestador").
// VENTANA ORQUESTADOR → INPUT → Crazy Wall / Bitácora / State JSON / Handoff → selector de modelos/agentes → MCP | HTTP+
// → pool de agentes activados → mismo trabajo / mismo objective_id → resultados → verificación.
// Botón: ORQUESTADOR OFF → chat normal · ORQUESTADOR ON → las órdenes van a los modelos/agentes activos, mismo state/job,
// cada agente con su ficha y su memoria (un chat hijo por agente: POST /chat/children, turno por puente_chat).
// El State JSON (con la bitácora) se guarda como archivo del chat padre en el Router (acción subir).
import { node } from "./api.js";
import { b64utf8 } from "./chat-aislado.js";
import { sha256, dagHijo, abrirHijo } from "./chat-agente-hijo.js";

const MAX_AGENTES = 3;
const claveSel = (s) => "riu_orq_" + s;

export function conectarOrquestador(ctx) {
  const { q, api, tell, chat } = ctx;
  let agentes = [];
  let estado = null;  // state del último objetivo de esta pantalla
  const sel = () => { try { return JSON.parse(sessionStorage.getItem(claveSel(chat().sesion)) || "[]"); } catch (e) { return []; } };
  const guardarSel = (v) => sessionStorage.setItem(claveSel(chat().sesion), JSON.stringify(v));
  const pintarBoton = () => {
    const on = !!chat().orq;
    q("#orq").textContent = "🎛 orquestador " + (on ? "ON" : "OFF") + " ▾";
    q("#orq-toggle").textContent = "ORQUESTADOR " + (on ? "ON" : "OFF");
    q("#orq-toggle").classList.toggle("on", on);
  };
  new MutationObserver(pintarBoton).observe(q("#chat-tabs"), { childList: true });
  q("#orq-bitacora").style.whiteSpace = "pre-wrap";
  q("#orq-state").style.cssText = "white-space:pre-wrap;max-height:180px;overflow:auto;margin:0";
  pintarBoton();

  const pintarAgentes = () => {
    const caja = q("#orq-agentes"), elegidos = sel();
    caja.replaceChildren();
    agentes.forEach((a) => {
      const e = elegidos.find((x) => x.agente === a.id);
      const fila = node("div", "", "va-item");
      const ck = Object.assign(document.createElement("input"), { type: "checkbox", checked: !!e });
      const modelo = document.createElement("select");
      (window.RIU_CONFIG?.modelos || []).forEach((m) => modelo.append(Object.assign(node("option", m.etiqueta), { value: m.id })));
      modelo.value = e ? e.modelo : chat().ficha;
      const cambiar = () => {
        let v = sel().filter((x) => x.agente !== a.id);
        if (ck.checked) {
          if (v.length >= MAX_AGENTES) { ck.checked = false; tell("Máximo " + MAX_AGENTES + " agentes activos"); return; }
          v = v.concat([{ agente: a.id, modelo: modelo.value }]);
        }
        guardarSel(v);
      };
      ck.addEventListener("change", cambiar);
      modelo.addEventListener("change", cambiar);
      const etiqueta = node("label", "", "va-check");
      etiqueta.append(ck, node("span", a.name + " · " + a.role, "fila-nom"));
      fila.append(etiqueta, modelo);
      caja.append(fila);
    });
  };
  const pintarEstado = () => {
    if (!estado) return;
    q("#orq-bitacora").textContent = estado.bitacora.map((b) => new Date(b.ts).toLocaleTimeString("es-CO", { hour12: false }) + " " + b.msg).join("\n");
    q("#orq-state").textContent = JSON.stringify(estado, null, 1);
    q("#orq-handoff").textContent = estado.handoff ? estado.handoff : "Sin handoff encendido en este chat (⚓ ancla → Mi handoff)";
    const wall = q("#orq-wall");
    wall.replaceChildren();
    estado.agentes.forEach((a) => {
      const icono = { PENDIENTE: "⏸", EJECUTANDO: "⏳", HECHO: "✅", FALLO: "⚠️" }[a.estado] || "•";
      const b = node("button", "", "fila");
      b.type = "button";
      b.append(node("span", `${icono} ${a.agente} · ${a.modelo} · ${a.estado}${a.ms ? " · " + a.ms + " ms" : ""}${a.verificacion ? " · verificación " + a.verificacion.resultado : ""}`, "fila-nom"));
      b.title = a.sesion_hija ? "Abrir el chat hijo " + a.sesion_hija : "";
      b.addEventListener("click", async () => {
        if (!a.sesion_hija || ctx.chats.some((x) => x.sesion === a.sesion_hija)) return;
        const padre = ctx.chats.find((x) => x.sesion === estado.sesion_padre);
        try { await abrirHijo(ctx, padre, a.sesion_hija, "↳ " + a.agente); q("#sh-orq").hidden = true; } catch (e) { tell(e.message); }
      });
      wall.append(b);
    });
  };

  q("#orq").addEventListener("click", async () => {
    if (!agentes.length) {
      try { agentes = (await api("/chat/agents")).agents || []; } catch (e) { tell(e.message); }
    }
    if (!estado || estado.sesion_padre !== chat().sesion) {  // tras recargar: el último State JSON guardado en el Router
      try {
        const f = ((await api(`/chat/files/${encodeURIComponent(chat().sesion)}`)).files || []).find((x) => x.nombre.startsWith("orquestador-obj-"));
        estado = f ? await api(`/chat/files/${encodeURIComponent(chat().sesion)}/${f.file_id}`) : null;
      } catch (e) { tell("GAP State JSON: " + e.message); }
      if (!estado) ["#orq-wall", "#orq-bitacora", "#orq-state", "#orq-handoff"].forEach((id) => q(id).replaceChildren());
    }
    pintarAgentes(); pintarBoton(); pintarEstado();
  });
  q("#orq-toggle").addEventListener("click", () => {
    const c = chat();
    if (c.padre) { tell("El orquestador se usa desde el chat padre"); return; }
    if (!c.orq && !sel().length) { tell("Elige al menos un agente activo para encender el orquestador"); return; }
    c.orq = !c.orq;
    ctx.guardar(); pintarBoton();
    tell("Orquestador " + (c.orq ? "ON: las órdenes van a los agentes activos" : "OFF: chat normal"));
  });

  ctx.orquestar = async (c, input) => {
    const activos = sel();
    if (!input.trim()) return;
    if (!activos.length) { tell("No hay agentes activos: elige en 🎛 orquestador"); return; }
    const objective_id = "obj-" + Date.now() + "-" + [...crypto.getRandomValues(new Uint8Array(2))].map((x) => x.toString(16).padStart(2, "0")).join("");
    estado = { objective_id, sesion_padre: c.sesion, via: "HTTP+", input_block_sha256: await sha256(input), input_bytes: new TextEncoder().encode(input).length,
      handoff: null, estado: "EJECUTANDO", ts_inicio: new Date().toISOString(), ts_fin: null, bitacora: [],
      agentes: activos.map((a) => ({ agente: a.agente, modelo: a.modelo, sesion_hija: null, estado: "PENDIENTE", ms: null, respuesta: null, verificacion: null })) };
    const log = (msg) => { estado.bitacora.push({ ts: new Date().toISOString(), msg }); pintarEstado(); };
    c.hist.append(ctx.burbuja(input, "user"));
    const pending = node("div", "🎛 Orquestador: " + activos.length + " agente(s) trabajando en " + objective_id + "…", "item message pending");
    c.hist.append(pending);
    c.ocupado = true; ctx.pintarTabs();
    log("INPUT recibido (" + estado.input_bytes + " bytes) · objective_id " + objective_id);
    try { const h = await window.RIU_ACCION("handoff_texto", { sesion: c.sesion }); if (h.encendido && h.texto) { estado.handoff = h.texto; log("Handoff del chat cargado"); } } catch (e) { log("Handoff: GAP " + e.message); }
    const dag = dagHijo(activos[0].agente, objective_id);
    dag.nodes = activos.map((a, i) => ({ id: "n" + (i + 1), agent: a.agente, route: { group: "default" }, instructions: "Objetivo " + objective_id + ": ejecuta el INPUT_BLOCK literal con tu ficha.", needs: [] }));
    await Promise.allSettled(estado.agentes.map(async (a) => {
      const t0 = Date.now();
      try {
        const r = await api(`/chat/children/${encodeURIComponent(c.sesion)}`, { method: "POST", body: { agente: a.agente, dag, input_block: input } });
        a.sesion_hija = r.sesion_hija; a.estado = "EJECUTANDO"; log(a.agente + " → chat hijo " + r.sesion_hija);
        if (estado.handoff) { await window.RIU_ACCION("handoff_texto", { sesion: a.sesion_hija, texto: estado.handoff }); log(a.agente + ": mismo handoff anclado a su chat hijo"); }
        const res = await window.RIU_HARNESS({ model: a.modelo, message: input, max_tokens: 1024, sesion: a.sesion_hija, anclados: [] });
        a.respuesta = res.reply || ""; a.ms = Date.now() - t0;
        const d = await api(`/chat/child/${encodeURIComponent(a.sesion_hija)}`);
        const ult = [...((d.history || {}).messages || [])].reverse().find((m) => m.role === "assistant");
        const fallos = [];
        if (d.input_block_sha256 !== estado.input_block_sha256 || d.input_block !== input) fallos.push("INPUT_BLOCK distinto");
        if ((d.dag || {}).id !== objective_id) fallos.push("objective_id distinto");
        if (!a.respuesta.trim()) fallos.push("sin respuesta");
        if (!ult || ult.content !== a.respuesta) fallos.push("respuesta no guardada en su memoria");
        a.verificacion = { resultado: fallos.length ? "FAIL" : "PASS", fallos };
        a.estado = fallos.length ? "FALLO" : "HECHO";
        log(a.agente + " " + a.estado + " (" + a.ms + " ms) · verificación " + a.verificacion.resultado + (fallos.length ? ": " + fallos.join(", ") : ""));
      } catch (e) { a.estado = "FALLO"; a.ms = Date.now() - t0; a.verificacion = { resultado: "FAIL", fallos: [e.message] }; log(a.agente + " FALLO: " + e.message); }
    }));
    estado.estado = estado.agentes.every((a) => a.estado === "HECHO") ? "HECHO" : "PARCIAL";
    estado.ts_fin = new Date().toISOString();
    log("Objetivo " + estado.estado);
    pending.remove();
    c.hist.append(ctx.burbuja("🎛 ORQUESTADOR · " + objective_id + " · " + estado.estado + "\n\n" +
      estado.agentes.map((a) => `[${a.agente} · ${a.modelo} · ${a.estado} · verificación ${a.verificacion ? a.verificacion.resultado : "-"}]\n${a.respuesta || (a.verificacion ? a.verificacion.fallos.join(", ") : "")}`).join("\n\n")));
    try {
      const nombre = "orquestador-" + objective_id + ".json";
      const r = await window.RIU_ACCION("subir", { sesion: c.sesion, nombre, tipo: "application/json", datos_b64: b64utf8(JSON.stringify(estado, null, 1)) });
      if (r.error) throw new Error(r.error);
      log("State JSON guardado en el Router: " + nombre);
      c.hist.append(node("div", "🗂 State JSON y bitácora guardados en el Router: " + nombre, "item message meta"));
    } catch (e) { log("State JSON: GAP " + e.message); }
    c.ocupado = false; ctx.pintarTabs();
    c.hist.scrollTop = c.hist.scrollHeight;
    if (ctx.refrescarArchivos) ctx.refrescarArchivos(c);
    return estado;
  };
}
