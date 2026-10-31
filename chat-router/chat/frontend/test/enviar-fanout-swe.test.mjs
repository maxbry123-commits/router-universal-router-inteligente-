import test from "node:test";
import assert from "node:assert/strict";

// modo paralelo: los modelos SWE/locales de la seleccion multiple van por el bridge (enviarSwe); el Router los rechaza (modelo no permitido en el plan)
const datos = new Map();
globalThis.localStorage = { getItem: (k) => datos.get(k) ?? null, setItem: (k, v) => datos.set(k, String(v)) };
globalThis.sessionStorage = { getItem: () => null };
globalThis.window = globalThis;
globalThis.addEventListener = () => {}; globalThis.removeEventListener = () => {};
globalThis.matchMedia = () => ({ matches: false });
const nodo = () => ({ children: [], events: {}, value: "", classList: { contains() { return false; } },
  append(...xs) { this.children.push(...xs); }, remove() {}, focus() {},
  addEventListener(k, fn) { this.events[k] = fn; },
});
globalThis.document = { readyState: "loading", addEventListener() {}, getElementById() { return null; }, createElement: nodo };
const { montarEnviar } = await import("../enviar-mensaje.js");
const filas = new Map(["#composer", "#message"].map((k) => [k, nodo()]));
const c = { sesion: "par", hist: nodo(), ficha: "nv-muse-glimmer", selectorQwen: null, paralelo: true, selectorQwenMulti: [] };
const harness = [], bridge = [], pintado = [];
globalThis.RIU_HARNESS = async (a) => { harness.push(a); return { reply: "del-harness", tools: [], finish_reason: "stop" }; };
globalThis.RIU_SELECTORES = { activo: "team-qwen" };
globalThis.RIU_CONFIG = { harnessUrl: "/harness" };
montarEnviar({ q: (k) => filas.get(k), chat: () => c, abajo() {}, burbuja: (t) => { pintado.push(String(t)); return nodo(); }, ajustarAlturaEditor() {}, pintarTabs() {},
  getModeUI: () => null, releerAnclas: () => [], chatTools: {}, FAST_SEL: () => false, getModo: () => "",
  previo: () => [], api: async (ruta, op) => { bridge.push({ ruta, body: op.body }); return { modelo_usado: op.body.model, choices: [{ message: { content: "del-bridge" }, finish_reason: "stop" }] }; }, tell() {},
});
const enviar = async () => { filas.get("#message").value = "hola"; await filas.get("#composer").events.submit({ preventDefault() {} }); };

test("paralelo: un modelo local HF va por el bridge (/web/v1) con su id real y uno del Router sigue por el Harness", async () => {
  c.selectorQwen = { model_id: "glm-5.3", label: "GLM", modelo_id_slug: "glm" };
  c.selectorQwenMulti = [{ model_id: "hf-liquid-lfm25", label: "Liquid AI (HF)", modelo_id_slug: "liquid" }, { model_id: "glm-5.3", label: "GLM", modelo_id_slug: "glm" }];
  await enviar();
  assert.equal(bridge.length, 1); assert.equal(bridge[0].ruta, "/web/v1/chat/completions"); assert.equal(bridge[0].body.model, "lfm2.5-350m");
  assert.equal(harness.length, 1); assert.equal(harness[0].model, "glm-5.3");
  const txt = pintado.join("\n");
  assert.match(txt, /Liquid AI \(HF\) ──\ndel-bridge/); assert.match(txt, /GLM ──\ndel-harness/);
});
