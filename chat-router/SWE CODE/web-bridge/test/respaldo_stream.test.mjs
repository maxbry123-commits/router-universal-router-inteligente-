// Streaming real de Groq/NVIDIA en respaldo.js: stream:true, fragmentos por callback, tool_calls por indice, TTFT/tokens/s,
// keep-alive, continuacion sin duplicar texto, AJUSTES por modelo, backoff con jitter, timeout por modelo y disponibilidad (GET /models).
// Todo contra servidores node:http locales y claves FALSAS (nunca reales, sin red externa).
import test from "node:test";
import assert from "node:assert/strict";
import http from "node:http";
import { respaldo, externo, local, BASES, MODELOS_API, AJUSTES, setClaves, limpiarClaves, limpiarEstado, estadoMetricas, disponibilidad } from "../src/respaldo.js";

const msgs = [{ role: "user", content: "hola" }];
const CONT = "Continúa exactamente donde terminó, sin repetir";
const rapido = (extra = {}) => ({ esperar: async () => {}, ...extra });
const espera = (ms) => new Promise((r) => setTimeout(r, ms));
const delta = (content, extra = {}) => ({ choices: [{ index: 0, delta: { content }, finish_reason: null }], ...extra });
const fin = (finish_reason, extra = {}) => ({ choices: [{ index: 0, delta: {}, finish_reason }], ...extra });
const ev = (o) => `data: ${typeof o === "string" ? o : JSON.stringify(o)}\n\n`;

// handler({ body, n, auth, url, req, res, conexion }) -> escribe en res; devuelve true si el ya respondio.
// por defecto (sin stream en el cuerpo) contesta JSON; con stream:true el handler decide.
const srv = (handler) => new Promise((listo) => {
  const vistos = [], chat = []; let n = 0, conexiones = 0;
  const s = http.createServer((req, res) => {
    let d = ""; req.on("data", (c) => d += c); req.on("end", () => {
      const v = { method: req.method, url: req.url, auth: req.headers.authorization, body: d ? JSON.parse(d) : null };
      vistos.push(v); if (v.url.endsWith("/chat/completions")) { chat.push(v); n++; }
      handler({ ...v, n, req, res });
    });
  });
  s.on("connection", () => { conexiones++; });
  s.listen(0, "127.0.0.1", () => listo({ s, vistos, chat, conexiones: () => conexiones, url: `http://127.0.0.1:${s.address().port}`, cerrar: () => { s.closeAllConnections?.(); s.close(); } }));
});
const sseHead = (res, extra = {}) => res.writeHead(200, { "content-type": "text/event-stream", "cache-control": "no-cache", ...extra });
const json = (res, status, o, headers = {}) => { res.writeHead(status, { "content-type": "application/json", ...headers }); res.end(JSON.stringify(o)); };
const sseCompleto = (res, eventos) => { sseHead(res); for (const e of eventos) res.write(ev(e)); res.end(ev("[DONE]")); };
const env1 = { GROQ_API_KEY: "gsk-FAKE-1" };
const recolector = () => { const partes = []; return { partes, onDelta: (t) => partes.push(t), texto: () => partes.join("") }; };

test.beforeEach(() => { limpiarEstado(); limpiarClaves(); });

// ---------- AJUSTES por modelo (pedir) ----------
test("AJUSTES: cada modelo manda sus parametros (temperature, top_p, max_tokens, reasoning_*) y los desconocidos no mandan nada", async () => {
  assert.deepEqual(AJUSTES["qwen/qwen3.8-27b"], { temperature: 1.0, top_p: 0.95, max_tokens: 2048, reasoning_effort: "medium", reasoning_format: "hidden" });
  assert.deepEqual(AJUSTES["minimaxai/minimax-m3.1-flash"], { temperature: 1.0, top_p: 0.95, max_tokens: 4096 });
  assert.deepEqual(AJUSTES["meta/muse-glimmer-30b"], { temperature: 1.0, top_p: 0.95, max_tokens: 4096 });
  assert.deepEqual(AJUSTES["nvidia/nemotron-3-ultra-550b-a55b"], { temperature: 1.0, top_p: 0.95, max_tokens: 4096 });
  assert.deepEqual(AJUSTES["z-ai/glm-5.3"], { temperature: 0.5, top_p: 1.0, max_tokens: 4096 });
  const g = await srv(({ res }) => json(res, 200, { choices: [{ finish_reason: "stop", message: { content: "ok" } }] }));
  Object.assign(BASES, { groq: g.url, nvidia: g.url });
  const tools = [{ type: "function", function: { name: "f", parameters: { type: "object" } } }];
  try {
    await externo("groq/qwen/qwen3.8-27b", msgs, { env: env1, opts: rapido() });
    await externo("nvidia/z-ai/glm-5.3", msgs, { env: { NVIDIA_API_KEY: "nv-FAKE-1" }, extra: { tools }, opts: rapido() });
    await externo("groq/otro-modelo", msgs, { env: env1, opts: rapido() });
    const [a, b, c] = g.chat.map((x) => x.body);
    assert.equal(a.model, "qwen/qwen3.8-27b"); assert.equal(a.reasoning_effort, "medium"); assert.equal(a.reasoning_format, "hidden"); assert.equal(a.max_tokens, 2048); assert.equal(a.temperature, 1.0); assert.equal(a.top_p, 0.95);
    assert.ok(!("stream" in a), "sin callback no se pide stream");
    assert.equal(b.model, "z-ai/glm-5.3"); assert.equal(b.temperature, 0.5); assert.equal(b.top_p, 1.0); assert.equal(b.max_tokens, 4096);
    assert.deepEqual(b.tools, tools); assert.equal(b.tool_choice, "auto");
    assert.deepEqual(Object.keys(c).sort(), ["messages", "model"], "modelo sin AJUSTES: solo model y messages");
  } finally { g.cerrar(); }
});

// ---------- streaming real ----------
test("stream real: pide stream:true con AJUSTES y entrega cada fragmento por callback ANTES de que termine la respuesta", async () => {
  let soltar; const puerta = new Promise((r) => { soltar = r; });
  const g = await srv(({ res }) => { sseHead(res); res.write(ev(delta("Hola "))); puerta.then(() => { res.write(ev(delta("mundo"))); res.write(ev(fin("stop"))); res.end(ev("[DONE]")); }); });
  Object.assign(BASES, { groq: g.url });
  const rc = recolector(); let primero;
  const vistoPrimero = new Promise((r) => { primero = r; });
  const p = externo("groq/qwen/qwen3.8-27b", msgs, { env: env1, opts: rapido(), onDelta: (t) => { rc.onDelta(t); primero(); } });
  try {
    await vistoPrimero;   // llega el primer fragmento mientras el servidor aun no cerro el stream
    assert.deepEqual(rc.partes, ["Hola "]); soltar();
    const r = await p;
    assert.deepEqual(rc.partes, ["Hola ", "mundo"]); assert.equal(r.salida, "Hola mundo"); assert.equal(r.finish_reason, "stop"); assert.equal(r.via, "groq");
    assert.equal(g.chat[0].body.stream, true); assert.equal(g.chat[0].body.reasoning_format, "hidden");
    assert.equal(g.chat[0].auth, "Bearer gsk-FAKE-1");
  } finally { soltar(); g.cerrar(); }
});

test("stream: tool_calls reconstruidos por indice (fragmentos intercalados), finish_reason tool_calls, sin texto de argumentos por el callback", async () => {
  const tc = (index, extra) => ({ choices: [{ index: 0, delta: { tool_calls: [{ index, ...extra }] }, finish_reason: null }] });
  const g = await srv(({ res }) => sseCompleto(res, [
    delta("Voy a leer. "),
    tc(0, { id: "call_a", type: "function", function: { name: "github_leer", arguments: "" } }),
    tc(1, { id: "call_b", type: "function", function: { name: "listar", arguments: "{\"d" } }),
    tc(0, { function: { arguments: "{\"ruta\":" } }),
    tc(1, { function: { arguments: "ir\":\".\"}" } }),
    tc(0, { function: { arguments: "\"README.md\"}" } }),
    fin("tool_calls"),
  ]));
  Object.assign(BASES, { groq: g.url });
  const rc = recolector();
  try {
    const r = await externo("groq/m", msgs, { env: env1, opts: rapido(), onDelta: rc.onDelta, extra: { tools: [{ type: "function", function: { name: "github_leer" } }] } });
    assert.equal(rc.texto(), "Voy a leer. "); assert.equal(r.salida, "Voy a leer. ");
    assert.equal(r.finish_reason, "tool_calls"); assert.equal(g.chat.length, 1, "tool_calls nunca se continua");
    assert.deepEqual(r.tool_calls, [
      { id: "call_a", type: "function", function: { name: "github_leer", arguments: "{\"ruta\":\"README.md\"}" } },
      { id: "call_b", type: "function", function: { name: "listar", arguments: "{\"dir\":\".\"}" } },
    ]);
    assert.doesNotThrow(() => r.tool_calls.forEach((t) => JSON.parse(t.function.arguments)));
    assert.equal(g.chat[0].body.tool_choice, "auto");
  } finally { g.cerrar(); }
});

test("stream: nombre de funcion repetido en cada fragmento no se duplica; argumentos vacios se normalizan a {}", async () => {
  const tc = (extra) => ({ choices: [{ delta: { tool_calls: [{ index: 0, ...extra }] }, finish_reason: null }] });
  const g = await srv(({ res }) => sseCompleto(res, [tc({ id: "c1", function: { name: "hora", arguments: "" } }), tc({ function: { name: "hora", arguments: "" } }), fin("stop")]));
  Object.assign(BASES, { groq: g.url });
  try {
    const r = await externo("groq/m", msgs, { env: env1, opts: rapido(), onDelta: () => {} });
    assert.equal(r.tool_calls.length, 1); assert.equal(r.tool_calls[0].function.name, "hora"); assert.equal(r.tool_calls[0].function.arguments, "{}");
    assert.equal(r.finish_reason, "tool_calls", "con tool_calls el finish_reason es tool_calls aunque el proveedor diga stop");
  } finally { g.cerrar(); }
});

test("stream: finish_reason=length continua solo (nueva peticion stream con el parcial) y el texto no se duplica", async () => {
  const g = await srv(({ res, n }) => sseCompleto(res, n === 1 ? [delta("AAA"), delta("BBB"), fin("length")] : [delta("CCC"), fin("stop")]));
  Object.assign(BASES, { groq: g.url });
  const rc = recolector();
  try {
    const r = await externo("groq/m", msgs, { env: env1, opts: rapido(), onDelta: rc.onDelta });
    assert.equal(rc.texto(), "AAABBBCCC"); assert.equal(r.salida, "AAABBBCCC"); assert.equal(r.finish_reason, "stop");
    assert.deepEqual(g.chat[1].body.messages.slice(-2), [{ role: "assistant", content: "AAABBB" }, { role: "user", content: CONT }]);
    assert.equal(g.chat[1].body.stream, true);
  } finally { g.cerrar(); }
});

test("stream cortado a mitad (sin finish_reason ni [DONE]): la SIGUIENTE clave continua desde lo ya entregado, sin repetirlo", async () => {
  const g = await srv(({ res, auth }) => {
    if (auth === "Bearer gsk-FAKE-1") { sseHead(res); res.write(ev(delta("AAA"))); setTimeout(() => res.destroy(), 20); return; }
    sseCompleto(res, [delta("BBB"), fin("stop")]);
  });
  Object.assign(BASES, { groq: g.url });
  const rc = recolector();
  try {
    const r = await externo("groq/m", msgs, { env: { ...env1, GROQ_API_KEY_2: "gsk-FAKE-2" }, opts: rapido(), onDelta: rc.onDelta });
    assert.equal(rc.texto(), "AAABBB", "AAA se entrego una sola vez"); assert.equal(r.salida, "AAABBB");
    assert.deepEqual(g.chat.map((c) => c.auth), ["Bearer gsk-FAKE-1", "Bearer gsk-FAKE-2"]);
    assert.deepEqual(g.chat[1].body.messages.slice(-2), [{ role: "assistant", content: "AAA" }, { role: "user", content: CONT }]);
  } finally { g.cerrar(); }
});

test("stream que termina limpio pero sin finish_reason ni [DONE] se trata como corte y rota de clave", async () => {
  const g = await srv(({ res, auth }) => { if (auth === "Bearer gsk-FAKE-1") { sseHead(res); res.end(ev(delta("X"))); return; } sseCompleto(res, [delta("Y"), fin("stop")]); });
  Object.assign(BASES, { groq: g.url });
  const rc = recolector();
  try {
    const r = await externo("groq/m", msgs, { env: { ...env1, GROQ_API_KEY_2: "gsk-FAKE-2" }, opts: rapido(), onDelta: rc.onDelta });
    assert.equal(r.salida, "XY"); assert.equal(rc.texto(), "XY");
  } finally { g.cerrar(); }
});

test("failover entre proveedores con stream: Groq muere tras emitir texto -> NVIDIA continua; lo emitido NO se repite y el flujo suma todo", async () => {
  const g = await srv(({ res, url }) => { if (url.endsWith("/models")) return json(res, 200, { data: [] }); sseHead(res); res.write(ev(delta("Parte uno. "))); setTimeout(() => res.destroy(), 20); });
  const n = await srv(({ res, url }) => { if (url.endsWith("/models")) return json(res, 200, { data: [] }); sseCompleto(res, [delta("Parte dos."), fin("stop")]); });
  Object.assign(BASES, { groq: g.url, nvidia: n.url });
  const rc = recolector(), flujo = { texto: "" }, inicios = [];
  try {
    const r = await respaldo(msgs, { env: { ...env1, NVIDIA_API_KEY: "nv-FAKE-1" }, opts: rapido(), onDelta: rc.onDelta, flujo, onInicio: (i) => inicios.push(i.via) });
    assert.equal(rc.texto(), "Parte uno. Parte dos."); assert.equal(r.salida, "Parte uno. Parte dos."); assert.equal(flujo.texto, r.salida);
    assert.equal(r.via, "nvidia");
    assert.deepEqual(n.chat[0].body.messages.slice(-2), [{ role: "assistant", content: "Parte uno. " }, { role: "user", content: CONT }]);
    assert.deepEqual(inicios, ["groq", "nvidia"]);
  } finally { g.cerrar(); n.cerrar(); }
});

test("failover a HF local tras texto emitido: local (sin stream) continua con el parcial y devuelve el texto completo; el callback no se invoca", async () => {
  const g = await srv(({ res, url }) => { if (url.endsWith("/models")) return json(res, 404, {}); sseHead(res); res.write(ev(delta("AAA"))); setTimeout(() => res.destroy(), 20); });
  const l = await srv(({ res }) => json(res, 200, { choices: [{ finish_reason: "stop", message: { content: "BBB" } }] }));
  Object.assign(BASES, { groq: g.url, nvidia: "http://127.0.0.1:9" });
  const rc = recolector(), flujo = { texto: "" };
  try {
    const r = await respaldo(msgs, { env: { ...env1, SWECODE_URL_S1: l.url }, opts: rapido(), onDelta: rc.onDelta, flujo });
    assert.equal(rc.texto(), "AAA", "solo lo del stream real pasa por el callback"); assert.equal(flujo.texto, "AAA");
    assert.equal(r.salida, "AAABBB"); assert.equal(r.via, "hf-local");
    assert.ok(!("stream" in l.chat[0].body), "la cola HF no recibe stream");
    assert.deepEqual(l.chat[0].body.messages.slice(-2), [{ role: "assistant", content: "AAA" }, { role: "user", content: CONT }]);
  } finally { g.cerrar(); l.cerrar(); }
});

test("429 antes de abrir el stream: Retry-After respetado (tope), clave enfriada y rota a la siguiente sin emitir nada", async () => {
  const g = await srv(({ res, auth }) => auth === "Bearer gsk-FAKE-1" ? json(res, 429, {}, { "retry-after": "30" }) : sseCompleto(res, [delta("de la 2"), fin("stop")]));
  Object.assign(BASES, { groq: g.url });
  const esperas = []; let t = 1_000_000; const rc = recolector();
  const opts = { esperar: async (ms) => { esperas.push(ms); }, ahora: () => t, cooldownMs: 60_000, esperaMax: 2000 };
  const env = { ...env1, GROQ_API_KEY_2: "gsk-FAKE-2" };
  try {
    const r = await externo("groq/m", msgs, { env, opts, onDelta: rc.onDelta });
    assert.equal(r.salida, "de la 2"); assert.deepEqual(esperas, [2000]);
    g.chat.length = 0; t += 30_000;
    await externo("groq/m", msgs, { env, opts, onDelta: () => {} });
    assert.deepEqual(g.chat.map((c) => c.auth), ["Bearer gsk-FAKE-2"], "dentro del cooldown la clave 1 ni se toca");
  } finally { g.cerrar(); }
});

test("timeout de inactividad en el stream: si el proveedor se calla tras emitir, NO rota de clave: enfria el proveedor y el texto emitido queda en parcial/flujo", async () => {
  const g = await srv(({ res, auth }) => { if (auth === "Bearer gsk-FAKE-1") { sseHead(res); res.write(ev(delta("AA"))); return; } sseCompleto(res, [delta("BB"), fin("stop")]); });
  Object.assign(BASES, { groq: g.url });
  const rc = recolector();
  try {
    await assert.rejects(() => externo("groq/m", msgs, { env: { ...env1, GROQ_API_KEY_2: "gsk-FAKE-2" }, opts: rapido({ timeoutMs: 120 }), onDelta: rc.onDelta }), (e) => e.code === "EXTERNO_FALLO" && e.parcial === "AA");
    assert.equal(rc.texto(), "AA"); assert.equal(g.chat.length, 1, "la clave 2 no se prueba");
  } finally { g.cerrar(); }
});

test("proveedor que ignora stream y contesta JSON: se entrega entero por el callback y el resultado es el mismo", async () => {
  const g = await srv(({ res }) => json(res, 200, { choices: [{ finish_reason: "stop", message: { content: "respuesta entera" } }] }));
  Object.assign(BASES, { groq: g.url });
  const rc = recolector();
  try {
    const r = await externo("groq/m", msgs, { env: env1, opts: rapido(), onDelta: rc.onDelta });
    assert.deepEqual(rc.partes, ["respuesta entera"]); assert.equal(r.salida, "respuesta entera"); assert.equal(r.finish_reason, "stop");
  } finally { g.cerrar(); }
});

test("JSON de proveedor con tool_calls (sin SSE) tambien se devuelve completo", async () => {
  const tc = [{ id: "c1", type: "function", function: { name: "f", arguments: "{}" } }];
  const g = await srv(({ res }) => json(res, 200, { choices: [{ finish_reason: "tool_calls", message: { content: null, tool_calls: tc } }] }));
  Object.assign(BASES, { groq: g.url });
  try {
    const r = await externo("groq/m", msgs, { env: env1, opts: rapido(), onDelta: () => {} });
    assert.deepEqual(r.tool_calls, tc); assert.equal(r.finish_reason, "tool_calls"); assert.equal(r.salida, "");
  } finally { g.cerrar(); }
});

test("parser SSE: eventos partidos en cualquier byte, CRLF, comentarios, lineas vacias y multibyte (emoji/ñ) partidos entre paquetes", async () => {
  const bytes = Buffer.from(": hola\r\n\r\n" + ev(delta("ñandú 😀 ")) .replace(/\n/g, "\r\n") + ev(delta("fin")) + ev(fin("stop")) + ev("[DONE]"));
  const g = await srv(({ res }) => { sseHead(res); let i = 0; const t = setInterval(() => { if (i >= bytes.length) { clearInterval(t); return res.end(); } res.write(bytes.subarray(i, i + 3)); i += 3; }, 1); });
  Object.assign(BASES, { groq: g.url });
  const rc = recolector();
  try {
    const r = await externo("groq/m", msgs, { env: env1, opts: rapido(), onDelta: rc.onDelta });
    assert.equal(rc.texto(), "ñandú 😀 fin"); assert.equal(r.salida, "ñandú 😀 fin"); assert.ok(rc.partes.every((p) => !p.includes("�")));
  } finally { g.cerrar(); }
});

test("error dentro del stream ({error}) o HTTP 5xx antes: rota de clave", async () => {
  const g = await srv(({ res, auth }) => {
    if (auth === "Bearer gsk-FAKE-1") return json(res, 503, {});
    if (auth === "Bearer gsk-FAKE-2") return sseCompleto(res, [{ error: { message: "boom gsk-FAKE-2", code: 500 } }]);
    sseCompleto(res, [delta("ok3"), fin("stop")]);
  });
  Object.assign(BASES, { groq: g.url });
  try {
    const r = await externo("groq/m", msgs, { env: { ...env1, GROQ_API_KEY_2: "gsk-FAKE-2", GROQ_API_KEY_3: "gsk-FAKE-3" }, opts: rapido(), onDelta: () => {} });
    assert.equal(r.salida, "ok3"); assert.equal(g.chat.length, 3);
  } finally { g.cerrar(); }
});

test("stream agotado: el error no contiene claves y conserva lo emitido en flujo", async () => {
  const g = await srv(({ res, auth }) => { sseHead(res); res.write(ev(delta("PARCIAL"))); res.write(ev({ error: { message: `eco ${auth}` } })); res.end(); });
  Object.assign(BASES, { groq: g.url });
  const flujo = { texto: "" };
  try {
    await assert.rejects(() => externo("groq/m", msgs, { env: { GROQ_API_KEY: "gsk-FAKE-SECRETA" }, opts: rapido(), onDelta: () => {}, flujo }), (e) => e.code === "EXTERNO_FALLO" && !e.message.includes("gsk-FAKE-SECRETA"));
    assert.equal(flujo.texto, "PARCIAL");
  } finally { g.cerrar(); }
});

test("keep-alive: dos streams seguidos reutilizan la MISMA conexion TCP", async () => {
  const g = await srv(({ res }) => sseCompleto(res, [delta("x"), fin("stop")]));
  Object.assign(BASES, { groq: g.url });
  try {
    await externo("groq/m", msgs, { env: env1, opts: rapido(), onDelta: () => {} });
    await espera(20);
    await externo("groq/m", msgs, { env: env1, opts: rapido(), onDelta: () => {} });
    await externo("groq/m", msgs, { env: env1, opts: rapido(), onDelta: () => {} });
    assert.equal(g.chat.length, 3); assert.equal(g.conexiones(), 1, "una sola conexion TCP reutilizada");
  } finally { g.cerrar(); }
});

test("metricas: TTFT y tokens/s con usage del proveedor; sin usage se estiman por fragmentos; estadoMetricas las resume sin claves", async () => {
  const g = await srv(({ res }) => { sseHead(res); setTimeout(() => { res.write(ev(delta("a"))); }, 60); setTimeout(() => { res.write(ev(delta("b"))); }, 120); setTimeout(() => { res.write(ev(fin("stop", { usage: { completion_tokens: 40, prompt_tokens: 5 } }))); res.end(ev("[DONE]")); }, 180); });
  Object.assign(BASES, { groq: g.url });
  try {
    const r = await externo("groq/qwen/qwen3.8-27b", msgs, { env: env1, opts: rapido(), onDelta: () => {} });
    const m = r.metricas;
    assert.equal(m.stream, true); assert.ok(m.ttft_ms >= 40 && m.ttft_ms < 1000, `ttft ${m.ttft_ms}`);
    assert.equal(m.tokens, 40); assert.equal(m.tokens_estimado, false); assert.ok(m.tokens_s > 0 && Number.isFinite(m.tokens_s));
    assert.ok(m.total_ms >= m.ttft_ms);
    const e = estadoMetricas(); const k = e["groq/qwen/qwen3.8-27b"];
    assert.equal(k.llamadas, 1); assert.ok(k.ttft_ms > 0 && k.ttft_prom_ms > 0 && k.tokens_s > 0);
    assert.ok(!JSON.stringify(e).includes("gsk-"));
  } finally { g.cerrar(); }
  const g2 = await srv(({ res }) => sseCompleto(res, [delta("a"), delta("b"), delta("c"), fin("stop")]));
  Object.assign(BASES, { groq: g2.url });
  try {
    const r = await externo("groq/m2", msgs, { env: env1, opts: rapido(), onDelta: () => {} });
    assert.equal(r.metricas.tokens, 3); assert.equal(r.metricas.tokens_estimado, true);
  } finally { g2.cerrar(); }
});

test("sin callback: ruta NO stream de siempre (sin stream en el cuerpo) y metricas basicas", async () => {
  const g = await srv(({ res }) => json(res, 200, { choices: [{ finish_reason: "stop", message: { content: "plano" } }] }));
  Object.assign(BASES, { groq: g.url });
  try {
    const r = await externo("groq/m", msgs, { env: env1, opts: rapido() });
    assert.equal(r.salida, "plano"); assert.ok(!("stream" in g.chat[0].body));
    assert.equal(r.metricas.stream, false); assert.ok(r.metricas.total_ms >= 0);
  } finally { g.cerrar(); }
});

test("abortar (cliente desconectado): signal cancela el stream y NO sigue rotando claves", async () => {
  const g = await srv(({ res }) => { sseHead(res); res.write(ev(delta("lento"))); });
  Object.assign(BASES, { groq: g.url });
  const ac = new AbortController(); const rc = recolector();
  const p = externo("groq/m", msgs, { env: { ...env1, GROQ_API_KEY_2: "gsk-FAKE-2" }, opts: rapido({ signal: ac.signal }), onDelta: (t) => { rc.onDelta(t); ac.abort(); } });
  try {
    await assert.rejects(p, (e) => e.code === "EXTERNO_FALLO" || e.code === "ABORTADO");
    assert.equal(g.chat.length, 1, "una sola peticion: no se prueba la otra clave");
  } finally { g.cerrar(); }
});

// ---------- backoff con jitter / timeouts ----------
test("backoff exponencial con jitter entre claves ante 5xx (no tras la ultima); 429 sigue usando Retry-After", async () => {
  const g = await srv(({ res, n }) => n < 4 ? json(res, 503, {}) : json(res, 200, { choices: [{ finish_reason: "stop", message: { content: "ok" } }] }));
  Object.assign(BASES, { groq: g.url });
  const esperas = [];
  const env = { GROQ_API_KEY: "gsk-FAKE-1", GROQ_API_KEY_2: "gsk-FAKE-2", GROQ_API_KEY_3: "gsk-FAKE-3", GROQ_API_KEY_4: "gsk-FAKE-4" };
  try {
    const r = await externo("groq/m", msgs, { env, opts: { esperar: async (ms) => esperas.push(ms), jitter: () => 1, backoffMs: 100, esperaMax: 2000 } });
    assert.equal(r.salida, "ok"); assert.deepEqual(esperas, [100, 200, 400]);
    limpiarEstado(); esperas.length = 0; g.chat.length = 0;
    const g2 = await srv(({ res }) => json(res, 500, {}));
    Object.assign(BASES, { groq: g2.url });
    await assert.rejects(() => externo("groq/m", msgs, { env, opts: { esperar: async (ms) => esperas.push(ms), jitter: () => 0, backoffMs: 100, esperaMax: 2000 } }));
    assert.equal(esperas.length, 3, "3 esperas para 4 claves: ninguna tras la ultima"); assert.deepEqual(esperas, [50, 100, 200], "jitter 0 = mitad del backoff");
    g2.cerrar();
  } finally { g.cerrar(); }
});

test("timeout configurable por modelo (opts.timeoutsModelo y env RIU_SWE_TIMEOUTS) distinto del global", async () => {
  const g = await srv(() => {});  // nunca contesta
  Object.assign(BASES, { groq: g.url });
  try {
    let t0 = Date.now();
    await assert.rejects(() => externo("groq/lento", msgs, { env: env1, opts: rapido({ timeoutMs: 5000, timeoutsModelo: { lento: 60 } }) }));
    assert.ok(Date.now() - t0 < 2000, "uso el timeout del modelo (60 ms), no el global");
    t0 = Date.now();
    await assert.rejects(() => externo("groq/qwen/qwen3.8-27b", msgs, { env: { ...env1, RIU_SWE_TIMEOUTS: JSON.stringify({ "qwen/qwen3.8-27b": 70 }) }, opts: rapido({ timeoutMs: 5000 }), onDelta: () => {} }));
    assert.ok(Date.now() - t0 < 2000, "env RIU_SWE_TIMEOUTS por modelo tambien en stream");
    t0 = Date.now();
    await assert.rejects(() => externo("groq/otro", msgs, { env: { ...env1, RIU_SWE_TIMEOUTS: "no-es-json" }, opts: rapido({ timeoutMs: 90 }) }));
    assert.ok(Date.now() - t0 < 2000, "env invalido se ignora y manda el global");
  } finally { g.cerrar(); }
});

// ---------- seleccion de modelo contra GET /models ----------
const modelos = (ids) => ({ data: ids.map((id) => ({ id })) });
test("Groq: si /models trae el id exacto qwen/qwen3.8-27b se usa ese aunque otro qwen3.8 venga antes", async () => {
  const g = await srv(({ res, url }) => url.endsWith("/models") ? json(res, 200, modelos(["qwen-3.8-x", "qwen/qwen3.8-27b"])) : json(res, 200, { choices: [{ finish_reason: "stop", message: { content: "ok" } }] }));
  Object.assign(BASES, { groq: g.url });
  try { await respaldo(msgs, { env: env1, opts: rapido() }); assert.equal(g.chat[0].body.model, "qwen/qwen3.8-27b"); } finally { g.cerrar(); }
});

test("NVIDIA: id exacto minimaxai/minimax-m3.1-flash antes que otro minimax/kimi; si falta, otro id autorizado presente; si ninguno, el por defecto", async () => {
  const con = async (ids) => {
    limpiarEstado();
    const n = await srv(({ res, url }) => url.endsWith("/models") ? json(res, 200, modelos(ids)) : json(res, 200, { choices: [{ finish_reason: "stop", message: { content: "ok" } }] }));
    Object.assign(BASES, { groq: "http://127.0.0.1:9", nvidia: n.url });
    try { await respaldo(msgs, { env: { NVIDIA_API_KEY: "nv-FAKE-1" }, opts: rapido() }); return n.chat[0].body.model; } finally { n.cerrar(); }
  };
  assert.equal(await con(["moonshotai/kimi-k2", "minimaxai/minimax-m3.1-flash"]), "minimaxai/minimax-m3.1-flash");
  assert.equal(await con(["otro/x", "z-ai/glm-5.3", "meta/muse-glimmer-30b"]), "meta/muse-glimmer-30b", "primero el orden de MODELOS_API entre los presentes");
  assert.equal(await con(["otro/x"]), "minimaxai/minimax-m3.1-flash");
});

// ---------- disponibilidad (NO DISPONIBLE, sin cambio silencioso) ----------
test("disponibilidad: marca DISPONIBLE / NO DISPONIBLE con GET /models de cada proveedor; SIN VERIFICAR si no hay clave o el proveedor no lista", async () => {
  const g = await srv(({ res, url }) => url.endsWith("/models") ? json(res, 200, modelos(["qwen/qwen3.8-27b", "otro"])) : json(res, 404, {}));
  const n = await srv(({ res, url }) => url.endsWith("/models") ? json(res, 200, modelos(["minimaxai/minimax-m3.1-flash", "meta/muse-glimmer-30b"])) : json(res, 404, {}));
  Object.assign(BASES, { groq: g.url, nvidia: n.url });
  try {
    const l = await disponibilidad({ env: { ...env1, NVIDIA_API_KEY: "nv-FAKE-1" }, opts: rapido() });
    const por = Object.fromEntries(l.map((x) => [x.id, x.estado]));
    assert.deepEqual(por, {
      "groq/qwen/qwen3.8-27b": "DISPONIBLE", "nvidia/minimaxai/minimax-m3.1-flash": "DISPONIBLE", "nvidia/meta/muse-glimmer-30b": "DISPONIBLE",
      "nvidia/nvidia/nemotron-3-ultra-550b-a55b": "NO DISPONIBLE", "nvidia/z-ai/glm-5.3": "NO DISPONIBLE",
    });
    assert.equal(l.length, MODELOS_API.length); assert.equal(l.find((x) => x.estado === "NO DISPONIBLE").disponible, false);
    assert.ok(!JSON.stringify(l).includes("FAKE"));
    // sin clave de NVIDIA: no se puede verificar (no se afirma que falte)
    limpiarEstado();
    const l2 = await disponibilidad({ env: env1, opts: rapido() });
    assert.equal(l2.find((x) => x.id.startsWith("nvidia/")).estado, "SIN VERIFICAR"); assert.equal(l2.find((x) => x.id.startsWith("nvidia/")).disponible, null);
    // proveedor caido: tampoco se afirma NO DISPONIBLE
    limpiarEstado(); Object.assign(BASES, { groq: "http://127.0.0.1:9", nvidia: n.url });
    const l3 = await disponibilidad({ env: { ...env1, NVIDIA_API_KEY: "nv-FAKE-1" }, opts: rapido() });
    assert.equal(l3.find((x) => x.id === "groq/qwen/qwen3.8-27b").estado, "SIN VERIFICAR");
  } finally { g.cerrar(); n.cerrar(); }
});

test("local() con flujo previo continua sin repetir y sin stream; setClaves sigue funcionando con streaming", async () => {
  const l = await srv(({ res }) => json(res, 200, { choices: [{ finish_reason: "stop", message: { content: "COLA" } }] }));
  const g = await srv(({ res, auth }) => sseCompleto(res, [delta(auth), fin("stop")]));
  Object.assign(BASES, { groq: g.url });
  try {
    const r = await local("lfm2.5-350m", msgs, { env: { SWECODE_URL_S1: l.url }, opts: rapido(), flujo: { texto: "CABEZA-" } });
    assert.equal(r.salida, "CABEZA-COLA");
    setClaves({ groq: ["gsk-INY-1"] });
    const r2 = await externo("groq/m", msgs, { env: {}, opts: rapido(), onDelta: () => {} });
    assert.equal(r2.salida, "Bearer gsk-INY-1");
  } finally { l.cerrar(); g.cerrar(); }
});

test("X-Ray: Groq y NVIDIA consultan /models en paralelo para no vencer el timeout 15 s del chat", async () => {
  let solicitudes = 0, soltar;
  const ambas = new Promise(ok => soltar = ok);
  const callback = ({ res, url }) => {
    if (!url.endsWith("/models")) return json(res, 404, {});
    solicitudes++;
    if (solicitudes === 2) soltar();
    ambas.then(() => json(res, 200, modelos(["qwen/qwen3.8-27b", "minimaxai/minimax-m3.1-flash"])));
  };
  const g = await srv(callback), n = await srv(callback);
  Object.assign(BASES, { groq: g.url, nvidia: n.url });
  try {
    const t = setTimeout(() => soltar(), 1500);
    try {
      const data = await disponibilidad({ env: { ...env1, NVIDIA_API_KEY: "nv-FAKE-1" }, opts: rapido() });
      assert.equal(solicitudes, 2, "no se esperó a que Groq terminara para preguntar a NVIDIA");
      assert.equal(data.length, MODELOS_API.length);
    } finally { clearTimeout(t); }
  } finally { g.cerrar(); n.cerrar(); }
});
