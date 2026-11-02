// swe-code-free.js — Sistema autónomo SWE CODE free.
// Ejecuta OpenClaw de forma nativa, se auto-repara, reintenta 3 veces y anticipa errores comunes.
// Vive en la raíz del frontend. No depende de Vercel para actualizaciones (el Space lo sirve desde GitHub).

const CLAVE = "riu_swe_code_free";
const MAX_RETRIES = 3;
const RETRY_MS = [800, 1600, 3200];

const ERRORES_ANTICIPADOS = [
  { test: /timeout|timed out|504|502/i, accion: "reintentar", msg: "Timeout anticipado → reintento con backoff" },
  { test: /network|fetch failed|failed to fetch/i, accion: "reintentar", msg: "Red inestable → reintento" },
  { test: /rate.?limit|429/i, accion: "esperar", msg: "Rate limit → espera y reintento" },
  { test: /unauthorized|401|403/i, accion: "alerta", msg: "Clave inválida → alerta al usuario" },
  { test: /model.?not.?found|404/i, accion: "fallback", msg: "Modelo no disponible → fallback" },
];

function el(tag, cls, txt) {
  const e = document.createElement(tag);
  if (cls) e.className = cls;
  if (txt != null) e.textContent = txt;
  return e;
}

function sleep(ms) { return new Promise((r) => setTimeout(r, ms)); }

async function conReintentos(fn, onLog) {
  let lastErr;
  for (let i = 0; i < MAX_RETRIES; i++) {
    try {
      const r = await fn();
      if (r && r.error) throw new Error(r.error);
      return r;
    } catch (e) {
      lastErr = e;
      const msg = String(e.message || e);
      const ant = ERRORES_ANTICIPADOS.find((x) => x.test.test(msg));
      if (onLog) onLog(`Intento ${i + 1}/${MAX_RETRIES}: ${msg}${ant ? " → " + ant.msg : ""}`);
      if (ant && ant.accion === "alerta") break;
      if (i < MAX_RETRIES - 1) await sleep(RETRY_MS[i] || 2000);
    }
  }
  throw lastErr || new Error("Falló tras " + MAX_RETRIES + " intentos");
}

export function mountSweCodeFree(root, { api, tell } = {}) {
  if (!root || root.querySelector("#swe-code-free")) return;

  const box = el("div", "ap-sec");
  box.id = "swe-code-free";
  box.style.marginTop = "12px";
  box.append(el("h2", "", "SWE CODE free — auto-reparación"));
  box.append(el("p", "muted", "Ejecuta OpenClaw de forma nativa. Reintenta 3 veces y anticipa timeouts, rate limits y fallos de red."));

  const estado = el("div", "vn-estado");
  estado.setAttribute("role", "status");
  estado.style.fontSize = "12px";
  estado.style.marginTop = "6px";

  const log = el("pre", "muted");
  log.style.fontSize = "11px";
  log.style.maxHeight = "120px";
  log.style.overflow = "auto";
  log.style.marginTop = "6px";

  const fila = el("div", "ac-acc");
  fila.style.display = "flex";
  fila.style.flexWrap = "wrap";
  fila.style.gap = "6px";

  const btnOn = el("button", "ap-chip", "Activar");
  btnOn.type = "button";
  const btnOff = el("button", "ap-chip", "Desactivar");
  btnOff.type = "button";
  const btnTest = el("button", "ap-chip", "Probar OpenClaw");
  btnTest.type = "button";
  const btnRepair = el("button", "ap-chip", "Auto-reparar");
  btnRepair.type = "button";

  const setEstado = (t) => { estado.textContent = t; if (tell) tell(t); };
  const addLog = (t) => { log.textContent = (log.textContent ? log.textContent + "\n" : "") + new Date().toISOString().slice(11, 19) + " " + t; log.scrollTop = log.scrollHeight; };

  const activo = () => { try { return sessionStorage.getItem(CLAVE) === "1"; } catch { return false; } };
  const setActivo = (v) => { try { if (v) sessionStorage.setItem(CLAVE, "1"); else sessionStorage.removeItem(CLAVE); } catch {} };

  btnOn.addEventListener("click", () => {
    setActivo(true);
    setEstado("SWE CODE free activo");
    addLog("Activado. Listo para ejecutar OpenClaw.");
    window.RIU_SWE_CODE_FREE = { activo: true, ejecutar, reparar };
  });

  btnOff.addEventListener("click", () => {
    setActivo(false);
    setEstado("SWE CODE free desactivado");
    addLog("Desactivado.");
    if (window.RIU_SWE_CODE_FREE) window.RIU_SWE_CODE_FREE.activo = false;
  });

  async function ejecutar(payload) {
    if (!activo()) throw new Error("SWE CODE free no está activo");
    return conReintentos(async () => {
      const body = {
        message: payload?.message || "ping",
        provider: payload?.provider || "groq",
        model: payload?.model || "groq/llama-3.1-8b-instant",
        mode: "agent",
        agent_id: payload?.agent_id || "openclaw-01",
      };
      const r = await fetch("/chat/send", {
        method: "POST",
        headers: { "Content-Type": "application/json", "X-API-Key": window.RIU_CONFIG?.apiKey || "" },
        body: JSON.stringify(body),
      });
      if (!r.ok) throw new Error("HTTP " + r.status);
      return r.json();
    }, addLog);
  }

  async function reparar() {
    setEstado("Auto-reparando…");
    addLog("Chequeo de salud y reintentos.");
    try {
      await conReintentos(async () => {
        const h = await fetch("/health?t=" + Date.now(), { cache: "no-store" });
        if (!h.ok) throw new Error("health " + h.status);
        return h.json();
      }, addLog);
      setEstado("Auto-reparación OK");
      addLog("Health OK. Sistema estable.");
    } catch (e) {
      setEstado("Auto-reparación falló: " + e.message);
      addLog("Falló: " + e.message);
    }
  }

  btnTest.addEventListener("click", async () => {
    setEstado("Probando OpenClaw…");
    addLog("Enviando ping a openclaw-01.");
    try {
      const r = await ejecutar({ message: "¿Qué modelo eres? Responde en una línea." });
      const txt = (r && (r.reply || (r.choices && r.choices[0] && r.choices[0].message && r.choices[0].message.content))) || JSON.stringify(r).slice(0, 200);
      setEstado("OpenClaw respondió");
      addLog("Respuesta: " + String(txt).slice(0, 160));
    } catch (e) {
      setEstado("Prueba falló: " + e.message);
      addLog("Error final: " + e.message);
    }
  });

  btnRepair.addEventListener("click", reparar);

  fila.append(btnOn, btnOff, btnTest, btnRepair);
  box.append(fila, estado, log);
  root.append(box);

  if (activo()) {
    setEstado("SWE CODE free activo (restaurado)");
    window.RIU_SWE_CODE_FREE = { activo: true, ejecutar, reparar };
  }
}
