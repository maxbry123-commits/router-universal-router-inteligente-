// chat-orquestador.js — Punto 6: mini-orquestador por chat raíz (interruptor ON/OFF en el Router).
// Rutas reales (vía api.js/LIVE_URL): GET|POST /chat/orquestador/{sesion}, GET …/runs y …/runs/{run_id}.
// Con ON el mensaje va a chat_async con `orquestador_nodos` (1..3); harness() de api.js no deja pasar ese campo
// ni devuelve `orquestador`, así que aquí se usa accion() de api.js (misma puerta puente_chat) y se sondea /resultado.
import { accion, api, node } from "../api.js";

const ERRORES = {
  ORQUESTADOR_EN_HIJA: "El orquestador solo se activa en el chat padre, no en un chat hijo.",
  RUN_INVALIDO: "Identificador de ejecución no válido.",
  RUN_NO_EXISTE: "Esa ejecución ya no existe en el Router.",
  SESION_INVALIDA: "La sesión de este chat no es válida.",
  "Not Found": "El Router todavía no tiene las rutas del orquestador.",
  "Failed to fetch": "Sin conexión con el Router.",
  TIEMPO_AGOTADO: "El orquestador superó el tiempo de espera.",
  ENCENDIENDO: "El orquestador solo usa fichas API; elige un modelo que no sea HF.",
};
const enEspanol = error => ERRORES[String(error?.message || "")] || `Error del Router: ${error?.message || "desconocido"}`;
const ESTADOS = { HECHO: "✓", PARCIAL: "◐", PLANIFICANDO: "…", EJECUTANDO: "…", PENDIENTE: "·", TIMEOUT: "⏱", FALLO: "✗", BLOQUEADO: "⊘" };
const hora = ts => { const n = Number(ts); const d = new Date(Number.isFinite(n) ? (n < 1e12 ? n * 1000 : n) : ts); return Number.isNaN(d.getTime()) ? "" : d.toLocaleString("es-CO", { dateStyle: "short", timeStyle: "medium" }); };
const ms = v => Number.isFinite(Number(v)) ? `${Math.round(Number(v))} ms` : "";
const ruta = (sesion, run) => `/chat/orquestador/${encodeURIComponent(sesion)}${run === undefined ? "" : run === "" ? "/runs" : "/runs/" + encodeURIComponent(run)}`;

// Mensaje orquestado: chat_async + sondeo de /resultado (máx. 10 min: 3 nodos × 150 s + resumen).
export async function enviarOrquestado({ model, message, max_tokens, sesion, anclados, nodos }) {
  let p = await accion("chat_async", { model, messages: [{ role: "user", content: message }], max_tokens, sesion,
    orquestador_nodos: nodos, ...(anclados?.length ? { anclados } : {}) });
  const limite = Date.now() + 600_000;
  while (p?.estado === "procesando" && p.proceso_id) {
    if (Date.now() > limite) throw new Error("TIEMPO_AGOTADO");
    await new Promise(ok => setTimeout(ok, 1500));
    try { p = await accion("resultado", { proceso_id: p.proceso_id }); } catch (error) { if (/fetch/i.test(error.message)) continue; throw error; }
  }
  if (p?.estado === "encendiendo") throw new Error("ENCENDIENDO");
  if (p?.error) throw new Error(p.error);
  return { reply: p?.choices?.[0]?.message?.content || "", orquestador: p?.orquestador || null };
}

export function montarOrquestador({ activo, abrirHija, refrescarHijas }) {
  const $ = s => document.querySelector(s);
  const aviso = (texto, error = false) => { $("#orq-estado").textContent = texto; $("#orq-estado").dataset.error = String(error); };
  let estado = { sesion: null, activo: false, limites: null };

  function pintarInterruptor() {
    const on = Boolean(estado.activo);
    $("#orq-switch").setAttribute("aria-checked", String(on));
    $("#orq-switch").textContent = on ? "Orquestador ON" : "Orquestador OFF";
    $("#orq-nodos-caja").hidden = !on;
    const l = estado.limites;
    $("#orq-limites").textContent = l ? `máx. ${l.max_nodos} nodos · ${l.timeout_nodo_s} s por nodo · ${l.herramientas_en_nodos ? "con" : "sin"} herramientas · ${l.recursion ? "con" : "sin"} recursión${l.solo_fichas_api ? " · solo fichas API" : ""}` : "";
    const max = Math.max(1, Math.min(3, Number(l?.max_nodos) || 3));
    if ($("#orq-nodos").options.length !== max) $("#orq-nodos").replaceChildren(...Array.from({ length: max }, (_, i) => Object.assign(node("option", `${i + 1} nodo${i ? "s" : ""}`), { value: String(i + 1) })));
  }

  async function cargar(id) {
    const chat = activo();
    if (chat.id !== id) return;
    $("#orq").hidden = Boolean(chat.padre);  // solo en chats raíz
    if (chat.padre) return;
    estado = { sesion: id, activo: false, limites: estado.limites };
    pintarInterruptor();
    aviso("Leyendo estado del orquestador…");
    try {
      const r = await api(ruta(id));
      if (activo().id !== id) return;
      estado = { sesion: id, activo: r.activo === true, limites: r.limites || null };
      pintarInterruptor();
      aviso("");
      void cargarRuns(id);
    } catch (error) { if (activo().id === id) aviso(`No se pudo leer el orquestador: ${enEspanol(error)}`, true); }
  }

  async function alternar() {
    const id = activo().id;
    if (estado.sesion !== id) return;
    $("#orq-switch").disabled = true;
    try {
      const r = await api(ruta(id), { method: "POST", body: { activo: !estado.activo } });
      if (activo().id !== id) return;
      estado = { sesion: id, activo: r.activo === true, limites: r.limites || estado.limites };
      pintarInterruptor();
      aviso(estado.activo ? "Orquestador activado para este chat." : "Orquestador desactivado.");
    } catch (error) { aviso(`No se pudo cambiar el orquestador: ${enEspanol(error)}`, true); }
    finally { $("#orq-switch").disabled = false; }
  }

  // Nodos a enviar si el orquestador está ON en ESTE chat (0 = mensaje normal sin orquestador_nodos).
  const nodosPara = id => (estado.sesion === id && estado.activo ? Number($("#orq-nodos").value) || 1 : 0);

  function abrirNodo(sesion, hija) {
    return async () => {
      try { await refrescarHijas(sesion); abrirHija(hija); } catch (error) { aviso(`No se pudo abrir el chat del nodo: ${enEspanol(error)}`, true); }
    };
  }

  // Tarjeta compacta bajo la respuesta orquestada: estado del run y cada nodo con agente, estado, ms y enlace a su hijo.
  function tarjeta(run, sesion) {
    const caja = node("div", "", "orq-run");
    caja.append(node("strong", `Orquestador · ${ESTADOS[run.estado] || ""} ${run.estado || "?"} · run ${String(run.run_id || "").slice(0, 12)}`));
    for (const n of Array.isArray(run.nodos) ? run.nodos : []) {
      const fila = node("div", `${ESTADOS[n.estado] || "·"} ${n.id} · ${n.agente || "?"} · ${n.estado || "?"}${n.ms != null ? " · " + ms(n.ms) : ""}`, "orq-nodo");
      if (n.sesion_hija) {
        const b = node("button", "Abrir hijo", "enlace");
        b.type = "button"; b.title = n.sesion_hija;
        b.addEventListener("click", abrirNodo(sesion, n.sesion_hija));
        fila.append(" ", b);
      }
      caja.append(fila);
    }
    if (run.run_id) {
      const d = node("button", "Ver detalle", "enlace");
      d.type = "button";
      d.addEventListener("click", () => void verRun(sesion, run.run_id));
      caja.append(d);
    }
    return caja;
  }

  async function cargarRuns(id) {
    try {
      const r = await api(ruta(id, ""));
      if (activo().id !== id) return;
      const runs = Array.isArray(r?.runs) ? r.runs : [];
      $("#orq-runs-titulo").textContent = `Ejecuciones del orquestador (${runs.length})`;
      $("#orq-runs-lista").replaceChildren(...runs.map(x => {
        const b = node("button", `${ESTADOS[x.estado] || ""} ${x.estado} · ${Array.isArray(x.nodos) ? x.nodos.length : x.nodos ?? "?"} nodo(s) · ${hora(x.ts_inicio)} · ${String(x.run_id).slice(0, 12)}`, "secondary orq-run-item");
        b.type = "button";
        b.addEventListener("click", () => void verRun(id, x.run_id));
        return b;
      }));
    } catch (error) { if (activo().id === id) $("#orq-runs-titulo").textContent = `Ejecuciones: ${enEspanol(error)}`; }
  }

  async function verRun(sesion, runId) {
    const caja = $("#orq-detalle");
    caja.hidden = false;
    caja.replaceChildren(node("small", "Cargando ejecución…", "muted"));
    $("#orq-runs").open = true;
    try {
      const r = await api(ruta(sesion, runId));
      const nodos = (Array.isArray(r.nodos) ? r.nodos : []).map(n => {
        const d = node("details", "", "orq-nodo-detalle");
        d.append(node("summary", `${ESTADOS[n.estado] || "·"} ${n.id} · ${n.agente} · ${n.estado}${n.ms != null ? " · " + ms(n.ms) : ""}${n.needs?.length ? " · necesita " + n.needs.join(", ") : ""}`),
          node("small", `Instrucciones: ${n.instrucciones || ""}`, "muted"), node("pre", n.error ? `ERROR: ${n.error}\n\n${n.respuesta || ""}` : n.respuesta || "(sin respuesta)", "bloque"));
        if (n.sesion_hija) { const b = node("button", "Abrir hijo", "enlace"); b.type = "button"; b.addEventListener("click", abrirNodo(sesion, n.sesion_hija)); d.append(b); }
        return d;
      });
      const dag = node("details", "");
      dag.append(node("summary", "DAG del run"), node("pre", JSON.stringify(r.dag, null, 2), "bloque"));
      caja.replaceChildren(node("strong", `Run ${r.run_id} · ${r.estado}`),
        node("small", `Modelo ${r.modelo || "?"} · ${hora(r.ts_inicio)} → ${hora(r.ts_fin) || "…"} · INPUT_BLOCK sha256 ${r.input_block_sha256 || "?"}`, "muted"),
        dag, ...nodos, node("pre", r.resumen || "(sin resumen)", "bloque"));
    } catch (error) { caja.replaceChildren(node("small", `No se pudo abrir la ejecución: ${enEspanol(error)}`, "muted")); }
  }

  $("#orq-switch").addEventListener("click", () => void alternar());
  return { cargar, nodosPara, tarjeta, cargarRuns };
}
