// A5-proveedores sobre respaldo.js: R3 (tool_calls fragmentados), R8 (timeouts), R9 (metricas con origen), 152-155 (errores, Retry-After, backoff, tope), 156-161 (cambio de proveedor visible).
// Servidores node:http locales y claves FALSAS (nunca reales, sin red externa).
import test from "node:test";
import assert from "node:assert/strict";
import http from "node:http";
import { externo, respaldo, local, BASES, LIMITES, MODELOS_API, TIMEOUT_DEFECTO_MS, TIMEOUTS_DEFECTO, PLAZO_BRIDGE_MS, timeoutDe, setClaves, limpiarClaves, limpiarEstado, nombreDeTrozos, ajustesFinales, clasificarError, TABLA_ERRORES, disponibilidad, estadoMetricas } from "../src/respaldo.js";
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
const AQUI = path.dirname(fileURLToPath(import.meta.url));
const RAIZ_REPO = path.resolve(AQUI, "../../../..");

const msgs = [{ role: "user", content: "hola" }];
const rapido = (extra = {}) => ({ esperar: async () => {}, ...extra });
const ev = (o) => `data: ${typeof o === "string" ? o : JSON.stringify(o)}\n\n`;
const srv = (handler) => new Promise((listo) => {
  const chat = []; let n = 0;
  const s = http.createServer((req, res) => {
    let d = ""; req.on("data", (c) => d += c); req.on("end", () => {
      const v = { url: req.url, auth: req.headers.authorization, body: d ? JSON.parse(d) : null };
      if (v.url.endsWith("/chat/completions")) { chat.push(v); n++; }
      handler({ ...v, n, req, res });
    });
  });
  s.listen(0, "127.0.0.1", () => listo({ s, chat, url: `http://127.0.0.1:${s.address().port}`, cerrar: () => { s.closeAllConnections?.(); s.close(); } }));
});
const sse = (res, eventos) => { res.writeHead(200, { "content-type": "text/event-stream" }); for (const e of eventos) res.write(ev(e)); res.end(ev("[DONE]")); };
const json = (res, status, o, headers = {}) => { res.writeHead(status, { "content-type": "application/json", ...headers }); res.end(JSON.stringify(o)); };
const tcd = (index, fn, extra = {}) => ({ choices: [{ index: 0, delta: { tool_calls: [{ index, ...extra, function: fn }] }, finish_reason: null }] });
const fin = (r) => ({ choices: [{ index: 0, delta: {}, finish_reason: r }] });
const herramienta = (name) => ({ type: "function", function: { name, parameters: { type: "object" } } });
const env1 = { GROQ_API_KEY: "gsk-FAKE-1" };

test.beforeEach(() => { limpiarEstado(); limpiarClaves(); });

// ---------- R3: nombres y argumentos fragmentados ----------
test("R3 nombreDeTrozos: una vez, repetido entero, acumulativo y en trozos disjuntos", () => {
  assert.equal(nombreDeTrozos([]), "");
  assert.equal(nombreDeTrozos(["leer"]), "leer");
  assert.equal(nombreDeTrozos(["leer", "leer", "leer"]), "leer");
  assert.equal(nombreDeTrozos(["git", "github", "github_leer"]), "github_leer");
  assert.equal(nombreDeTrozos(["github_", "leer"]), "github_leer");
});

test("R3 stream: github_ + leer = github_leer, dos llamadas intercaladas no se mezclan y los argumentos se concatenan en orden", async () => {
  const g = await srv(({ res }) => sse(res, [
    tcd(0, { name: "github_", arguments: "" }, { id: "c0", type: "function" }), tcd(1, { name: "disco_", arguments: "" }, { id: "c1" }),
    tcd(0, { name: "leer", arguments: '{"ruta"' }), tcd(1, { name: "escribir", arguments: '{"a":' }), tcd(0, { arguments: ':"x"}' }), tcd(1, { arguments: "1}" }), fin("tool_calls")]));
  Object.assign(BASES, { groq: g.url });
  try {
    const r = await externo("groq/qwen/qwen3.8-27b", msgs, { env: env1, opts: rapido(), onDelta: () => {}, extra: { tools: [herramienta("github_leer"), herramienta("disco_escribir")] } });
    assert.deepEqual(r.tool_calls.map((t) => [t.id, t.function.name, t.function.arguments]), [["c0", "github_leer", '{"ruta":"x"}'], ["c1", "disco_escribir", '{"a":1}']]);
    assert.deepEqual(r.tools_invalidas, []);
  } finally { g.cerrar(); }
});

test("R3: un nombre que no coincide con las herramientas declaradas o argumentos JSON incompletos se MARCAN (la llamada no se pierde)", async () => {
  const g = await srv(({ res }) => sse(res, [tcd(0, { name: "github_", arguments: "{}" }, { id: "c0" }), tcd(1, { name: "disco_escribir", arguments: "{" }, { id: "c1" }), fin("tool_calls")]));
  Object.assign(BASES, { groq: g.url });
  try {
    const r = await externo("groq/qwen/qwen3.8-27b", msgs, { env: env1, opts: rapido(), onDelta: () => {}, extra: { tools: [herramienta("github_leer"), herramienta("disco_escribir")] } });
    assert.equal(r.tool_calls.length, 2);
    assert.deepEqual(r.tools_invalidas, [{ id: "c0", nombre: "github_", motivo: "nombre_no_declarado" }, { id: "c1", nombre: "disco_escribir", motivo: "argumentos_json_incompletos" }]);
    assert.equal(r.metricas.tools_invalidas, 2);
  } finally { g.cerrar(); }
});

test("R3 sin stream (JSON completo) tambien valida los nombres declarados", async () => {
  const g = await srv(({ res }) => json(res, 200, { choices: [{ finish_reason: "tool_calls", message: { content: null, tool_calls: [{ id: "c0", type: "function", function: { name: "inventada", arguments: "{}" } }] } }] }));
  Object.assign(BASES, { groq: g.url });
  try {
    const r = await externo("groq/qwen/qwen3.8-27b", msgs, { env: env1, opts: rapido(), extra: { tools: [herramienta("github_leer")] } });
    assert.deepEqual(r.tools_invalidas.map((x) => x.motivo), ["nombre_no_declarado"]);
  } finally { g.cerrar(); }
});

// ---------- R7: precedencia de parametros (defecto del modelo primero, explicitos validos del llamador despues, limites reales del proveedor) ----------
test("R7 ajustesFinales: el defecto del modelo se aplica primero y el explicito valido del llamador manda; invalidos se ignoran y los excesos se recortan con aviso", () => {
  assert.equal(LIMITES["qwen/qwen3.8-27b"].max_tokens, 16384);  // oficial: console.groq.com/docs/model/qwen/qwen3.8-27b (MAX OUTPUT TOKENS 16,384)
  assert.deepEqual(ajustesFinales("meta/muse-glimmer-30b", {}).ajustes, { temperature: 1.0, top_p: 0.95, max_tokens: 4096 });
  const a = ajustesFinales("meta/muse-glimmer-30b", { params: { temperature: 0.2, max_tokens: 10 } });
  assert.deepEqual(a.ajustes, { temperature: 0.2, top_p: 0.95, max_tokens: 10 }); assert.equal(a.info, null);
  const b = ajustesFinales("qwen/qwen3.8-27b", { params: { max_tokens: 99999, temperature: "x", top_p: 9, reasoning_effort: "high" } });
  assert.equal(b.ajustes.max_tokens, 16384); assert.equal(b.ajustes.temperature, 1.0); assert.equal(b.ajustes.top_p, 0.95); assert.equal(b.ajustes.reasoning_effort, "high");
  assert.deepEqual(b.info, { ignorados: ["temperature", "top_p"], recortados: { max_tokens: { pedido: 99999, aplicado: 16384 } } });
  assert.deepEqual(ajustesFinales("groq/otro", { params: { temperature: 0.3 } }).ajustes, { temperature: 0.3 });  // modelo sin ajustes: solo lo explicito
});

test("R7: el cuerpo enviado al proveedor lleva el parametro explicito recortado y la metrica avisa", async () => {
  const g = await srv(({ res }) => json(res, 200, { choices: [{ finish_reason: "stop", message: { content: "ok" } }] }));
  Object.assign(BASES, { groq: g.url });
  try {
    const r = await externo("groq/qwen/qwen3.8-27b", msgs, { env: env1, opts: rapido(), extra: { params: { max_tokens: 50000, temperature: 0.4 } } });
    assert.equal(g.chat[0].body.max_tokens, 16384); assert.equal(g.chat[0].body.temperature, 0.4);
    assert.deepEqual(r.metricas.parametros.recortados.max_tokens, { pedido: 50000, aplicado: 16384 });
  } finally { g.cerrar(); }
});

// ---------- R8: tabla unica de timeouts, sin limites contradictorios ----------
test("R8: ningun timeout por defecto supera el plazo del bridge (BRIDGE_DEADLINE_MS 100 s) y el global es menor que el plazo", () => {
  assert.equal(PLAZO_BRIDGE_MS, 100000);
  assert.ok(TIMEOUT_DEFECTO_MS < PLAZO_BRIDGE_MS, "antes 120 s > 100 s: el modelo podia vivir mas que la respuesta entera");
  const r = { timeoutMs: TIMEOUT_DEFECTO_MS };
  for (const modelo of Object.keys(TIMEOUTS_DEFECTO)) assert.ok(timeoutDe(modelo, {}, r) <= PLAZO_BRIDGE_MS, modelo);
  assert.equal(timeoutDe("qwen/qwen3.8-27b", {}, r), 60000);
  assert.equal(timeoutDe("nvidia/nemotron-3-ultra-550b-a55b", {}, r), PLAZO_BRIDGE_MS);  // la tabla dice 300 s (Python); en el bridge manda el plazo de 100 s
  assert.equal(timeoutDe("modelo-desconocido", {}, r), TIMEOUT_DEFECTO_MS);
  assert.equal(timeoutDe("qwen/qwen3.8-27b", { BRIDGE_DEADLINE_MS: "40000" }, r), 40000, "el plazo del bridge configurable tambien recorta");
});

test("R8: la tabla del bridge es la misma que la de Python/politicas_modelo.json (Groq 60 s en todas partes)", () => {
  const pol = JSON.parse(fs.readFileSync(path.join(RAIZ_REPO, "router-mvp/fichas/fichas_qwen/fichas/politicas_modelo.json"), "utf8")).politicas_externos;
  const ids = MODELOS_API.filter(m => /^(groq|nvidia)\//.test(m.id)).map(m => m.id);
  assert.equal(ids.length, 5); // tabla R8 original, otros proveedores no tienen los mismos timeouts
  for (const id of ids) {
    const modelo = id.slice(id.indexOf("/") + 1);
    assert.equal(TIMEOUTS_DEFECTO[modelo], pol[id].timeout_s * 1000, id);
    assert.equal(timeoutDe(modelo, {}, { timeoutMs: TIMEOUT_DEFECTO_MS }), Math.min(pol[id].timeout_s * 1000, PLAZO_BRIDGE_MS), id);
  }
  const py = fs.readFileSync(path.join(RAIZ_REPO, "chat-router/chat/backend/mvp/compute.py"), "utf8");
  for (const id of ids) assert.match(py, new RegExp(`"${id.replace(/[.*+?^${}()|[\]\\]/g, "\\$&")}":\\s+${pol[id].timeout_s},`), `compute.py TIMEOUTS_MODELO_S ${id}`);
});

test("R8: un timeout explicito del operador (BRIDGE_RESPALDO_MS / opts) se respeta; el deadline del servidor sigue siendo el limite exterior", async () => {
  const g = await srv(({ res }) => { setTimeout(() => json(res, 200, { choices: [{ finish_reason: "stop", message: { content: "tarde" } }] }), 400); });
  Object.assign(BASES, { groq: g.url });
  try {
    await assert.rejects(externo("groq/qwen/qwen3.8-27b", msgs, { env: env1, opts: rapido({ timeoutsModelo: { "qwen/qwen3.8-27b": 100 } }) }), (e) => e.code === "EXTERNO_FALLO");
  } finally { g.cerrar(); }
});

// ---------- 148: sin Llama ----------
test("148: el catalogo del bridge conserva solo los modelos pedidos y no añade Llama; coincide con modelos.py", () => {
  assert.ok(!MODELOS_API.some((m) => /llama/i.test(m.id)));
  const py = fs.readFileSync(path.join(RAIZ_REPO, "chat-router/agentes/adaptadores/modelos.py"), "utf8");
  const ext = [...py.matchAll(/^\s+"((?:groq|nvidia)\/[^"]+)": \{"provider"/gm)].map((m) => m[1]);
  assert.deepEqual(MODELOS_API.map((m) => m.id).filter(i => /^(groq|nvidia)\//.test(i)).sort(), ext.sort());  // 163/183: una sola lista autorizada, sin contradiccion entre el bridge y el catalogo Python
});

// ---------- 152: tabla de errores (una politica distinta por familia) ----------
test("152 clasificarError: 429 limite temporal; 402 credito/cuota; 401/403 credencial; timeout/red; 5xx temporal; 400/404 peticion invalida", () => {
  const t = (x) => clasificarError(x).tipo;
  assert.equal(t(429), "limite_temporal"); assert.equal(t(402), "credito_cuota"); assert.equal(t(401), "credencial_permiso"); assert.equal(t(403), "credencial_permiso");
  assert.equal(t(408), "timeout_red"); assert.equal(clasificarError(null, { red: true }).tipo, "timeout_red");
  for (const c of [500, 502, 503, 504, 529]) assert.equal(t(c), "servidor_temporal", String(c));
  for (const c of [400, 404, 422]) assert.equal(t(c), "peticion_invalida", String(c));
  const huella = Object.values(TABLA_ERRORES).map((e) => [e.reintentar, e.rotarClave, e.respetaRetryAfter, e.enfriarClave].join());
  assert.equal(new Set(huella).size, Object.keys(TABLA_ERRORES).length, "una politica distinta por familia");
});

test("152: 402 rota a la siguiente clave sin reintentar la misma y la clave sin credito no se prueba primero en la llamada siguiente", async () => {
  const g = await srv(({ res, auth }) => auth === "Bearer gsk-FAKE-1" ? json(res, 402, { error: "sin credito" }) : json(res, 200, { choices: [{ finish_reason: "stop", message: { content: "de la 2" } }] }));
  Object.assign(BASES, { groq: g.url });
  const env = { GROQ_API_KEY: "gsk-FAKE-1", GROQ_API_KEY_2: "gsk-FAKE-2" };
  try {
    assert.equal((await externo("groq/qwen/qwen3.8-27b", msgs, { env, opts: rapido() })).salida, "de la 2");
    assert.deepEqual(g.chat.map((x) => x.auth), ["Bearer gsk-FAKE-1", "Bearer gsk-FAKE-2"]);
    await externo("groq/qwen/qwen3.8-27b", msgs, { env, opts: rapido() });
    assert.deepEqual(g.chat.slice(2).map((x) => x.auth), ["Bearer gsk-FAKE-2"], "402: clave enfriada 10 min");
  } finally { g.cerrar(); }
});

test("152: el error final lleva su familia (tipo) y el status, sin claves", async () => {
  for (const [status, tipo] of [[503, "servidor_temporal"], [400, "peticion_invalida"], [401, "credencial_permiso"], [402, "credito_cuota"], [429, "limite_temporal"]]) {
    limpiarEstado();
    const g = await srv(({ res }) => json(res, status, { error: "x" }));
    Object.assign(BASES, { groq: g.url });
    try {
      await assert.rejects(externo("groq/qwen/qwen3.8-27b", msgs, { env: env1, opts: rapido() }), (e) => e.code === "EXTERNO_FALLO" && e.tipo === tipo && e.status === status && !/gsk-FAKE/.test(e.message));
    } finally { g.cerrar(); }
  }
});

// ---------- 153-155 / 207: Retry-After, backoff+jitter, tope ----------
test("207/153: HTTP 429 con Retry-After: se espera lo indicado (con tope), la clave queda enfriada y se rota; sin Retry-After usa la espera por defecto", async () => {
  const esperas = [];
  const g = await srv(({ res, auth }) => auth === "Bearer gsk-FAKE-1" ? json(res, 429, { error: "rl" }, { "retry-after": "1" }) : json(res, 200, { choices: [{ finish_reason: "stop", message: { content: "ok" } }] }));
  Object.assign(BASES, { groq: g.url });
  try {
    await externo("groq/qwen/qwen3.8-27b", msgs, { env: { GROQ_API_KEY: "gsk-FAKE-1", GROQ_API_KEY_2: "gsk-FAKE-2" }, opts: { esperar: async (ms) => { esperas.push(ms); }, esperaMax: 5000 } });
    assert.deepEqual(esperas, [1000]);  // Retry-After: 1 s respetado (la cabecera manda sobre el defecto de 500 ms)
  } finally { g.cerrar(); }
});

test("154/155: el backoff entre claves es exponencial con jitter y los intentos estan acotados por las claves (no hay bucle infinito)", async () => {
  const esperas = [];
  const g = await srv(({ res }) => json(res, 503, { error: "x" }));
  Object.assign(BASES, { groq: g.url });
  try {
    const env = Object.fromEntries(Array.from({ length: 5 }, (_, i) => [i ? `GROQ_API_KEY_${i}` : "GROQ_API_KEY", `gsk-FAKE-${i}`]));
    await assert.rejects(externo("groq/qwen/qwen3.8-27b", msgs, { env, opts: { esperar: async (ms) => { esperas.push(ms); }, jitter: () => 1, backoffMs: 100, esperaMax: 100000 } }), (e) => e.status === 503);
    assert.equal(g.chat.length, 5, "una peticion por clave, ni una mas");
    assert.deepEqual(esperas, [100, 200, 400, 800]);  // exponencial; sin espera tras la ultima clave
    esperas.length = 0; limpiarEstado(); g.chat.length = 0;
    await assert.rejects(externo("groq/qwen/qwen3.8-27b", msgs, { env, opts: { esperar: async (ms) => { esperas.push(ms); }, jitter: () => 0, backoffMs: 100, esperaMax: 100000 } }), (e) => e.status === 503);
    assert.deepEqual(esperas, [50, 100, 200, 400]);  // jitter 0 = mitad del valor
  } finally { g.cerrar(); }
});

// ---------- R9: metricas con origen ----------
test("R9 stream: tokens del proveedor (usage) -> origen 'proveedor'; sin usage -> 'estimado' (fragmentos); duracion y TTFT presentes", async () => {
  const conUso = await srv(({ res }) => sse(res, [{ choices: [{ delta: { content: "a" } }] }, { choices: [{ delta: { content: "b" }, finish_reason: "stop" }], usage: { completion_tokens: 40, prompt_tokens: 3, total_tokens: 43 } }]));
  Object.assign(BASES, { groq: conUso.url });
  try {
    const m = (await externo("groq/qwen/qwen3.8-27b", msgs, { env: env1, opts: rapido(), onDelta: () => {} })).metricas;
    assert.equal(m.origen_tokens, "proveedor"); assert.equal(m.tokens, 40); assert.equal(m.tokens_estimado, false);
    assert.ok(m.ttft_ms >= 0 && m.total_ms >= m.ttft_ms);
  } finally { conUso.cerrar(); }
  const sinUso = await srv(({ res }) => sse(res, [{ choices: [{ delta: { content: "a" } }] }, { choices: [{ delta: { content: "b" }, finish_reason: "stop" }] }]));
  Object.assign(BASES, { groq: sinUso.url });
  try {
    const m = (await externo("groq/qwen/qwen3.8-27b", msgs, { env: env1, opts: rapido(), onDelta: () => {} })).metricas;
    assert.equal(m.origen_tokens, "estimado"); assert.equal(m.tokens_estimado, true);
  } finally { sinUso.cerrar(); }
});

test("R9 sin stream: duracion, tokens del proveedor y tokens/s calculados; TTFT no aplica; sin usage no se inventan tokens", async () => {
  const g = await srv(({ res }) => json(res, 200, { choices: [{ finish_reason: "stop", message: { content: "ok" } }], usage: { completion_tokens: 20, prompt_tokens: 2, total_tokens: 22 } }));
  Object.assign(BASES, { groq: g.url });
  try {
    const m = (await externo("groq/qwen/qwen3.8-27b", msgs, { env: env1, opts: rapido() })).metricas;
    assert.equal(m.stream, false); assert.equal(m.tokens, 20); assert.equal(m.origen_tokens, "proveedor"); assert.equal(m.ttft_ms, null); assert.ok(m.total_ms >= 0);
    assert.ok(m.tokens_s === null || m.tokens_s > 0);
  } finally { g.cerrar(); }
  const h = await srv(({ res }) => json(res, 200, { choices: [{ finish_reason: "stop", message: { content: "ok" } }] }));
  Object.assign(BASES, { groq: h.url });
  try {
    const m = (await externo("groq/qwen/qwen3.8-27b", msgs, { env: env1, opts: rapido() })).metricas;
    assert.equal(m.tokens, null); assert.equal(m.origen_tokens, null); assert.equal(m.tokens_s, null);
  } finally { h.cerrar(); }
});

// ---------- 156-161: cambio de proveedor visible, sin perder ni repetir llamadas ----------
test("156-161: si Groq cae a mitad de una llamada a herramienta, NVIDIA entrega las tool_calls COMPLETAS una sola vez y el cambio queda a la vista (via, usado, intentos)", async () => {
  const groq = await srv(({ res }) => { res.writeHead(200, { "content-type": "text/event-stream" }); res.write(ev(tcd(0, { name: "github_", arguments: "" }, { id: "c0" }))); setTimeout(() => res.destroy(), 20); });
  const nvidia = await srv(({ res }) => sse(res, [tcd(0, { name: "github_leer", arguments: '{"ruta":"a"}' }, { id: "n0" }), fin("tool_calls")]));
  Object.assign(BASES, { groq: groq.url, nvidia: nvidia.url });
  const inicios = [];
  try {
    const r = await respaldo(msgs, { env: { GROQ_API_KEY: "gsk-FAKE-1", NVIDIA_API_KEY: "nv-FAKE-1" }, opts: rapido(), onDelta: () => {}, onInicio: (i) => inicios.push(i), extra: { tools: [herramienta("github_leer")] } });
    assert.equal(r.via, "nvidia"); assert.match(r.usado, /^nvidia\//);
    assert.deepEqual(r.tool_calls.map((t) => [t.id, t.function.name, t.function.arguments]), [["n0", "github_leer", '{"ruta":"a"}']]);  // ni perdida ni duplicada: la de Groq nunca se entrego (estaba incompleta)
    assert.deepEqual(inicios.map((i) => i.via), ["groq", "nvidia"], "onInicio avisa de CADA proveedor intentado: el cambio no se oculta");
    assert.deepEqual(r.intentos.map((x) => [x.via, x.ok]), [["groq", false], ["nvidia", true]]);
    assert.equal(r.intentos[0].tipo, "timeout_red"); assert.ok(!JSON.stringify(r.intentos).includes("gsk-FAKE"));
    assert.equal(nvidia.chat.length, 1, "la operacion externa (la peticion al proveedor de respaldo) se hace una sola vez");
  } finally { groq.cerrar(); nvidia.cerrar(); }
});

test("157/160: respaldo() siempre devuelve el proveedor y el modelo realmente usados, incluso sin cambio", async () => {
  const g = await srv(({ res }) => json(res, 200, { choices: [{ finish_reason: "stop", message: { content: "ok" } }] }));
  Object.assign(BASES, { groq: g.url });
  try {
    const r = await respaldo(msgs, { env: env1, opts: rapido() });
    assert.equal(r.via, "groq"); assert.equal(r.usado, "groq/qwen/qwen3.8-27b"); assert.deepEqual(r.intentos.map((x) => [x.via, x.ok]), [["groq", true]]);
  } finally { g.cerrar(); }
});

// ---------- 184: catalogo en cache con TTL controlado ----------
test("184: GET /models se cachea por TTL (cacheMs) y vuelve a consultarse al vencer; un fallo del proveedor se recuerda poco (cacheFalloMs)", async () => {
  let n = 0;
  const g = await srv(({ res, url }) => { if (url.endsWith("/models")) { n++; return json(res, 200, { data: [{ id: "qwen/qwen3.8-27b" }] }); } json(res, 200, {}); });
  Object.assign(BASES, { groq: g.url });
  let t = 1000;
  const opts = { ahora: () => t, cacheMs: 5000 };
  try {
    const a = await disponibilidad({ env: env1, opts });
    assert.equal(a.find((m) => m.id === "groq/qwen/qwen3.8-27b").estado, "DISPONIBLE");
    await disponibilidad({ env: env1, opts }); assert.equal(n, 1, "dentro del TTL no se vuelve a consultar");
    t += 4999; await disponibilidad({ env: env1, opts }); assert.equal(n, 1);
    t += 2; await disponibilidad({ env: env1, opts }); assert.equal(n, 2, "vencido el TTL se consulta de nuevo");
  } finally { g.cerrar(); }
});

test("R6/190: si GET /models falla el modelo queda SIN VERIFICAR (nunca DISPONIBLE) y no se cambia por otro", async () => {
  const g = await srv(({ res }) => json(res, 503, { error: "x" }));
  Object.assign(BASES, { groq: g.url, nvidia: g.url });
  try {
    const d = await disponibilidad({ env: { ...env1, NVIDIA_API_KEY: "nv-FAKE-1" } });
    for (const m of d) { assert.equal(m.estado, "SIN VERIFICAR"); assert.equal(m.disponible, null); }
  } finally { g.cerrar(); }
});

// ---------- 192: observabilidad sin credenciales ----------
test("192: estadoMetricas y los errores solo llevan numeros/ids: ninguna clave", async () => {
  const g = await srv(({ res }) => sse(res, [{ choices: [{ delta: { content: "a" }, finish_reason: "stop" }], usage: { completion_tokens: 3 } }]));
  Object.assign(BASES, { groq: g.url });
  try {
    await externo("groq/qwen/qwen3.8-27b", msgs, { env: { GROQ_API_KEY: "gsk-SECRETA-123456" }, opts: rapido(), onDelta: () => {} });
    const e = estadoMetricas()["groq/qwen/qwen3.8-27b"];
    assert.ok(e.llamadas === 1 && e.ttft_ms !== undefined && e.tokens_s !== undefined);
    assert.ok(!JSON.stringify(estadoMetricas()).includes("SECRETA"));
  } finally { g.cerrar(); }
  const h = await srv(({ res }) => json(res, 400, { error: "bad gsk-SECRETA-123456" }));
  Object.assign(BASES, { groq: h.url });
  try { await assert.rejects(externo("groq/qwen/qwen3.8-27b", msgs, { env: { GROQ_API_KEY: "gsk-SECRETA-123456" }, opts: rapido() }), (e) => !e.message.includes("SECRETA")); } finally { h.cerrar(); }
});
