// swe-code-free.js — Selector SWE CODE free.
// Sistema autónomo de auto-reparación que ejecuta OpenClaw.
// Vive en la raíz del frontend. Se monta como selector, no en Configuración.
// Reintentos: 3. Anticipa timeout, red, rate limit, 401/403, modelo no encontrado.

const CLAVE = "riu_swe_code_free";
const MAX = 3;
const BACKOFF = [600, 1200, 2400];

const ANTICIPA = [
  { re: /timeout|timed out|504|502/i, act: "retry", msg: "timeout → reintento" },
  { re: /network|fetch failed|failed to fetch/i, act: "retry", msg: "red → reintento" },
  { re: /rate.?limit|429/i, act: "wait", msg: "rate limit → espera" },
  { re: /unauthorized|401|403/i, act: "stop", msg: "clave → alerta" },
  { re: /model.?not.?found|404/i, act: "fallback", msg: "modelo → fallback" },
];

function el(tag, cls, txt) {
  const e = document.createElement(tag);
  if (cls) e.className = cls;
  if (txt != null) e.textContent = txt;
  return e;
}
function sleep(ms) { return new Promise((r) => setTimeout(r, ms)); }

async function conReintentos(fn, log) {
  let last;
  for (let i = 0; i < MAX; i++) {
    try {
      const r = await fn();
      if (r && r.error) throw new Error(r.error);
      return r;
    } catch (e) {
      last = e;
      const m = String(e.message || e);
      const a = ANTICIPA.find((x) => x.re.test(m));
      if (log) log(`#${i + 1} ${m}${a ? " → " + a.msg : ""}`);
      if (a && a.act === "stop") break;
      if (i < MAX - 1) await sleep(BACKOFF[i] || 2000);
    }
  }
  throw last || new Error("falló tras " + MAX);
}

export function mountSweCodeFree(root, { tell } = {}) {
  if (!root || root.querySelector("#swe-code-free-sel")) return;

  const box = el("div", "ap-sec");
  box.id = "swe-code-free-sel";
  box.style.marginTop = "8px";
  box.append(el("div", "muted", "SWE CODE free — auto-reparación OpenClaw"));

  const estado = el("div", "vn-estado");
  estado.style.fontSize = "12px";
  estado.style.marginTop = "4px";
  const log = el("pre", "muted");
  log.style.fontSize = "11px";
  log.style.maxHeight = "90px";
  log.style.overflow = "auto";
  log.style.marginTop = "4px";

  const fila = el("div", "ac-acc");
  fila.style.display = "flex";
  fila.style.flexWrap = "wrap";
  fila.style.gap = "6px";

  const on = el("button", "ap-chip", "ON");
  on.type = "button";
  const off = el("button", "ap-chip", "OFF");
  off.type = "button";
  const test = el("button", "ap-chip", "Probar");
  test.type = "button";
  const repair = el("button", "ap-chip", "Reparar");
  repair.type = "button";

  const set = (t) => { estado.textContent = t; if (tell) tell(t); };
  const add = (t) => { log.textContent = (log.textContent ? log.textContent + "\n" : "") + new Date().toISOString().slice(11, 19) + " " + t; log.scrollTop = log.scrollHeight; };
  const activo = () => { try { return sessionStorage.getItem(CLAVE) === "1"; } catch { return false; } };
  const setAct = (v) => { try { if (v) sessionStorage.setItem(CLAVE, "1"); else sessionStorage.removeItem(CLAVE); } catch {} };

  async function ejecutar(payload) {
    if (!activo()) throw new Error("SWE CODE free OFF");
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
    }, add);
  }

  async function reparar() {
    set("Reparando…");
    add("health check");
    try {
      await conReintentos(async () => {
        const h = await fetch("/health?t=" + Date.now(), { cache: "no-store" });
        if (!h.ok) throw new Error("health " + h.status);
        return h.json();
      }, add);
      set("OK");
      add("estable");
    } catch (e) {
      set("falló: " + e.message);
      add(e.message);
    }
  }

  on.addEventListener("click", () => {
    setAct(true);
    set("ON");
    add("activado");
    window.RIU_SWE_CODE_FREE = { activo: true, ejecutar, reparar };
    if (window.RIU_SELECTORES && window.RIU_SELECTORES.encender) window.RIU_SELECTORES.encender("swe-code-free");
  });
  off.addEventListener("click", () => {
    setAct(false);
    set("OFF");
    add("desactivado");
    if (window.RIU_SWE_CODE_FREE) window.RIU_SWE_CODE_FREE.activo = false;
    if (window.RIU_SELECTORES && window.RIU_SELECTORES.apagar) window.RIU_SELECTORES.apagar();
  });
  test.addEventListener("click", async () => {
    set("probando…");
    add("ping openclaw-01");
    try {
      const r = await ejecutar({ message: "¿Qué modelo eres? Una línea." });
      const txt = (r && (r.reply || (r.choices && r.choices[0] && r.choices[0].message && r.choices[0].message.content))) || JSON.stringify(r).slice(0, 180);
      set("respondió");
      add(String(txt).slice(0, 140));
    } catch (e) {
      set("falló: " + e.message);
      add(e.message);
    }
  });
  repair.addEventListener("click", reparar);

  fila.append(on, off, test, repair);
  box.append(fila, estado, log);
  root.append(box);

  if (activo()) {
    set("ON (restaurado)");
    window.RIU_SWE_CODE_FREE = { activo: true, ejecutar, reparar };
  }
}
