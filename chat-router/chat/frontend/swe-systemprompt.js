// Unica autoridad: Router MVP -> control.prompt_on, sincronizado por el bridge SWE CODE.
// GET/POST /web/v1/system-prompt-on: el proxy existente reenvia a SWE CODE :7870,
// y ese bridge confirma el estado con /plugins/puente_chat/call/agent_access_lock.
// Nunca interpretar un 404, 401 o 503 como "ON"; nunca fingir un cambio.
import { api } from "./api.js";

const RUTA = "/web/v1/system-prompt-on";
let estado = null, cargado = false, ultimoError = "";

async function llamar(metodo, on) {
  const p = await api(RUTA, {
    method: metodo,
    ...(metodo === "POST" ? { body: { on } } : {}),
  });
  if (p?.ok !== true || typeof p.on !== "boolean") throw new Error("SYSTEM_PROMPT_ESTADO_NO_CONFIRMADO");
  if (metodo === "POST" && p.on !== on) throw new Error("SYSTEM_PROMPT_CAMBIO_NO_CONFIRMADO");
  return p.on;
}

export const systemPromptOnCache = () => estado; // null = SIN VERIFICAR, distinto de OFF
export const systemPromptError = () => ultimoError;

export async function cargarSystemPromptOn({ forzar = false } = {}) {
  if (cargado && !forzar) return estado;
  try {
    estado = await llamar("GET");
    ultimoError = "";
    cargado = true;
  } catch (e) {
    estado = null;
    ultimoError = String(e?.message || "SIN_CONEXION");
    cargado = false; // siguiente intento vuelve a preguntar al servidor
  }
  return estado;
}

export async function alternarSystemPromptOn() {
  if (estado === null) await cargarSystemPromptOn({ forzar: true });
  if (estado === null) throw new Error(ultimoError || "SYSTEM_PROMPT_NO_VERIFICADO");
  const nuevo = !estado;
  try {
    const confirmado = await llamar("POST", nuevo);
    estado = confirmado;
    ultimoError = "";
    cargado = true;
    return estado;
  } catch (e) {
    // Estado previo preservado; la UI NO muestra exito ante un fallo del servidor.
    ultimoError = String(e?.message || "CAMBIO_NO_CONFIRMADO");
    throw e;
  }
}
