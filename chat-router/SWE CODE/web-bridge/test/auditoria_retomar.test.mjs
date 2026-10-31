// Auditoria forense (puntos 3, 6, 11, 12, 13) en retomar_local.js. Servidores falsos node:http, claves FALSAS.
import test from "node:test";
import assert from "node:assert/strict";
import http from "node:http";
import fs from "node:fs";
import os from "node:os";
import path from "node:path";
import { retomarLocal } from "../src/retomar_local.js";
import { BASES, limpiarEstado, limpiarClaves } from "../src/respaldo.js";

const CONT = "Continúa exactamente donde terminó, sin repetir";
const MODELO = "qwen2.5-coder-1.5b";
const msgs = [{ role: "user", content: "escribe la funcion A" }];
const ok = (content, finish_reason = "stop", extra = {}, usage) => ({ status: 200, json: { choices: [{ finish_reason, message: { role: "assistant", content, ...extra } }], ...(usage ? { usage } : {}) } });
const tmp = () => fs.mkdtempSync(path.join(os.tmpdir(), "rla-"));
const fake = (handler) => new Promise((listo) => {
  const chat = []; let n = 0;
  const s = http.createServer((req, res) => {
    let d = ""; req.on("data", (c) => d += c); req.on("end", () => {
      const v = { url: req.url, auth: req.headers.authorization, body: d ? JSON.parse(d) : null };
      if (v.url.endsWith("/chat/completions")) { chat.push(v); n++; }
      const r = handler({ ...v, n }) || { status: 404, json: {} };
      res.writeHead(r.status, { "content-type": "application/json" }); res.end(JSON.stringify(r.json ?? {}));
    });
  }).listen(0, "127.0.0.1", () => listo({ chat, url: `http://127.0.0.1:${s.address().port}`, cerrar: () => { s.closeAllConnections?.(); s.close(); } }));
});
const base0 = { groq: BASES.groq, nvidia: BASES.nvidia };
test.beforeEach(() => { limpiarEstado(); limpiarClaves(); });
test.afterEach(() => Object.assign(BASES, base0));

test("3: retomarLocal pide UNA respuesta por vuelta (continuaciones 0): el bucle continua y guarda checkpoint entre vueltas", async () => {
  const s1 = await fake(({ n }) => (n < 3 ? ok("p" + n, "length") : ok("fin", "stop"))); const dir = tmp();
  try {
    // sin inyectar continuaciones: con el valor por defecto (8) la 1ª vuelta se tragaria las 3 peticiones
    const r = await retomarLocal("t-cont", MODELO, msgs, { env: { BRIDGE_STATE_DIR: dir, SWECODE_URL_S1: s1.url }, opts: { esperar: async () => {} }, maxVueltas: 1 });
    assert.equal(s1.chat.length, 1, "una peticion por vuelta"); assert.equal(r.parcial, true); assert.equal(r.finish_reason, "length");
    const ck = JSON.parse(fs.readFileSync(path.join(dir, "checkpoints", "t-cont.json"), "utf8"));
    assert.equal(ck.parcial, "p1"); assert.equal(ck.secciones.length, 1);
    const r2 = await retomarLocal("t-cont", MODELO, msgs, { env: { BRIDGE_STATE_DIR: dir, SWECODE_URL_S1: s1.url }, opts: { esperar: async () => {} } });
    assert.equal(r2.salida, "p1p2fin"); assert.equal(s1.chat.length, 3);
    assert.deepEqual(s1.chat[1].body.messages.slice(-2), [{ role: "assistant", content: "p1" }, { role: "user", content: CONT }]);
  } finally { s1.cerrar(); }
});

test("12: el resultado lleva el servidor local (S1/S2/S3) que respondio", async () => {
  const s1 = await fake(() => ({ status: 500, json: {} })), s2 = await fake(() => ok("de S2")); const dir = tmp();
  try {
    const r = await retomarLocal("t-srv", MODELO, msgs, { env: { BRIDGE_STATE_DIR: dir, SWECODE_URL_S1: s1.url, SWECODE_URL_S2: s2.url }, opts: { esperar: async () => {} } });
    assert.equal(r.salida, "de S2"); assert.equal(r.servidor, "S2");
    const ck = JSON.parse(fs.readFileSync(path.join(dir, "checkpoints", "t-srv.json"), "utf8"));
    assert.equal(ck.secciones[0].servidor, "S2");
    const b = await retomarLocal("t-srv", MODELO, msgs, { env: { BRIDGE_STATE_DIR: dir, SWECODE_URL_S1: s1.url, SWECODE_URL_S2: s2.url } });
    assert.equal(b.desde_checkpoint, true); assert.equal(b.servidor, "S2");
  } finally { s1.cerrar(); s2.cerrar(); }
});

test("11: el resultado lleva metricas con usage sumado de las vueltas de esta ejecucion", async () => {
  const s1 = await fake(({ n }) => (n === 1 ? ok("A", "length", {}, { prompt_tokens: 4, completion_tokens: 1, total_tokens: 5 }) : ok("B", "stop", {}, { prompt_tokens: 6, completion_tokens: 2, total_tokens: 8 }))); const dir = tmp();
  try {
    const r = await retomarLocal("t-uso", MODELO, msgs, { env: { BRIDGE_STATE_DIR: dir, SWECODE_URL_S1: s1.url }, opts: { esperar: async () => {} } });
    assert.equal(r.salida, "AB");
    assert.deepEqual([r.metricas.prompt_tokens, r.metricas.completion_tokens, r.metricas.total_tokens], [10, 3, 13]);
  } finally { s1.cerrar(); }
});

test("13: el origen del contrato (openclaw) se guarda en el checkpoint y manda en la ruta del Harness", async () => {
  const s1 = await fake(() => ok("X")); const dir = tmp();
  const guardados = [];
  const fetchFalso = async (url, init) => { const b = JSON.parse(init.body); if (b.tool === "guardar") guardados.push(b.args.nombre); return { ok: true, status: 200, json: async () => ({ status: "error", error: "no" }) }; };
  try {
    const r = await retomarLocal("t-or", MODELO, msgs, { origen: "openclaw", fetch: fetchFalso, env: { BRIDGE_STATE_DIR: dir, SWECODE_URL_S1: s1.url, RIU_DEEPSEEK_HARNESS_URL: "http://127.0.0.1:9", RIU_API_KEY: "k-falsa-123" }, opts: { esperar: async () => {} } });
    assert.equal(r.salida, "X");
    assert.ok(guardados.length >= 1 && guardados.every((n) => n === "tareas/swe/openclaw/t-or/checkpoint.json"), guardados.join());
    assert.equal(JSON.parse(fs.readFileSync(path.join(dir, "checkpoints", "t-or.json"), "utf8")).origen, "openclaw");
  } finally { s1.cerrar(); }
});

test("6: con sinRespaldo el fallo del modelo pedido NO cae a otro modelo: error claro con el codigo del proveedor", async () => {
  const g = await fake(({ url }) => (url.endsWith("/models") ? { status: 200, json: { data: [] } } : { status: 500, json: {} }));
  const s1 = await fake(() => ok("OTRO-MODELO")); const dir = tmp();
  Object.assign(BASES, { groq: g.url });
  try {
    const e = { env: { BRIDGE_STATE_DIR: dir, GROQ_API_KEY: "gsk_FAKEKEYNOREAL1234567890", SWECODE_URL_S1: s1.url }, opts: { esperar: async () => {} } };
    await assert.rejects(() => retomarLocal("t-sr", "groq/qwen/qwen3.8-27b", msgs, { ...e, sinRespaldo: true }), (er) => er.code === "EXTERNO_FALLO");
    assert.equal(s1.chat.length, 0, "no se llamo a ningun otro modelo");
    // sin la bandera (comportamiento de siempre) si hay respaldo
    const r = await retomarLocal("t-sr2", "groq/qwen/qwen3.8-27b", msgs, e);
    assert.equal(r.salida, "OTRO-MODELO");
  } finally { g.cerrar(); s1.cerrar(); }
});
