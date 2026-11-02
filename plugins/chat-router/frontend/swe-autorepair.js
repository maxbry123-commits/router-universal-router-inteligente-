// swe-autorepair.js — Auto-reparación para SWE CODE / SWEN CODE free.
// Reintentos, clasificación de errores, estado visible, y gancho para modificar el propio sistema.
const MAX_DEF = 3;
const BACKOFF = [600, 1200, 2400];

export const REGLAS = [
  { re: /timeout|timed out|504|502/i, act: "retry", msg: "timeout → reintento" },
  { re: /network|fetch failed|failed to fetch/i, act: "retry", msg: "red → reintento" },
  { re: /rate.?limit|429/i, act: "wait", msg: "rate limit → espera" },
  { re: /unauthorized|401|403/i, act: "stop", msg: "clave → alerta" },
  { re: /model.?not.?found|404/i, act: "fallback", msg: "modelo → fallback" },
  { re: /STREAM_CORTADO|STREAM_ERROR/i, act: "retry", msg: "stream → reintento" },
];

export function clasificar(msg) {
  const m = String(msg || "");
  return REGLAS.find((r) => r.re.test(m)) || { act: "retry", msg: "genérico → reintento" };
}

export function estadoReparacion(t) {
  try {
    const el = document.getElementById("swe-reparacion");
    if (el) el.textContent = t;
    if (window.RIU_CHAT && window.RIU_CHAT.avisa) window.RIU_CHAT.avisa(t);
  } catch {}
}

function sleep(ms) { return new Promise((r) => setTimeout(r, ms)); }

export async function conReintentos(fn, opts = {}) {
  const max = opts.max || MAX_DEF;
  const onLog = opts.onLog || (() => {});
  const clas = opts.clasificar || clasificar;
  let last;
  for (let i = 0; i < max; i++) {
    try {
      const r = await fn();
      if (r && r.error) throw new Error(r.error.message || r.error.code || r.error);
      return r;
    } catch (e) {
      last = e;
      const msg = String(e.message || e);
      const c = clas(msg);
      onLog(`#${i + 1}/${max} ${msg} → ${c.msg}`);
      if (c.act === "stop") break;
      if (i < max - 1) await sleep(BACKOFF[i] || 2000);
    }
  }
  throw last || new Error("falló tras " + max);
}

// Gancho para que SWE CODE free pueda modificar su propio sistema (propuestas aprobadas).
export const SISTEMA = {
  reglas: REGLAS,
  agregarRegla(re, act, msg) {
    if (re instanceof RegExp) REGLAS.push({ re, act, msg });
  },
  async aplicarParche(api, parche) {
    // parche: { archivo, buscar, reemplazar } — solo si el backend lo permite
    if (!api || !parche || !parche.archivo) throw new Error("parche inválido");
    return api("/chat/swe/parche", { method: "POST", body: parche });
  },
};
window.RIU_SWE_AUTOREPAIR = SISTEMA;
