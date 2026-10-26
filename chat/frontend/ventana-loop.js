// ventana-loop.js — LOOP del chat: objetivo, plan y tareas. Se guardan en yaiwes.md y en el proyecto LOOP.
import { el, btn, ventana, vivo, SIN_BACKEND } from "./ventanas-control.js";
import { leer, escribir } from "./almacen.js";
import { crearProyecto, listaProyectos } from "./objetivos-ancla.js";

const PARTES = ["objetivo", "plan", "tarea", "verificar"];
const NOMBRE = { objetivo: "contexto", plan: "plan", tarea: "actuar", verificar: "observar" };
const SIGUE = { objetivo: "plan", plan: "tarea", tarea: "verificar", verificar: "objetivo" };
const CLAVE = "riu_loop";
const MARCA = ["<!-- loop-yaiwes -->", "<!-- /loop-yaiwes -->"];
let estado = { on: false, paso: 0, fase: "apagado", nota: "apagado", objetivo: "", plan: "", tareas: "" };
let reloj = 0;      // temporizador del Seguir (0 = en pausa)
let enVuelo = false;  // un solo paso a la vez: ni el reloj ni los clics lo solapan
let backend = "";   // "" aún no se sabe · "servidor" /api/loop respondió · "sin" no hay servidor y el LOOP corre solo en este chat
try { estado = Object.assign(estado, JSON.parse(sessionStorage.getItem(CLAVE) || "") || {}); } catch (e) {}

const tope = () => (specEcc && specEcc.tope) || 8;
const pausaPor = (nota) => ((specEcc && specEcc.wachdog && specEcc.wachdog.pausa_si) || ["falta ", "sin ", "nada ", "tope"]).some((p) => String(nota || "").startsWith(p));
const intervalo = () => Math.max(50, Number(specEcc && specEcc.wachdog && specEcc.wachdog.intervalo_ms) || 3000);
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
let specEcc = null;
let cable = "";
function avisarPlugin() {
  if (cable || !specEcc || !specEcc.plugin) return;
  const base = String((window.RIU_CONFIG || {}).proxyDestino || "").replace(/\/$/, "");
  if (!base) { cable = "chat"; return; }
  cable = "espera";
  const h = { "Content-Type": "application/json" };
  const k = sessionStorage.getItem("riu_clave");
  if (k) { h["X-API-Key"] = k; h.Authorization = "Bearer " + k; }
  const ctrl = new AbortController();
  setTimeout(() => ctrl.abort(), 2500);
  fetch(base + "/plugins/" + specEcc.plugin + "/call/paso", { method: "POST", headers: h, body: JSON.stringify({ accion: "paso" }), signal: ctrl.signal })
    .then((r) => { cable = r.ok ? "harness" : "chat"; })
    .catch(() => { cable = "chat"; })
    .then(() => { if (window.__riuLoopPintar) window.__riuLoopPintar(); });
}
async function spec() {
  if (specEcc) return specEcc;
  const r = await fetch("/chat/ui/LOOP-wachdog-cola.json");
  if (!r.ok) throw new Error("sin motor");
  const j = await r.json();
  specEcc = { componentes: j.cola, tope: j.wachdog.tope, plugin: j.plugin, botones: j.botones, wachdog: j.wachdog };
  return specEcc;
}
function etiqueta(id, fb) {
  const b = specEcc && (specEcc.botones || []).find((x) => x.id === id);
  return (b && b.texto) || fb;
}
function eccPaso(e, spec) {
  const comps = {};
  spec.componentes.forEach((c) => { comps[c.fase] = c; });
  const fase = comps[e.fase] ? e.fase : "objetivo";
  const c = comps[fase];
  const tareas = String(e.tareas || "").split(/\n/).map((s) => s.trim()).filter(Boolean);
  const hecho = e.hecho || 0;
  if (c.op === "exigir") {
    const valor = String(e[c.campo] || "").trim();
    if (!valor) return { ...e, on: true, fase, nota: c.falta, disparo: "" };
    return anotar(e, { on: true, fase: c.siguiente, nota: c.id, disparo: valor.slice(0, 180) });
  }
  if (c.op === "tomar") {
    if (!tareas.length || hecho >= tareas.length) return { ...e, on: true, fase, nota: c.falta, disparo: "" };
    return anotar(e, { on: true, fase: c.siguiente, nota: c.id, disparo: tareas[hecho].slice(0, 180) });
  }
  if (!e.disparo) return { ...e, on: true, fase, nota: c.falta };
  const hecho2 = hecho + 1;
  const n = (e.paso || 0) + 1;
  if (n >= spec.tope) return anotar(e, { on: false, fase: "apagado", paso: n, hecho: hecho2, nota: "tope", disparo: e.disparo });
  return anotar(e, { on: true, fase: c.siguiente, paso: n, hecho: hecho2, nota: hecho2 >= tareas.length ? "vuelta completa" : c.id, disparo: e.disparo });
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
    return anotar(e, { on: true, fase: "verificar", nota: "tarea", disparo: tareas[hecho].slice(0, 180) });
  }
  if (!e.disparo) return { ...e, on: true, fase: "verificar", nota: "nada que verificar" };
  const hecho2 = hecho + 1;
  const paso = (e.paso || 0) + 1;
  if (paso >= tope()) return anotar(e, { on: false, fase: "apagado", paso, hecho: hecho2, nota: "tope", disparo: e.disparo });
  return anotar(e, { on: true, fase: "objetivo", paso, hecho: hecho2, nota: hecho2 >= tareas.length ? "vuelta completa" : "verificado", disparo: e.disparo });
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
  if (accion === "paso") { if (enVuelo) return estado; enVuelo = true; }
  try { return await pedirReal(accion); } finally { if (accion === "paso") enVuelo = false; }
}
async function pedirReal(accion) {
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
    backend = "servidor";
  } catch (e) {
    backend = "sin";
    if (accion === "encender") estado = { ...estado, ...texto, on: true, fase: "objetivo", nota: "en este chat" };
    else if (accion === "apagar") estado = { ...estado, ...texto, on: false, fase: "apagado", nota: "apagado" };
    else if (accion === "reiniciar") estado = { ...estado, ...texto, on: true, fase: "objetivo", paso: 0, hecho: 0, disparo: "", nota: "reinicio", traza: [] };
    else if (accion === "paso" && estado.on) {
      try { estado = eccPaso({ ...estado, ...texto, on: true }, await spec()); }
      catch (err) { estado = disparar({ ...estado, ...texto, on: true }); }
    }
  }
  guardar();
  marcarBoton();
  if (accion === "paso") avisarPlugin();
  return estado;
}

let gen = 0;  // cada Seguir/Pausa abre una generación: un paso viejo en vuelo no reprograma el reloj
function parar() { gen++; if (reloj) { clearTimeout(reloj); reloj = 0; } }
function latido() {  // un paso, y solo cuando termina se programa el siguiente (sin solaparse); el intervalo sale del JSON
  if (reloj) return;
  const miGen = ++gen;
  const tic = async () => {
    if (!estado.on || pausaPor(estado.nota)) { reloj = 0; if (window.__riuLoopPintar) window.__riuLoopPintar(); return; }
    await pedir("paso");
    if (window.__riuLoopPintar) window.__riuLoopPintar();
    if (miGen !== gen) return;  // lo pausaron o reiniciaron mientras el paso estaba en vuelo
    if (!estado.on || pausaPor(estado.nota)) { reloj = 0; if (window.__riuLoopPintar) window.__riuLoopPintar(); return; }
    reloj = setTimeout(tic, intervalo());
  };
  reloj = setTimeout(tic, intervalo());
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

async function enlazarProyecto(aviso) {
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
  guardar();
  const base = "proyecto LOOP enlazado · " + p.items.length + " tareas";
  if (!window.RIU_ACCION) { if (aviso) aviso.textContent = base + " · " + SIN_BACKEND + ": solo en este chat"; return; }
  try {
    await window.RIU_ACCION("proyecto", { op: "upsert", project_id: p.project_id, nombre: "LOOP", encendido: true });
    if (aviso) aviso.textContent = base + " · guardado en el servidor";
  } catch (e) { if (aviso) aviso.textContent = base + " · el servidor no lo guardó (" + (e.message || "sin respuesta") + ")"; }
}

function pintarLoop(cuerpo) {
  const aviso = vivo(el("div", "cv-est"));
  const partes = el("div", "loop-partes");
  const mando = el("div", "loop-mando");
  const centro = el("div", "loop-centro");
  const pct = el("div", "loop-pct", "0%");
  const barra = el("div", "loop-barra");
  const relleno = el("div", "loop-relleno");
  const lista = el("div", "loop-lista");
  barra.setAttribute("role", "progressbar"); barra.setAttribute("aria-label", "Avance del LOOP");
  barra.setAttribute("aria-valuemin", "0"); barra.setAttribute("aria-valuemax", "100"); barra.setAttribute("aria-valuenow", "0");
  lista.setAttribute("role", "list");
  barra.append(relleno);
  centro.append(pct, barra, lista);
  const objetivo = el("textarea", "vn-ta"); objetivo.id = "loop-objetivo"; objetivo.rows = 1; objetivo.placeholder = "Objetivo"; objetivo.setAttribute("aria-label", "Objetivo del LOOP"); objetivo.value = estado.objetivo || "";
  const plan = el("textarea", "vn-ta"); plan.id = "loop-plan"; plan.rows = 1; plan.placeholder = "Plan"; plan.setAttribute("aria-label", "Plan del LOOP"); plan.value = estado.plan || "";
  const tareas = el("textarea", "vn-ta"); tareas.id = "loop-tareas"; tareas.rows = 2; tareas.placeholder = "Tareas, una por línea"; tareas.setAttribute("aria-label", "Tareas del LOOP, una por línea"); tareas.value = estado.tareas || "";
  const pintar = () => {
    partes.replaceChildren();
    PARTES.forEach((p) => { const s = el("span", estado.fase === p ? "on" : "", NOMBRE[p]); partes.append(s); });
    const todas = lineas();
    const hechas = Math.min(estado.hecho || 0, todas.length);
    const n = todas.length ? Math.round(hechas * 100 / todas.length) : 0;
    pct.textContent = n + "% · " + hechas + " de " + todas.length;
    relleno.style.width = n + "%"; barra.setAttribute("aria-valuenow", String(n)); barra.setAttribute("aria-valuetext", pct.textContent);
    lista.replaceChildren();
    if (!todas.length) lista.append(el("div", "fila-desc", "Sin tareas"));
    todas.forEach((t, i) => {
      const ahora = estado.fase === "verificar" && i === hechas;
      const marca = ahora ? "ahora" : i < hechas ? "hecha" : "pendiente";
      const row = el("div", "loop-tarea" + (ahora ? " ahora" : i < hechas ? " hecha" : "")); row.setAttribute("role", "listitem");
      row.append(el("span", "", marca), el("span", "", t));
      lista.append(row);
    });
    const bloqueado = /^(falta |sin |nada )/.test(estado.nota || "");
    const sigue = NOMBRE[SIGUE[estado.fase] || "objetivo"];
    const traza = Array.isArray(estado.traza) ? estado.traza : [];
    const marcha = !estado.on ? "apagado" : reloj ? "en curso" : "en pausa";
    mando.replaceChildren(
      el("div", "", marcha + (bloqueado ? " · bloqueado" : "") + " · vuelta " + (estado.paso || 0) + "/" + tope()),
      el("div", "", "siguiente: " + sigue + (cable === "harness" ? " · en el harness" : backend === "sin" || cable === "chat" ? " · " + SIN_BACKEND + ": corre solo en este chat" : "")),
    );
    traza.forEach((t) => mando.append(el("div", "", t)));
    if (!traza.length) mando.append(el("div", "", "sin traza"));
    aviso.textContent = bloqueado ? estado.nota : (estado.disparo ? "observado" : "sin disparo");
    if (auto) { auto.textContent = reloj ? "Pausa" : "Seguir"; auto.setAttribute("aria-pressed", reloj ? "true" : "false"); }
    if (enc) enc.setAttribute("aria-pressed", estado.on ? "true" : "false");
  };
  let auto = null, enc = null, anclarGob = null;
  [objetivo, plan, tareas].forEach((x) => x.addEventListener("input", () => { leerCampos(); pintar(); }));
  window.__riuLoopPintar = pintar;
  enc = btn(etiqueta("encender", "Encender"), "secondary", async () => { enc.disabled = true; try { await pedir("encender"); pintar(); } finally { enc.disabled = false; } });
  const apa = btn(etiqueta("apagar", "Apagar"), "secondary", async () => { apa.disabled = true; try { await pedir("apagar"); parar(); pintar(); } finally { apa.disabled = false; } });
  const di = btn(etiqueta("disparar", "Disparar"), "secondary", async () => { if (!estado.on) { aviso.textContent = "enciéndelo primero"; return; } di.disabled = true; try { await pedir("paso"); pintar(); } finally { di.disabled = false; } });
  auto = btn(etiqueta("seguir", "Seguir"), "secondary", () => { if (!estado.on) { aviso.textContent = "enciéndelo primero"; return; } if (reloj) parar(); else latido(); pintar(); });
  const re = btn(etiqueta("reiniciar", "Reiniciar"), "secondary", async () => { parar(); re.disabled = true; try { await pedir("reiniciar"); pintar(); } finally { re.disabled = false; } });
  const gy = btn(etiqueta("yaiwes", "Yaiwes"), "secondary", async () => { if (gy.disabled) return; gy.disabled = true; try { await guardarYaiwes(aviso); if (anclarGob) await anclarGob(); } finally { gy.disabled = false; } });
  gy.title = "Guardar en yaiwes.md";
  const ep = btn(etiqueta("proyecto", "Proyecto"), "secondary", async () => { if (ep.disabled) return; ep.disabled = true; try { await enlazarProyecto(aviso); } finally { ep.disabled = false; } });
  ep.title = "Enlazar al proyecto";
  const fila = el("div", "cv-form");
  fila.append(enc, apa, di, auto, re, gy, ep);
  const md = el("textarea", "vn-ta");
  md.rows = 3; md.placeholder = "Yaiwes.md — pega aquí el objetivo"; md.setAttribute("aria-label", "Yaiwes.md");
  const fases = ["objetivo", "plan", "tarea", "verificar"];
  estado.modelos = estado.modelos || {};
  const modelos = () => ((window.RIU_SELECTOR_QWEN && window.RIU_SELECTOR_QWEN.modelos) || []).filter((m) => m.model_id && !/image|tts|asr|wan|realtime/i.test(m.model_id + " " + (m.label || "")));
  const filaMod = el("div", "cv-form");
  filaMod.style.cssText = "display:grid;grid-template-columns:1fr 1fr;gap:6px";
  fases.forEach((f) => {
    const s = el("select"); s.setAttribute("aria-label", "Modelo de " + f); s.style.width = "100%";
    const opts = modelos();
    if (!opts.length) s.append(new Option("Qwen 3.8 Max", "qwen3.8-max"));
    opts.forEach((m) => s.append(new Option(m.label, m.model_id)));
    s.value = estado.modelos[f] || "qwen3.8-max";
    s.onchange = () => { estado.modelos[f] = s.value; guardar(); };
    const lab = el("label"); lab.style.cssText = "display:flex;flex-direction:column;gap:2px;font-size:11px;min-width:0";
    lab.append(el("span", "", f), s);
    filaMod.append(lab);
  });
  const perfil = el("select"); perfil.setAttribute("aria-label", "Perfil");
  ["document", "code", "frontend", "api"].forEach((v) => perfil.append(new Option(v, v)));
  const ruta = el("input"); ruta.placeholder = "archivo.txt"; ruta.setAttribute("aria-label", "Ruta de aceptación");
  const nct = vivo(el("div", "cv-est"));
  const gobBox = el("div", "cv-est");
  let proc = "", poll = 0, gob = "", gobPoll = 0;
  const modeloChat = () => {
    const q = window.RIU_SELECTOR_QWEN, s = q && q.seleccion;
    if (!s) return "qwen3.8-max";
    const hit = (q.modelos || []).find((m) => m.modelo_id_slug === s.modelo_id_slug);
    return (hit && hit.model_id) || s.model_id || "qwen3.8-max";
  };
  const pararPoll = () => { if (poll) { clearInterval(poll); poll = 0; } };
  const pararGob = () => { if (gobPoll) { clearInterval(gobPoll); gobPoll = 0; } };
  const pintarGob = (r) => {
    const res = r.resultado || {};
    const lista = Array.isArray(res.ciclos) ? res.ciclos : [];
    const wd = res.watchdog || {};
    const trozos = [r.estado || "", res.status || ""];
    if (wd.estado) trozos.push("watchdog " + wd.estado);
    nct.textContent = trozos.filter(Boolean).join(" · ");
    gobBox.replaceChildren();
    const tareas = el("ul", "riu-tareas");
    lista.forEach((c) => {
      if (!c || typeof c !== "object") { const li = el("li"); li.append(el("span", "riu-tilde"), el("span", "riu-tarea-t", String(c))); tareas.append(li); return; }
      const li = el("li", c.ok === true ? "hecha" : "");
      const tilde = el("span", "riu-tilde", c.ok === true ? "✓" : c.ok === false ? "✕" : "");
      if (c.ok === false) { li.style.borderColor = "#ff5d5d"; tilde.style.background = "#ff5d5d"; tilde.style.color = "#fff"; tilde.style.borderColor = "#ff5d5d"; }
      li.append(tilde, el("span", "riu-tarea-t", [c.ciclo, c.motor, c.recibo].filter((x) => x != null && x !== "").join(" · ")));
      tareas.append(li);
    });
    if (tareas.childElementCount) gobBox.append(tareas);
    (Array.isArray(wd.fallos) ? wd.fallos : []).forEach((f) => gobBox.append(el("div", "", "fallo · " + (typeof f === "string" ? f : JSON.stringify(f)))));
    const c5 = lista[5];
    const pasos = c5 && c5.microciclo && c5.microciclo[0] && c5.microciclo[0].pasos;
    if (pasos && typeof pasos === "object") Object.keys(pasos).forEach((k) => {
      const v = pasos[k];
      const row = el("div", "", k + " · " + String(v));
      if (v === true) row.style.color = "#3dd68c";
      if (v === false) row.style.color = "#ff5d5d";
      gobBox.append(row);
    });
  };
  const leerGob = async () => {
    if (!gob) return;
    try {
      const r = await window.RIU_PLUGIN("nct_loop", "estado", { proceso_id: gob });
      pintarGob(r);
      if (String(r.estado || "") !== "procesando") pararGob();
    } catch (e) { nct.textContent = e.message; pararGob(); }
  };
  anclarGob = async () => {
    if (!md.value.trim()) { nct.textContent = "falta el objetivo"; return; }
    pararGob();
    try {
      const r = await window.RIU_PLUGIN("nct_loop", "gobernar", { objetivo: md.value, modelo: modeloChat(), sesion: sesion() });
      gob = r.proceso_id || "";
      const nombres = Array.isArray(r.ciclos) ? r.ciclos.join(" ") : "";
      nct.textContent = [r.estado || "", gob, nombres].filter(Boolean).join(" · ");
      if (gob) gobPoll = setInterval(leerGob, 2000);
    } catch (e) { nct.textContent = e.message; pararGob(); }
  };
  const leerEstado = async () => {
    if (!proc) return;
    try {
      const r = await window.RIU_PLUGIN("nct_loop", "estado", { proceso_id: proc });
      const st = String(r.estado || r.status || "");
      const res = r.resultado || {};
      const motores = Array.isArray(res.skills_ejecutadas) ? res.skills_ejecutadas.filter(Boolean) : [];
      nct.textContent = [proc, st || "sin estado", res.status || "", motores.length ? "motor code · " + motores.join(", ") : ""].filter(Boolean).join(" · ");
      if (res.trace || res.receipts) gobBox.textContent = JSON.stringify({ trace: res.trace, receipts: res.receipts }).slice(0, 500);
      if (/DONE_VERIFICADO|BLOCKED|FAIL/.test(st + " " + (res.status || ""))) pararPoll();
    } catch (e) { nct.textContent = e.message; pararPoll(); }
  };
  const ejecutar = btn("EJECUTAR", "action", async () => {
    if (!md.value.trim()) { nct.textContent = "falta el objetivo"; return; }
    ejecutar.disabled = true; pararPoll();
    try {
      const r = await window.RIU_PLUGIN("nct_loop", "ejecutar", {
        objetivo: md.value, modelo: (estado.modelos && estado.modelos.tarea) || modeloChat(), profile: perfil.value, motor: "coda",
        auto_skills: true, top_skills: 3, skills: ["verification-loop"],
        secciones: estado.modelos || {},
        acceptance: ruta.value.trim() ? [{ op: "verify_exists", path: ruta.value.trim() }] : [],
      });
      proc = r.proceso_id || "";
      nct.textContent = proc ? proc + " · " + modeloChat() : JSON.stringify(r).slice(0, 160);
      if (proc) poll = setInterval(leerEstado, 3000);
    } catch (e) { nct.textContent = e.message; }
    ejecutar.disabled = false;
  });
  const cancelarN = btn("CANCELAR", "secondary", async () => {
    if (!proc && !gob) { nct.textContent = "no hay proceso"; return; }
    try {
      if (proc) { await window.RIU_PLUGIN("nct_loop", "cancelar", { proceso_id: proc }); pararPoll(); }
      if (gob) { await window.RIU_PLUGIN("nct_loop", "cancelar", { proceso_id: gob }); pararGob(); gob = ""; }
      nct.textContent = (proc || "") + " · cancelado";
    } catch (e) { nct.textContent = e.message; }
  });
  const salud = btn("Health", "secondary", async () => {
    try { const r = await window.RIU_PLUGIN("nct_loop", "status", {}); nct.textContent = JSON.stringify(r).slice(0, 180); }
    catch (e) { nct.textContent = e.message; }
  });
  const ancla = btn("Constitución", "secondary", () => { const x = document.querySelector("#btn-ancla"); if (x) x.click(); });
  const pend = btn("Pendientes", "secondary", () => { const x = document.querySelector("#btn-pendientes"); if (x) x.click(); });
  const tools = btn("Tools", "secondary", () => { const x = document.querySelector("#btn-tools"); if (x) x.dispatchEvent(new MouseEvent("contextmenu", { bubbles: true, cancelable: true })); });
  const nctFila = el("div", "cv-form");
  nctFila.style.cssText = "display:grid;grid-template-columns:1fr 1fr;gap:6px";
  perfil.style.gridColumn = "1 / -1";
  ejecutar.style.gridColumn = "1 / -1";
  nctFila.append(perfil, ejecutar, cancelarN, salud, ancla, pend, tools);
  cuerpo.replaceChildren(el("div", "cv-sec", "Yaiwes.md"), md, filaMod, ruta, nctFila, nct, gobBox, el("div", "cv-sec", "LOOP"), partes, mando, fila, centro, objetivo, plan, tareas, aviso);
  pintar();
}

const montar = () => { ventana("loop", "LOOP", pintarLoop); marcarBoton(); };
new MutationObserver(montar).observe(document.body, { childList: true, subtree: true });
montar();
if (estado.on) latido();
spec().catch(() => {});
