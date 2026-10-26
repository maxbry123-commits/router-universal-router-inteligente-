// ventana-servidor.js — Servidor del Router: encender / apagar / reiniciar el Space. La orden sale de /api/power en Vercel (el Router dormido no puede recibirla).
import { el, btn, ventana } from "./ventanas-control.js";
const ESTILO = { RUNNING: "enabled", PAUSED: "pending", SLEEPING: "pending", STOPPED: "pending", BUILDING: "progress", APP_STARTING: "progress", RUNNING_BUILDING: "progress" };
async function power(metodo, accion, forzar) {
  const cuerpo = accion ? { accion, ...(forzar ? { forzar: true } : {}) } : undefined;
  const r = await fetch("/api/power", { method: metodo, headers: { "Content-Type": "application/json", "X-API-Key": sessionStorage.getItem("riu_clave") || "" }, body: cuerpo ? JSON.stringify(cuerpo) : undefined });
  const d = await r.json().catch(() => ({}));
  if (!r.ok) throw new Error(r.status === 401 ? "clave incorrecta (usa la del chat)" : r.status === 404 ? "disponible solo en la web de Vercel" : r.status === 402 ? "Hugging Face: faltan créditos (" + (d.detail || "402") + ")" : d.detail || "HTTP " + r.status);
  return d;
}
function haceMin(t) {
  let n = typeof t === "number" ? t : Date.parse(String(t || ""));
  if (!Number.isFinite(n)) return null;
  if (n < 1e12) n *= 1000;
  return Math.max(0, Math.round((Date.now() - n) / 60000));
}
async function mantener(siempre) {
  const r = await fetch("/plugins/puente_chat/call/mantener_encendido", { method: "POST", headers: { "Content-Type": "application/json", "X-API-Key": sessionStorage.getItem("riu_clave") || "" }, body: JSON.stringify({ siempre: !!siempre }) });
  const d = await r.json().catch(() => ({}));
  if (!r.ok) throw new Error(d.detail || d.error || d.reason || ("HTTP " + r.status));
  const res = d.result && typeof d.result === "object" ? d.result : d;
  if (res.ok === false) throw new Error(res.detail || res.error || "no se pudo dejar encendido");
  return res;
}
async function salud() {
  const base = String((window.RIU_CONFIG && window.RIU_CONFIG.proxyDestino) || "").replace(/\/$/, "");
  const r = await fetch((base || "") + "/health", { headers: { "X-API-Key": sessionStorage.getItem("riu_clave") || "" } });
  if (!r.ok) throw new Error("HTTP " + r.status);
  return r.json();
}
async function pintarPower(cuerpo) {
  const est = el("div", "cv-est"), chip = el("span", "tag-status pending", "…"), hw = el("div", "muted");
  const tareasEl = el("div", "muted", "Tareas en curso: …"), latidoEl = el("div", "muted", "Último latido: …");
  let espera = 0, enCurso = 0, pendiente = "", siempreOn = false, tocando = false;
  const ver = (d) => { chip.className = "tag-status " + (/ERROR/.test(d.stage || "") ? "warning" : ESTILO[d.stage] || "pending"); chip.textContent = d.stage || "sin estado"; hw.textContent = d.hardware ? "Hardware: " + d.hardware + (d.hardware === "cpu-basic" ? " (gratis)" : " · el hardware de pago consume créditos") : ""; return d; };
  const leer = async () => {
    let d = null;
    try { d = ver(await power("GET")); }
    catch (x) { chip.className = "tag-status warning"; chip.textContent = "error"; est.textContent = "⚠️ " + x.message; }
    try {
      const s = await salud();
      const n = Number(s && s.tareas_en_curso);
      enCurso = Number.isFinite(n) ? n : 0;
      tareasEl.textContent = "Tareas en curso: " + (Number.isFinite(n) ? n : "—");
      const min = s && s.latido ? haceMin(s.latido.t) : null;
      const aviso = !!(s && s.latido && s.latido.ok === false);
      latidoEl.textContent = (aviso ? "⚠️ " : "") + "Último latido: " + (min === null ? "sin dato" : "hace " + min + " min");
      if (!tocando && s && typeof s.mantener_siempre === "boolean") { siempreOn = s.mantener_siempre; pintarSw(); }
    } catch (e) { enCurso = 0; tareasEl.textContent = "Tareas en curso: —"; latidoEl.textContent = "Último latido: sin dato"; }
    return d;
  };
  const seguir = async () => { const mia = ++espera; for (let i = 0; i < 60 && mia === espera; i++) { await new Promise((r) => setTimeout(r, 5000)); const d = await leer(); if (!d) return; if (d.stage === "RUNNING") { est.textContent = "✅ listo: el Router está encendido"; return; } if (/ERROR/.test(d.stage || "")) { est.textContent = "⚠️ el Space terminó en " + d.stage; return; } } if (mia === espera) est.textContent = "⚠️ sigue arrancando tras 5 minutos; revisa el Space"; };
  const lanzar = async (b, texto, accion, forzar) => { b.disabled = true; est.textContent = "Enviando " + accion + "…"; try { ver(await power("POST", accion, forzar)); est.textContent = accion === "apagar" ? "Pausa pedida" : "Arrancando… (consulto cada 5 s)"; if (accion !== "apagar") seguir(); else { espera++; setTimeout(leer, 4000); } } catch (x) { est.textContent = "⚠️ " + x.message; } finally { b.disabled = false; b.textContent = texto; pendiente = ""; } };
  const boton = (texto, accion, confirmar) => { const b = btn(texto, "secondary"); let t = 0;
    b.onclick = () => {
      if ((accion === "apagar" || accion === "reiniciar") && enCurso > 0) { pendiente = accion; est.textContent = "Hay " + enCurso + " tareas en curso; apagar las cortaría"; return; }
      if (!confirmar) return lanzar(b, texto, accion, false);
      if (t) { clearTimeout(t); t = 0; return lanzar(b, texto, accion, false); }
      b.textContent = "¿Seguro? Confirmar"; est.textContent = "Pulsa de nuevo para " + accion + " el Router"; t = setTimeout(() => { t = 0; b.textContent = texto; est.textContent = ""; }, 5000);
    }; return b; };
  const forzar = btn("Forzar de todos modos", "secondary"); let paso = 0, tf = 0;
  const resetF = () => { paso = 0; forzar.textContent = "Forzar de todos modos"; };
  forzar.onclick = () => {
    if (!pendiente) { est.textContent = "Elige Apagar o Reiniciar"; return; }
    if (paso === 0) { paso = 1; forzar.textContent = "¿Seguro? 1/2"; clearTimeout(tf); tf = setTimeout(resetF, 5000); return; }
    if (paso === 1) { paso = 2; forzar.textContent = "Confirmar otra vez"; clearTimeout(tf); tf = setTimeout(resetF, 5000); return; }
    clearTimeout(tf); const accion = pendiente; resetF(); lanzar(forzar, "Forzar de todos modos", accion, true);
  };
  const sw = btn("Dejar encendido hasta que yo lo apague", "secondary");
  sw.setAttribute("aria-pressed", "false");
  const pintarSw = () => sw.setAttribute("aria-pressed", siempreOn ? "true" : "false");
  sw.onclick = async () => {
    const antes = siempreOn, quiere = !antes;
    tocando = true; sw.disabled = true;
    try {
      const res = await mantener(quiere);
      siempreOn = !!res.siempre; pintarSw();
      est.textContent = siempreOn ? "Encendido fijo: el servidor no se duerme hasta que lo apagues" : "Encendido fijo desactivado";
    } catch (e) { siempreOn = antes; pintarSw(); est.textContent = "⚠️ " + e.message; }
    finally { tocando = false; sw.disabled = false; }
  };
  const fila = el("div", "cv-form"); fila.append(boton("Encender", "encender", false), boton("Apagar", "apagar", true), boton("Reiniciar", "reiniciar", true), btn("Actualizar", "secondary", leer), forzar, sw);
  cuerpo.replaceChildren(el("div", "cv-sec", "Servidor del Router"), el("div", "cv-fila", ""), hw, tareasEl, latidoEl, fila, est); cuerpo.children[1].append(chip);
  await leer();
}
const montar = () => ventana("power", "Servidor del Router", pintarPower);
new MutationObserver(montar).observe(document.body, { childList: true, subtree: true });
montar();
