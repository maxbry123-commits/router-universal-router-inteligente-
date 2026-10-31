// Auditoria forense (puntos 2, 4, 5, 11, 12): failover por timeout, ids de tool_calls, regla Qwen 3.8, usage en metricas y servidor local.
// Servidores node:http locales, claves FALSAS (nunca reales).
import test from "node:test";
import assert from "node:assert/strict";
import http from "node:http";
import { respaldo, externo, local, BASES, setClaves, limpiarClaves, limpiarEstado } from "../src/respaldo.js";

const msgs = [{ role: "user", content: "hola" }];
const ok = (content, finish_reason = "stop", extra = {}, usage) => ({ status: 200, json: { choices: [{ finish_reason, message: { role: "assistant", content, ...extra } }], ...(usage ? { usage } : {}) } });
const fake = (handler) => new Promise((listo) => {
  const vistos = [], chat = []; let n = 0;
  const s = http.createServer((req, res) => {
    let d = ""; req.on("data", (c) => d += c); req.on("end", () => {
      const v = { method: req.method, url: req.url, auth: req.headers.authorization, body: d ? JSON.parse(d) : null };
      vistos.push(v); if (v.url.endsWith("/chat/completions")) { chat.push(v); n++; }
      const r = handler({ ...v, n, res }) || { status: 404, json: {} };
      if (r.colgar) return;
      if (r.sse) { res.writeHead(200, { "content-type": "text/event-stream" }); for (const e of r.sse) res.write(`data: ${typeof e === "string" ? e : JSON.stringify(e)}\n\n`); return res.end(); }
      res.writeHead(r.status, { "content-type": "application/json" }); res.end(JSON.stringify(r.json ?? {}));
    });
  }).listen(0, "127.0.0.1", () => listo({ s, vistos, chat, url: `http://127.0.0.1:${s.address().port}`, cerrar: () => { s.closeAllConnections?.(); s.close(); } }));
});
const modelos = (ids) => ({ status: 200, json: { object: "list", data: ids.map((id) => ({ id })) } });
const rapido = (extra = {}) => ({ esperar: async () => {}, ...extra });

test.beforeEach(() => { limpiarEstado(); limpiarClaves(); });

// ---------- 2: timeout enfria el proveedor entero ----------
test("2: el primer timeout de una clave corta el proveedor (no prueba las demas claves) y lo enfria", async () => {
  const g = await fake(() => ({ colgar: true }));
  Object.assign(BASES, { groq: g.url });
  const env = { GROQ_API_KEY: "gsk-FAKE-1", GROQ_API_KEY_2: "gsk-FAKE-2", GROQ_API_KEY_3: "gsk-FAKE-3" };
  try {
    await assert.rejects(() => externo("groq/m", msgs, { env, opts: rapido({ timeoutMs: 80 }) }), (e) => e.code === "EXTERNO_FALLO");
    assert.equal(g.chat.length, 1, "una sola peticion colgada, no una por clave");
    await assert.rejects(() => externo("groq/m", msgs, { env, opts: rapido({ timeoutMs: 80 }) }), (e) => e.code === "EXTERNO_FALLO" && /enfriad/.test(e.message));
    assert.equal(g.chat.length, 1, "proveedor enfriado: ni una peticion mas");
  } finally { g.cerrar(); }
});

test("2: HTTP 408 tambien enfria el proveedor entero", async () => {
  const g = await fake(() => ({ status: 408, json: {} }));
  Object.assign(BASES, { groq: g.url });
  try {
    await assert.rejects(() => externo("groq/m", msgs, { env: { GROQ_API_KEY: "gsk-FAKE-1", GROQ_API_KEY_2: "gsk-FAKE-2" }, opts: rapido() }));
    assert.equal(g.chat.length, 1);
  } finally { g.cerrar(); }
});

test("2: respaldo() no reentra en el proveedor enfriado por timeout y sigue con NVIDIA", async () => {
  const g = await fake(({ url }) => url.endsWith("/models") ? modelos([]) : { colgar: true });
  const n = await fake(({ url }) => url.endsWith("/models") ? modelos([]) : ok("de nvidia"));
  Object.assign(BASES, { groq: g.url, nvidia: n.url });
  const env = { GROQ_API_KEY: "gsk-FAKE-1", GROQ_API_KEY_2: "gsk-FAKE-2", NVIDIA_API_KEY: "nvapi-FAKE-1" };
  try {
    await assert.rejects(() => externo("groq/m", msgs, { env, opts: rapido({ timeoutMs: 80 }) }));
    const antes = g.vistos.length;
    const r = await respaldo(msgs, { env, opts: rapido({ timeoutMs: 80 }) });
    assert.equal(r.salida, "de nvidia"); assert.equal(r.via, "nvidia");
    assert.equal(g.vistos.length, antes, "Groq enfriado: respaldo no le manda NADA (ni /models ni chat)");
  } finally { g.cerrar(); n.cerrar(); }
});

// ---------- 4: tool_calls sin id ----------
test("4: tool_calls sin id (JSON) reciben call_<n>_<index>; los que traen id lo conservan", async () => {
  const tcs = [{ type: "function", function: { name: "a", arguments: "{}" } }, { id: "call_x", type: "function", function: { name: "b", arguments: "{}" } }, { id: "", type: "function", function: { name: "c", arguments: "{}" } }];
  const g = await fake(() => ok("", "tool_calls", { tool_calls: tcs }));
  Object.assign(BASES, { groq: g.url });
  try {
    const r = await externo("groq/m", msgs, { env: { GROQ_API_KEY: "gsk-FAKE-1" }, opts: rapido() });
    const ids = r.tool_calls.map((t) => t.id);
    assert.match(ids[0], /^call_\d+_0$/); assert.equal(ids[1], "call_x"); assert.match(ids[2], /^call_\d+_2$/);
    assert.equal(new Set(ids).size, 3);
  } finally { g.cerrar(); }
});

test("4: tool_calls sin id en streaming tambien reciben call_<n>_<index>", async () => {
  const tc = (index, extra) => ({ choices: [{ index: 0, delta: { tool_calls: [{ index, ...extra }] }, finish_reason: null }] });
  const g = await fake(() => ({ sse: [tc(0, { type: "function", function: { name: "a", arguments: "{}" } }), tc(1, { type: "function", function: { name: "b", arguments: "{}" } }), { choices: [{ index: 0, delta: {}, finish_reason: "tool_calls" }] }, "[DONE]"] }));
  Object.assign(BASES, { groq: g.url });
  try {
    const r = await externo("groq/m", msgs, { env: { GROQ_API_KEY: "gsk-FAKE-1" }, opts: rapido(), onDelta: () => {} });
    assert.match(r.tool_calls[0].id, /^call_\d+_0$/); assert.match(r.tool_calls[1].id, /^call_\d+_1$/);
  } finally { g.cerrar(); }
});

// ---------- 5: regla Qwen 3.8 ----------
test("5: la regla de descubrimiento de Groq casa qwen3.8 y NO qwen3-8b", async () => {
  const g = await fake(({ url }) => url.endsWith("/models") ? modelos(["qwen/qwen3-8b-instruct", "qwen3-8b", "llama-x", "qwen/qwen3.8-pro"]) : ok("hola"));
  Object.assign(BASES, { groq: g.url });
  try {
    await respaldo(msgs, { env: { GROQ_API_KEY: "gsk-FAKE-1" }, opts: rapido() });
    assert.equal(g.chat[0].body.model, "qwen/qwen3.8-pro");
  } finally { g.cerrar(); }
  limpiarEstado();
  const h = await fake(({ url }) => url.endsWith("/models") ? modelos(["qwen/qwen3-8b-instruct", "qwen3-8b"]) : ok("hola"));
  Object.assign(BASES, { groq: h.url });
  try {
    await respaldo(msgs, { env: { GROQ_API_KEY: "gsk-FAKE-1" }, opts: rapido() });
    assert.equal(h.chat[0].body.model, "qwen/qwen3.8-27b", "qwen3-8b NO es Qwen 3.8: cae al id por defecto");
  } finally { h.cerrar(); }
});

// ---------- 11: usage en metricas ----------
test("11: metricas lleva prompt/completion/total tokens del proveedor (JSON, sumando continuaciones)", async () => {
  const g = await fake(({ n }) => n === 1 ? ok("AA", "length", {}, { prompt_tokens: 10, completion_tokens: 5, total_tokens: 15 }) : ok("BB", "stop", {}, { prompt_tokens: 20, completion_tokens: 7, total_tokens: 27 }));
  Object.assign(BASES, { groq: g.url });
  try {
    const r = await externo("groq/m", msgs, { env: { GROQ_API_KEY: "gsk-FAKE-1" }, opts: rapido() });
    assert.equal(r.metricas.prompt_tokens, 30); assert.equal(r.metricas.completion_tokens, 12); assert.equal(r.metricas.total_tokens, 42);
  } finally { g.cerrar(); }
});

test("11: metricas lleva prompt/completion/total tokens tambien en streaming (usage del ultimo fragmento)", async () => {
  const g = await fake(() => ({ sse: [{ choices: [{ index: 0, delta: { content: "hola" }, finish_reason: null }] }, { choices: [{ index: 0, delta: {}, finish_reason: "stop" }], usage: { prompt_tokens: 9, completion_tokens: 3, total_tokens: 12 } }, "[DONE]"] }));
  Object.assign(BASES, { groq: g.url });
  try {
    const r = await externo("groq/m", msgs, { env: { GROQ_API_KEY: "gsk-FAKE-1" }, opts: rapido(), onDelta: () => {} });
    assert.equal(r.metricas.prompt_tokens, 9); assert.equal(r.metricas.completion_tokens, 3); assert.equal(r.metricas.total_tokens, 12);
  } finally { g.cerrar(); }
});

// ---------- 12: servidor local ----------
test("12: local() devuelve el servidor (S1/S2/S3) que respondio", async () => {
  const a = await fake(() => ({ status: 500, json: {} })), b = await fake(() => ok("de S2"));
  try {
    const r = await local("lfm2.5-350m", msgs, { env: { SWECODE_URL_S1: a.url, SWECODE_URL_S2: b.url }, opts: rapido() });
    assert.equal(r.salida, "de S2"); assert.equal(r.servidor, "S2");
  } finally { a.cerrar(); b.cerrar(); }
});
