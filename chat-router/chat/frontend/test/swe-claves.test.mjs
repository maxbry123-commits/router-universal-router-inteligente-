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

// ---- banco del servidor (fetch simulado) ----
const { guardar, borrar, estado, textoConteos } = await import("../swe-claves.js");
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

test("guardar: POST a /web/v1/claves con X-API-Key, estado con conteos y sin valores", async () => {
  const { llamadas, m } = entorno({ respuestas: [{ status: 200, json: { ok: true, groq: 2, nvidia: 1 } }], ls: { riu_swe_claves: JSON.stringify({ groq: "vieja" }) } });
  const t = await guardar({ groq: "  gsk_SECRETA  ", nvidia: "nvapi-OTRA", otro: "x" });
  assert.equal(t, "Groq: 2 guardadas · NVIDIA: 1 guardada");
  assert.ok(!t.includes("SECRETA") && !t.includes("OTRA"));
  assert.equal(llamadas.length, 1);
  assert.equal(llamadas[0].url, BASE + "/web/v1/claves"); assert.equal(llamadas[0].metodo, "POST");
  assert.equal(llamadas[0].headers["X-API-Key"], "clave-chat");
  assert.deepEqual(llamadas[0].body, { groq: "gsk_SECRETA", nvidia: "nvapi-OTRA" });
  assert.ok(!m.has("riu_swe_claves"), "guardadas en el banco: se retira el respaldo local");
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

test("borrar: DELETE al servidor y limpia el respaldo local", async () => {
  const { llamadas, m } = entorno({ respuestas: [{ status: 200, json: { ok: true, groq: 0, nvidia: 0 } }], ls: { riu_swe_claves: JSON.stringify({ groq: "x" }) } });
  assert.equal(await borrar(), "Claves borradas");
  assert.equal(llamadas[0].metodo, "DELETE"); assert.equal(llamadas[0].headers["X-API-Key"], "clave-chat");
  assert.ok(!m.has("riu_swe_claves"));
});

test("401, 400 y 503: mensaje claro, sin respaldo local y sin valores", async () => {
  for (const [st, code, re] of [[401, "", /clave del chat incorrecta/i], [400, "CLAVE_INVALIDA", /formato inv/i], [503, "", /sin clave de acceso|no tiene clave de acceso/i]]) {
    const { m } = entorno({ respuestas: [{ status: st, json: code ? { error: { code } } : {} }] });
    const t = await guardar({ groq: "gsk_SECRETA" });
    assert.match(t, re, String(st)); assert.ok(!t.includes("SECRETA"));
    assert.ok(!m.has("riu_swe_claves"), "no se guarda localmente un error de autenticacion/formato");
  }
});

test("404, 500 y sin red: respaldo en localStorage y lo dice", async () => {
  for (const r of [{ status: 404 }, { status: 502 }, { red: true }]) {
    const { m } = entorno({ respuestas: [r] });
    const t = await guardar({ groq: "gsk_SECRETA" });
    assert.match(t, /Groq: guardada solo en este navegador/); assert.ok(!t.includes("SECRETA"));
    assert.deepEqual(JSON.parse(m.get("riu_swe_claves")), { groq: "gsk_SECRETA" });
  }
});

test("borrar con el servidor caido: borra local y avisa; estado con servidor caido muestra el respaldo", async () => {
  const { m } = entorno({ respuestas: [{ red: true }], ls: { riu_swe_claves: JSON.stringify({ nvidia: "nvapi-1" }) } });
  assert.match(await estado(), /NVIDIA: guardada solo en este navegador/);
  entorno({ respuestas: [{ red: true }], ls: { riu_swe_claves: JSON.stringify({ nvidia: "nvapi-1" }) } });
  const t = await borrar(); assert.match(t, /Claves borradas.*solo se borró este navegador/);
  assert.deepEqual(leerClaves(), {});
});
