// ventana-watchdog.js — ficha del Watchdog. No corre 48 horas en el navegador.
import { el, btn, ventana, vivo, SIN_BACKEND } from "./ventanas-control.js";

const K = "riu_watchdog";
const LIM = { min: 10, max: 2880 };
let presets = [["10 min", 10], ["1 h", 60], ["24 h", 1440], ["48 h", 2880]];
let ciclo = ["plan", "ejecutar", "observar", "verificar", "decidir"];
let ficha = { estado: "borrador", minutos: 10, objetivo: "", validado: false };
try { ficha = Object.assign(ficha, JSON.parse(sessionStorage.getItem(K) || "")); } catch (e) {}

const MIN_MS = 60000;
const fin = () => (ficha.inicio || 0) + (Number(ficha.minutos) || 0) * MIN_MS;
function vencer() {  // un watchdog "activo" cuyo plazo ya pasó deja de figurar como activo
  if (ficha.estado === "activo" && ficha.inicio && Date.now() >= fin()) { ficha.estado = "vencido"; guardar(); return true; }
  return false;
}
function guardar() {
  try { sessionStorage.setItem(K, JSON.stringify(ficha)); } catch (e) {}
  if (window.RIU_ACCION) window.RIU_ACCION("cuaderno", { op: "guardar", clave: "watchdog", valor: ficha }).catch(() => {});
}
function marcar() {
  const b = document.querySelector("#btn-watchdog");
  if (!b) return;
  vencer();
  b.setAttribute("aria-pressed", ficha.estado === "activo" ? "true" : "false");
}

function pintar(cuerpo) {
  const aviso = vivo(el("div", "cv-est"));
  const estado = vivo(el("div", "wd-estado"));
  const min = el("input");
  min.type = "number"; min.min = String(LIM.min); min.max = String(LIM.max); min.value = ficha.minutos;
  min.setAttribute("aria-label", "Duración en minutos");
  const botonesPreset = [];
  const obj = el("textarea", "vn-ta");
  obj.rows = 2; obj.placeholder = "Objetivo comprobable"; obj.setAttribute("aria-label", "Objetivo comprobable del watchdog"); obj.value = ficha.objetivo || "";
  const ver = () => {
    vencer();
    const quedan = ficha.estado === "activo" && ficha.inicio ? " · quedan " + Math.max(0, Math.ceil((fin() - Date.now()) / MIN_MS)) + " min" : ficha.estado === "pausa" && ficha.restante != null ? " · quedan " + Math.ceil(ficha.restante / MIN_MS) + " min" : "";
    estado.textContent = ficha.estado + " · " + ficha.minutos + " min" + quedan + " · " + (ficha.cable || SIN_BACKEND + ": sin ejecución en el servidor");
    aviso.textContent = ficha.estado === "vencido" ? "el plazo terminó; valida y activa de nuevo" : ficha.validado ? "plan válido" : "sin validar";
    botonesPreset.forEach(([b, n]) => b.setAttribute("aria-pressed", Number(min.value) === n ? "true" : "false"));
    marcar();
  };
  const tomar = () => { ficha.minutos = Number(min.value); ficha.objetivo = obj.value.trim(); };
  const cable = async () => {
    const base = String((window.RIU_CONFIG && window.RIU_CONFIG.proxyDestino) || "https://comand-center-1-riu-router.hf.space").replace(/\/$/, "");
    const h = { "Content-Type": "application/json" };
    const k = sessionStorage.getItem("riu_clave");
    if (k) { h["X-API-Key"] = k; h.Authorization = "Bearer " + k; }
    try {
      const s = await fetch(base + "/health");
      if (!s.ok) return SIN_BACKEND + ": el router no responde";
    } catch (e) { return SIN_BACKEND + ": el router no responde"; }
    try {
      const p = await fetch(base + "/plugins/loop_wachdog/call/paso", { method: "POST", headers: h, body: "{}" });
      return p.ok ? "en el harness" : SIN_BACKEND + ": router ok · el plugin loop_wachdog no está";
    } catch (e) { return SIN_BACKEND + ": router ok · el plugin loop_wachdog no está"; }
  };
  const revisar = () => {  // devuelve el motivo por el que el plan no vale, o "" si vale
    tomar();
    if (!ficha.objetivo) return "falta objetivo";
    if (!(ficha.minutos >= LIM.min && ficha.minutos <= LIM.max)) return "la duración va de " + LIM.min + " a " + LIM.max + " minutos";
    return "";
  };
  const validar = btn("Validar", "secondary", () => {
    const mal = revisar();
    if (mal) { ficha.validado = false; aviso.textContent = mal; guardar(); marcar(); return; }
    ficha.validado = true; ficha.estado = ficha.estado === "cancelado" || ficha.estado === "vencido" ? "borrador" : ficha.estado; guardar(); ver();
  });
  const invalidar = () => { ficha.validado = false; tomar(); guardar(); ver(); };  // cambiar minutos u objetivo obliga a validar otra vez
  min.addEventListener("input", invalidar);
  obj.addEventListener("input", invalidar);
  const activar = btn("Activar", "secondary", async () => {
    if (ficha.estado === "activo") { aviso.textContent = "ya está activo"; return; }
    if (!ficha.validado) { aviso.textContent = "valida primero"; return; }
    const mal = revisar();
    if (mal) { ficha.validado = false; aviso.textContent = mal; guardar(); marcar(); return; }
    const total = ficha.minutos * MIN_MS;
    ficha.inicio = ficha.estado === "pausa" && ficha.restante > 0 ? Date.now() - (total - ficha.restante) : Date.now();
    ficha.restante = null;
    ficha.estado = "activo";
    ficha.cable = "comprobando el router";
    guardar(); ver();
    activar.disabled = true;
    ficha.cable = await cable();
    guardar(); ver();
    activar.disabled = false;
  });
  const pausar = btn("Pausar", "secondary", () => { if (ficha.estado !== "activo") { aviso.textContent = "no está activo"; return; } ficha.restante = Math.max(0, fin() - Date.now()); ficha.estado = "pausa"; guardar(); ver(); });
  const cancelar = btn("Cancelar", "secondary", () => { ficha.estado = "cancelado"; ficha.validado = false; ficha.inicio = null; ficha.restante = null; guardar(); ver(); });
  const pres = el("div", "cv-form");
  presets.forEach(([t, n]) => { const b = btn(t, "secondary", () => { min.value = String(n); ficha.minutos = n; ficha.validado = false; guardar(); ver(); }); botonesPreset.push([b, n]); pres.append(b); });
  const fila = el("div", "cv-form");
  fila.append(validar, activar, pausar, cancelar);
  const pasos = el("div", "loop-partes");
  ciclo.forEach((n) => pasos.append(el("span", "", n)));
  cuerpo.replaceChildren(estado, el("div", "fila-desc", "Minutos"), min, pres, obj, pasos, aviso, fila);
  ver();
}

fetch("/chat/ui/LOOP-wachdog-cola.json").then((r) => r.json()).then((j) => {
  if (!j.studio) return;
  LIM.min = j.studio.minutos_min;
  LIM.max = j.studio.minutos_max;
  if (Array.isArray(j.studio.presets)) presets = j.studio.presets;
  if (Array.isArray(j.studio.ciclo)) ciclo = j.studio.ciclo;
}).catch(() => {});

const montar = () => { ventana("watchdog", "Watchdog", pintar); marcar(); };
new MutationObserver(montar).observe(document.body, { childList: true, subtree: true });
montar();
if (!ficha.objetivo && window.RIU_ACCION) {
  window.RIU_ACCION("cuaderno", { op: "leer", clave: "watchdog" }).then((r) => {
    if (!r || !r.valor || typeof r.valor !== "object" || ficha.objetivo) return;
    ficha = Object.assign(ficha, r.valor);
    guardar();
  }).catch(() => {});
}
