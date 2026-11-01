import test from "node:test";
import assert from "node:assert/strict";

// R1 (auditoria 3): el navegador NO guarda claves en localStorage ni las reenvia; el banco del servidor es la unica fuente. Marcadores de prueba, ninguna clave real.
function simular(inicial) {
  const m = new Map(Object.entries(inicial || {}));
  globalThis.localStorage = { getItem: (k) => (m.has(k) ? m.get(k) : null), setItem: (k, v) => { m.set(k, String(v)); }, removeItem: (k) => { m.delete(k); } };
  return m;
}
const C = await import("../swe-claves.js");
const { guardar, borrar, estado, textoConteos, purgarLocal, CLAVE_LS } = C;

test("R1 la API local de claves ya no existe: no hay leerClaves/guardarClave/borrarClaves", () => {
  for (const f of ["leerClaves", "guardarClave", "borrarClaves"]) assert.equal(typeof C[f], "undefined", f);
  assert.equal(CLAVE_LS, "riu_swe_claves");
});

test("R1 purgarLocal borra una clave que quedo en el navegador por versiones anteriores y no falla sin localStorage", () => {
  const m = simular({ riu_swe_claves: JSON.stringify({ groq: "MARCADOR-VIEJO" }), otra: "x" });
  purgarLocal(); assert.ok(!m.has("riu_swe_claves")); assert.ok(m.has("otra"));
  delete globalThis.localStorage; purgarLocal();
  globalThis.localStorage = { getItem() { throw new Error("bloqueado"); }, setItem() { throw new Error("bloqueado"); }, removeItem() { throw new Error("bloqueado"); } }; purgarLocal();
  delete globalThis.localStorage;
});

// ---- banco del servidor (fetch simulado) ----
const BASE = "https://router-test.hf.space";
function entorno({ respuestas = [], clave = "clave-chat", ls } = {}) {
  const m = simular(ls);
  globalThis.window = { RIU_CONFIG: { apiBase: BASE } };
  globalThis.sessionStorage = { getItem: (k) => (k === "riu_clave" ? clave : null) };
  const llamadas = [];
  globalThis.fetch = async (url, op) => {
    llamadas.push({ url, metodo: op.method, headers: op.headers, body: op.body ? JSON.parse(op.body) : undefined });
    const r = respuestas.shift() || { status: 200, json: { ok: true, groq: 0, nvidia: 0 } };
    if (r.red) throw new TypeError("fetch failed");
    return { ok: r.status >= 200 && r.status < 300, status: r.status, json: async () => r.json || {} };
  };
  return { m, llamadas };
}
const sinClaves = (m) => assert.ok(![...m.values()].some((v) => /MARCADOR/.test(v)), "ningun valor de clave queda en localStorage");

test("guardar: POST a /web/v1/claves con X-API-Key, estado con conteos y sin valores; nada en localStorage", async () => {
  const { llamadas, m } = entorno({ respuestas: [{ status: 200, json: { ok: true, groq: 2, nvidia: 1 } }] });
  const t = await guardar({ groq: "  MARCADOR-PRUEBA-A  ", nvidia: "MARCADOR-PRUEBA-B", otro: "x" });
  assert.equal(t, "Groq: 2 guardadas · NVIDIA: 1 guardada");
  assert.ok(!t.includes("MARCADOR"));
  assert.equal(llamadas.length, 1);
  assert.equal(llamadas[0].url, BASE + "/web/v1/claves"); assert.equal(llamadas[0].metodo, "POST");
  assert.equal(llamadas[0].headers["X-API-Key"], "clave-chat");
  assert.deepEqual(llamadas[0].body, { groq: "MARCADOR-PRUEBA-A", nvidia: "MARCADOR-PRUEBA-B" });
  sinClaves(m);
});

test("guardar sin valores no llama al servidor", async () => {
  const { llamadas } = entorno();
  assert.equal(await guardar({ groq: "  ", nvidia: "" }), "Nada que guardar");
  assert.equal(llamadas.length, 0);
});

test("estado: GET con X-API-Key y conteos", async () => {
  const { llamadas } = entorno({ respuestas: [{ status: 200, json: { ok: true, groq: 1, nvidia: 0 } }] });
  assert.equal(await estado(), "Groq: 1 guardada");
  assert.equal(llamadas[0].metodo, "GET"); assert.equal(llamadas[0].headers["X-API-Key"], "clave-chat");
  assert.equal(textoConteos({ groq: 0, nvidia: 0 }), "Sin claves guardadas en el servidor");
});

test("borrar: DELETE al servidor", async () => {
  const { llamadas } = entorno({ respuestas: [{ status: 200, json: { ok: true, groq: 0, nvidia: 0 } }] });
  assert.equal(await borrar(), "Claves borradas del servidor");
  assert.equal(llamadas[0].metodo, "DELETE"); assert.equal(llamadas[0].headers["X-API-Key"], "clave-chat");
});

test("401, 400 y 503: mensaje claro, sin guardar nada y sin valores", async () => {
  for (const [st, code, re] of [[401, "", /clave del chat incorrecta/i], [400, "CLAVE_INVALIDA", /formato inv/i], [503, "", /sin clave de acceso|no tiene clave de acceso/i]]) {
    const { m } = entorno({ respuestas: [{ status: st, json: code ? { error: { code } } : {} }] });
    const t = await guardar({ groq: "MARCADOR-PRUEBA-A" });
    assert.match(t, re, String(st)); assert.ok(!t.includes("MARCADOR")); sinClaves(m);
  }
});

test("R1 404, 502 y sin red: NO hay respaldo local; se dice que no se guardo nada y que el servidor es la unica fuente", async () => {
  for (const r of [{ status: 404 }, { status: 502 }, { red: true }]) {
    const { m } = entorno({ respuestas: [r] });
    const x = await C.guardarConEstado({ groq: "MARCADOR-PRUEBA-A" });
    assert.equal(x.ok, false); assert.match(x.texto, /No se guardó nada.*servidor/); assert.ok(!x.texto.includes("MARCADOR"));
    sinClaves(m); assert.equal(m.size, 0);
  }
});

test("R1 con el servidor caido: estado = «Sin verificar…» (no se inventa), borrar no borra nada local", async () => {
  entorno({ respuestas: [{ red: true }] });
  assert.match(await estado(), /^Sin verificar: el servidor no respondió/);
  entorno({ respuestas: [{ red: true }] });
  assert.match(await borrar(), /No se borró nada: el servidor no respondió/);
});
