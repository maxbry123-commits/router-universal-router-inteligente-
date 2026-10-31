// Auditoria forense en server.js REAL (puntos 1, 6, 7, 10, 11, 12, 13). Proveedores y Harness falsos (node:http); claves FALSAS.
import test, { before, after } from "node:test";
import assert from "node:assert/strict";
import fs from "node:fs";
import http from "node:http";
import os from "node:os";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { prepararApp, arrancar, limpiar, registrarMock, TMP } from "./helpers/bridge_app.mjs";
import { ACCESO_TEST } from "./helpers/acceso.mjs";

const AQUI = path.dirname(fileURLToPath(import.meta.url));
const CONT = "Continúa exactamente donde terminó, sin repetir";
const KGROQ = "gsk_FAKEKEYNOREAL1234567890", KH = "acceso-falso-harness-123", TOKEN = "token-bridge-de-prueba";
const ok = (content, finish_reason = "stop", extra = {}, usage) => ({ status: 200, json: { choices: [{ finish_reason, message: { role: "assistant", content, ...extra } }], ...(usage ? { usage } : {}) } });
const mock = (handler) => new Promise((listo) => {
  const chat = []; let n = 0;
  const s = http.createServer((req, res) => {
    let d = ""; req.on("data", (c) => d += c); req.on("end", () => {
      const v = { url: req.url, auth: req.headers.authorization, body: d ? JSON.parse(d) : null };
      if (v.url.endsWith("/chat/completions")) { chat.push(v); n++; }
      const r = handler({ ...v, n }) || { status: 404, json: {} };
      res.writeHead(r.status, { "content-type": "application/json" }); res.end(JSON.stringify(r.json ?? {}));
    });
  }).listen(0, "127.0.0.1", () => { registrarMock(s); listo({ chat, url: `http://127.0.0.1:${s.address().port}` }); });
});
const harness = () => new Promise((listo) => {
  const almacen = new Map();
  const s = http.createServer((req, res) => {
    let d = ""; req.on("data", (c) => d += c); req.on("end", () => {
      const b = JSON.parse(d); const json = (o) => { res.writeHead(200, { "content-type": "application/json" }); res.end(JSON.stringify(o)); };
      if (b.tool === "guardar") { almacen.set(b.args.nombre, b.args.valor); return json({ status: "ok", result: { nombre: b.args.nombre } }); }
      return almacen.has(b.args.nombre) ? json({ status: "ok", result: { nombre: b.args.nombre, valor: almacen.get(b.args.nombre) } }) : json({ status: "error", error: "no encontrado" });
    });
  }).listen(0, "127.0.0.1", () => { registrarMock(s); listo({ almacen, url: `http://127.0.0.1:${s.address().port}` }); });
});
const modelosVacios = ({ url }) => (url.endsWith("/models") ? { status: 200, json: { data: [] } } : null);
const post = async (srv, ruta, body, headers = {}) => {
  const r = await fetch(srv.base + ruta, { method: "POST", headers: { "content-type": "application/json", ...headers }, body: JSON.stringify(body) });
  const texto = await r.text(); let json = null; try { json = JSON.parse(texto); } catch { /* sse */ }
  return { status: r.status, headers: r.headers, texto, json };
};
const chat = (srv, body, headers) => post(srv, "/v1/chat/completions", { model: "qwen2.5-coder-1.5b", messages: [{ role: "user", content: "escribe A" }], ...body }, headers);
const disco = (n) => fs.mkdtempSync(path.join(os.tmpdir(), `aud-${n}-`));
const sse = (texto) => texto.split("\n\n").filter((b) => b.startsWith("data: ") && !b.includes("[DONE]")).map((b) => JSON.parse(b.slice(6)));

before(() => {
  prepararApp();
  // motor falso: MOTOR_MODO=fail hace fallar la web (para comprobar el respaldo de swecode-*)
  fs.writeFileSync(path.join(TMP, "app", "src", "motor.js"), `export async function consultarWeb(m) { if (process.env.MOTOR_MODO === 'fail') throw Object.assign(new Error('roto'), { code: 'SELECTOR_BROKEN' }); return 'WEB[' + m + ']'; }\nexport async function salud() { return {}; }\n`);
});
after(() => { limpiar(); });

// ---------- 1: checkpoint derivado ----------
test("1: modelo local + conv_id sin tarea_id: deriva tarea_id <conv_id>-<sha256 12>, el mismo envio reintentado REANUDA sin repetir y uno distinto es tarea nueva (sin 409)", async () => {
  let fase = 1;
  const s1 = await mock(({ body, n }) => fase === 1 ? (n === 1 ? ok("AAA", "length") : { status: 500, json: {} }) : body.messages.at(-1).content === CONT ? ok("-BBB") : ok("OTRA-RESP"));
  const B = await arrancar("deriva", { BRIDGE_STATE_DIR: disco("d"), SWECODE_URL_S1: s1.url });
  const r1 = await chat(B, { conv_id: "conv-1" });
  assert.notEqual(r1.status, 200, "la 2ª seccion falla");
  fase = 2; s1.chat.length = 0;
  const r2 = await chat(B, { conv_id: "conv-1" });
  assert.equal(r2.status, 200, r2.texto); assert.equal(r2.json.choices[0].message.content, "AAA-BBB");
  assert.match(r2.json.tarea.id, /^conv-1-[0-9a-f]{12}$/); assert.equal(r2.json.tarea.reanudado, true);
  assert.equal(s1.chat.length, 1, "no repite la seccion 1");
  const r3 = await chat(B, { conv_id: "conv-1", messages: [{ role: "user", content: "OTRO mensaje distinto" }] });
  assert.equal(r3.status, 200, r3.texto); assert.notEqual(r3.json.tarea.id, r2.json.tarea.id); assert.equal(r3.json.tarea.reanudado, false);
  const r4 = await chat(B, { conv_id: "conv-1", model: "lfm2.5-350m" });  // mismo texto, otro modelo: otra tarea, no 409
  assert.equal(r4.status, 200, r4.texto); assert.notEqual(r4.json.tarea.id, r2.json.tarea.id);
});

test("1: sin conv_id nada cambia (no hay tarea ni checkpoint); un tarea_id explicito manda; el id derivado cumple <=64 y [A-Za-z0-9_-]", async () => {
  const s1 = await mock(() => ok("X")); const dir = disco("e");
  const B = await arrancar("deriva2", { BRIDGE_STATE_DIR: dir, SWECODE_URL_S1: s1.url });
  const a = await chat(B, {}); assert.equal(a.status, 200); assert.equal(a.json.tarea, undefined); assert.equal(fs.existsSync(path.join(dir, "checkpoints")), false);
  const b = await chat(B, { conv_id: "mia", tarea_id: "explicita-1" }); assert.equal(b.json.tarea.id, "explicita-1");
  const c = await chat(B, { conv_id: "x".repeat(80) }); assert.equal(c.status, 200, c.texto);
  assert.ok(c.json.tarea.id.length <= 64 && /^[A-Za-z0-9_-]+$/.test(c.json.tarea.id), c.json.tarea.id);
  const d = await chat(B, { conv_id: "web", model: "web-qwen38max" }); assert.equal(d.status, 200); assert.equal(d.json.tarea, undefined, "un modelo web no deriva tarea");
});

// ---------- 6: no cambiar de modelo en silencio ----------
test("6: modelo explicito groq/ que falla -> 502 EXTERNO_FALLO sin caer a otro modelo; respaldo:true si lo permite", async () => {
  const g = await mock((q) => modelosVacios(q) || { status: 500, json: {} }), s1 = await mock(() => ok("DE-HF-LOCAL"));
  const B = await arrancar("expl", { BRIDGE_STATE_DIR: disco("f"), TEST_GROQ_URL: g.url, GROQ_API_KEY: KGROQ, SWECODE_URL_S1: s1.url, BRIDGE_RESPALDO_MS: "3000" });
  const r = await chat(B, { model: "groq/qwen/qwen3.8-27b" });
  assert.equal(r.status, 502, r.texto); assert.equal(r.json.error.code, "EXTERNO_FALLO"); assert.match(r.json.error.message, /GROQ/);
  assert.equal(s1.chat.length, 0, "no se llamo a otro modelo"); assert.ok(!r.texto.includes(KGROQ));
  const c = await chat(B, { model: "groq/qwen/qwen3.8-27b", respaldo: true });
  assert.equal(c.status, 200, c.texto); assert.equal(c.json.choices[0].message.content, "DE-HF-LOCAL"); assert.equal(c.json.via_respaldo, "hf-local");
});

test("6: modelo explicito que el proveedor no tiene (404) -> 502 NO_DISPONIBLE; local caido -> 502 HF_LOCAL_FALLO sin saltar a Groq; con tarea_id tambien", async () => {
  const g = await mock((q) => modelosVacios(q) || { status: 404, json: {} }), s1 = await mock(() => ({ status: 500, json: {} }));
  const gok = await mock((q) => modelosVacios(q) || ok("GROQ-RESPONDE"));
  const B = await arrancar("expl2", { BRIDGE_STATE_DIR: disco("g"), TEST_GROQ_URL: g.url, GROQ_API_KEY: KGROQ, SWECODE_URL_S1: s1.url, BRIDGE_RESPALDO_MS: "3000" });
  const nd = await chat(B, { model: "groq/qwen/qwen3.8-27b" });
  assert.equal(nd.status, 502); assert.equal(nd.json.error.code, "NO_DISPONIBLE"); assert.ok(nd.json.error.message.length > 5);
  const B2 = await arrancar("expl3", { BRIDGE_STATE_DIR: disco("h"), TEST_GROQ_URL: gok.url, GROQ_API_KEY: KGROQ, SWECODE_URL_S1: s1.url, BRIDGE_RESPALDO_MS: "3000" });
  const lo = await chat(B2, {});
  assert.equal(lo.status, 502, lo.texto); assert.equal(lo.json.error.code, "HF_LOCAL_FALLO"); assert.equal(gok.chat.length, 0, "no salta a Groq");
  const lt = await chat(B2, { tarea_id: "t-sin-respaldo" });
  assert.equal(lt.status, 502, lt.texto); assert.equal(gok.chat.length, 0, "ni con tarea_id");
});

test("6: swecode-* sigue cayendo al respaldo cuando la web falla (el modelo no es explicito)", async () => {
  const g = await mock((q) => modelosVacios(q) || ok("RESPALDO-GROQ"));
  const B = await arrancar("swe-resp", { BRIDGE_STATE_DIR: disco("i"), TEST_GROQ_URL: g.url, GROQ_API_KEY: KGROQ, BRIDGE_RESPALDO_MS: "3000", MOTOR_MODO: "fail" });
  const r = await chat(B, { model: "swecode-solucion" });
  assert.equal(r.status, 200, r.texto); assert.equal(r.json.via_respaldo, "groq"); assert.equal(r.json.choices[0].message.content, "RESPALDO-GROQ");
});

// ---------- 7: puerto ----------
test("7: puerto por defecto 7870 en server.js y responses.js (BRIDGE_PORT sigue mandando)", async () => {
  const srv = fs.readFileSync(path.join(AQUI, "..", "src", "server.js"), "utf8");
  assert.match(srv, /process\.env\.BRIDGE_PORT \|\| 7870/); assert.ok(!/\b7860\b/.test(srv));
  const { montarResponses } = await import("../src/responses.js");
  const viejo = process.env.BRIDGE_PORT, f = globalThis.fetch; delete process.env.BRIDGE_PORT;
  let url = null; const rutas = {};
  globalThis.fetch = async (u) => { url = String(u); return { ok: false, status: 500, json: async () => null, headers: new Headers() }; };
  try {
    montarResponses({ post: (p, fn) => { rutas[p] = fn; } });
    await rutas["/v1/responses"]({ body: { model: "groq/qwen/qwen3.8-27b", input: "hola" }, headers: {} }, { status() { return this; }, json() { return this; } });
    assert.match(url, /^http:\/\/127\.0\.0\.1:7870\//);
    process.env.BRIDGE_PORT = "9123"; url = null;
    await rutas["/v1/responses"]({ body: { model: "groq/qwen/qwen3.8-27b", input: "hola" }, headers: {} }, { status() { return this; }, json() { return this; } });
    assert.match(url, /:9123\//);
  } finally { globalThis.fetch = f; if (viejo === undefined) delete process.env.BRIDGE_PORT; else process.env.BRIDGE_PORT = viejo; }
});

// ---------- 10: /v1/openclaw con BRIDGE_TOKEN ----------
test("10: GET /v1/openclaw acepta BRIDGE_TOKEN (solo lectura, sin secretos); /v1/claves sigue exigiendo la clave de acceso", async () => {
  const B = await arrancar("oc-token", { BRIDGE_STATE_DIR: disco("j"), BRIDGE_TOKEN: TOKEN, GROQ_API_KEY: KGROQ });
  const bearer = { authorization: `Bearer ${TOKEN}`, "x-api-key": "" };
  const oc = await fetch(B.base + "/v1/openclaw", { headers: bearer });
  assert.ok([200, 404].includes(oc.status), `con BRIDGE_TOKEN no es 401/503: ${oc.status}`);
  assert.ok(!(await oc.text()).includes(KGROQ));
  assert.equal((await fetch(B.base + "/v1/openclaw", { headers: { "x-api-key": "", authorization: "Bearer otro" } })).status, 401);
  assert.equal((await fetch(B.base + "/v1/openclaw", { method: "DELETE", headers: bearer })).status, 401, "solo lectura: otros metodos siguen cerrados");
  assert.equal((await fetch(B.base + "/v1/claves", { headers: bearer })).status, 401);
  assert.equal((await fetch(B.base + "/v1/claves", { headers: { "x-api-key": ACCESO_TEST } })).status, 200);
});

// ---------- 11 / 12: usage y servidor ----------
test("11+12: usage del JSON y del ultimo chunk SSE sale de metricas; `servidor` (S1/S2/S3) se expone en JSON y SSE", async () => {
  const s1 = await mock(() => ok("hola", "stop", {}, { prompt_tokens: 7, completion_tokens: 3, total_tokens: 10 }));
  const B = await arrancar("usage", { BRIDGE_STATE_DIR: disco("k"), SWECODE_URL_S1: s1.url });
  const j = await chat(B, {});
  assert.deepEqual(j.json.usage, { prompt_tokens: 7, completion_tokens: 3, total_tokens: 10 }); assert.equal(j.json.servidor, "S1");
  const s = await chat(B, { stream: true });
  const chunks = sse(s.texto), ultimo = chunks.at(-1);
  assert.equal(ultimo.choices[0].finish_reason, "stop"); assert.deepEqual(ultimo.usage, { prompt_tokens: 7, completion_tokens: 3, total_tokens: 10 }); assert.equal(ultimo.servidor, "S1");
  const t = await chat(B, { conv_id: "u-1" });  // por la ruta del checkpoint tambien
  assert.deepEqual(t.json.usage, { prompt_tokens: 7, completion_tokens: 3, total_tokens: 10 }); assert.equal(t.json.servidor, "S1");
  const g = await mock((q) => modelosVacios(q) || ok("x"));
  const B2 = await arrancar("usage0", { BRIDGE_STATE_DIR: disco("l"), TEST_GROQ_URL: g.url, GROQ_API_KEY: KGROQ });
  const sin = await chat(B2, { model: "groq/qwen/qwen3.8-27b" });
  assert.deepEqual(sin.json.usage, { prompt_tokens: 0, completion_tokens: 0, total_tokens: 0 }, "sin usage del proveedor: ceros como siempre"); assert.equal(sin.json.servidor, undefined);
});

// ---------- 13: origen hacia el checkpoint ----------
test("13: el origen del cuerpo (openclaw|yaiwes) llega a la ruta del checkpoint en el Harness", async () => {
  const s1 = await mock(() => ok("X")), h = await harness();
  const B = await arrancar("origen", { BRIDGE_STATE_DIR: disco("m"), SWECODE_URL_S1: s1.url, RIU_DEEPSEEK_HARNESS_URL: h.url, RIU_API_KEY: KH });
  await chat(B, { tarea_id: "to-1", origen: "openclaw" });
  await chat(B, { tarea_id: "to-2" });
  assert.ok(h.almacen.has("tareas/swe/openclaw/to-1/checkpoint.json"), [...h.almacen.keys()].join());
  assert.ok(h.almacen.has("tareas/swe/bridge/to-2/checkpoint.json"));
});
