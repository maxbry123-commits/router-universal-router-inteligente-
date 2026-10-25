// ventana-loop.js — LOOP del chat: objetivo, plan y tareas. Se guardan en yaiwes.md y en el proyecto LOOP.
import { el, btn, ventana } from "./ventanas-control.js";
import { leer, escribir } from "./almacen.js";
import { crearProyecto, listaProyectos } from "./objetivos-ancla.js";

const PARTES = ["objetivo", "plan", "tarea", "verificar"];
const CLAVE = "riu_loop";
const MARCA = ["<!-- loop-yaiwes -->", "<!-- /loop-yaiwes -->"];
let estado = { on: false, paso: 0, fase: "apagado", nota: "apagado", objetivo: "", plan: "", tareas: "" };
let reloj = 0;
try { estado = Object.assign(estado, JSON.parse(sessionStorage.getItem(CLAVE) || "") || {}); } catch (e) {}

function guardar() { try { sessionStorage.setItem(CLAVE, JSON.stringify(estado)); } catch (e) {} }
function sesion() { return sessionStorage.getItem("riu_sesion") || "web-general"; }
function marcarBoton() {
  const b = document.querySelector("#btn-loop");
  if (!b) return;
  b.setAttribute("aria-pressed", estado.on ? "true" : "false");
  b.title = estado.on ? "LOOP encendido" : "LOOP apagado";
}
function leerCampos() {
  const o = document.querySelector("#loop-objetivo");
  if (!o) return;
  estado.objetivo = o.value;
  estado.plan = document.querySelector("#loop-plan").value;
  estado.tareas = document.querySelector("#loop-tareas").value;
}
function lineas() { return String(estado.tareas || "").split(/\n/).map((x) => x.trim()).filter(Boolean); }
function bloque() {
  const tareas = lineas().map((t) => "- " + t).join("\n") || "- (sin tareas)";
  return MARCA[0] + "\n# LOOP\n## Objetivo\n" + (estado.objetivo || "") + "\n## Plan\n" + (estado.plan || "") + "\n## Tareas\n" + tareas + "\n## Motor\n" + PARTES.join("\n") + "\n" + MARCA[1];
}
function meter(prev) {
  const i = prev.indexOf(MARCA[0]), j = prev.indexOf(MARCA[1]);
  if (i >= 0 && j > i) return prev.slice(0, i) + bloque() + prev.slice(j + MARCA[1].length);
  return (prev.trim() ? prev.trim() + "\n\n" : "") + bloque();
}

async function pedir(accion) {
  leerCampos();
  const s = sesion();
  const texto = { objetivo: estado.objetivo || "", plan: estado.plan || "", tareas: estado.tareas || "" };
  try {
    const r = await fetch(accion ? "/api/loop" : "/api/loop?sesion=" + encodeURIComponent(s), {
      method: accion ? "POST" : "GET",
      headers: { "Content-Type": "application/json" },
      body: accion ? JSON.stringify({ accion, sesion: s, ...texto }) : undefined,
    });
    if (!r.ok) throw new Error("HTTP " + r.status);
    estado = Object.assign(texto, await r.json());
  } catch (e) {
    if (accion === "encender") estado = { ...texto, on: true, paso: estado.paso || 0, fase: "objetivo", nota: "en este chat" };
    else if (accion === "apagar") estado = { ...texto, on: false, paso: estado.paso || 0, fase: "apagado", nota: "apagado" };
    else if (accion === "paso" && estado.on) {
      const fase = PARTES[(PARTES.indexOf(estado.fase) + 1) % PARTES.length];
      estado = { ...texto, on: true, paso: estado.paso + (fase === "objetivo" ? 1 : 0), fase, nota: "en este chat" };
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

async function guardarYaiwes(aviso) {
  leerCampos();
  const ta = document.querySelector("#mi-handoff");
  const texto = meter(ta ? ta.value : "");
  if (ta) ta.value = texto;
  let nota = "escrito en yaiwes.md de este chat";
  try {
    if (window.RIU_ACCION) {
      const r = await window.RIU_ACCION("handoff_texto", { sesion: sesion(), texto });
      const est = document.querySelector("#mh-estado");
      if (est && r) est.textContent = r.encendido ? "encendido" : "apagado";
      nota = r && r.encendido ? "yaiwes.md encendido" : nota;
    }
  } catch (e) { nota = "quedó en el campo yaiwes.md; el servidor no confirmó"; }
  guardar();
  if (aviso) aviso.textContent = nota;
}

function enlazarProyecto(aviso) {
  leerCampos();
  crearProyecto("LOOP");
  const t = leer("riu_proy_v1", {});
  t.global = Array.isArray(t.global) ? t.global : [];
  const p = t.global.find((x) => x.nombre === "LOOP") || listaProyectos().find((x) => x.nombre === "LOOP");
  if (!p) { if (aviso) aviso.textContent = "no pude crear el proyecto"; return; }
  p.notas = [estado.objetivo, estado.plan].filter(Boolean).join("\n");
  p.items = lineas().map((x) => "texto:" + x.slice(0, 2000));
  p.on = true;
  escribir("riu_proy_v1", t);
  try { if (window.RIU_ACCION) window.RIU_ACCION("proyecto", { op: "upsert", project_id: p.project_id, nombre: "LOOP", encendido: true }).catch(() => {}); } catch (e) {}
  guardar();
  if (aviso) aviso.textContent = "proyecto LOOP enlazado · " + p.items.length + " tareas";
}

function pintarLoop(cuerpo) {
  const aviso = el("div", "cv-est");
  const partes = el("div", "loop-partes");
  const objetivo = el("textarea", "vn-ta"); objetivo.id = "loop-objetivo"; objetivo.rows = 2; objetivo.placeholder = "Objetivo"; objetivo.value = estado.objetivo || "";
  const plan = el("textarea", "vn-ta"); plan.id = "loop-plan"; plan.rows = 2; plan.placeholder = "Plan"; plan.value = estado.plan || "";
  const tareas = el("textarea", "vn-ta"); tareas.id = "loop-tareas"; tareas.rows = 3; tareas.placeholder = "Tareas, una por línea"; tareas.value = estado.tareas || "";
  const pintar = () => {
    partes.replaceChildren();
    PARTES.forEach((p) => { const s = el("span", estado.fase === p ? "on" : "", p); partes.append(s); });
    const n = lineas().length;
    const actual = n ? lineas()[estado.paso % n] : "";
    aviso.textContent = (estado.on ? "encendido" : "apagado") + " · " + estado.fase + (actual ? " · " + actual : "");
  };
  window.__riuLoopPintar = pintar;
  const enc = btn("Encender", "secondary", async () => { enc.disabled = true; try { await pedir("encender"); latido(); pintar(); } finally { enc.disabled = false; } });
  const apa = btn("Apagar", "secondary", async () => { apa.disabled = true; try { await pedir("apagar"); if (reloj) { clearInterval(reloj); reloj = 0; } pintar(); } finally { apa.disabled = false; } });
  const gy = btn("Guardar en yaiwes.md", "secondary", () => guardarYaiwes(aviso));
  const ep = btn("Enlazar al proyecto", "secondary", () => enlazarProyecto(aviso));
  const fila = el("div", "cv-form");
  fila.append(enc, apa, gy, ep);
  cuerpo.replaceChildren(el("div", "cv-sec", "LOOP"), partes, objetivo, plan, tareas, fila, el("div", "fila-desc", "El motor va en cuatro partes: objetivo, plan, tarea y verificar. yaiwes.md no se borra: solo se reemplaza el bloque del LOOP."), aviso);
  pintar();
  if (estado.on) latido();
}

const montar = () => { ventana("loop", "LOOP", pintarLoop); marcarBoton(); if (estado.on) latido(); };
new MutationObserver(montar).observe(document.body, { childList: true, subtree: true });
montar();
