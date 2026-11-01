// Integracion de server.js REAL: tarea_id en /v1/chat/completions y POST /v1/secciones/:id/retomar para modelos locales HF / Groq.
// S1 y Harness DeepSeek falsos (node:http); claves FALSAS. Reinicio = matar el bridge y arrancar otro con OTRO disco.
import test, { before, after } from "node:test";
import assert from "node:assert/strict";
import fs from "node:fs";
import http from "node:http";
import os from "node:os";
import path from "node:path";
import { prepararApp, arrancar, limpiar, registrarMock, TMP } from "./helpers/bridge_app.mjs";
import './helpers/acceso.mjs';

const CONT = "Continúa exactamente donde terminó, sin repetir";
const KH = "acceso-falso-harness-123", KGROQ = "gsk_FAKEKEYNOREAL1234567890";
const ok = (content, finish_reason = "stop") => ({ status: 200, json: { choices: [{ finish_reason, message: { role: "assistant", content } }] } });

const mock = (handler) => new Promise((listo) => {
  const chat = []; let n = 0;
  const s = http.createServer((req, res) => {
    let d = ""; req.on("data", (c) => d += c); req.on("end", () => {
      const v = { url: req.url, auth: req.headers.authorization, body: d ? JSON.parse(d) : null };
      if (v.url.endsWith("/chat/completions")) { chat.push(v); n++; }
      const r = handler({ ...v, n, req }) || { status: 404, json: {} };
      res.writeHead(r.status, { "content-type": "application/json" }); res.end(JSON.stringify(r.json ?? {}));
    });
  }).listen(0, "127.0.0.1", () => { registrarMock(s); listo({ chat, url: `http://127.0.0.1:${s.address().port}` }); });
});
const harness = () => new Promise((listo) => {
  const almacen = new Map(), crudos = [];
  const s = http.createServer((req, res) => {
    let d = ""; req.on("data", (c) => d += c); req.on("end", () => {
      crudos.push({ url: req.url, clave: req.headers["x-api-key"], d }); const b = JSON.parse(d); const json = (o) => { res.writeHead(200, { "content-type": "application/json" }); res.end(JSON.stringify(o)); };
      if (req.headers["x-api-key"] !== KH) return json({ status: "error", error: "clave de acceso invalida" });
      if (b.tool === "guardar") { almacen.set(b.args.nombre, b.args.valor); return json({ status: "ok", result: { nombre: b.args.nombre } }); }
      return almacen.has(b.args.nombre) ? json({ status: "ok", result: { nombre: b.args.nombre, valor: almacen.get(b.args.nombre) } }) : json({ status: "error", error: "no encontrado" });
    });
  }).listen(0, "127.0.0.1", () => { registrarMock(s); listo({ almacen, crudos, url: `http://127.0.0.1:${s.address().port}` }); });
});
const post = async (srv, ruta, body, headers = {}) => {
  const r = await fetch(srv.base + ruta, { method: "POST", headers: { "content-type": "application/json", ...headers }, ...(body ? { body: JSON.stringify(body) } : {}) });
  return { status: r.status, headers: r.headers, json: await r.json().catch(() => null) };
};
const chat = (srv, body, headers) => post(srv, "/v1/chat/completions", { model: "qwen2.5-coder-1.5b", messages: [{ role: "user", content: "escribe A" }], ...body }, headers);
const disco = (n) => fs.mkdtempSync(path.join(os.tmpdir(), `ret-${n}-`));
const arch = (dir, id) => path.join(dir, "checkpoints", `${id}.json`);

before(() => { prepararApp(); });
after(() => { limpiar(); });

test("sin tarea_id el comportamiento no cambia: no se crea checkpoint ni se toca el Harness", async () => {
  const s1 = await mock(() => ok("normal")), h = await harness(), dir = disco("a");
  const B = await arrancar("sin-tarea", { BRIDGE_STATE_DIR: dir, SWECODE_URL_S1: s1.url, RIU_DEEPSEEK_HARNESS_URL: h.url, RIU_API_KEY: KH });
  const r = await chat(B, {});
  assert.equal(r.status, 200); assert.equal(r.json.choices[0].message.content, "normal"); assert.equal(r.json.tarea, undefined);
  assert.equal(fs.existsSync(path.join(dir, "checkpoints")), false); assert.equal(h.crudos.length, 0);
});

test("con tarea_id: usa retomarLocal, guarda en el Harness y en local, y el 2º llamado devuelve lo guardado sin llamar al modelo", async () => {
  const s1 = await mock(({ n }) => ok("RESP-" + n)), h = await harness(), dir = disco("b");
  const B = await arrancar("con-tarea", { BRIDGE_STATE_DIR: dir, SWECODE_URL_S1: s1.url, RIU_DEEPSEEK_HARNESS_URL: h.url, RIU_API_KEY: KH });
  const a = await chat(B, { tarea_id: "tarea-1" });
  // 140: finish_reason=stop NO cierra la tarea: queda RESPUESTA_COMPLETA hasta que el cliente confirme
  assert.equal(a.status, 200); assert.equal(a.json.choices[0].message.content, "RESP-1"); assert.equal(a.json.tarea.id, "tarea-1"); assert.equal(a.json.tarea.estado, "RESPUESTA_COMPLETA");
  assert.equal(JSON.parse(fs.readFileSync(arch(dir, "tarea-1"), "utf8")).estado, "RESPUESTA_COMPLETA");
  assert.ok(h.almacen.has("tareas/swe/bridge/tarea-1/checkpoint.json")); assert.ok(h.crudos.every((c) => c.clave === KH));
  const b = await chat(B, { tarea_id: "tarea-1" }, {});
  assert.equal(b.json.choices[0].message.content, "RESP-1"); assert.equal(b.json.tarea.desde_checkpoint, true); assert.equal(s1.chat.length, 1);
});

test("tarea_id tambien por cabecera x-tarea-id; invalido -> 400; otra tarea con el mismo id -> 409; un modelo web ignora tarea_id", async () => {
  const s1 = await mock(() => ok("X")), dir = disco("c");
  const B = await arrancar("cab", { BRIDGE_STATE_DIR: dir, SWECODE_URL_S1: s1.url });
  assert.equal((await chat(B, {}, { "x-tarea-id": "por-cabecera" })).json.tarea.id, "por-cabecera");
  assert.ok(fs.existsSync(arch(dir, "por-cabecera")));
  const mal = await chat(B, { tarea_id: "../x" }); assert.equal(mal.status, 400); assert.equal(mal.json.error.code, "TAREA_ID_INVALIDO");
  const otra = await chat(B, { tarea_id: "por-cabecera", messages: [{ role: "user", content: "OTRA" }] });
  assert.equal(otra.status, 409); assert.equal(otra.json.error.code, "CHECKPOINT_OTRA_TAREA");
  const web = await chat(B, { model: "web-qwen38max", tarea_id: "../x" }); assert.equal(web.status, 200); assert.equal(web.json.tarea, undefined);
});

test("reinicio: el bridge cae a mitad (length), arranca otro con OTRO disco y POST /v1/secciones/:id/retomar continua desde el Harness sin repetir la seccion", async () => {
  let fase = 1;
  const s1 = await mock(({ body, n }) => fase === 1 ? (n === 1 ? ok("AAA", "length") : { status: 500, json: {} }) : body.messages.at(-1).content === CONT ? ok("-BBB") : ok("AAA", "length"));
  const h = await harness();
  const env = { SWECODE_URL_S1: s1.url, RIU_DEEPSEEK_HARNESS_URL: h.url, RIU_API_KEY: KH };
  const B1 = await arrancar("rei-1", { BRIDGE_STATE_DIR: disco("d1"), ...env });
  const r1 = await chat(B1, { tarea_id: "tarea-r" });
  assert.notEqual(r1.status, 200, "la 2ª seccion falla (modelo caido, sin respaldo)");
  assert.notEqual(r1.json.error.code, "CHECKPOINT_OTRA_TAREA");
  await B1.matar();
  fase = 2; s1.chat.length = 0;
  const B2 = await arrancar("rei-2", { BRIDGE_STATE_DIR: disco("d2"), ...env });
  const r2 = await post(B2, "/v1/secciones/tarea-r/retomar", { tarea_completa: true });
  assert.equal(r2.status, 200, JSON.stringify(r2.json));
  assert.equal(r2.json.choices[0].message.content, "AAA-BBB"); assert.equal(s1.chat.length, 1, "no repite la seccion 1");
  assert.deepEqual(s1.chat[0].body.messages.slice(-2), [{ role: "assistant", content: "AAA" }, { role: "user", content: CONT }]);
  assert.equal((await post(B2, "/v1/secciones/tarea-r/retomar")).status, 409, "ya completa");
  // y la tarea ya terminada, pedida de nuevo con el mismo id y mensajes, no llama al modelo
  s1.chat.length = 0; const r3 = await chat(B2, { tarea_id: "tarea-r" });
  assert.equal(r3.json.choices[0].message.content, "AAA-BBB"); assert.equal(s1.chat.length, 0);
});

test("retomar sigue funcionando para secciones web y 404 si no existe en ningun sitio", async () => {
  const dir = disco("e"); fs.mkdirSync(path.join(dir, "checkpoints"));
  fs.writeFileSync(arch(dir, "media"), JSON.stringify({ modo: "solucion", modelo: "qwen38max", texto: "TEXTO", total: 3, enviados: 1 }));
  const B = await arrancar("web", { BRIDGE_STATE_DIR: dir, WEB_ACCOUNTS: "a@x.com", WEB_PASS: "pw" });
  const r = await post(B, "/v1/secciones/media/retomar"); assert.equal(r.status, 200); assert.equal(r.json.choices[0].message.content, "WEB[qwen38max]");
  assert.equal((await post(B, "/v1/secciones/no-hay/retomar")).status, 404);
});

test("modelo groq/qwen/qwen3.8-27b con tarea_id: va por Groq con la clave, guarda el checkpoint SIN la clave y retomar lo ve", async () => {
  const g = await mock(({ url }) => url.endsWith("/models") ? { status: 200, json: { data: [] } } : ok("DE-GROQ")), dir = disco("f");
  const B = await arrancar("groq", { BRIDGE_STATE_DIR: dir, TEST_GROQ_URL: g.url, GROQ_API_KEY: KGROQ });
  const r = await chat(B, { model: "groq/qwen/qwen3.8-27b", tarea_id: "tarea-g" });
  assert.equal(r.status, 200); assert.equal(r.json.choices[0].message.content, "DE-GROQ"); assert.equal(r.json.via_respaldo, "groq");
  assert.equal(g.chat[0].auth, "Bearer " + KGROQ);
  assert.ok(!fs.readFileSync(arch(dir, "tarea-g"), "utf8").includes("FAKEKEYNOREAL"));
  assert.equal((await post(B, "/v1/secciones/tarea-g/retomar", { tarea_completa: true })).status, 200, "sin confirmar devuelve lo guardado y la confirma");
  assert.equal(g.chat.length, 1, "no vuelve a llamar al modelo");
  assert.equal((await post(B, "/v1/secciones/tarea-g/retomar")).status, 409);
});

test("tool_calls con tarea_id: se devuelven al cliente (las corre el Harness) y repetir la peticion no vuelve a llamar al modelo", async () => {
  const tcs = [{ id: "call_9", type: "function", function: { name: "escribir", arguments: "{}" } }];
  const s1 = await mock(() => ({ status: 200, json: { choices: [{ finish_reason: "tool_calls", message: { role: "assistant", content: null, tool_calls: tcs } }] } })), dir = disco("g");
  const B = await arrancar("tools", { BRIDGE_STATE_DIR: dir, SWECODE_URL_S1: s1.url });
  const a = await chat(B, { tarea_id: "tarea-t", tools: [{ type: "function", function: { name: "escribir" } }] });
  assert.equal(a.json.choices[0].finish_reason, "tool_calls"); assert.deepEqual(a.json.choices[0].message.tool_calls.map((t) => t.id), ["call_9"]);
  const b = await chat(B, { tarea_id: "tarea-t", tools: [{ type: "function", function: { name: "escribir" } }] });
  assert.deepEqual(b.json.choices[0].message.tool_calls.map((t) => t.id), ["call_9"]); assert.equal(s1.chat.length, 1);
});
