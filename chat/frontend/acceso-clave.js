// acceso-clave.js — la clave de acceso al servidor (cabecera X-API-Key), que api.js lee de sessionStorage "riu_clave".
// Hasta ahora NADA en la interfaz la pedia ni la guardaba: si el servidor la exige, cada mensaje y cada accion fallaban y no habia como arreglarlo.
// Aqui: se pide SOLO cuando el servidor rechaza la peticion (401/403) y se reintenta sola; se puede recordar en este dispositivo; y se puede escribir y probar en Configuración.
import { el, boton, cargarCss } from "./ventanas-comun.js";
const K = "riu_clave", KR = "riu_clave_recordada";
export const esAuth = (e) => /(^|\D)(401|403)(\D|$)|unauthori[sz]ed|forbidden|api[ -]?key|x-api-key|clave|password|credencial|no autoriz|acceso denegado/i.test(String((e && e.message) || e || ""));
export function restaurarClave() { try { if (!sessionStorage.getItem(K)) { const r = localStorage.getItem(KR); if (r) sessionStorage.setItem(K, r); } } catch (e) {} }
export const hayClave = () => { try { return !!sessionStorage.getItem(K); } catch (e) { return false; } };
export const claveRecordada = () => { try { return !!localStorage.getItem(KR); } catch (e) { return false; } };
export function guardarClave(k, recordar) { try { sessionStorage.setItem(K, k); if (recordar) localStorage.setItem(KR, k); else localStorage.removeItem(KR); } catch (e) {} }
export function olvidarClave() { try { sessionStorage.removeItem(K); localStorage.removeItem(KR); } catch (e) {} }
restaurarClave();
let abierta = null;
export function pedirClave(motivo) {
  if (abierta) return abierta;
  cargarCss("acceso-clave");
  abierta = new Promise((resolve) => {
    const fondo = el("div", "ac-fondo"); fondo.setAttribute("role", "dialog"); fondo.setAttribute("aria-modal", "true"); fondo.setAttribute("aria-label", "Clave de acceso");
    const caja = el("div", "ac-caja"), inp = el("input", "vn-in"), lab = el("label", "ac-rec"), chk = el("input");
    inp.type = "password"; inp.autocomplete = "off"; inp.placeholder = "Clave de acceso al servidor"; inp.setAttribute("aria-label", "Clave de acceso"); chk.type = "checkbox"; lab.append(chk, el("span", "", "Recordar en este dispositivo"));
    const fin = (v) => { fondo.remove(); abierta = null; resolve(v); };
    const ok = boton("Guardar y reintentar", "mini", () => { const k = inp.value.trim(); if (!k) { inp.focus(); return; } guardarClave(k, chk.checked); fin(k); });
    inp.addEventListener("keydown", (e) => { if (e.key === "Enter") { e.preventDefault(); ok.click(); } });
    const fila = el("div", "ac-acc"); fila.append(ok, boton("Cancelar", "mini", () => fin(null)));
    caja.append(el("strong", "", "Clave de acceso"), el("p", "muted", motivo || "El servidor pidió la clave."), inp, lab, fila); fondo.append(caja); document.body.append(fondo); inp.focus();
  });
  return abierta;
}
export async function conReintentoDeClave(fn) {
  try { return await fn(); } catch (e) {
    if (!esAuth(e)) throw e;
    const k = await pedirClave("El servidor rechazó la petición (" + String((e && e.message) || e).slice(0, 100) + "). Escribe la clave de acceso."); if (!k) throw e;
    return await fn();
  }
}
// envuelve las dos llamadas al servidor (mensajes y acciones): si piden clave, la piden y reintentan una vez
export function instalarAuth() {
  for (const n of ["RIU_HARNESS", "RIU_ACCION"]) { const f = window[n]; if (typeof f !== "function" || f.__riuAuth) continue; const w = (...a) => conReintentoDeClave(() => f(...a)); w.__riuAuth = true; if (f.__riuCtx) w.__riuCtx = true; window[n] = w; }
}
// en el chat: las burbujas de error ("GAP: …") traen Reintentar y Clave de acceso
export function montarAcceso({ root, q, tell }) {
  const hist = q("#histories"); if (!hist || hist.dataset.acc) return; hist.dataset.acc = "1"; cargarCss("acceso-clave");
  const reintentar = () => { const c = q("#composer"), m = q("#message"); if (c && m && m.value.trim()) c.requestSubmit(); else tell("Escribe o pega tu mensaje otra vez"); };
  const equipar = () => hist.querySelectorAll(".message.error").forEach((m) => {
    if (m.dataset.ac) return; m.dataset.ac = "1"; if (!/^GAP:/.test(m.textContent)) return;
    const f = el("div", "ac-acc");
    f.append(boton("Reintentar", "mini", reintentar), boton("Clave de acceso…", "mini", async () => { const k = await pedirClave("Escribe la clave del servidor y reintenta."); if (k) { tell("Clave guardada"); reintentar(); } }));
    m.append(f);
  });
  new MutationObserver(() => requestAnimationFrame(equipar)).observe(hist, { childList: true, subtree: true });
  const t = setInterval(() => { if (!root.isConnected) { clearInterval(t); return; } equipar(); }, 800);  // respaldo por si el observador no avisa
}
// en Configuración: escribir, recordar y probar la clave
export function montarAccesoConfig(root, { avisa }) {
  const caja = root.querySelector("#ap-acceso"); if (!caja || caja.dataset.ok) return; caja.dataset.ok = "1";
  const inp = el("input", "vn-in"), lab = el("label", "ac-rec"), chk = el("input"), est = el("div", "vn-estado"), fila = el("div", "ac-acc");
  inp.type = "password"; inp.autocomplete = "off"; inp.placeholder = hayClave() ? "Hay una clave guardada en esta sesión (escribe otra para cambiarla)" : "Clave de acceso al servidor"; inp.setAttribute("aria-label", "Clave de acceso");
  chk.type = "checkbox"; chk.checked = claveRecordada(); lab.append(chk, el("span", "", "Recordar en este dispositivo")); est.setAttribute("role", "status");
  fila.append(
    boton("Guardar", "mini", () => { const k = inp.value.trim(); if (!k) { avisa("Escribe la clave"); return; } guardarClave(k, chk.checked); inp.value = ""; inp.placeholder = "Clave guardada"; avisa("Clave guardada"); }),
    boton("Probar conexión", "mini", async () => { est.textContent = "Probando…"; try { await window.RIU_ACCION("status", {}); est.textContent = "Conexión correcta con el servidor."; } catch (e) { est.textContent = esAuth(e) ? "El servidor rechazó la clave: " + e.message : "No se pudo conectar: " + e.message; } }),
    boton("Olvidar", "mini rojo", () => { olvidarClave(); inp.placeholder = "Clave de acceso al servidor"; chk.checked = false; avisa("Clave olvidada"); }));
  caja.append(inp, lab, fila, est, el("div", "vn-estado", "La clave se guarda solo en este navegador y solo se envía al servidor del chat."));
}
