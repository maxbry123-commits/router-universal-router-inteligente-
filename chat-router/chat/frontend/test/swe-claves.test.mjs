import test from "node:test";
import assert from "node:assert/strict";

function simular(inicial) {
  const m = new Map(Object.entries(inicial || {}));
  globalThis.localStorage = { getItem: (k) => (m.has(k) ? m.get(k) : null), setItem: (k, v) => { m.set(k, String(v)); }, removeItem: (k) => { m.delete(k); } };
  return m;
}
const { leerClaves, guardarClave, borrarClaves, CLAVE_LS } = await import("../swe-claves.js");

test("la clave de localStorage es riu_swe_claves", () => { assert.equal(CLAVE_LS, "riu_swe_claves"); });

test("guardar y leer: groq y nvidia, recortando espacios", () => {
  const m = simular();
  guardarClave("groq", "  gsk_abc  "); guardarClave("nvidia", "\tnvapi-xyz\n");
  assert.deepEqual(leerClaves(), { groq: "gsk_abc", nvidia: "nvapi-xyz" });
  assert.ok(m.has("riu_swe_claves"));
});

test("un valor vacio o solo espacios no guarda ni pisa la clave existente", () => {
  simular();
  guardarClave("groq", "gsk_1"); guardarClave("groq", "   "); guardarClave("nvidia", "");
  assert.deepEqual(leerClaves(), { groq: "gsk_1" });
});

test("proveedor desconocido se ignora", () => {
  simular(); guardarClave("otro", "x");
  assert.deepEqual(leerClaves(), {});
});

test("borrar deja todo vacio", () => {
  const m = simular(); guardarClave("groq", "gsk_1"); borrarClaves();
  assert.deepEqual(leerClaves(), {}); assert.ok(!m.has("riu_swe_claves"));
});

test("JSON corrupto o de tipo raro no rompe", () => {
  for (const v of ["{no es json", "null", "42", "[1,2]", '"texto"', '{"groq":5,"nvidia":null}']) {
    simular({ riu_swe_claves: v });
    assert.deepEqual(leerClaves(), {}, v);
  }
  simular({ riu_swe_claves: "{corrupto" }); guardarClave("groq", "gsk_ok");
  assert.deepEqual(leerClaves(), { groq: "gsk_ok" });
});

test("acepta listas de claves y descarta las vacias", () => {
  simular({ riu_swe_claves: JSON.stringify({ groq: [" k1 ", "", "k2", 3], nvidia: [] }) });
  assert.deepEqual(leerClaves(), { groq: ["k1", "k2"] });
});

test("sin localStorage o con localStorage que lanza: sin claves, sin excepcion", () => {
  delete globalThis.localStorage;
  assert.deepEqual(leerClaves(), {}); guardarClave("groq", "x"); borrarClaves();
  globalThis.localStorage = { getItem() { throw new Error("bloqueado"); }, setItem() { throw new Error("bloqueado"); }, removeItem() { throw new Error("bloqueado"); } };
  assert.deepEqual(leerClaves(), {}); guardarClave("groq", "x"); borrarClaves();
});
