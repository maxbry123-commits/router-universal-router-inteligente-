// swe-code-free.js — SWE CODE free con cuentas, clave universal, sesiones y sistemas múltiples.
// OpenClaw usa los correos anotados y la misma clave para Qwen/DeepSeek/Claude/OpenAI web.
// Modelos permitidos por el plan: qwen3.8-max, qwen3.8-flash, qwen3.7-max, qwen3.7-plus, qwen3.6-flash,
// glm-5.3, glm-5.2, deepseek-v4-pro, deepseek-v4-pro-0813, deepseek-v4-flash-0731, deepseek-v4.1-flash, deepseek-v4.1-flash-1017
import { conReintentos, clasificar, estadoReparacion, SISTEMA } from "./swe-autorepair.js";

const CLAVE_UNIV = "770361793Max$";
const CLAVE = "riu_swe_code_free";
const CLAVE_AGENTE = "riu_swe_agente";
const CLAVE_SESION = "riu_swe_sesion";
const CLAVE_CORREO = "riu_swe_correo";

export const CORREOS = [
  { nombre: "Maxbry", email: "maxbry123@gmail.com" },
  { nombre: "Antonio", email: "planeta123usa@gmail.com" },
  { nombre: "Luna", email: "luna123eu@gmail.com" },
  { nombre: "Maria", email: "m37474597@gmail.com" },
  { nombre: "Maxbry Odreman", email: "abc1tienda@gmail.com" },
  { nombre: "Jugf Tashir", email: "nct1luna@gmail.com" },
  { nombre: "Nct2sol Saler", email: "nct2sol2@gmail.com" },
  { nombre: "Papeu Mendif", email: "papeumendif@gmail.com" },
  { nombre: "Pluto Mickey", email: "nct3pluton@gmail.com" },
  { nombre: "Mini Mctgc", email: "nct4jupiter@gmail.com" },
  { nombre: "Briseida Mendoza", email: "briseidamendozabernal@gmail.com" },
];

export const SISTEMAS = [
  { id: "consil-qwen-ds", nombre: "Ask cónsil Qwen+DeepSeek", provider: "web", modelos: ["qwen3.8-max", "deepseek-v4-flash-0731"] },
  { id: "claude", nombre: "Claude (Anthropic)", provider: "web", modelos: ["qwen3.8-max"] },
  { id: "openai", nombre: "OpenAI", provider: "web", modelos: ["qwen3.8-max"] },
  { id: "deepseek", nombre: "DeepSeek", provider: "web", modelos: ["deepseek-v4-flash-0731"] },
  { id: "qwen38", nombre: "Qwen 3.8 Max web", provider: "web", modelos: ["qwen3.8-max"] },
  { id: "qwen37", nombre: "Qwen 3.7 Max web", provider: "web", modelos: ["qwen3.7-max"] },
];

function el(tag, cls, txt) {
  const e = document.createElement(tag);
  if (cls) e.className = cls;
  if (txt != null) e.textContent = txt;
  return e;
}

function sesionActual() {
  try { return window.RIU_CHAT?.chat?.()?.sesion || sessionStorage.getItem(CLAVE_SESION) || "web-general"; } catch { return "web-general"; }
}
function claveActual() {
  try { return sessionStorage.getItem("riu_clave") || CLAVE_UNIV; } catch { return CLAVE_UNIV; }
}
function agenteActual() {
  try { return sessionStorage.getItem(CLAVE_AGENTE) || "openclaw-01"; } catch { return "openclaw-01"; }
}
function correoActual() {
  try { return sessionStorage.getItem(CLAVE_CORREO) || CORREOS[0].email; } catch { return CORREOS[0].email; }
}

export function mountSweCodeFree(root, { tell } = {}) {
  if (!root || root.querySelector("#swe-code-free-sel")) return;

  const box = el("div", "ap-sec");
  box.id = "swe-code-free-sel";
  box.style.marginTop = "8px";
  box.append(el("div", "muted", "SWE CODE free — OpenClaw · correos · clave · sesiones · sistemas"));

  const estado = el("div", "vn-estado");
  estado.style.fontSize = "12px";
  estado.style.marginTop = "4px";
  const log = el("pre", "muted");
  log.style.fontSize = "11px";
  log.style.maxHeight = "140px";
  log.style.overflow = "auto";
  log.style.marginTop = "4px";

  const fila = el("div", "ac-acc");
  fila.style.display = "flex";
  fila.style.flexWrap = "wrap";
  fila.style.gap = "6px";

  const on = el("button", "ap-chip", "ON"); on.type = "button";
  const off = el("button", "ap-chip", "OFF"); off.type = "button";
  const test = el("button", "ap-chip", "Probar"); test.type = "button";
  const repair = el("button", "ap-chip", "Reparar"); repair.type = "button";
  const correoBtn = el("button", "ap-chip", "Correo"); correoBtn.type = "button";
  const sesionBtn = el("button", "ap-chip", "Sesión"); sesionBtn.type = "button";
  const usuarioBtn = el("button", "ap-chip", "Usuario"); usuarioBtn.type = "button";
  const sistemasBtn = el("button", "ap-chip", "Sistemas"); sistemasBtn.type = "button";

  const set = (t) => { estado.textContent = t; if (tell) tell(t); try { estadoReparacion(t); } catch {} };
  const add = (t) => { log.textContent = (log.textContent ? log.textContent + "\n" : "") + new Date().toISOString().slice(11, 19) + " " + t; log.scrollTop = log.scrollHeight; };
  const activo = () => { try { return sessionStorage.getItem(CLAVE) === "1"; } catch { return false; } };
  const setAct = (v) => { try { if (v) sessionStorage.setItem(CLAVE, "1"); else sessionStorage.removeItem(CLAVE); } catch {} };

  async function ejecutar(payload) {
    if (!activo()) throw new Error("SWE CODE free OFF");
    const ses = payload?.sesion || sesionActual();
    const ag = payload?.agent_id || agenteActual();
    const email = payload?.email || correoActual();
    return conReintentos(async () => {
      const body = {
        message: payload?.message || "ping",
        provider: payload?.provider || "web",
        model: payload?.model || "qwen3.8-max",
        mode: "agent",
        agent_id: ag,
        sesion: ses,
        email,
        clave: claveActual(),
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
    add("health + capacidades");
    try {
      await conReintentos(async () => {
        const h = await fetch("/health?t=" + Date.now(), { cache: "no-store" });
        if (!h.ok) throw new Error("health " + h.status);
        return h.json();
      }, { max: 2, onLog: add });
      const cap = await fetch("/chat/swe/capacidades", { headers: { "X-API-Key": claveActual() } }).then(r => r.json()).catch(() => null);
      const disponibles = cap && cap.agentes ? Object.entries(cap.agentes).filter(([k, v]) => v.disponible).map(([k]) => k).join(", ") : "n/a";
      set("OK · clave presente · agentes: " + disponibles);
      add("sesión: " + sesionActual() + " · correo: " + correoActual());
    } catch (e) {
      set("falló: " + e.message);
      add(e.message);
    }
  }

  function cambiarUsuario() {
    const actual = agenteActual();
    const nuevo = prompt("Agente (openclaw-01…10, openhands…):", actual) || actual;
    try { sessionStorage.setItem(CLAVE_AGENTE, nuevo); } catch {}
    set("Usuario: " + nuevo);
    add("agente → " + nuevo);
  }

  function cambiarSesion() {
    const actual = sesionActual();
    const nueva = prompt("Sesión (web-general, qwen, deepseek, claude, openai…):", actual) || actual;
    try { sessionStorage.setItem(CLAVE_SESION, nueva); } catch {}
    set("Sesión: " + nueva);
    add("sesión → " + nueva);
  }

  function elegirCorreo() {
    const lista = CORREOS.map((c, i) => (i + 1) + ". " + c.nombre + " <" + c.email + ">").join("\n");
    const idx = prompt("Elige correo (número):\n" + lista, "1");
    const n = parseInt(idx, 10) - 1;
    if (n >= 0 && n < CORREOS.length) {
      try { sessionStorage.setItem(CLAVE_CORREO, CORREOS[n].email); } catch {}
      set("Correo: " + CORREOS[n].email);
      add("correo → " + CORREOS[n].email);
    }
  }

  async function elegirSistema() {
    const lista = SISTEMAS.map((s, i) => (i + 1) + ". " + s.nombre).join("\n");
    const idx = prompt("Sistema a ejecutar:\n" + lista, "1");
    const n = parseInt(idx, 10) - 1;
    if (n >= 0 && n < SISTEMAS.length) {
      const s = SISTEMAS[n];
      set("Sistema: " + s.nombre);
      add("sistema → " + s.id);
      if (s.id === "consil-qwen-ds") {
        for (const m of s.modelos) {
          try {
            const r = await ejecutar({ message: "Analiza en 1 linea: ping", model: m, provider: s.provider, sesion: m.includes("deepseek") ? "deepseek" : "qwen" });
            add(m + ": " + String(r.reply || "").slice(0, 60));
          } catch (e) { add(m + " err: " + e.message); }
        }
      } else {
        ejecutar({ message: "Inicia sesión en " + s.nombre + " con correo " + correoActual() + " y clave universal. Si no abre, cambia de sesión.", model: s.modelos[0], provider: s.provider }).catch(e => add("err: " + e.message));
      }
    }
  }

  on.addEventListener("click", () => {
    setAct(true);
    set("ON · " + agenteActual() + " · " + sesionActual() + " · " + correoActual().split("@")[0]);
    add("activado · clave universal");
    window.RIU_SWE_CODE_FREE = { activo: true, ejecutar, reparar, cambiarUsuario, cambiarSesion, elegirCorreo, elegirSistema, CORREOS, SISTEMAS, clave: claveActual };
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
      const r = await ejecutar({ message: "¿Qué modelo eres? Sesión: " + sesionActual() + " correo: " + correoActual() });
      const txt = (r && (r.reply || (r.choices && r.choices[0] && r.choices[0].message && r.choices[0].message.content))) || JSON.stringify(r).slice(0, 180);
      set("respondió");
      add(String(txt).slice(0, 140));
    } catch (e) {
      set("falló: " + e.message);
      add(e.message);
    }
  });
  repair.addEventListener("click", reparar);
  correoBtn.addEventListener("click", elegirCorreo);
  sesionBtn.addEventListener("click", cambiarSesion);
  usuarioBtn.addEventListener("click", cambiarUsuario);
  sistemasBtn.addEventListener("click", elegirSistema);

  fila.append(on, off, test, repair, correoBtn, sesionBtn, usuarioBtn, sistemasBtn);
  box.append(fila, estado, log);
  root.append(box);

  if (activo()) {
    set("ON (restaurado) · " + agenteActual() + " · " + correoActual().split("@")[0]);
    window.RIU_SWE_CODE_FREE = { activo: true, ejecutar, reparar, cambiarUsuario, cambiarSesion, elegirCorreo, elegirSistema, CORREOS, SISTEMAS, clave: claveActual };
  }
}
