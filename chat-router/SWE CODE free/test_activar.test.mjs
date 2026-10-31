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

test("id completo groq/ nvidia/ se consume entero del prompt, sin elegir otro modelo en silencio", () => {
  let a = activar(F + "solo nvidia/z-ai/glm-5.3 deploy");
  assert.deepEqual([a.modelo, a.prompt], ["nvidia/z-ai/glm-5.3", "deploy"]);
  a = activar(F + "con groq/qwen/qwen3.8-27b arregla api.js");
  assert.deepEqual([a.modelo, a.prompt], ["groq/qwen/qwen3.8-27b", "arregla api.js"]);
  a = activar(F + "nvidia/nvidia/nemotron-3-ultra-550b-a55b revisa esto");
  assert.deepEqual([a.modelo, a.prompt], ["nvidia/nvidia/nemotron-3-ultra-550b-a55b", "revisa esto"]);
  a = activar(F + "modelo nvidia/minimaxai/minimax-m3.1-flash deploy");
  assert.deepEqual([a.modelo, a.prompt], ["nvidia/minimaxai/minimax-m3.1-flash", "deploy"]);
  a = activar(F + "solo nvidia/z-ai/glm-5.3");  // sin prompt: el id se consume igual
  assert.deepEqual([a.modelo, a.prompt], ["nvidia/z-ai/glm-5.3", ""]);
});

test("id completo de modelo local se consume entero", () => {
  for (const id of ["lfm2.5-350m", "qwen2.5-coder-1.5b", "qwen3.5-0.8b", "qwen3-0.6b"]) {
    const a = activar(F + `solo ${id} deploy`);
    assert.deepEqual([a.modelo, a.prompt], [id, "deploy"], id);
  }
  assert.deepEqual(resumen(F + "lfm2.5-350m revisa esto"), ["consulta", "lfm2.5-350m", "revisa esto"]);
});

test("alias nuevos: muse/glimmer, nemotron, glm, minimax, qwen3.5, qwen3", () => {
  const casos = [
    ["solo muse revisa", "nvidia/meta/muse-glimmer-30b"], ["con glimmer revisa", "nvidia/meta/muse-glimmer-30b"],
    ["solo nemotron revisa", "nvidia/nvidia/nemotron-3-ultra-550b-a55b"], ["solo glm revisa", "nvidia/z-ai/glm-5.3"],
    ["solo glm 5.3 revisa", "nvidia/z-ai/glm-5.3"], ["solo minimax revisa", "nvidia/minimaxai/minimax-m3.1-flash"],
    ["solo qwen3.5 revisa", "qwen3.5-0.8b"], ["solo qwen3 revisa", "qwen3-0.6b"],
    ["nemotron revisa", "nvidia/nvidia/nemotron-3-ultra-550b-a55b"], ["glm revisa", "nvidia/z-ai/glm-5.3"],
  ];
  for (const [t, id] of casos) { const a = activar(F + t); assert.deepEqual([a.modelo, a.prompt], [id, "revisa"], t); }
  // los alias existentes de qwen no cambian
  assert.equal(activar(F + "solo qwen3.8 revisa").modelo, "web-qwen38max");
  assert.equal(activar(F + "solo qwen3.7 revisa").modelo, "web-qwen37max");
});

test("alias nuevos sin keyword no se comen la frase", () => {
  assert.equal(activar(F + "glm no responde").prompt, "glm no responde");
  assert.equal(activar(F + "nemotron falla").prompt, "nemotron falla");
  assert.equal(activar(F + "nemotron falla").modelo, "consenso");
});

test("version de glm no registrada no elige glm-5.3 en silencio", () => {
  const a = activar(F + "solo glm-5.2 deploy");
  assert.equal(a.modelo, "consenso");
  assert.equal(a.prompt, "solo glm-5.2 deploy");
});
