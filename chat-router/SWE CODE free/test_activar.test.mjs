import test from "node:test";
import assert from "node:assert/strict";
import { createRequire } from "node:module";
const { activar } = createRequire(import.meta.url)("./activar.js");

test("groq y nvidia se eligen por nombre, igual que los demas modelos", () => {
  assert.equal(activar("SWEN CODE free solo groq arregla el login").modelo, "groq/llama-3.3-70b-versatile");
  assert.equal(activar("SWEN CODE free con nvidia revisa esto").modelo, "nvidia/meta/llama-3.3-70b-instruct");
  assert.equal(activar("SWEN CODE free nvidia revisa esto").prompt, "revisa esto");
});

test("lo anterior sigue igual", () => {
  const a = activar("SWEN CODE free chat 2 modo solucion solo deepseek v4 arregla api.js");
  assert.deepEqual([a.conv_id, a.modo, a.modelo, a.prompt], ["chat-2", "solucion", "web-dsv4-flash", "arregla api.js"]);
  assert.equal(activar("hola"), null);
});
