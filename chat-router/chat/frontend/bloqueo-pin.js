// bloqueo-pin.js — RUI 10 otp-input llevado a un uso real: bloqueo OPCIONAL del chat con PIN de 4 dígitos.
// Es privacidad local: tapa el chat en ESTE navegador; no es seguridad del servidor. Apagado por defecto (sin PIN guardado no hace nada).
// El PIN no se guarda: solo un resumen SHA-256 con sal. 5 fallos = 30 s de espera. "Olvidé mi PIN" borra los chats locales y quita el bloqueo.
const CLAVE = "riu_pin_v1";
const hex = (buf) => [...new Uint8Array(buf)].map((b) => b.toString(16).padStart(2, "0")).join("");
async function resumen(pin, sal) { return hex(await crypto.subtle.digest("SHA-256", new TextEncoder().encode(sal + ":" + pin))); }
const leer = () => { try { return JSON.parse(localStorage.getItem(CLAVE) || "null"); } catch (e) { return null; } };
export const pinDisponible = () => !!(globalThis.crypto && globalThis.crypto.subtle);
export const pinActivo = () => { const v = leer(); return !!(v && v.sal && v.h); };
export async function fijarPin(pin) {
  if (!/^\d{4}$/.test(pin)) throw new Error("El PIN son 4 dígitos");
  const sal = hex(crypto.getRandomValues(new Uint8Array(12)));
  localStorage.setItem(CLAVE, JSON.stringify({ sal, h: await resumen(pin, sal), fallos: 0, hasta: 0 }));
}
export async function verificarPin(pin) {
  const v = leer(); if (!v) return { ok: true };
  const ahora = Date.now();
  if (v.hasta && ahora < v.hasta) return { ok: false, espera: Math.ceil((v.hasta - ahora) / 1000) };
  if ((await resumen(pin, v.sal)) === v.h) { v.fallos = 0; v.hasta = 0; localStorage.setItem(CLAVE, JSON.stringify(v)); return { ok: true }; }
  v.fallos = (v.fallos || 0) + 1;
  if (v.fallos >= 5) { v.hasta = ahora + 30000; v.fallos = 0; }
  localStorage.setItem(CLAVE, JSON.stringify(v));
  return { ok: false, espera: v.hasta > ahora ? 30 : 0 };
}
export function quitarPin() { try { localStorage.removeItem(CLAVE); } catch (e) {} }
export function borrarDatosLocales() {
  try { Object.keys(localStorage).filter((k) => k.startsWith("riu_") && k !== "riu_tema" && k !== "riu_apariencia_v1").forEach((k) => localStorage.removeItem(k)); } catch (e) {}
}
// caja de 4 casillas (se avanza solo, se pega el PIN entero, Retroceso vuelve atrás, avisa al completarse)
export function crearOtp(n, alCompletar) {
  const caja = document.createElement("div"); caja.className = "riu-otp"; caja.setAttribute("role", "group"); caja.setAttribute("aria-label", "PIN de " + n + " dígitos");
  const ins = [];
  const valor = () => ins.map((x) => x.value).join("");
  const comprobar = () => { if (valor().length === n && alCompletar) alCompletar(valor()); };
  for (let i = 0; i < n; i++) {
    const x = document.createElement("input");
    x.type = "password"; x.inputMode = "numeric"; x.maxLength = 1; x.pattern = "[0-9]*"; x.autocomplete = i === 0 ? "one-time-code" : "off"; x.setAttribute("aria-label", "Dígito " + (i + 1));
    x.addEventListener("input", () => { x.value = x.value.replace(/\D/g, "").slice(-1); if (x.value && ins[i + 1]) ins[i + 1].focus(); comprobar(); });
    x.addEventListener("keydown", (e) => {
      if (e.key === "Backspace" && !x.value && ins[i - 1]) { ins[i - 1].value = ""; ins[i - 1].focus(); }
      if (e.key === "ArrowLeft" && ins[i - 1]) ins[i - 1].focus();
      if (e.key === "ArrowRight" && ins[i + 1]) ins[i + 1].focus();
    });
    x.addEventListener("paste", (e) => {
      const t = ((e.clipboardData && e.clipboardData.getData("text")) || "").replace(/\D/g, "").slice(0, n); if (!t) return;
      e.preventDefault(); [...t].forEach((c, k) => { ins[k].value = c; }); ins[Math.min(t.length, n - 1)].focus(); comprobar();
    });
    x.addEventListener("focus", () => x.select());
    ins.push(x); caja.append(x);
  }
  caja.limpiar = () => { ins.forEach((x) => { x.value = ""; }); ins[0].focus(); };
  caja.sacudir = () => { caja.classList.remove("mal"); void caja.offsetWidth; caja.classList.add("mal"); };
  caja.enfocar = () => ins[0].focus();
  return caja;
}
export function bloquear() {
  if (!pinActivo() || document.getElementById("riu-pin")) return;
  const shell = document.querySelector(".shell"); if (shell) shell.inert = true;
  const o = document.createElement("div"); o.id = "riu-pin"; o.setAttribute("role", "dialog"); o.setAttribute("aria-modal", "true"); o.setAttribute("aria-label", "Chat bloqueado");
  const t = document.createElement("strong"); t.textContent = "Chat bloqueado";
  const s = document.createElement("p"); s.className = "muted"; s.textContent = "Escribe tu PIN de 4 dígitos";
  const msg = document.createElement("p"); msg.className = "riu-pin-msg"; msg.setAttribute("role", "alert");
  const otp = crearOtp(4, async (pin) => {
    const r = await verificarPin(pin);
    if (r.ok) { o.remove(); if (shell) shell.inert = false; return; }
    otp.sacudir(); otp.limpiar(); msg.textContent = r.espera ? "Demasiados intentos: espera " + r.espera + " s" : "PIN incorrecto";
  });
  const olv = document.createElement("button"); olv.type = "button"; olv.className = "mini"; olv.textContent = "Olvidé mi PIN";
  olv.addEventListener("click", () => { if (confirm("Se borrarán los chats guardados en este navegador y se quitará el bloqueo. ¿Continuar?")) { borrarDatosLocales(); location.reload(); } });
  o.append(t, s, otp, msg, olv); document.body.append(o); otp.enfocar();
}
export function iniciarBloqueo() { if (pinActivo()) bloquear(); }
