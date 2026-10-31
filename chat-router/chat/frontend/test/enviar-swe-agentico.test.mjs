import test from "node:test";
import assert from "node:assert/strict";

// enviar-mensaje.js con el selector SWE CODE / SWEN CODE free: individual+agentico OFF = camino de hoy (bridge); workflow != individual o agentico ON = contrato TareaSWE al backend YAIWES (/chat/swe/*).
const datos = new Map();
globalThis.localStorage = { getItem: (k) => datos.get(k) ?? null, setItem: (k, v) => datos.set(k, String(v)), removeItem: (k) => datos.delete(k) };
globalThis.sessionStorage = { getItem: () => null };
globalThis.window = globalThis; globalThis.Event = class { constructor(t) { this.type = t; } };
globalThis.addEventListener = () => {}; globalThis.removeEventListener = () => {};
globalThis.matchMedia = () => ({ matches: false });
const nodo = () => ({ children: [], events: {}, value: "", className: "", textContent: "", classList: { contains() { return false; } },
  append(...xs) { this.children.push(...xs); }, remove() {}, focus() {}, dispatchEvent() {}, addEventListener(k, fn) { this.events[k] = fn; },
});
globalThis.document = { readyState: "loading", addEventListener() {}, getElementById() { return null; }, createElement: nodo };
const { montarEnviar } = await import("../enviar-mensaje.js");
const S = await import("../swe-directo.js");
const filas = new Map(["#composer", "#message"].map((k) => [k, nodo()]));
const c = { sesion: "chat-001", hist: nodo(), ficha: "x", selectorQwen: null, project_id: null };
const llamadas = [], pintado = [];
const OK = { harness: "ok", agentes: Object.fromEntries(["openclaw", "swe-agent", "openhands", "opencode", "codex", "claude-code"].map((a) => [a, { disponible: true }])), workflows: { swe_code: { disponible: true }, liquid_mirror: { disponible: true } } };
let capacidades = OK, estadoFinal = "DONE";
const api = async (ruta, op) => {
  llamadas.push({ ruta, body: op && op.body });
  if (ruta === "/chat/swe/capacidades") return capacidades;
  if (ruta === "/chat/swe/iniciar") return { ok: true, resultado: { task_id: op.body.task_id, estado: estadoFinal === "DONE" ? "EJECUTANDO" : estadoFinal, ...(estadoFinal === "REQUIERE_APROBACION" ? { pendiente_aprobacion: { op_id: "0123456789abcdef", paso: "escribe", agente: "codex", modelo: "hf/qwen2.5-coder-1.5b", permisos: { escritura: true } } } : {}) } };
  if (ruta === "/chat/swe/avanzar") return { ok: true, resultado: { task_id: op.body.task_id, estado: "DONE", resultado_tool: "listo desde el agente", evidencia: ["recibo:z9"] } };
  if (ruta === "/chat/swe/aprobar") return { ok: true, resultado: { task_id: op.body.task_id, estado: "CONTINUAR" } };
  return { modelo_usado: op.body.model, choices: [{ message: { content: "del-bridge" }, finish_reason: "stop" }] };
};
globalThis.RIU_SELECTORES = { activo: "swen-code-free" };
globalThis.RIU_SWE = { "swen-code-free": { model_id: "hf-liquid-lfm25", label: "Liquid" }, "swe-code": { model_id: "hf-liquid-lfm25", label: "Liquid" } };
globalThis.RIU_CONFIG = {};
montarEnviar({ q: (k) => filas.get(k), chat: () => c, abajo() {}, burbuja: (t) => { pintado.push(String(t)); return nodo(); }, ajustarAlturaEditor() {}, pintarTabs() {},
  getModeUI: () => null, releerAnclas: () => [], chatTools: {}, FAST_SEL: () => false, getModo: () => "", previo: () => [], api, tell() {} });
const enviar = async (txt = "hola") => { llamadas.length = 0; pintado.length = 0; c.hist.children.length = 0; filas.get("#message").value = txt; await filas.get("#composer").events.submit({ preventDefault() {} }); };
const textos = () => c.hist.children.map((x) => x.textContent || "").join("\n");
test.beforeEach(() => { S.olvidarCapacidades(); datos.clear(); capacidades = OK; estadoFinal = "DONE"; });

test("individual + agentico OFF: camino de hoy (bridge), sin tocar /chat/swe/*", async () => {
  await enviar();
  assert.deepEqual(llamadas.map((l) => l.ruta), ["/web/v1/chat/completions"]);
  assert.equal(llamadas[0].body.model, "lfm2.5-350m"); assert.ok(pintado.includes("del-bridge"));
});

test("workflow SWE CODE: el contrato TareaSWE va a /chat/swe/iniciar y avanza; el resultado y la evidencia vuelven al mismo chat; no pasa por el bridge", async () => {
  S.guardarSeleccion({ workflow: "swe_code" });
  await enviar("Revisar proyecto");
  const rutas = llamadas.map((l) => l.ruta);
  assert.deepEqual(rutas, ["/chat/swe/capacidades", "/chat/swe/iniciar", "/chat/swe/avanzar"]);
  const ini = llamadas[1].body;
  assert.equal(ini.origen, "yaiwes"); assert.equal(ini.workflow, "swe_code"); assert.equal(ini.mensaje, "Revisar proyecto"); assert.equal(ini.sesion, "chat-001"); assert.equal(ini.aprobacion, false);
  assert.match(pintado.join("\n"), /listo desde el agente[\s\S]*recibo:z9/);
  assert.match(textos(), /SWE · swe_code/);
});

test("modo agentico ON con workflow individual tambien va por el contrato; liquid_mirror manda a Liquid 1/2", async () => {
  S.guardarSeleccion({ modo_agentico: true, workflow: "liquid_mirror" });
  await enviar("Revisar y desplegar");
  const ini = llamadas.find((l) => l.ruta === "/chat/swe/iniciar").body;
  assert.equal(ini.workflow, "liquid_mirror"); assert.equal(ini.modo_agentico, true); assert.equal(ini.modelo_lector, "hf/lfm2.5-350m"); assert.equal(ini.modelo_tool, "hf/lfm2.5-350m");
  assert.ok(!llamadas.some((l) => /chat\/completions/.test(l.ruta)));
});

test("un agente NO DISPONIBLE se dice en el chat y no se manda a otro (ni al bridge ni al Router)", async () => {
  S.guardarSeleccion({ modo_agentico: true });
  capacidades = { harness: "ok", agentes: { openclaw: { disponible: true } } };
  await enviar();
  assert.deepEqual(llamadas.map((l) => l.ruta), ["/chat/swe/capacidades"]);
  assert.match(textos(), /GAP: SELECCION_NO_DISPONIBLE.*SWE-agent.*NO DISPONIBLE/);
});

test("REQUIERE_APROBACION: boton Aprobar que llama a /chat/swe/aprobar con el task_id (sin campo aprobacion) y pinta el resultado", async () => {
  S.guardarSeleccion({ workflow: "swe_code", modo_agentico: true });
  estadoFinal = "REQUIERE_APROBACION";
  await enviar("Revisar y desplegar");
  const boton = c.hist.children.flatMap((x) => x.children || []).find((x) => /mx-aprobar/.test(x.className));
  assert.ok(boton, "hay boton de aprobar");
  const id = llamadas.find((l) => l.ruta === "/chat/swe/iniciar").body.task_id;
  llamadas.length = 0; pintado.length = 0;
  await boton.onclick();
  assert.deepEqual(llamadas.map((l) => l.ruta), ["/chat/swe/aprobar", "/chat/swe/avanzar"]);
  assert.equal(llamadas[0].body.task_id, id); assert.equal(llamadas[0].body.op_id, "0123456789abcdef"); assert.ok(!("aprobacion" in llamadas[0].body) && !("operador" in llamadas[0].body));
  assert.ok(pintado.some((t) => /listo desde el agente/.test(t)));
});
