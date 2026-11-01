import test from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";

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
const doc = JSON.parse(readFileSync(new URL("../../backend/mvp/modelos.json", import.meta.url)));
const modelos = ["texto", "imagen", "audio", "video"].flatMap((t) => doc[t].map((m) => m.id));
const previo = [{ role: "user", content: "hola" }, { role: "assistant", content: "respuesta anterior" }];
const filas = new Map(["#composer", "#message"].map((k) => [k, nodo()]));
const c = { sesion: "prueba-envio", hist: nodo(), ficha: "nv-muse-glimmer", selectorQwen: null };
const recibidas = [];
const respuesta = { reply: "ok", tools: [], finish_reason: "stop" };
globalThis.RIU_HARNESS = async (a) => { recibidas.push(a); return respuesta; };
globalThis.RIU_SELECTORES = { activo: "team-qwen" };
montarEnviar({ q: (k) => filas.get(k), chat: () => c, abajo() {}, burbuja: nodo, ajustarAlturaEditor() {}, pintarTabs() {},
  getModeUI: () => null, releerAnclas: () => [], chatTools: {}, FAST_SEL: () => false, getModo: () => "",
  previo: () => previo, api: async (ruta, opts) => {
    if (ruta === "/web/v1/chat/completions") {
      recibidas.push({ ruta, ...opts.body });
      return { modelo_usado: opts.body.model, choices: [{ message: { content: "modelo: " + opts.body.model }, finish_reason: "stop" }] };
    }
    assert.equal(ruta, "/chat/send"); recibidas.push(opts.body); return respuesta;
  }, tell() {},
});
const enviar = async () => { filas.get("#message").value = "¿Qué modelo eres?"; await filas.get("#composer").events.submit({ preventDefault() {} }); };

test("cada modelo viaja canónico con su ficha y el historial en ambas rutas de envío", async () => {
  for (const harness of [true, false]) for (const [selector, ficha] of [["team-qwen", "1"], ["team-5-mvp", "5"]]) {
    globalThis.RIU_CONFIG = { harnessUrl: harness ? "/harness" : "" };
    RIU_SELECTORES.activo = selector;
    for (const id of modelos) {
      c.selectorQwen = { model_id: id, modelo_id_slug: "alias-no-canonico", label: id };
      const antes = recibidas.length; await enviar();
      assert.equal(recibidas.length, antes + 1, id);
      const a = recibidas.at(-1), qwen = harness ? a.qwen : a;
      assert.equal(a.model, id); assert.equal(qwen.modelo, id); assert.equal(qwen.ficha_qwen, ficha);
      assert.deepEqual(a.contexto_previo, previo); assert.equal(c.ocupado, false);
    }
  }
});

test("paralelo usa el mismo id canónico para cada modelo sin añadir qw-", async () => {
  globalThis.RIU_CONFIG = { harnessUrl: "/harness" }; RIU_SELECTORES.activo = "team-qwen";
  c.paralelo = true;
  c.selectorQwenMulti = ["glm-5.3", "deepseek-v4.1-flash"].map((id) => ({ model_id: id, label: id, modelo_id_slug: "alias" }));
  const antes = recibidas.length; await enviar();
  assert.equal(recibidas.length, antes + 2);
  assert.deepEqual(recibidas.slice(antes).map((a) => [a.model, a.qwen.modelo]), c.selectorQwenMulti.map((m) => [m.model_id, m.model_id]));
});

test("X-Ray objetivos: Groq y NVIDIA activos se envían por bridge con su ID exacto, nunca por Qwen/Harness", async () => {
  RIU_CONFIG = { harnessUrl: "/harness" }; c.paralelo = false; c.selectorQwen = null;
  globalThis.RIU_GROQ = { modelo: "groq/qwen/qwen3.8-27b", aviso: "" };
  globalThis.RIU_SWE_CENTRAL = { modeloVentana: (v) => v === "nvidia" ? "nvidia/z-ai/glm-5.3" : "" , bloqueo: () => "" };
  for (const [selector, esperado] of [["groq", "groq/qwen/qwen3.8-27b"], ["nvidia-groq-team", "nvidia/z-ai/glm-5.3"]]) {
    RIU_SELECTORES.activo = selector;
    const before = recibidas.length; await enviar();
    assert.equal(recibidas.length, before + 1, selector);
    assert.equal(recibidas.at(-1).ruta, "/web/v1/chat/completions");
    assert.equal(recibidas.at(-1).model, esperado, "no se cambia el modelo");
    assert.equal(c.ocupado, false);
  }
});
test("X-Ray objetivos: un selector Qwen nunca se bloquea por falta de Groq", async () => {
  RIU_CONFIG = { harnessUrl: "/harness" }; c.paralelo = false; RIU_SELECTORES.activo = "team-qwen";
  c.selectorQwen = { model_id: "qwen3.8-max", label: "Qwen 3.8 Max" };
  globalThis.RIU_GROQ = { modelo: "", aviso: "sin conexión con Router" };
  const before = recibidas.length; await enviar();
  assert.equal(recibidas.length, before + 1);
  assert.equal(recibidas.at(-1).model, "qwen3.8-max");
});
