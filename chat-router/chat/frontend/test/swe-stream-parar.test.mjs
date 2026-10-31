import test from "node:test";
import assert from "node:assert/strict";
import http from "node:http";

// (2) Detener = parar y esperar: conducir/enviarTareaSwe dejan de avanzar y el fetch de enviarSwe se aborta.
// (3) Parciales: stream:true + lector SSE contra un servidor HTTP falso (api.js real, fetch real hacia 127.0.0.1). Sin claves reales.
const datos = new Map();
globalThis.window = globalThis;
globalThis.localStorage = { getItem: (k) => datos.get(k) ?? null, setItem: (k, v) => datos.set(k, String(v)), removeItem: (k) => datos.delete(k) };
globalThis.sessionStorage = { getItem: () => "k" };
globalThis.addEventListener = () => {}; globalThis.removeEventListener = () => {}; globalThis.dispatchEvent = () => true;
globalThis.document = { addEventListener() {}, visibilityState: "visible" };
globalThis.location = { hostname: "x.hf.space", origin: "https://x.hf.space", search: "" };
globalThis.CustomEvent = class { constructor(t, o) { this.type = t; this.detail = o && o.detail; } };
const HF = "https://comand-center-1-riu-router.hf.space";
window.RIU_CONFIG = { proxyDestino: HF, liveUrl: "" };

let local = "", peticiones = [], guion = () => {};
const srv = http.createServer((req, res) => {
  let cuerpo = ""; req.on("data", (d) => (cuerpo += d));
  req.on("end", () => { const p = { url: req.url, body: cuerpo ? JSON.parse(cuerpo) : null, cerrada: false }; peticiones.push(p); res.on("close", () => { p.cerrada = true; }); guion(req, res, p); });
});
await new Promise((ok) => srv.listen(0, "127.0.0.1", ok));
local = "http://127.0.0.1:" + srv.address().port;
const fetchReal = globalThis.fetch;
globalThis.fetch = (url, opts) => fetchReal(String(url).replace(HF, local), opts);
test.after(() => { srv.closeAllConnections?.(); srv.close(); });

const { api } = await import("../api.js");
const S = await import("../swe-directo.js");
const base = { model: "web-qwen38max", historial: [], mensaje: "hola", sesion: "s" };
const sseHead = (res) => res.writeHead(200, { "content-type": "text/event-stream; charset=utf-8", "cache-control": "no-cache" });
const ch = (delta, fin = null, extra = {}) => "data: " + JSON.stringify({ id: "c1", object: "chat.completion.chunk", choices: [{ index: 0, delta, finish_reason: fin }], ...extra }) + "\n\n";
const esperar = (ms) => new Promise((ok) => setTimeout(ok, ms));
test.beforeEach(() => { peticiones = []; datos.clear(); });

test("armar manda stream:true (los modelos van por el bridge) y enviarSwe lo envia en el POST", async () => {
  assert.equal(S.armar(base).stream, true);
  guion = (_q, res) => { res.writeHead(200, { "content-type": "application/json" }); res.end(JSON.stringify({ choices: [{ message: { content: "json" }, finish_reason: "stop" }] })); };
  await S.enviarSwe(api, base);
  assert.equal(peticiones[0].body.stream, true); assert.equal(peticiones[0].url, "/v1/chat/completions");
});

test("SSE: chunks partidos a mitad de evento, CRLF y comentarios keepalive; los parciales son acumulados y la respuesta final el texto completo", async () => {
  guion = async (_q, res) => {
    sseHead(res);
    const todo = ": keepalive\r\n\r\n" + ch({ role: "assistant" }).replace(/\n/g, "\r\n") + ch({ content: "Hola " }) + ": otro comentario\n\n" + ch({ content: "mundo" }) + ch({}, "stop", { modelo_usado: "web-qwen38max", via_respaldo: "groq" }) + "data: [DONE]\n\n";
    for (let i = 0; i < todo.length; i += 7) { res.write(todo.slice(i, i + 7)); await esperar(2); }  // trozos de 7 bytes: parten eventos y CRLF
    res.end();
  };
  const parciales = [];
  const r = await S.enviarSwe(api, { ...base, alParcial: (t) => parciales.push(t) });
  assert.equal(r.reply, "Hola mundo"); assert.equal(r.finish_reason, "stop"); assert.match(r.nota, /groq/);
  assert.deepEqual(parciales.filter((x, i, a) => a.indexOf(x) === i), ["Hola ", "Hola mundo"]);
  assert.ok(parciales.every((p, i) => i === 0 || p.startsWith(parciales[i - 1])), "cada parcial extiende al anterior");
});

test("SSE: varias lineas data: de un mismo evento se unen y un JSON roto se ignora sin romper el resto", async () => {
  guion = (_q, res) => {
    sseHead(res);
    res.write('data: {"choices":[{"delta":\ndata: {"content":"A"},"finish_reason":null}]}\n\n'.replace("{\"content\"", "{\"content\""));
    res.write("data: {no es json\n\n");
    res.write(ch({ content: "B" })); res.write(ch({}, "stop")); res.end("data: [DONE]\n\n");
  };
  const r = await S.enviarSwe(api, base);
  assert.equal(r.reply, "AB");
});

test("si el servidor responde JSON normal (no SSE) cae al camino de siempre", async () => {
  guion = (_q, res) => { res.writeHead(200, { "content-type": "application/json" }); res.end(JSON.stringify({ modelo_usado: "web-qwen38max", via_primaria: "web", choices: [{ message: { content: "completo" }, finish_reason: "stop" }] })); };
  const parciales = [];
  const r = await S.enviarSwe(api, { ...base, alParcial: (t) => parciales.push(t) });
  assert.equal(r.reply, "completo"); assert.match(r.nota, /vía web/); assert.deepEqual(parciales, []);
});

test("SSE con tool_calls: devuelve los nombres como hoy (Tools pedidas), con los argumentos partidos en deltas", async () => {
  guion = (_q, res) => {
    sseHead(res);
    res.write(ch({ tool_calls: [{ index: 0, id: "c1", type: "function", function: { name: "github_leer", arguments: "{\"a\":" } }] }));
    res.write(ch({ tool_calls: [{ index: 0, function: { arguments: "1}" } }] }));
    res.write(ch({ tool_calls: [{ index: 1, id: "c2", type: "function", function: { name: "ls", arguments: "{}" } }] }));
    res.write(ch({}, "tool_calls")); res.end("data: [DONE]\n\n");
  };
  const r = await S.enviarSwe(api, { ...base, model: "groq/qwen/qwen3.8-27b", ejecutor_tools: "openclaw" });
  assert.deepEqual(r.tools, []); assert.deepEqual(r.pedidas, ["github_leer", "ls"]); assert.equal(r.finish_reason, "tool_calls"); assert.match(r.reply, /Tools pedidas: github_leer, ls/); assert.match(r.nota, /OpenClaw/);
  assert.equal(peticiones[0].url, "/web/v1/chat/completions");
});

test("SSE: un chunk de error sin texto es un GAP con su codigo; con texto parcial se conserva el texto y se avisa en la nota", async () => {
  guion = (_q, res) => { sseHead(res); res.write(ch({}, "error", { error: { code: "RESPALDO_AGOTADO", message: "nada responde" } })); res.end("data: [DONE]\n\n"); };
  await assert.rejects(() => S.enviarSwe(api, base), /GAP: RESPALDO_AGOTADO · nada responde/);
  guion = (_q, res) => { sseHead(res); res.write(ch({ content: "Solo esto. " })); res.write(ch({}, "error", { error: { code: "UPSTREAM", message: "cayo" } })); res.end("data: [DONE]\n\n"); };
  const r = await S.enviarSwe(api, base);
  assert.equal(r.reply, "Solo esto. "); assert.match(r.nota, /UPSTREAM/); assert.notEqual(r.finish_reason, "stop");
});

test("un 4xx/5xx con JSON de error sigue lanzando el mismo error de siempre", async () => {
  guion = (_q, res) => { res.writeHead(502, { "content-type": "application/json" }); res.end(JSON.stringify({ error: { code: "BRIDGE_CAIDO", message: "x" } })); };
  await assert.rejects(() => S.enviarSwe(api, base), /BRIDGE_CAIDO/);
});

test("Detener: la senal aborta el fetch (el servidor ve la conexion cerrada) y enviarSwe lanza PROCESO_DETENIDO, tambien a mitad del stream", async () => {
  guion = (_q, res) => { sseHead(res); res.write(ch({ content: "parte " })); };  // nunca termina
  const ac = new AbortController(), parciales = [];
  const p = S.enviarSwe(api, { ...base, signal: ac.signal, alParcial: (t) => { parciales.push(t); ac.abort(); } });
  await assert.rejects(p, /PROCESO_DETENIDO/);
  assert.deepEqual(parciales, ["parte "]);
  for (let i = 0; i < 50 && !peticiones[0].cerrada; i++) await esperar(10);
  assert.ok(peticiones[0].cerrada, "el servidor ve la conexion cerrada");
  // abortada antes de responder (cabeceras sin llegar)
  guion = () => {};  // el servidor nunca responde
  const ac2 = new AbortController(), p2 = S.enviarSwe(api, { ...base, signal: ac2.signal });
  setTimeout(() => ac2.abort(), 30);
  await assert.rejects(p2, /PROCESO_DETENIDO/);
});

test("api(): sin senal ni sse todo sigue igual (JSON)", async () => {
  guion = (_q, res) => { res.writeHead(200, { "content-type": "application/json" }); res.end('{"ok":true}'); };
  assert.deepEqual(await api("/health"), { ok: true });
});

// ---- Detener en tareas SWE (workflow/agentico): parar() corta el bucle de avance ----
const OK = { harness: "ok", agentes: Object.fromEntries(["openclaw", "swe-agent", "openhands", "opencode", "codex", "claude-code"].map((a) => [a, { disponible: true }])), workflows: { swe_code: { disponible: true }, liquid_mirror: { disponible: true } } };
const apiTarea = (log, { avanzar } = {}) => async (ruta, op) => {
  log.push({ ruta, signal: op && op.signal });
  if (ruta === "/chat/swe/capacidades") return OK;
  if (ruta === "/chat/swe/iniciar") return { ok: true, resultado: { task_id: op.body.task_id, estado: "EJECUTANDO" } };
  if (ruta === "/chat/swe/avanzar") return avanzar ? avanzar(op) : { ok: true, resultado: { task_id: op.body.task_id, estado: "EJECUTANDO" } };
  throw new Error("ruta inesperada " + ruta);
};
test("enviarTareaSwe con parar(): tras Detener no vuelve a llamar a avanzar (antes seguia hasta MAX_AVANCES) y lanza PROCESO_DETENIDO", async () => {
  S.guardarSeleccion({ workflow: "swe_code" }); S.olvidarCapacidades();
  const log = []; let detenido = false;
  const api2 = apiTarea(log, { avanzar: (op) => { detenido = true; return { ok: true, resultado: { task_id: op.body.task_id, estado: "EJECUTANDO" } }; } });
  await assert.rejects(() => S.enviarTareaSwe(api2, { mensaje: "x", sesion: "s", parar: () => detenido }), /PROCESO_DETENIDO/);
  assert.equal(log.filter((l) => l.ruta === "/chat/swe/avanzar").length, 1);
});
test("enviarTareaSwe sin parar sigue avanzando hasta MAX_AVANCES (comportamiento previo)", async () => {
  S.guardarSeleccion({ workflow: "swe_code" }); S.olvidarCapacidades();
  const log = [];
  await assert.rejects(() => S.enviarTareaSwe(apiTarea(log), { mensaje: "x", sesion: "s" }), /SWE_SIN_PROGRESO/);
  assert.equal(log.filter((l) => l.ruta === "/chat/swe/avanzar").length, S.MAX_AVANCES);
});
test("parar() ya activo antes de iniciar: no se crea la tarea", async () => {
  S.guardarSeleccion({ workflow: "swe_code" }); S.olvidarCapacidades();
  const log = [];
  await assert.rejects(() => S.enviarTareaSwe(apiTarea(log), { mensaje: "x", sesion: "s", parar: () => true }), /PROCESO_DETENIDO/);
  assert.ok(!log.some((l) => l.ruta === "/chat/swe/iniciar"));
});
test("la senal se pasa a cada operacion /chat/swe/* y un PROCESO_DETENIDO no se disfraza de SWE_HARNESS_ERROR", async () => {
  S.guardarSeleccion({ workflow: "swe_code" }); S.olvidarCapacidades();
  const log = [], ac = new AbortController();
  const api2 = apiTarea(log, { avanzar: () => { ac.abort(); throw new Error("PROCESO_DETENIDO"); } });
  await assert.rejects(() => S.enviarTareaSwe(api2, { mensaje: "x", sesion: "s", signal: ac.signal }), (e) => e.message === "PROCESO_DETENIDO");
  assert.ok(log.filter((l) => l.ruta !== "/chat/swe/capacidades").every((l) => l.signal === ac.signal));
});
test("aprobarYContinuarSwe tambien respeta parar()", async () => {
  S.guardarSeleccion({ workflow: "swe_code" });
  const log = []; let n = 0;
  const api2 = async (ruta, op) => { log.push(ruta); return { ok: true, resultado: { task_id: op.body.task_id, estado: "EJECUTANDO" } }; };
  await assert.rejects(() => S.aprobarYContinuarSwe(api2, { task_id: "t1", op_id: "0123456789abcdef", sesion: "s", parar: () => ++n > 1 }), /PROCESO_DETENIDO/);
  assert.ok(log.filter((r) => r === "/chat/swe/avanzar").length <= 1);
});
