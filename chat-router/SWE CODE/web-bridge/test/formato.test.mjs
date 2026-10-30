import test from "node:test";
import assert from "node:assert/strict";
import { conFormato, textoFormato } from "../src/formato.js";

test("lee el FORMATO_SALIDA.md unico del chat (sin copiarlo)", () => {
  assert.match(textoFormato(), /FORMATO DE SALIDA/);
});

test("agrega el formato como primer mensaje de sistema", () => {
  const m = conFormato([{ role: "user", content: "hola" }]);
  assert.equal(m[0].role, "system"); assert.match(m[0].content, /FORMATO DE SALIDA/); assert.equal(m[1].content, "hola");
});

test("no lo duplica si el Router MVP ya lo puso, y no toca el arreglo original", () => {
  const ya = [{ role: "system", content: textoFormato() }, { role: "user", content: "x" }];
  assert.equal(conFormato(ya).length, 2);
  const orig = [{ role: "user", content: "hola" }]; conFormato(orig); assert.equal(orig.length, 1);
});

test("si el archivo no existe sigue sin formato y sin romper", () => {
  process.env.RIU_FORMATO_PATH = "/no/existe.md";
  assert.equal(conFormato([{ role: "user", content: "a" }]).length, 1);
});
