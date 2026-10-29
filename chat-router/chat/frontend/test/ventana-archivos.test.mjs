import test from "node:test";
import assert from "node:assert/strict";
globalThis.window = { addEventListener() {}, location: { origin: "http://x" } };
globalThis.sessionStorage = { getItem: () => null };
globalThis.localStorage = { getItem: () => null, setItem() {} };
globalThis.location = { origin: "http://x", search: "", hostname: "x" };
const { parsearPegado, parsearYaml, armarPayload, filaVacia } = await import("../ventana-archivos.js");

test("YAML a filas", () => {
  const f = parsearPegado("- accion: descargar\n  origen: github.com/o/r\n  destino: p/r\n  extraer: true\n  readme: true\n- accion: buscar\n  origen: p/r\n  patron: \"TODO\"\n");
  assert.equal(f.length, 2);
  assert.deepEqual([f[0].accion, f[0].extraer, f[0].readme, f[0].destino], ["descargar", true, true, "p/r"]);
  assert.equal(f[1].patron, "TODO");
});
test("JSON lista y {cola}", () => {
  assert.equal(parsearPegado('[{"accion":"copiar","origen":"a","destino":"b"}]')[0].accion, "copiar");
  assert.equal(parsearPegado('{"cola":[{"accion":"mover","origen":"a","destino":"b"}]}').length, 1);
});
test("errores de pegado", () => {
  assert.throws(() => parsearPegado(""), /nada/);
  assert.throws(() => parsearPegado("[{"), /JSON/);
  assert.throws(() => parsearPegado("hola"), /trabajos/);
});
test("payload", () => {
  const p = armarPayload([{ accion: "descargar", origen: " https://x/y.zip ", destino: "d", extraer: true, readme: false }, { accion: "listar", origen: "d", destino: "ignorado" }, filaVacia()]);
  assert.equal(p.cola.length, 2);
  assert.deepEqual(p.cola[0], { accion: "descargar", origen: "https://x/y.zip", sobrescribir: false, destino: "d", extraer: true, readme: false });
  assert.equal(p.cola[1].destino, undefined);
  assert.throws(() => armarPayload([{ accion: "copiar", origen: "a" }]), /destino/);
  assert.throws(() => armarPayload([{ accion: "buscar", origen: "a" }]), /buscar/);
  assert.throws(() => armarPayload([filaVacia()]), /vacía/);
});
