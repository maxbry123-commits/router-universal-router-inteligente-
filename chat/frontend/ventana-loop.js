// ventana-loop.js — LOOP del chat: encender, un paso, verificar, repetir, apagar.
// El ciclo vive en esta ventana. /api/loop guarda el estado; si esa ruta no está, sigue en este chat.
import { el, btn, ventana } from "./ventanas-control.js";

const FASES = ["leer", "paso", "verificar", "repetir"];
const CLAVE = "riu_loop";
let estado = { on: false, paso: 0, fase: "apagado", nota: "apagado" };
let reloj = 0;
try { estado = JSON.parse(sessionStorage.getItem(CLAVE) || "") || estado; } catch (e) {}

function guardar() { try { sessionStorage.setItem(CLAVE, JSON.stringify(estado)); } catch (e) {} }
function sesion() { return sessionStorage.getItem("riu_sesion") || "web-general"; }
function marcarBoton() {
  const b = document.querySelector("#btn-loop");
  if (!b) return;
  b.setAttribute("aria-pressed", estado.on ? "true" : "false");
  b.title = estado.on ? "LOOP encendido" : "LOOP apagado";
}

async function pedir(accion) {
  const s = sesion();
  try {
    const r = await fetch(accion ? "/api/loop" : "/api/loop?sesion=" + encodeURIComponent(s), {
      method: accion ? "POST" : "GET",
      headers: { "Content-Type": "application/json" },
      body: accion ? JSON.stringify({ accion, sesion: s }) : undefined,
    });
    if (!r.ok) throw new Error("HTTP " + r.status);
    estado = await r.json();
  } catch (e) {
    if (accion === "encender") estado = { on: true, paso: estado.paso || 0, fase: "leer", nota: "en este chat" };
    else if (accion === "apagar") estado = { on: false, paso: estado.paso || 0, fase: "apagado", nota: "apagado" };
    else if (accion === "paso" && estado.on) {
      const fase = FASES[(FASES.indexOf(estado.fase) + 1) % FASES.length];
      estado = { on: true, paso: estado.paso + (fase === "leer" ? 1 : 0), fase, nota: "en este chat" };
    }
  }
  guardar();
  marcarBoton();
  return estado;
}

function latido() {
  if (reloj) return;
  reloj = setInterval(() => { if (estado.on) pedir("paso").then(() => { if (window.__riuLoopPintar) window.__riuLoopPintar(); }); else { clearInterval(reloj); reloj = 0; } }, 3000);
}

function pintarLoop(cuerpo) {
  const est = el("div", "cv-est");
  const chip = el("span", "tag-status pending", "apagado");
  const detalle = el("div", "muted");
  const pintar = () => {
    chip.className = "tag-status " + (estado.on ? "enabled" : "pending");
    chip.textContent = estado.on ? "encendido" : "apagado";
    detalle.textContent = "Fase: " + estado.fase + " · vueltas: " + estado.paso + (estado.nota ? " · " + estado.nota : "");
  };
  window.__riuLoopPintar = pintar;
  const enc = btn("Encender", "secondary", async () => { enc.disabled = true; try { await pedir("encender"); latido(); pintar(); } finally { enc.disabled = false; } });
  const apa = btn("Apagar", "secondary", async () => { apa.disabled = true; try { await pedir("apagar"); if (reloj) { clearInterval(reloj); reloj = 0; } pintar(); } finally { apa.disabled = false; } });
  const fila = el("div", "cv-form");
  fila.append(enc, apa);
  const nota = el("div", "fila-desc", "Ciclo: leer, un paso, verificar, repetir. Apagar lo corta. ECC no está en Skills; el ciclo usa verificar-antes-de-cerrar.");
  cuerpo.replaceChildren(el("div", "cv-sec", "LOOP"), el("div", "cv-fila"), detalle, fila, nota, est);
  cuerpo.children[1].append(chip);
  pintar();
  if (estado.on) latido();
}

const montar = () => { ventana("loop", "LOOP", pintarLoop); marcarBoton(); };
new MutationObserver(montar).observe(document.body, { childList: true, subtree: true });
montar();
