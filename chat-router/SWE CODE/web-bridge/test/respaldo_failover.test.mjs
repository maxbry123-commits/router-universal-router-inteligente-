// Pruebas del respaldo: descubrimiento de modelos, continuacion automatica y failover por clave/proveedor.
// Todo con un servidor HTTP falso local y claves FALSAS (nunca reales).
import test from "node:test";
import assert from "node:assert/strict";
import http from "node:http";
import { respaldo, externo, local, BASES, idsRespaldo, MODELOS_API, setClaves, limpiarClaves, limpiarEstado } from "../src/respaldo.js";

const msgs = [{ role: "user", content: "hola" }];
const CONT = "Continúa exactamente donde terminó, sin repetir";
const ok = (content, finish_reason = "stop", extra = {}) => ({ status: 200, json: { choices: [{ finish_reason, message: { role: "assistant", content, ...extra } }] } });

// handler({method,url,auth,body,n}) -> {status, json, headers}; n = numero de peticion de chat (1..)
const fake = (handler) => new Promise((listo) => {
  const vistos = []; const chat = []; let n = 0;
  const s = http.createServer((req, res) => {
    let d = ""; req.on("data", (c) => d += c); req.on("end", () => {
      const v = { method: req.method, url: req.url, auth: req.headers.authorization, body: d ? JSON.parse(d) : null };
      vistos.push(v);
      if (v.url.endsWith("/chat/completions")) { chat.push(v); n++; }
      const r = handler({ ...v, n }) || { status: 404, json: {} };
      if (r.colgar) return;  // simula timeout: no contesta
      res.writeHead(r.status, { "content-type": "application/json", ...(r.headers || {}) }); res.end(JSON.stringify(r.json ?? {}));
    });
  }).listen(0, "127.0.0.1", () => listo({ s, vistos, chat, url: `http://127.0.0.1:${s.address().port}`, cerrar: () => { s.closeAllConnections?.(); s.close(); } }));
});
const modelos = (ids) => ({ status: 200, json: { object: "list", data: ids.map((id) => ({ id })) } });
const rapido = (extra = {}) => ({ esperar: async () => {}, ...extra });

test.beforeEach(() => { limpiarEstado(); limpiarClaves(); });

// ---------- continuacion automatica ----------
test("finish_reason=length: continua solo, concatena y devuelve el finish_reason final real", async () => {
  const g = await fake(({ url, n }) => url.endsWith("/models") ? modelos([]) : n === 1 ? ok("AAA", "length") : n === 2 ? ok("BBB", "length") : ok("CCC", "stop"));
  Object.assign(BASES, { groq: g.url });
  try {
    const r = await externo("groq/m", msgs, { env: { GROQ_API_KEY: "gsk-FAKE-1" }, opts: rapido() });
    assert.equal(r.salida, "AAABBBCCC"); assert.equal(r.finish_reason, "stop"); assert.equal(g.chat.length, 3);
    const m2 = g.chat[1].body.messages;
    assert.deepEqual(m2.slice(-2), [{ role: "assistant", content: "AAA" }, { role: "user", content: CONT }]);
    const m3 = g.chat[2].body.messages;
    assert.deepEqual(m3.slice(-2), [{ role: "assistant", content: "AAABBB" }, { role: "user", content: CONT }]);
    assert.deepEqual(m3.slice(0, 1), msgs);
  } finally { g.cerrar(); }
});

test("continuacion: tope de vueltas (inyectable, por defecto 8) y finish_reason final = length", async () => {
  const g = await fake(() => ok("x", "length"));
  Object.assign(BASES, { groq: g.url });
  try {
    const r = await externo("groq/m", msgs, { env: { GROQ_API_KEY: "gsk-FAKE-1" }, opts: rapido({ continuaciones: 3 }) });
    assert.equal(g.chat.length, 4); assert.equal(r.salida, "xxxx"); assert.equal(r.finish_reason, "length");
    g.chat.length = 0;
    await externo("groq/m", msgs, { env: { GROQ_API_KEY: "gsk-FAKE-1" }, opts: rapido() });
    assert.equal(g.chat.length, 9, "1 llamada + 8 continuaciones por defecto");
  } finally { g.cerrar(); }
});

test("continuacion: NO continua si hay tool_calls aunque diga length", async () => {
  const tc = [{ id: "c1", type: "function", function: { name: "f", arguments: "{}" } }];
  const g = await fake(() => ok("parcial", "length", { tool_calls: tc }));
  Object.assign(BASES, { groq: g.url });
  try {
    const r = await externo("groq/m", msgs, { env: { GROQ_API_KEY: "gsk-FAKE-1" }, opts: rapido() });
    assert.equal(g.chat.length, 1); assert.deepEqual(r.tool_calls, tc);
  } finally { g.cerrar(); }
});

test("continuacion: corte por ~15k tokens (usage) sin finish_reason tambien continua; stop explicito no", async () => {
  const g = await fake(({ n }) => n === 1 ? { status: 200, json: { usage: { completion_tokens: 16384 }, choices: [{ message: { content: "AA" } }] } } : ok("BB", "stop"));
  Object.assign(BASES, { groq: g.url });
  try {
    const r = await externo("groq/m", msgs, { env: { GROQ_API_KEY: "gsk-FAKE-1" }, opts: rapido() });
    assert.equal(r.salida, "AABB"); assert.equal(g.chat.length, 2);
  } finally { g.cerrar(); }
  const g2 = await fake(() => ({ status: 200, json: { usage: { completion_tokens: 16000 }, choices: [{ finish_reason: "stop", message: { content: "listo" } }] } }));
  Object.assign(BASES, { groq: g2.url });
  try {
    const r = await externo("groq/m", msgs, { env: { GROQ_API_KEY: "gsk-FAKE-1" }, opts: rapido() });
    assert.equal(r.salida, "listo"); assert.equal(g2.chat.length, 1);
  } finally { g2.cerrar(); }
});

test("continuacion: si una vuelta falla se conserva lo ya recibido (finish length)", async () => {
  const g = await fake(({ n }) => n === 1 ? ok("AAA", "length") : { status: 500, json: {} });
  Object.assign(BASES, { groq: g.url });
  try {
    const r = await externo("groq/m", msgs, { env: { GROQ_API_KEY: "gsk-FAKE-1" }, opts: rapido() });
    assert.equal(r.salida, "AAA"); assert.equal(r.finish_reason, "length");
  } finally { g.cerrar(); }
});

test("continuacion tambien en HF local", async () => {
  const l = await fake(({ n }) => n === 1 ? ok("L1", "length") : ok("L2", "stop"));
  try {
    const r = await local("lfm2.5-350m", msgs, { env: { SWECODE_URL_S1: l.url }, opts: rapido() });
    assert.equal(r.salida, "L1L2"); assert.equal(r.via, "hf-local");
  } finally { l.cerrar(); }
});

// ---------- failover por clave ----------
test("429 en la clave 1 y OK en la 2: respeta Retry-After con tope 2 s y enfria la clave ~60 s", async () => {
  const g = await fake(({ auth }) => auth === "Bearer gsk-FAKE-1" ? { status: 429, headers: { "retry-after": "30" }, json: {} } : ok("de la 2"));
  Object.assign(BASES, { groq: g.url });
  let t = 1_000_000; const esperas = [];
  const opts = { esperar: async (ms) => { esperas.push(ms); }, ahora: () => t, cooldownMs: 60_000, esperaMax: 2000 };
  const env = { GROQ_API_KEY: "gsk-FAKE-1", GROQ_API_KEY_2: "gsk-FAKE-2" };
  try {
    const r = await externo("groq/m", msgs, { env, opts });
    assert.equal(r.salida, "de la 2"); assert.deepEqual(g.chat.map((c) => c.auth), ["Bearer gsk-FAKE-1", "Bearer gsk-FAKE-2"]);
    assert.deepEqual(esperas, [2000]);
    // dentro del cooldown la clave 1 ni se toca
    g.chat.length = 0; t += 30_000;
    await externo("groq/m", msgs, { env, opts });
    assert.deepEqual(g.chat.map((c) => c.auth), ["Bearer gsk-FAKE-2"]);
    // pasado el cooldown vuelve a probarse
    g.chat.length = 0; t += 40_000;
    await externo("groq/m", msgs, { env, opts });
    assert.equal(g.chat[0].auth, "Bearer gsk-FAKE-1");
  } finally { g.cerrar(); }
});

test("429 sin Retry-After: espera corta (<= tope) y pasa a la siguiente clave", async () => {
  const g = await fake(({ n }) => n === 1 ? { status: 429, json: {} } : ok("ok"));
  Object.assign(BASES, { groq: g.url });
  const esperas = [];
  try {
    const r = await externo("groq/m", msgs, { env: { GROQ_API_KEY: "gsk-FAKE-1", GROQ_API_KEY_2: "gsk-FAKE-2" }, opts: { esperar: async (ms) => esperas.push(ms), esperaMax: 2000 } });
    assert.equal(r.salida, "ok"); assert.ok(esperas.length === 1 && esperas[0] <= 2000);
  } finally { g.cerrar(); }
});

test("401/403 descarta esa clave y sigue con la siguiente (incluidas las inyectadas)", async () => {
  const g = await fake(({ auth }) => auth === "Bearer gsk-FAKE-1" ? { status: 401, json: {} } : auth === "Bearer gsk-FAKE-2" ? { status: 403, json: {} } : ok("de la inyectada"));
  Object.assign(BASES, { groq: g.url });
  setClaves({ groq: ["gsk-FAKE-3"] });
  try {
    const r = await externo("groq/m", msgs, { env: { GROQ_API_KEY: "gsk-FAKE-1", GROQ_API_KEY_2: "gsk-FAKE-2" }, opts: rapido() });
    assert.equal(r.salida, "de la inyectada"); assert.equal(g.chat.length, 3);
  } finally { g.cerrar(); }
});

test("rota entre hasta 20 claves por proveedor ante 402/408/5xx", async () => {
  const codigos = [402, 408, 500, 502, 503, 504];
  const g = await fake(({ n }) => n < 20 ? { status: codigos[n % codigos.length], json: {} } : ok("la 20"));
  Object.assign(BASES, { groq: g.url });
  setClaves({ groq: Array.from({ length: 30 }, (_, i) => `gsk-FAKE-I${i}`) });
  try {
    const r = await externo("groq/m", msgs, { env: {}, opts: rapido() });
    assert.equal(r.salida, "la 20"); assert.equal(g.chat.length, 20);
  } finally { g.cerrar(); }
});

test("timeout por llamada: pasa a la siguiente clave", async () => {
  const g = await fake(({ auth }) => auth === "Bearer gsk-FAKE-1" ? { colgar: true } : ok("ok2"));
  Object.assign(BASES, { groq: g.url });
  try {
    const r = await externo("groq/m", msgs, { env: { GROQ_API_KEY: "gsk-FAKE-1", GROQ_API_KEY_2: "gsk-FAKE-2" }, opts: rapido({ timeoutMs: 80 }) });
    assert.equal(r.salida, "ok2"); assert.equal(g.chat.length, 2);
  } finally { g.cerrar(); }
});

// ---------- failover por proveedor ----------
test("402 en Groq (todas las claves) y OK en NVIDIA", async () => {
  const g = await fake(({ url }) => url.endsWith("/models") ? modelos(["qwen3-8b-x"]) : { status: 402, json: {} });
  const n = await fake(({ url }) => url.endsWith("/models") ? modelos([]) : ok("de nvidia"));
  Object.assign(BASES, { groq: g.url, nvidia: n.url });
  try {
    const r = await respaldo(msgs, { env: { GROQ_API_KEY: "gsk-FAKE-1", GROQ_API_KEY_2: "gsk-FAKE-2", NVIDIA_API_KEY: "nv-FAKE-1" }, opts: rapido() });
    assert.equal(r.via, "nvidia"); assert.equal(r.salida, "de nvidia"); assert.equal(g.chat.length, 2);
  } finally { g.cerrar(); n.cerrar(); }
});

test("todo caido (Groq y NVIDIA) -> HF local S1 falla y S2 responde", async () => {
  const g = await fake(() => ({ status: 503, json: {} })), n = await fake(() => ({ status: 429, json: {} }));
  const l1 = await fake(() => ({ status: 500, json: {} })), l2 = await fake(() => ok("de S2"));
  Object.assign(BASES, { groq: g.url, nvidia: n.url });
  try {
    const r = await respaldo(msgs, { env: { GROQ_API_KEY: "gsk-FAKE-1", NVIDIA_API_KEY: "nv-FAKE-1", SWECODE_URL_S1: l1.url, SWECODE_URL_S2: l2.url }, opts: rapido() });
    assert.equal(r.via, "hf-local"); assert.equal(r.salida, "de S2"); assert.equal(l2.chat.length, 1);
  } finally { g.cerrar(); n.cerrar(); l1.cerrar(); l2.cerrar(); }
});

test("ninguna clave aparece en errores ni en logs (aunque el servidor las devuelva)", async () => {
  const claveG = "gsk-FAKE-SECRETA-123", claveN = "nv-FAKE-SECRETA-456";
  const eco = ({ auth }) => ({ status: 500, json: { error: { message: `bad key ${auth}` } } });
  const g = await fake(eco), n = await fake(eco);
  Object.assign(BASES, { groq: g.url, nvidia: n.url });
  const capturado = []; const orig = {};
  for (const m of ["log", "error", "warn", "info", "debug"]) { orig[m] = console[m]; console[m] = (...a) => capturado.push(a.map(String).join(" ")); }
  const w = process.stderr.write.bind(process.stderr); let err = "";
  try {
    setClaves({ groq: [claveG] });
    let e1; try { await respaldo(msgs, { env: { NVIDIA_API_KEY: claveN }, opts: rapido() }); } catch (e) { e1 = e; }
    let e2; try { await externo("groq/m", msgs, { env: {}, opts: rapido() }); } catch (e) { e2 = e; }
    assert.equal(e1.code, "RESPALDO_AGOTADO");
    for (const txt of [e1.message, e2.message, JSON.stringify(e1), capturado.join("\n"), err]) {
      assert.ok(!txt.includes(claveG) && !txt.includes(claveN), "la clave no debe salir");
      assert.ok(!/gsk-FAKE|nv-FAKE/.test(txt));
    }
  } finally { for (const m of Object.keys(orig)) console[m] = orig[m]; void w; g.cerrar(); n.cerrar(); }
});

// ---------- descubrimiento de modelos ----------
test("Groq: descubre el id Qwen 3.8 con GET /models, lo cachea (una sola consulta) y lo usa", async () => {
  const g = await fake(({ url }) => url.endsWith("/models") ? modelos(["llama-3.3-70b-versatile", "qwen/qwen3-8b-instruct", "qwen-3.8-x"]) : ok("hola"));
  Object.assign(BASES, { groq: g.url });
  const env = { GROQ_API_KEY: "gsk-FAKE-1" };
  try {
    await respaldo(msgs, { env, opts: rapido() }); await respaldo(msgs, { env, opts: rapido() });
    assert.equal(g.chat[0].body.model, "qwen/qwen3-8b-instruct");
    assert.equal(g.vistos.filter((v) => v.url.endsWith("/models")).length, 1);
    assert.equal(g.vistos.find((v) => v.url.endsWith("/models")).auth, "Bearer gsk-FAKE-1");
    assert.equal(g.vistos.find((v) => v.url.endsWith("/models")).method, "GET");
  } finally { g.cerrar(); }
});

test("Groq sin Qwen 3.8: usa RIU_SWE_GROQ_MODELO, y si no, el id por defecto", async () => {
  const g = await fake(({ url }) => url.endsWith("/models") ? modelos(["llama-3.3-70b-versatile", "qwen3-32b"]) : ok("hola"));
  Object.assign(BASES, { groq: g.url });
  try {
    await respaldo(msgs, { env: { GROQ_API_KEY: "gsk-FAKE-1", RIU_SWE_GROQ_MODELO: "mi-modelo" }, opts: rapido() });
    assert.equal(g.chat.at(-1).body.model, "mi-modelo");
    limpiarEstado();
    await respaldo(msgs, { env: { GROQ_API_KEY: "gsk-FAKE-1" }, opts: rapido() });
    assert.equal(g.chat.at(-1).body.model, "qwen/qwen3.8-27b");
  } finally { g.cerrar(); }
});

test("Groq: si /models falla (caido) usa el id por defecto sin romper", async () => {
  const g = await fake(({ url }) => url.endsWith("/models") ? { status: 500, json: {} } : ok("hola"));
  Object.assign(BASES, { groq: g.url });
  try {
    const r = await respaldo(msgs, { env: { GROQ_API_KEY: "gsk-FAKE-1" }, opts: rapido() });
    assert.equal(r.salida, "hola"); assert.equal(g.chat[0].body.model, "qwen/qwen3.8-27b");
  } finally { g.cerrar(); }
});

const nvidiaCon = async (ids, env = {}) => {
  const n = await fake(({ url }) => url.endsWith("/models") ? modelos(ids) : ok("hola"));
  Object.assign(BASES, { groq: "http://127.0.0.1:9", nvidia: n.url });
  try {
    await respaldo(msgs, { env: { NVIDIA_API_KEY: "nv-FAKE-1", ...env }, opts: rapido() });
    return { modelo: n.chat[0].body.model, consultas: n.vistos.filter((v) => v.url.endsWith("/models")).length };
  } finally { n.cerrar(); }
};

test("NVIDIA: primero minimax/kimi/deepseek-v4 (el primero de la lista)", async () => {
  assert.equal((await nvidiaCon(["meta/llama-3.3-70b-instruct", "nvidia/muse-nemotron-3-super", "moonshotai/kimi-k2", "minimaxai/minimax-m2"])).modelo, "moonshotai/kimi-k2");
  limpiarEstado();
  assert.equal((await nvidiaCon(["a/b", "deepseek-ai/deepseek-v4-pro"])).modelo, "deepseek-ai/deepseek-v4-pro");
});

test("NVIDIA sin MiniMax/Kimi/DeepSeek: muse/glimmer + nemotron-3-super; si no, el por defecto", async () => {
  assert.equal((await nvidiaCon(["meta/llama-3.3-70b-instruct", "nvidia/nemotron-3-super-120b", "nvidia/glimmer-nemotron-3-super"])).modelo, "nvidia/glimmer-nemotron-3-super");
  limpiarEstado();
  assert.equal((await nvidiaCon(["meta/llama-3.3-70b-instruct", "nvidia/nemotron-3-super-120b"])).modelo, "minimaxai/minimax-m3.1-flash");
});

test("NVIDIA: RIU_SWE_NVIDIA_MODELO manda y ni siquiera consulta /models", async () => {
  const r = await nvidiaCon(["minimaxai/minimax-m2"], { RIU_SWE_NVIDIA_MODELO: "forzado/m" });
  assert.equal(r.modelo, "forzado/m"); assert.equal(r.consultas, 0);
});

test("idsRespaldo sigue sin red: MODELOS_API + locales, sin los dos Llama", async () => {
  const g = await fake(() => ok("x"));
  Object.assign(BASES, { groq: g.url, nvidia: g.url });
  try {
    const ids = idsRespaldo({ GROQ_API_KEY: "gsk-FAKE-1" });
    assert.deepEqual(ids, [...MODELOS_API.map((m) => m.id), "lfm2.5-350m", "qwen2.5-coder-1.5b", "qwen3.5-0.8b", "qwen3-0.6b"]);
    assert.deepEqual(MODELOS_API.map((m) => m.id), ["groq/qwen/qwen3.8-27b", "nvidia/minimaxai/minimax-m3.1-flash", "nvidia/meta/muse-glimmer-30b", "nvidia/nvidia/nemotron-3-ultra-550b-a55b", "nvidia/z-ai/glm-5.3"]);
    assert.ok(!ids.some((i) => /llama/i.test(i)), "los dos Llama fueron retirados");
    assert.equal(ids.filter((i) => /muse-glimmer/.test(i)).length, 1, "Muse Glimmer aparece una sola vez");
    assert.equal(g.vistos.length, 0);
  } finally { g.cerrar(); }
});

test("el timeout por defecto sube a 120000 ms", async () => {
  const { TIMEOUT_DEFECTO_MS } = await import("../src/respaldo.js");
  assert.equal(TIMEOUT_DEFECTO_MS, 120000);
});
