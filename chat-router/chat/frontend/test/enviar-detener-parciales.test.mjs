import test from "node:test";
import assert from "node:assert/strict";

// enviar-mensaje.js: Detener en tareas SWE corta el bucle de avance y aborta el fetch; el stream SSE del bridge alimenta riu-progreso con `parcial`.
const datos = new Map();
globalThis.localStorage = { getItem: (k) => datos.get(k) ?? null, setItem: (k, v) => datos.set(k, String(v)), removeItem: (k) => datos.delete(k) };
globalThis.sessionStorage = { getItem: () => null };
globalThis.window = globalThis; globalThis.Event = class { constructor(t) { this.type = t; } };
globalThis.CustomEvent = class { constructor(t, o) { this.type = t; this.detail = o && o.detail; } };
const eventos = [];
globalThis.dispatchEvent = (e) => { eventos.push(e); return true; };
globalThis.addEventListener = () => {}; globalThis.removeEventListener = () => {};
globalThis.matchMedia = () => ({ matches: false });
const nodo = () => ({ children: [], events: {}, value: "", className: "", textContent: "", isConnected: true, style: {}, classList: { contains() { return false; }, add() {} },
  append(...xs) { this.children.push(...xs); }, before() {}, replaceChildren() {}, setAttribute() {}, querySelectorAll() { return []; }, querySelector() { return nodo(); }, remove() {}, focus() {}, dispatchEvent() {}, addEventListener(k, fn) { this.events[k] = fn; } });
globalThis.document = { readyState: "loading", addEventListener() {}, getElementById() { return null; }, createElement: nodo };
const { montarEnviar } = await import("../enviar-mensaje.js");
const S = await import("../swe-directo.js");
const filas = new Map(["#composer", "#message"].map((k) => [k, nodo()]));
const c = { sesion: "chat-001", hist: nodo(), ficha: "x", selectorQwen: null, project_id: null };
const llamadas = [];
const OK = { harness: "ok", agentes: Object.fromEntries(["openclaw", "swe-agent", "openhands", "opencode", "codex", "claude-code"].map((a) => [a, { disponible: true }])), workflows: { swe_code: { disponible: true }, liquid_mirror: { disponible: true } } };
let alAvanzar = () => {}, respuestaBridge = null;
const api = async (ruta, op) => {
  llamadas.push({ ruta, body: op && op.body, signal: op && op.signal, sse: op && op.sse });
  if (ruta === "/chat/swe/capacidades") return OK;
  if (ruta === "/chat/swe/iniciar") return { ok: true, resultado: { task_id: op.body.task_id, estado: "EJECUTANDO" } };
  if (ruta === "/chat/swe/avanzar") { alAvanzar(llamadas.filter((l) => l.ruta === "/chat/swe/avanzar").length); return { ok: true, resultado: { task_id: op.body.task_id, estado: "EJECUTANDO" } }; }
  return respuestaBridge(op);
};
globalThis.RIU_SELECTORES = { activo: "swen-code-free" };
globalThis.RIU_SWE = { "swen-code-free": { model_id: "web-qwen38max", label: "Qwen" }, "swe-code": { model_id: "hf-liquid-lfm25", label: "Liquid" } };
globalThis.RIU_CONFIG = {};
montarEnviar({ q: (k) => filas.get(k), chat: () => c, abajo() {}, burbuja: (t) => nodo(), ajustarAlturaEditor() {}, pintarTabs() {},
  getModeUI: () => null, releerAnclas: () => [], chatTools: {}, FAST_SEL: () => false, getModo: () => "", previo: () => [], api, tell() {} });
const enviar = async (txt = "hola") => { llamadas.length = 0; eventos.length = 0; c.hist.children.length = 0; c.detenerFlag = false; filas.get("#message").value = txt; await filas.get("#composer").events.submit({ preventDefault() {} }); };
const textos = () => c.hist.children.map((x) => x.textContent || "").join("\n");
test.beforeEach(() => { S.olvidarCapacidades(); datos.clear(); });

test("Detener a mitad de una tarea SWE: no se llama a avanzar hasta 24 veces; la senal de la peticion queda abortada", async () => {
  S.guardarSeleccion({ workflow: "swe_code", modo_agentico: true });
  alAvanzar = (n) => { if (n === 2) { c.detenerFlag = true; c.detenerFn(); } };  // lo mismo que hace el boton Detener (panel-chat.js)
  await enviar("Revisar proyecto");
  const avances = llamadas.filter((l) => l.ruta === "/chat/swe/avanzar");
  assert.equal(avances.length, 2, "tras Detener no hay mas avanzar");
  assert.ok(avances.every((l) => l.signal && l.signal.aborted === true), "la senal de abortar llego al api y quedo abortada");
  assert.match(textos(), /proceso detenido por el usuario/);
});

test("stream SSE del bridge: el chat recibe riu-progreso con parcial acumulado y al final la respuesta completa", async () => {
  S.guardarSeleccion({ workflow: "individual", modo_agentico: false });
  const ch = (t) => `data: ${JSON.stringify({ choices: [{ delta: { content: t }, finish_reason: null }] })}\r\n\r\n`;
  respuestaBridge = (op) => {
    assert.equal(op.body.stream, true); assert.equal(op.sse, true);
    const enc = new TextEncoder(), partes = [ch("Hola "), ch("mun"), ch("do"), `data: ${JSON.stringify({ choices: [{ delta: {}, finish_reason: "stop" }] })}\n\ndata: [DONE]\n\n`];
    return { __sse: new Response(new ReadableStream({ start(ctl) { for (const p of partes) ctl.enqueue(enc.encode(p)); ctl.close(); } }), { headers: { "content-type": "text/event-stream" } }) };
  };
  await enviar("saluda");
  const parciales = eventos.filter((e) => e.type === "riu-progreso" && e.detail && e.detail.parcial).map((e) => e.detail.parcial);
  assert.deepEqual(parciales, ["Hola ", "Hola mun", "Hola mundo"]);
  assert.ok(eventos.every((e) => !e.detail || e.detail.sesion === "chat-001"));
  assert.match(textos(), /SWE · web-qwen38max/);
});

test("Detener durante el stream: se aborta la peticion del bridge y se dice que se detuvo", async () => {
  S.guardarSeleccion({ workflow: "individual", modo_agentico: false });
  let senal;
  respuestaBridge = (op) => {
    senal = op.signal;
    const enc = new TextEncoder();
    return { __sse: new Response(new ReadableStream({ start(ctl) { ctl.enqueue(enc.encode(`data: ${JSON.stringify({ choices: [{ delta: { content: "algo " } }] })}\n\n`)); setTimeout(() => { c.detenerFlag = true; c.detenerFn(); }, 20); } }), { headers: { "content-type": "text/event-stream" } }) };
  };
  await enviar("larga");
  assert.ok(senal && senal.aborted, "la senal se aborto");
  assert.match(textos(), /proceso detenido por el usuario/);
});
