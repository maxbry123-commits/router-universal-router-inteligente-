import test from "node:test";
import assert from "node:assert/strict";

const datos = new Map();
globalThis.localStorage = { getItem: (k) => datos.get(k) ?? null, setItem: (k, v) => datos.set(k, String(v)) };
globalThis.sessionStorage = { getItem: () => null };
globalThis.window = globalThis;
const { aplicarAMensaje, reglaDeOtroModelo } = await import("../contexto.js");
const { instalarContexto } = await import("../chat-contexto.js");
const regla = "El modelo activo es qwen3.8-flash. Responde con ese nombre y su familia.";
const reglas = JSON.stringify({ idioma: "es", reglas: [{ on: true, texto: regla }, { on: true, texto: "Sé breve." }, { on: false, texto: "Apagada" }] });
localStorage.setItem("riu_reglas_v1", reglas);

test("solo omite la identidad obsoleta en el envío, sin modificar las reglas guardadas", () => {
  const mensaje = aplicarAMensaje("¿Qué modelo eres?", null, "glm-5.3");
  assert.ok(!mensaje.includes(regla)); assert.ok(mensaje.includes("Sé breve."));
  assert.ok(mensaje.includes("español")); assert.ok(mensaje.endsWith("¿Qué modelo eres?"));
  assert.ok(!mensaje.includes("Apagada"));
  assert.equal(localStorage.getItem("riu_reglas_v1"), reglas);
});

test("conserva una regla coincidente, menciones a modelos y envíos sin selección", () => {
  assert.ok(aplicarAMensaje("hola", null, "qwen3.8-flash").includes(regla));
  assert.ok(aplicarAMensaje("hola").includes(regla));
  for (const texto of ["Compara GLM 5.3 con qwen3.8-flash", "El modelo activo es útil", "No uses qwen3.8-flash"]) assert.equal(reglaDeOtroModelo(texto, "glm-5.3"), false);
});

test("el wrapper usa el modelo de ficha 1 y 5; las fichas 2/3 siguen literales", () => {
  globalThis.RIU_HARNESS = (a) => a; instalarContexto();
  for (const ficha of ["1", "5"]) {
    const entrada = { model: "nv-muse-glimmer", message: "¿Qué modelo eres?", qwen: { ficha_qwen: ficha, modelo: "glm-5.3" } };
    const salida = RIU_HARNESS(entrada);
    assert.ok(!salida.message.includes(regla)); assert.ok(salida.message.includes("Sé breve."));
    assert.equal(entrada.message, "¿Qué modelo eres?");
    assert.equal(salida.qwen.modelo, "glm-5.3");
  }
  for (const ficha of ["2", "3"]) assert.equal(RIU_HARNESS({ message: "  literal\n", qwen: { ficha_qwen: ficha } }).message, "  literal\n");
  assert.equal(localStorage.getItem("riu_reglas_v1"), reglas);
});
