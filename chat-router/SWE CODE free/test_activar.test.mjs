import test from "node:test";
import assert from "node:assert/strict";
import { createRequire } from "node:module";
const { activar } = createRequire(import.meta.url)("./activar.js");

test("groq y nvidia se eligen por nombre, igual que los demas modelos", () => {
  assert.equal(activar("SWEN CODE free solo groq arregla el login").modelo, "groq/qwen/qwen3.8-27b");
  assert.equal(activar("SWEN CODE free con nvidia revisa esto").modelo, "nvidia/minimaxai/minimax-m3.1-flash");
  assert.equal(activar("SWEN CODE free nvidia revisa esto").prompt, "revisa esto");
});

test("lo anterior sigue igual", () => {
  const a = activar("SWEN CODE free chat 2 modo solucion solo deepseek v4 arregla api.js");
  assert.deepEqual([a.conv_id, a.modo, a.modelo, a.prompt], ["chat-2", "solucion", "web-dsv4-flash", "arregla api.js"]);
  assert.equal(activar("hola"), null);
});

test("el modo asesoria existe y se activa por el prefijo", () => {
  const a = activar("SWEN CODE free modo asesoria proyecto nuevo de pagos");
  assert.deepEqual([a.modo, a.prompt], ["asesoria", "proyecto nuevo de pagos"]);
});

const F = "SWEN CODE free ";
const resumen = (t) => { const a = activar(t); return a.error ? { error: a.error } : [a.modo, a.modelo, a.prompt]; };

test("palabra tras con/solo/modelo que no es alias se queda en el prompt, sin error", () => {
  assert.deepEqual(resumen(F + "solo necesito que revises auth.js"), ["consulta", "consenso", "solo necesito que revises auth.js"]);
  assert.deepEqual(resumen(F + "con el codigo X falla"), ["consulta", "consenso", "con el codigo X falla"]);
  assert.deepEqual(resumen(F + "modelo de datos para usuarios"), ["consulta", "consenso", "modelo de datos para usuarios"]);
});

test("'modelo <alias mal escrito>' exacto si es error; con mas texto no", () => {
  assert.match(activar(F + "modelo qwen4").error, /modelo desconocido: qwen4/);
  assert.match(activar(F + "modo solucion modelo deepsek").error, /modelo desconocido/);
  assert.equal(activar(F + "modelo datos").error, undefined);
  assert.equal(activar(F + "modelo qwen4 explicado").error, undefined);
});

test("modo: lo que no es modo queda en el prompt; nombre de modo mal escrito es error", () => {
  assert.deepEqual(resumen(F + "modo oscuro no funciona"), ["consulta", "consenso", "modo oscuro no funciona"]);
  assert.match(activar(F + "modo revisoin x").error, /modo desconocido: revisoin/);
  assert.match(activar(F + "modo solusion x").error, /modo desconocido/);
});

test("acepta tildes en modos y alias", () => {
  assert.deepEqual(resumen(F + "modo revisión del login"), ["revision", "web-qwen38max", "del login"]);
  assert.deepEqual(resumen(F + "modo solución bug en api.js"), ["solucion", "web-qwen38max", "bug en api.js"]);
  assert.equal(activar(F + "cóncilio que hacer").modelo, "consenso");
});

test("la clave tolera espacios iniciales", () => {
  const a = activar("   \n  SWEN CODE free modo archivos lista todo");
  assert.deepEqual([a.modo, a.prompt], ["archivos", "lista todo"]);
});

test("alias sin keyword: solo primera palabra y con mas texto; no se come la frase", () => {
  assert.equal(activar(F + "todos los tests fallan").prompt, "todos los tests fallan");
  assert.equal(activar(F + "deepseek no responde").prompt, "deepseek no responde");
  assert.equal(activar(F + "deepseek").prompt, "deepseek");
  const a = activar(F + "deepseek revisa esto");
  assert.deepEqual([a.modelo, a.prompt], ["web-dsv4-flash", "revisa esto"]);
  assert.equal(activar(F + "revisa con groq esto").prompt, "revisa con groq esto");
  assert.equal(activar(F + "concilio que hacer con X").modelo, "consenso");
  assert.equal(activar(F + "con todos los tests fallan").modelo, "consenso");
});

test("API intacta y entradas raras no revientan", () => {
  const m = createRequire(import.meta.url)("./activar.js");
  for (const k of ["activar", "MODOS", "CLAVE", "MODELOS_ALIAS", "PIPELINES"]) assert.ok(k in m, k);
  assert.equal(activar(undefined), null);
  assert.equal(activar(42), null);
});
