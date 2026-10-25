// ventana-watchdog.js — ficha del Watchdog. No corre 48 horas en el navegador.
import { el, btn, ventana } from "./ventanas-control.js";

const K = "riu_watchdog";
const LIM = { min: 10, max: 2880 };
let presets = [["10 min", 10], ["1 h", 60], ["24 h", 1440], ["48 h", 2880]];
let ciclo = ["plan", "ejecutar", "observar", "verificar", "decidir"];
let ficha = { estado: "borrador", minutos: 10, objetivo: "", validado: false };
try { ficha = Object.assign(ficha, JSON.parse(sessionStorage.getItem(K) || "")); } catch (e) {}

function guardar() { try { sessionStorage.setItem(K, JSON.stringify(ficha)); } catch (e) {} }
function marcar() {
  const b = document.querySelector("#btn-watchdog");
  if (!b) return;
  b.setAttribute("aria-pressed", ficha.estado === "activo" ? "true" : "false");
}

function pintar(cuerpo) {
  const aviso = el("div", "cv-est");
  const estado = el("div", "wd-estado");
  const min = el("input");
  min.type = "number"; min.min = String(LIM.min); min.max = String(LIM.max); min.value = ficha.minutos;
  min.setAttribute("aria-label", "Duración en minutos");
  const obj = el("textarea", "vn-ta");
  obj.rows = 2; obj.placeholder = "Objetivo comprobable"; obj.value = ficha.objetivo || "";
  const ver = () => {
    estado.textContent = ficha.estado + " · " + ficha.minutos + " min · sin ejecución en el servidor";
    aviso.textContent = ficha.validado ? "plan válido" : "sin validar";
    marcar();
  };
  const tomar = () => { ficha.minutos = Number(min.value); ficha.objetivo = obj.value.trim(); };
  const validar = btn("Validar", "secondary", () => {
    tomar();
    if (!ficha.objetivo) { ficha.validado = false; aviso.textContent = "falta objetivo"; guardar(); marcar(); return; }
    if (!(ficha.minutos >= LIM.min && ficha.minutos <= LIM.max)) { ficha.validado = false; aviso.textContent = "la duración va de " + LIM.min + " a " + LIM.max + " minutos"; guardar(); marcar(); return; }
    ficha.validado = true; ficha.estado = ficha.estado === "cancelado" ? "borrador" : ficha.estado; guardar(); ver();
  });
  const activar = btn("Activar", "secondary", () => { if (!ficha.validado) { aviso.textContent = "valida primero"; return; } ficha.estado = "activo"; guardar(); ver(); });
  const pausar = btn("Pausar", "secondary", () => { if (ficha.estado !== "activo") { aviso.textContent = "no está activo"; return; } ficha.estado = "pausa"; guardar(); ver(); });
  const cancelar = btn("Cancelar", "secondary", () => { ficha.estado = "cancelado"; ficha.validado = false; guardar(); ver(); });
  const pres = el("div", "cv-form");
  presets.forEach(([t, n]) => pres.append(btn(t, "secondary", () => { min.value = String(n); ficha.minutos = n; ficha.validado = false; guardar(); ver(); })));
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
