// ventana-loop.js — LOOP del chat: objetivo, plan y tareas. Se guardan en yaiwes.md y en el proyecto LOOP.
import { el, btn, ventana } from "./ventanas-control.js";
import { leer, escribir } from "./almacen.js";
import { crearProyecto, listaProyectos } from "./objetivos-ancla.js";

const PARTES = ["objetivo", "plan", "tarea", "verificar"];
const NOMBRE = { objetivo: "contexto", plan: "plan", tarea: "actuar", verificar: "observar" };
const SIGUE = { objetivo: "plan", plan: "tarea", tarea: "verificar", verificar: "objetivo" };
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
function anotar(e, extra) {
  const item = extra.nota + ": " + String(extra.disparo || "").slice(0, 80);
  const traza = (Array.isArray(e.traza) ? e.traza : []).concat(item).slice(-4);
  return { ...e, ...extra, traza };
}
function disparar(e) {
  const tareas = String(e.tareas || "").split(/\n/).map((s) => s.trim()).filter(Boolean);
  const fase = PARTES.includes(e.fase) ? e.fase : "objetivo";
  const hecho = e.hecho || 0;
  if (fase === "objetivo") {
    if (!String(e.objetivo || "").trim()) return { ...e, on: true, fase, nota: "falta objetivo", disparo: "" };
    return anotar(e, { on: true, fase: "plan", nota: "objetivo", disparo: String(e.objetivo).trim().slice(0, 180) });
  }
  if (fase === "plan") {
    if (!String(e.plan || "").trim()) return { ...e, on: true, fase, nota: "falta plan", disparo: "" };
    return anotar(e, { on: true, fase: "tarea", nota: "plan", disparo: String(e.plan).trim().slice(0, 180) });
  }
  if (fase === "tarea") {
    if (!tareas.length || hecho >= tareas.length) return { ...e, on: true, fase, nota: "sin tareas", disparo: "" };
    return anotar(e, { on: true, fase: "verificar", hecho: hecho + 1, nota: "tarea", disparo: tareas[hecho].slice(0, 180) });
  }
  if (!e.disparo) return { ...e, on: true, fase: "verificar", nota: "nada que verificar" };
  const paso = (e.paso || 0) + 1;
  if (paso >= 8) return anotar(e, { on: false, fase: "apagado", paso, nota: "tope", disparo: e.disparo });
  return anotar(e, { on: true, fase: "objetivo", paso, nota: hecho >= tareas.length ? "vuelta completa" : "verificado", disparo: e.disparo });
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
    if (accion === "encender") estado = { ...estado, ...texto, on: true, fase: "objetivo", nota: "en este chat" };
    else if (accion === "apagar") estado = { ...estado, ...texto, on: false, fase: "apagado", nota: "apagado" };
    else if (accion === "paso" && estado.on) estado = disparar({ ...estado, ...texto, on: true });
  }
  guardar();
  marcarBoton();
  return estado;
}

function latido() {
  if (reloj) return;
  reloj = setInterval(() => {
    if (!estado.on || /^(falta |sin |nada |tope)/.test(estado.nota || "")) { clearInterval(reloj); reloj = 0; return; }
    pedir("paso").then(() => { if (window.__riuLoopPintar) window.__riuLoopPintar(); });
  }, 3000);
}

async function guardarYaiwes(aviso) {
  leerCampos();
  const ta = document.querySelector("#mi-handoff");
  let base = ta ? ta.value : "";
  let nota = "escrito en yaiwes.md de este chat";
  try {
    if (window.RIU_ACCION) {
      const actual = await window.RIU_ACCION("handoff_texto", { sesion: sesion() });
      if (actual && typeof actual.texto === "string" && actual.texto.trim()) base = actual.texto;
      const texto = meter(base);
      if (ta) ta.value = texto;
      const r = await window.RIU_ACCION("handoff_texto", { sesion: sesion(), texto });
      const est = document.querySelector("#mh-estado");
      if (est && r) est.textContent = r.encendido ? "encendido" : "apagado";
      nota = r && r.encendido ? "yaiwes.md encendido" : nota;
    } else if (ta) ta.value = meter(base);
  } catch (e) {
    if (ta) ta.value = meter(base);
    nota = "quedó en el campo yaiwes.md; el servidor no confirmó";
  }
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
  const mando = el("div", "loop-mando");
  const centro = el("div", "loop-centro");
  const pct = el("div", "loop-pct", "0%");
  const barra = el("div", "loop-barra");
  const relleno = el("div", "loop-relleno");
  const lista = el("div", "loop-lista");
  barra.append(relleno);
  centro.append(pct, barra, lista);
  const objetivo = el("textarea", "vn-ta"); objetivo.id = "loop-objetivo"; objetivo.rows = 1; objetivo.placeholder = "Objetivo"; objetivo.value = estado.objetivo || "";
  const plan = el("textarea", "vn-ta"); plan.id = "loop-plan"; plan.rows = 1; plan.placeholder = "Plan"; plan.value = estado.plan || "";
  const tareas = el("textarea", "vn-ta"); tareas.id = "loop-tareas"; tareas.rows = 2; tareas.placeholder = "Tareas, una por línea"; tareas.value = estado.tareas || "";
  const pintar = () => {
    partes.replaceChildren();
    PARTES.forEach((p) => { const s = el("span", estado.fase === p ? "on" : "", NOMBRE[p]); partes.append(s); });
    const todas = lineas();
    const hechas = Math.min(estado.hecho || 0, todas.length);
    const n = todas.length ? Math.round(hechas * 100 / todas.length) : 0;
    pct.textContent = n + "% · " + hechas + " de " + todas.length;
    relleno.style.width = n + "%";
    lista.replaceChildren();
    if (!todas.length) lista.append(el("div", "fila-desc", "Sin tareas"));
    todas.forEach((t, i) => {
      const row = el("div", "loop-tarea" + (i < hechas ? " hecha" : ""));
      row.append(el("span", "", i < hechas ? "hecha" : "pendiente"), el("span", "", t));
      lista.append(row);
    });
    const bloqueado = /^(falta |sin |nada )/.test(estado.nota || "");
    const sigue = NOMBRE[SIGUE[estado.fase] || "objetivo"];
    const traza = Array.isArray(estado.traza) ? estado.traza : [];
    const marcha = !estado.on ? "apagado" : reloj ? "en curso" : "en pausa";
    mando.replaceChildren(
      el("div", "", marcha + (bloqueado ? " · bloqueado" : "") + " · vuelta " + (estado.paso || 0) + "/8"),
      el("div", "", "siguiente: " + sigue),
    );
    traza.forEach((t) => mando.append(el("div", "", t)));
    if (!traza.length) mando.append(el("div", "", "sin traza"));
    aviso.textContent = bloqueado ? estado.nota : (estado.disparo ? "observado" : "sin disparo");
    if (auto) auto.textContent = reloj ? "Pausa" : "Seguir";
  };
  let auto = null;
  [objetivo, plan, tareas].forEach((x) => x.addEventListener("input", () => { leerCampos(); pintar(); }));
  window.__riuLoopPintar = pintar;
  const enc = btn("Encender", "secondary", async () => { enc.disabled = true; try { await pedir("encender"); pintar(); } finally { enc.disabled = false; } });
  const apa = btn("Apagar", "secondary", async () => { apa.disabled = true; try { await pedir("apagar"); if (reloj) { clearInterval(reloj); reloj = 0; } pintar(); } finally { apa.disabled = false; } });
  const di = btn("Disparar", "secondary", async () => { if (!estado.on) { aviso.textContent = "enciéndelo primero"; return; } di.disabled = true; try { await pedir("paso"); pintar(); } finally { di.disabled = false; } });
  auto = btn("Seguir", "secondary", () => { if (!estado.on) { aviso.textContent = "enciéndelo primero"; return; } if (reloj) { clearInterval(reloj); reloj = 0; } else latido(); pintar(); });
  const gy = btn("Guardar en yaiwes.md", "secondary", () => guardarYaiwes(aviso));
  const ep = btn("Enlazar al proyecto", "secondary", () => enlazarProyecto(aviso));
  const fila = el("div", "cv-form");
  fila.append(enc, apa, di, auto, gy, ep);
  cuerpo.replaceChildren(el("div", "cv-sec", "LOOP"), partes, mando, centro, objetivo, plan, tareas, fila, aviso);
  pintar();
}

const montar = () => { ventana("loop", "LOOP", pintarLoop); marcarBoton(); };
new MutationObserver(montar).observe(document.body, { childList: true, subtree: true });
montar();
if (estado.on) latido();
