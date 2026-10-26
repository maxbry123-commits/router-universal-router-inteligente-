import test from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";

const storage = () => { const m = new Map(); return { getItem: (k) => m.get(k) ?? null, setItem: (k, v) => m.set(k, String(v)), removeItem: (k) => m.delete(k) }; };
globalThis.localStorage = storage(); globalThis.sessionStorage = storage();
localStorage.setItem("riu_catalogo_qwen", JSON.stringify(["glm-5.2"]));
sessionStorage.setItem("riu_clave", "prueba");
globalThis.window = globalThis;
globalThis.addEventListener = () => {}; globalThis.dispatchEvent = () => {};
globalThis.CustomEvent = class { constructor(type, opts) { this.type = type; this.detail = opts?.detail; } };
globalThis.MutationObserver = class { observe() {} };
const nodo = (tag) => ({ tagName: tag, children: [], attrs: {}, events: {}, textContent: "", hidden: true,
  classList: { toggle() {}, contains() { return false; } },
  append(...xs) { this.children.push(...xs); }, replaceChildren() { this.children = []; },
  addEventListener(k, fn) { this.events[k] = fn; }, setAttribute(k, v) { this.attrs[k] = v; },
});
globalThis.document = { readyState: "loading", addEventListener() {}, getElementById() { return null; }, createElement: nodo };
const doc = JSON.parse(readFileSync(new URL("../../backend/mvp/modelos.json", import.meta.url)));
const catalogo = (plan) => ["texto", "imagen", "audio", "video"].flatMap((tipo) => doc[tipo].filter((m) => m[plan]).map((m) => ({ model_id: m.id, tipo })));
let respuesta = catalogo("p");
globalThis.fetch = async (url) => {
  assert.equal(url, "/chat/providers/qwen/models");
  return { ok: true, status: 200, headers: { get: () => "application/json" }, json: async () => ({ models: respuesta }) };
};
const { gruposModelos, conectarSelectorModelos } = await import("../chat-selector-modelos.js");
const ids = (grupos) => grupos.flatMap((g) => g.modelos.map((m) => m[3]));

test("los dos planes se pintan completos desde el catálogo, sin modelos extra", () => {
  for (const plan of ["p", "t"]) assert.deepEqual(ids(gruposModelos(catalogo(plan))), catalogo(plan).map((m) => m.model_id));
  assert.equal(catalogo("p").length, 22); assert.equal(catalogo("t").length, 31);
  assert.equal(gruposModelos(["glm-5.3"])[0].modelos[0][1], "GLM 5.3");
  assert.deepEqual(ids(gruposModelos([null, {}, "glm-5.3", "glm-5.3"])), ["glm-5.3"]);
});

test("ambas hojas refrescan la caché y eligen el id canónico en su selector", async () => {
  const elementos = Object.fromEntries(["#sel-nuevo", "#sel-mvp", "#sh-modelos-lista", "#sh-modelos", "#chat-tabs", "#sh-modelos .va-head strong"].map((k) => [k, nodo("div")]));
  const c = { sesion: "prueba", selectorQwen: null };
  globalThis.RIU_SELECTORES = { encender(id) { this.activo = id; }, apagar() { this.activo = null; } };
  assert.deepEqual(RIU_SELECTOR_QWEN.modelos.map((m) => m.model_id), ["glm-5.2"]);
  conectarSelectorModelos({ q: (k) => elementos[k], chat: () => c, guardar() {}, tell() {} });
  await new Promise(setImmediate);
  const filas = () => elementos["#sh-modelos-lista"].children.flatMap((n) => n.children).filter((n) => n.tagName === "button");
  const label = (n) => n.children[1].children[0].textContent;
  assert.equal(filas().length, 22);
  assert.deepEqual(new Set(RIU_SELECTOR_QWEN.modelos.map((m) => m.model_id)), new Set(catalogo("p").map((m) => m.model_id)));
  filas().find((n) => label(n) === "GLM 5.3").events.click();
  assert.equal(c.selectorQwen.model_id, "glm-5.3"); assert.equal(RIU_SELECTORES.activo, "team-qwen");
  respuesta = catalogo("t");
  elementos["#sel-mvp"].events.click(); await new Promise(setImmediate);
  assert.equal(elementos["#sh-modelos .va-head strong"].textContent, "Team 5 MVP");
  assert.equal(filas().length, 31);
  filas().find((n) => label(n) === "Kimi K2.7 Code").events.click();
  assert.equal(c.selectorQwen.model_id, "kimi-k2.7-code"); assert.equal(RIU_SELECTORES.activo, "team-5-mvp");
  assert.deepEqual(JSON.parse(localStorage.getItem("riu_catalogo_qwen")), respuesta);
});
