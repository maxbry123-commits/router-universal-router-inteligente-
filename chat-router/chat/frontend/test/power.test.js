// node --test chat/frontend/test/power.test.js — la función con Hugging Face simulado (sin red, sin token real).
const test = require("node:test"), assert = require("node:assert");
const handler = require("../api/power.js");
const CLAVE = "clave-prueba", TOKEN = "hf_token_secreto_de_prueba";
process.env.RIU_ROUTER_API_KEY = CLAVE; process.env.HF_POWER_TOKEN = TOKEN; process.env.HF_SPACE_ID = "dueno/space";
const llamar = async (req, hf) => {
  const vistas = []; globalThis.fetch = async (url, opt) => {
    if (String(url).endsWith("/health")) return { ok: true, status: 200, text: async () => JSON.stringify({ tareas_en_curso: 0, latido: { t: 0, ok: true } }) };
    vistas.push([url, opt.method, opt.headers.Authorization]); return hf;
  };
  let codigo, cuerpo; const res = { setHeader() {}, status(c) { codigo = c; return this; }, json(b) { cuerpo = b; return this; } };
  await handler({ headers: { "x-api-key": CLAVE, ...(req.headers || {}) }, method: "GET", ...req }, res);
  return { codigo, cuerpo, vistas };
};
const hf = (estado, objeto) => ({ ok: estado < 400, status: estado, text: async () => JSON.stringify(objeto) });

test("sin clave o con clave mala: 401 y no se llama a Hugging Face", async () => {
  for (const headers of [{ "x-api-key": undefined }, { "x-api-key": "otra" }]) {
    const r = await llamar({ headers }, hf(200, {})); assert.equal(r.codigo, 401); assert.equal(r.vistas.length, 0);
  }
});
test("estado = GET /runtime", async () => {
  const r = await llamar({}, hf(200, { stage: "PAUSED", hardware: { current: null, requested: "cpu-basic" } }));
  assert.deepEqual([r.codigo, r.cuerpo.stage, r.cuerpo.hardware], [200, "PAUSED", "cpu-basic"]);
  assert.deepEqual(r.vistas[0], ["https://huggingface.co/api/spaces/dueno/space/runtime", "GET", "Bearer " + TOKEN]);
});
test("encender y reiniciar = POST /restart; apagar = POST /pause", async () => {
  for (const [accion, ruta] of [["encender", "/restart"], ["reiniciar", "/restart"], ["apagar", "/pause"]]) {
    const r = await llamar({ method: "POST", body: { accion } }, hf(200, { stage: "BUILDING" }));
    assert.deepEqual([r.codigo, r.vistas[0][0], r.vistas[0][1]], [200, "https://huggingface.co/api/spaces/dueno/space" + ruta, "POST"]);
  }
});
test("accion invalida: 400 sin llamar a Hugging Face", async () => {
  const r = await llamar({ method: "POST", body: { accion: "borrar" } }, hf(200, {})); assert.equal(r.codigo, 400); assert.equal(r.vistas.length, 0);
});
test("402 (faltan creditos) se devuelve claro y el token nunca aparece", async () => {
  const r = await llamar({ method: "POST", body: { accion: "encender" } }, hf(402, { error: "Payment required: add credits" }));
  assert.deepEqual([r.codigo, r.cuerpo.detail], [402, "Payment required: add credits"]);
  for (const caso of [r, await llamar({}, hf(200, { stage: "RUNNING" })), await llamar({ method: "POST", body: { accion: "apagar" } }, hf(500, { error: "x" }))])
    assert.ok(!JSON.stringify(caso.cuerpo).includes(TOKEN));
});
test("Hugging Face caido: 502 claro", async () => {
  globalThis.fetch = async () => { throw new Error("red"); };
  let c, b; await handler({ headers: { "x-api-key": CLAVE }, method: "GET" }, { setHeader() {}, status(x) { c = x; return this; }, json(x) { b = x; return this; } });
  assert.equal(c, 502); assert.ok(!JSON.stringify(b).includes(TOKEN));
});
const pedir = async (fetchFn, body) => {
  globalThis.fetch = fetchFn;
  let codigo, cuerpo; const res = { setHeader() {}, status(c) { codigo = c; return this; }, json(b) { cuerpo = b; return this; } };
  await handler({ headers: { "x-api-key": CLAVE }, method: "POST", body }, res);
  return { codigo, cuerpo };
};
test("N>0 bloquea apagar y reiniciar; forzar pasa; N=0 pasa; Router dormido pasa", async () => {
  const hfOk = () => ({ ok: true, status: 200, text: async () => JSON.stringify({ stage: "PAUSED" }) });
  const health = (n) => ({ ok: true, status: 200, text: async () => JSON.stringify({ tareas_en_curso: n, latido: { t: 1, ok: true } }) });
  for (const accion of ["apagar", "reiniciar"]) {
    const r = await pedir(async (url) => String(url).endsWith("/health") ? health(3) : hfOk(), { accion });
    assert.deepEqual([r.codigo, r.cuerpo.detail], [409, "hay 3 tareas en curso"]);
    const ok = await pedir(async (url) => String(url).endsWith("/health") ? health(3) : hfOk(), { accion, forzar: true });
    assert.equal(ok.codigo, 200);
    const cero = await pedir(async (url) => String(url).endsWith("/health") ? health(0) : hfOk(), { accion });
    assert.equal(cero.codigo, 200);
    const dormido = await pedir(async (url) => { if (String(url).endsWith("/health")) throw new Error("dormido"); return hfOk(); }, { accion });
    assert.equal(dormido.codigo, 200);
  }
});
