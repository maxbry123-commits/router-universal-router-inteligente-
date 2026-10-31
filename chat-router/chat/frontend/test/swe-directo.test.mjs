import test from "node:test";
import assert from "node:assert/strict";
import { esSwe, armar, enviarSwe } from "../swe-directo.js";

test("reconoce los ids SWE del selector y deja pasar a los demas modelos por el Router", () => {
  for (const m of ["web-qwen38max", "swecode-asesoria", "hf-liquid-lfm25", "swe-agent-lfm25", "lfm2.5-350m", "groq/llama-3.3-70b-versatile", "nvidia/meta/llama-3.3-70b-instruct"]) assert.ok(esSwe(m), m);
  for (const m of ["qwen3.8-max", "glm-5.3", "deepseek-v4-pro", "", null]) assert.ok(!esSwe(m), String(m));
});

test("arma el POST OpenAI con el historial, la sesion y el proyecto; los alias hf-* se traducen al id real", () => {
  const b = armar({ model: "hf-liquid-lfm25", historial: [{ role: "user", content: "a" }, { role: "assistant", content: "b" }], mensaje: "c", sesion: "s1", proyecto: "P" });
  assert.equal(b.model, "lfm2.5-350m"); assert.equal(b.conv_id, "s1"); assert.equal(b.proyecto, "P");
  assert.deepEqual(b.messages.map((m) => m.content), ["a", "b", "c"]);
});

test("enviarSwe usa /v1/chat/completions y devuelve la forma que pinta el chat", async () => {
  let visto;
  const api = async (ruta, op) => { visto = { ruta, op }; return { modelo_usado: "web-qwen38max", via_respaldo: "groq", choices: [{ message: { content: "listo" }, finish_reason: "stop" }] }; };
  const r = await enviarSwe(api, { model: "web-qwen38max", historial: [], mensaje: "hola", sesion: "s" });
  assert.equal(visto.ruta, "/v1/chat/completions"); assert.equal(visto.op.method, "POST");
  assert.equal(r.reply, "listo"); assert.equal(r.finish_reason, "stop"); assert.match(r.nota, /groq/);
});

test("si la respuesta no trae texto lanza el error con su codigo (no se pinta como respuesta del modelo)", async () => {
  await assert.rejects(() => enviarSwe(async () => ({ error: { code: "RESPALDO_AGOTADO", message: "nada responde" } }), { model: "web-qwen38max", historial: [], mensaje: "x", sesion: "s" }), /GAP: RESPALDO_AGOTADO/);
});

import { SWE_LISTAS, esSelectorSwe } from "../swe-directo.js";

test("hay dos selectores propios, SWE CODE y SWEN CODE free, cada uno con sus modelos y todos pasan por esSwe", () => {
  assert.deepEqual(Object.keys(SWE_LISTAS).sort(), ["swe-code", "swen-code-free"]);
  assert.ok(esSelectorSwe("swe-code") && esSelectorSwe("swen-code-free") && !esSelectorSwe("groq") && !esSelectorSwe("constructor"));
  for (const [id, l] of Object.entries(SWE_LISTAS)) {
    assert.ok(l.modelos.length >= 4, id);
    for (const [mid] of l.modelos) assert.ok(esSwe(mid), mid + " debe enrutarse por el bridge");
  }
  assert.ok(SWE_LISTAS["swen-code-free"].modelos.some(([m]) => m === "swecode-asesoria"));
  assert.ok(SWE_LISTAS["swe-code"].modelos.some(([m]) => m === "hf-liquid-lfm25"));
});

test("esSwe no se deja engañar por propiedades heredadas y un GAP del bridge es un error, no una respuesta", async () => {
  assert.ok(!esSwe("constructor") && !esSwe("__proto__") && !esSwe("toString"));
  await assert.rejects(() => enviarSwe(async () => ({ error: { code: "RESPALDO_AGOTADO", message: "nada responde" } }), { model: "web-qwen38max", historial: [], mensaje: "x", sesion: "s" }), /RESPALDO_AGOTADO/);
});

test("el historial que viaja al modelo SWE se acota (no se manda todo el chat a un modelo de 350M)", () => {
  const h = Array.from({ length: 50 }, (_, i) => ({ role: i % 2 ? "assistant" : "user", content: "m" + i }));
  const b = armar({ model: "lfm2.5-350m", historial: h, mensaje: "ultimo", sesion: "s" });
  assert.ok(b.messages.length <= 21); assert.equal(b.messages.at(-1).content, "ultimo");
});

test("armar incluye claves SOLO si hay alguna guardada; nunca van en el texto de error ni en la nota", async () => {
  const m = new Map();
  globalThis.localStorage = { getItem: (k) => (m.has(k) ? m.get(k) : null), setItem: (k, v) => { m.set(k, String(v)); }, removeItem: (k) => { m.delete(k); } };
  const base = { model: "web-qwen38max", historial: [], mensaje: "x", sesion: "s" };
  assert.ok(!("claves" in armar(base)), "sin claves guardadas no hay campo claves");
  m.set("riu_swe_claves", JSON.stringify({ groq: " gsk_SECRETA ", nvidia: "nvapi-OTRA" }));
  assert.deepEqual(armar(base).claves, { groq: "gsk_SECRETA", nvidia: "nvapi-OTRA" });
  m.set("riu_swe_claves", "{corrupto");
  assert.ok(!("claves" in armar(base)));
  m.set("riu_swe_claves", JSON.stringify({ groq: "gsk_SECRETA" }));
  const r1 = await enviarSwe(async (_r, op) => { assert.equal(op.body.claves.groq, "gsk_SECRETA"); return { choices: [{ message: { content: "ok" } }] }; }, base);
  assert.ok(!JSON.stringify(r1).includes("gsk_SECRETA"), "la nota no lleva la clave");
  await assert.rejects(() => enviarSwe(async () => ({ error: { code: "X", message: "rechazo" } }), base), (e) => !/gsk_SECRETA/.test(e.message));
  delete globalThis.localStorage;
  assert.ok(!("claves" in armar(base)), "sin localStorage -> sin claves");
});

test("SWEN CODE free incluye Groq y NVIDIA (usan las claves de Configuracion por el bridge)", () => {
  const ids = SWE_LISTAS["swen-code-free"].modelos.map(([m]) => m);
  assert.ok(ids.includes("groq/llama-3.3-70b-versatile") && ids.includes("nvidia/meta/llama-3.3-70b-instruct"));
});
