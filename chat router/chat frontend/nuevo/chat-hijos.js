// chat-hijos.js — Punto 5: agente anclado → chat HIJO con su ficha, un plan riu.dag/v1 y el INPUT_BLOCK literal.
// Rutas reales del Router (vía api.js/LIVE_URL): GET /chat/agents, POST|GET /chat/children/{sesion}, GET /chat/child/{hija}.
// El INPUT_BLOCK se envía tal cual (sin recortar ni normalizar) y el navegador comprueba que su sha256 coincide
// con el input_block_sha256 que devuelve el Router. En el hijo se habla con chat_async y sesion = sesion_hija.
import { api, node } from "../api.js";
import { hijas, registrarHijas } from "./chat-sesion.js";

const MAX_INPUT_BLOCK = 200_000;  // caracteres, como el Router: nunca se recorta, se rechaza
const ERRORES = {
  AGENTE_NO_EXISTE: "Ese agente no existe en el Router.",
  AGENTE_O_FICHA: "Hay que elegir un agente (o una ficha propia), no ambos.",
  FICHA_INVALIDA: "La ficha del agente no es válida.",
  INPUT_BLOCK_VACIO: "El INPUT_BLOCK está vacío.",
  INPUT_BLOCK_MUY_GRANDE: "El INPUT_BLOCK supera el límite del Router (200 000 caracteres).",
  DAG_INPUT_BLOCK_DISTINTO: "El plan DAG lleva un INPUT_BLOCK distinto al enviado.",
  SESION_HIJA_MUY_LARGA: "El id del chat hijo superaría 60 caracteres; usa un agente con id más corto.",
  SESION_INVALIDA: "La sesión de este chat no es válida.",
  HIJA_NO_EXISTE: "Ese chat hijo no existe en el Router.",
  JSON_MUY_GRANDE: "La ficha o el plan son demasiado grandes.",
  SIN_CRYPTO: "Este navegador no permite calcular sha256 (requiere https).",
  "Not Found": "El Router todavía no tiene las rutas de chats hijos.",
  "Failed to fetch": "Sin conexión con el Router.",
};
const enEspanol = error => {
  const m = String(error?.message || "");
  if (m.startsWith("DAG_INVALIDO")) return `El plan DAG no es válido${m.slice(12) ? ": " + m.slice(13) : "."}`;
  return ERRORES[m] || `Error del Router: ${m || "desconocido"}`;
};

export async function sha256Hex(texto) {
  if (!globalThis.crypto?.subtle) throw new Error("SIN_CRYPTO");
  const resumen = await crypto.subtle.digest("SHA-256", new TextEncoder().encode(texto));
  return Array.from(new Uint8Array(resumen), b => b.toString(16).padStart(2, "0")).join("");
}

// Plan mínimo válido (dag.validate): schema, 1 nodo con id, route.group "default" e instrucciones. El input_block lo une el Router.
export function planMinimo(agente) {
  return { schema: "riu.dag/v1", id: `plan-hijo-${agente}`,
    nodes: [{ id: "n1", route: { group: "default" }, instructions: `Ejecuta el INPUT_BLOCK literal como el agente ${agente}, según su ficha.` }] };
}

export function montarHijos({ activo, abrir, repintar }) {
  const $ = s => document.querySelector(s);
  const estado = (texto, error = false) => { $("#hijo-estado").textContent = texto; $("#hijo-estado").dataset.error = String(error); };
  let agentes = null;  // promesa única: la lista se pide una vez por carga de página

  function cargarAgentes() {
    agentes ||= api("/chat/agents").then(r => {
      const lista = Array.isArray(r?.agents) ? r.agents : [];
      $("#hijo-agente").append(...lista.map(a => Object.assign(node("option", `${a.name || a.id} · ${a.role || ""}`), { value: a.id })));
      estado(lista.length ? "" : "El Router no tiene agentes.");
    }).catch(error => { agentes = null; estado(`No se pudieron cargar los agentes: ${enEspanol(error)}`, true); });
    return agentes;
  }

  async function crear() {
    const padre = activo();
    if (padre.padre) return estado("Abre el chat padre para anclar otro agente.", true);
    const agente = $("#hijo-agente").value;
    const texto = $("#hijo-input").value;  // literal: sin trim ni normalización
    if (!agente) return estado("Elige un agente.", true);
    if (!texto.trim()) return estado(ERRORES.INPUT_BLOCK_VACIO, true);
    if ([...texto].length > MAX_INPUT_BLOCK) return estado(ERRORES.INPUT_BLOCK_MUY_GRANDE, true);
    $("#hijo-crear").disabled = true;
    estado("Creando chat hijo…");
    try {
      const enviado = await sha256Hex(texto);
      const r = await api(`/chat/children/${encodeURIComponent(padre.id)}`, { method: "POST",
        body: { agente, dag: planMinimo(agente), input_block: texto } });
      const bytes = new TextEncoder().encode(texto).length;
      const ok = r.input_block_sha256 === enviado && r.input_block_bytes === bytes;
      registrarHijas(padre.id, [{ ...r, sha_enviado: enviado }]);
      $("#hijo-input").value = "";
      $("#hijos").open = false;
      abrir(r.sesion_hija);
      estado(ok ? `✓ ${r.sesion_hija}: sha256 enviado = sha256 del Router` : `✗ ${r.sesion_hija}: el sha256 del Router no coincide con lo enviado`, !ok);
    } catch (error) {
      estado(`No se pudo crear el chat hijo: ${enEspanol(error)}`, true);
    } finally { $("#hijo-crear").disabled = false; }
  }

  function pintarFicha(chat, r, calculado) {
    const f = r.ficha || {};
    // ✓ solo si: sha del texto recibido = sha que informa el Router = sha registrado al crear = sha de lo enviado (si se creó aquí)
    const coincide = calculado === r.input_block_sha256 && (!chat.input_block_sha256 || chat.input_block_sha256 === calculado)
      && (!chat.sha_enviado || chat.sha_enviado === calculado);
    const caja = $("#hijo-ficha");
    const prompt = node("details", "");
    prompt.append(node("summary", "Prompt del agente"), node("pre", f.system_prompt || "(sin prompt)", "bloque"));
    const modelos = Array.isArray(f.models) ? f.models.map(m => typeof m === "string" ? m : m?.model || m?.id || JSON.stringify(m)).join(", ") : "";
    caja.replaceChildren(
      node("strong", `Agente anclado: ${f.name || r.agente} (${f.id || r.agente})`),
      node("small", `${f.role || "sin rol"} · hijo #${r.n} de ${r.padre}${modelos ? ` · modelos: ${modelos}` : ""}`, "muted"),
      prompt,
      node("small", `Plan ${r.dag?.schema || "?"} · ${Array.isArray(r.dag?.nodes) ? r.dag.nodes.length : 0} nodo(s)`, "muted"),
      node("span", "INPUT_BLOCK (solo lectura, literal)", "muted"),
      node("pre", r.input_block, "bloque input-block"),
      node("small", `${coincide ? "✓" : "✗"} sha256 ${r.input_block_sha256} · ${r.input_block_bytes} bytes · ` +
        (coincide ? (chat.sha_enviado ? "coincide con lo enviado" : "coincide con el texto guardado") : "NO coincide"), coincide ? "sha ok" : "sha mal"));
    caja.hidden = false;
  }

  // Trae del Router la lista de hijos del padre (también los que crea el orquestador, Punto 6) y repinta si cambió.
  async function refrescar(padre) {
    const r = await api(`/chat/children/${encodeURIComponent(padre)}`);
    const antes = JSON.stringify(hijas(padre).map(h => h.id));
    registrarHijas(padre, r?.children, true);
    const actual = activo();
    if ((actual.padre || actual.id) === padre && antes !== JSON.stringify(hijas(padre).map(h => h.id))) repintar();
  }

  // Al abrir un chat: si es hijo, muestra su ficha + INPUT_BLOCK; si es padre, trae sus hijos del Router.
  async function cargar(id) {
    const chat = activo();
    if (chat.id !== id) return;
    estado("");
    $("#hijos").hidden = Boolean(chat.padre);
    if (!chat.padre) {
      $("#hijo-ficha").hidden = true;
      try { await refrescar(id); } catch (error) { if (activo().id === id) estado(`No se pudieron cargar los chats hijos: ${enEspanol(error)}`, true); }
      return;
    }
    $("#hijo-ficha").hidden = false;
    $("#hijo-ficha").replaceChildren(node("small", "Cargando ficha del agente…", "muted"));
    try {
      const r = await api(`/chat/child/${encodeURIComponent(id)}?limit=1`);
      const calculado = await sha256Hex(String(r.input_block ?? ""));
      if (activo().id === id) pintarFicha(chat, r, calculado);
    } catch (error) {
      if (activo().id === id) $("#hijo-ficha").replaceChildren(node("small", `No se pudo leer el chat hijo: ${enEspanol(error)}`, "muted"));
    }
  }

  $("#hijos").addEventListener("toggle", () => { if ($("#hijos").open) void cargarAgentes(); });
  $("#hijo-crear").addEventListener("click", () => void crear());
  return { cargar, refrescar };
}
