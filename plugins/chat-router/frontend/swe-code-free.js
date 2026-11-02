// swe-code-free.js — Selector SWE CODE free mejorado.
// Sistema autónomo de auto-reparación que ejecuta OpenClaw.
// Soporta: sesión, clave, cambio de usuario/agente, ejecución de correo y tareas.
import { conReintentos, clasificar, estadoReparacion, SISTEMA } from "./swe-autorepair.js";

const CLAVE = "riu_swe_code_free";
const CLAVE_AGENTE = "riu_swe_agente";
const CLAVE_SESION = "riu_swe_sesion";

function el(tag, cls, txt) {
  const e = document.createElement(tag);
  if (cls) e.className = cls;
  if (txt != null) e.textContent = txt;
  return e;
}
function sleep(ms) { return new Promise((r) => setTimeout(r, ms)); }

function sesionActual() {
  try { return window.RIU_CHAT?.chat?.()?.sesion || sessionStorage.getItem(CLAVE_SESION) || "web-general"; } catch { return "web-general"; }
}
function claveActual() {
  try { return sessionStorage.getItem("riu_clave") || window.RIU_CONFIG?.apiKey || ""; } catch { return ""; }
}
function agenteActual() {
  try { return sessionStorage.getItem(CLAVE_AGENTE) || "openclaw-01"; } catch { return "openclaw-01"; }
}

export function mountSweCodeFree(root, { tell } = {}) {
  if (!root || root.querySelector("#swe-code-free-sel")) return;

  const box = el("div", "ap-sec");
  box.id = "swe-code-free-sel";
  box.style.marginTop = "8px";
  box.append(el("div", "muted", "SWE CODE free — OpenClaw · sesión · clave · usuario"));

  const estado = el("div", "vn-estado");
  estado.style.fontSize = "12px";
  estado.style.marginTop = "4px";
  const log = el("pre", "muted");
  log.style.fontSize = "11px";
  log.style.maxHeight = "120px";
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
  const correo = el("button", "ap-chip", "Correo");
  correo.type = "button";
  const sesionBtn = el("button", "ap-chip", "Sesión");
  sesionBtn.type = "button";
  const usuarioBtn = el("button", "ap-chip", "Usuario");
  usuarioBtn.type = "button";

  const set = (t) => { estado.textContent = t; if (tell) tell(t); estadoReparacion(t); };
  const add = (t) => { log.textContent = (log.textContent ? log.textContent + "\n" : "") + new Date().toISOString().slice(11, 19) + " " + t; log.scrollTop = log.scrollHeight; };
  const activo = () => { try { return sessionStorage.getItem(CLAVE) === "1"; } catch { return false; } };
  const setAct = (v) => { try { if (v) sessionStorage.setItem(CLAVE, "1"); else sessionStorage.removeItem(CLAVE); } catch {} };

  async function ejecutar(payload) {
    if (!activo()) throw new Error("SWE CODE free OFF");
    const ses = payload?.sesion || sesionActual();
    const ag = payload?.agent_id || agenteActual();
    return conReintentos(async () => {
      const body = {
        message: payload?.message || "ping",
        provider: payload?.provider || "groq",
        model: payload?.model || "groq/llama-3.1-8b-instant",
        mode: "agent",
        agent_id: ag,
        sesion: ses,
      };
      const r = await fetch("/chat/send", {
        method: "POST",
        headers: { "Content-Type": "application/json", "X-API-Key": claveActual() },
        body: JSON.stringify(body),
      });
      if (!r.ok) throw new Error("HTTP " + r.status);
      return r.json();
    }, { max: 3, onLog: add, clasificar });
  }

  async function reparar() {
    set("Reparando…");
    add("health check + clave");
    try {
      await conReintentos(async () => {
        const h = await fetch("/health?t=" + Date.now(), { cache: "no-store" });
        if (!h.ok) throw new Error("health " + h.status);
        return h.json();
      }, { max: 2, onLog: add });
      set("OK · clave: " + (claveActual() ? "presente" : "ausente"));
      add("estable · sesión: " + sesionActual());
    } catch (e) {
      set("falló: " + e.message);
      add(e.message);
    }
  }

  function cambiarUsuario() {
    const actual = agenteActual();
    const nuevo = prompt("Agente OpenClaw (ej. openclaw-01 … openclaw-10):", actual) || actual;
    try { sessionStorage.setItem(CLAVE_AGENTE, nuevo); } catch {}
    set("Usuario: " + nuevo);
    add("agente → " + nuevo);
  }

  function cambiarSesion() {
    const actual = sesionActual();
    const nueva = prompt("Sesión (web-general, qwen, deepseek…):", actual) || actual;
    try { sessionStorage.setItem(CLAVE_SESION, nueva); } catch {}
    set("Sesión: " + nueva);
    add("sesión → " + nueva);
  }

  async function escribirCorreo() {
    const para = prompt("Para (email):", "") || "";
    const asunto = prompt("Asunto:", "Mensaje de OpenClaw") || "Mensaje";
    const cuerpo = prompt("Cuerpo:", "Hola, esto es una prueba desde SWE CODE free.") || "";
    if (!para) { set("sin destinatario"); return; }
    set("enviando correo…");
    add("correo → " + para);
    try {
      const r = await ejecutar({
        message: `Escribe un correo a ${para} con asunto "${asunto}" y cuerpo: ${cuerpo}. Usa la cuenta web conectada.`,
        agent_id: agenteActual(),
        sesion: sesionActual(),
      });
      const txt = (r && (r.reply || (r.choices && r.choices[0] && r.choices[0].message && r.choices[0].message.content))) || JSON.stringify(r).slice(0, 180);
      set("correo enviado");
      add(String(txt).slice(0, 140));
    } catch (e) {
      set("falló correo: " + e.message);
      add(e.message);
    }
  }

  on.addEventListener("click", () => {
    setAct(true);
    set("ON · " + agenteActual() + " · " + sesionActual());
    add("activado");
    window.RIU_SWE_CODE_FREE = { activo: true, ejecutar, reparar, cambiarUsuario, cambiarSesion, escribirCorreo, SISTEMA };
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
    add("ping " + agenteActual());
    try {
      const r = await ejecutar({ message: "¿Qué modelo eres? Una línea. Sesión: " + sesionActual() });
      const txt = (r && (r.reply || (r.choices && r.choices[0] && r.choices[0].message && r.choices[0].message.content))) || JSON.stringify(r).slice(0, 180);
      set("respondió");
      add(String(txt).slice(0, 140));
    } catch (e) {
      set("falló: " + e.message);
      add(e.message);
    }
  });
  repair.addEventListener("click", reparar);
  correo.addEventListener("click", escribirCorreo);
  sesionBtn.addEventListener("click", cambiarSesion);
  usuarioBtn.addEventListener("click", cambiarUsuario);

  fila.append(on, off, test, repair, correo, sesionBtn, usuarioBtn);
  box.append(fila, estado, log);
  root.append(box);

  if (activo()) {
    set("ON (restaurado) · " + agenteActual());
    window.RIU_SWE_CODE_FREE = { activo: true, ejecutar, reparar, cambiarUsuario, cambiarSesion, escribirCorreo, SISTEMA };
  }
}
