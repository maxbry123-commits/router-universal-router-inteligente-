// almacen.js — lectura/escritura JSON en localStorage (claves versionadas) + aviso de cambios. Lo usan workflows, constitución, claves y anclaje.
export const KEYS = { workflows: "riu_workflows_v1", constitucion: "riu_constitucion_v1", claves: "riu_claves_v1", destinos: "riu_destinos_v1", agentes: "riu_agentes_v1", sandbox: "riu_sandbox_v1" };
export const leer = (k, def) => { try { const v = JSON.parse(localStorage.getItem(k) || "null"); return v == null ? def : v; } catch (e) { return def; } };
export const escribir = (k, v) => { try { localStorage.setItem(k, JSON.stringify(v)); } catch (e) { return false; } try { window.dispatchEvent(new CustomEvent("riu:almacen", { detail: k })); } catch (e) {} cuadernoGuardar(k, v); return true; };
const CUADERNO = { riu_tareas_v1: "tareas", riu_hechas_v1: "hechas", riu_comandos_v1: "comandos", riu_sesion_v1: "sesion", riu_reglas_v1: "reglas" };
export function cuadernoGuardar(k, v) {
  const clave = CUADERNO[k];
  if (!clave || typeof window.RIU_ACCION !== "function") return;
  window.RIU_ACCION("cuaderno", { op: "guardar", clave, valor: v }).catch(() => {});
}
export async function cuadernoTraer(k, vacio) {
  const clave = CUADERNO[k];
  if (!clave || !vacio() || typeof window.RIU_ACCION !== "function") return null;
  try {
    const r = await window.RIU_ACCION("cuaderno", { op: "leer", clave });
    if (r && r.valor != null && vacio()) { localStorage.setItem(k, JSON.stringify(r.valor)); return r.valor; }
  } catch (e) {}
  return null;
}
export const hash = (t) => { let h = 0; const s = String(t); for (let i = 0; i < s.length; i++) h = (h * 31 + s.charCodeAt(i)) | 0; return String(h); };
export const uid = () => Math.random().toString(36).slice(2, 9);
