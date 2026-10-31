// Pruebas de checkpoint_hf.js: guardar/leer el checkpoint por la herramienta REAL del Harness DeepSeek
// (POST {RIU_DEEPSEEK_HARNESS_URL}/invoke, cabecera X-API-Key, cuerpo {action:"invoke", tool:"guardar"|"leer", args:{nombre, valor}})
// y, sin Harness, en BRIDGE_STATE_DIR/checkpoints/<id>.json. Harness falso con node:http; claves FALSAS.
import test from "node:test";
import assert from "node:assert/strict";
import http from "node:http";
import fs from "node:fs";
import os from "node:os";
import path from "node:path";
import { guardarCheckpoint, leerCheckpoint, idValido, sanear } from "../src/checkpoint_hf.js";

const CLAVE_HARNESS = "acceso-falso-harness-123";
const tmp = () => fs.mkdtempSync(path.join(os.tmpdir(), "ckhf-"));

// Harness falso: guarda en un Map lo que recibe en "guardar" y lo devuelve en "leer" (como el almacen HF real, valor = string)
async function harnessFalso({ clave = CLAVE_HARNESS, modo = "ok" } = {}) {
  const almacen = new Map(), peticiones = [];
  const s = http.createServer((req, res) => {
    let d = ""; req.on("data", (c) => d += c); req.on("end", () => {
      const cuerpo = d ? JSON.parse(d) : null;
      peticiones.push({ method: req.method, url: req.url, clave: req.headers["x-api-key"], cuerpo, crudo: d });
      if (modo === "colgar") return;
      const json = (o, st = 200) => { res.writeHead(st, { "content-type": "application/json" }); res.end(JSON.stringify(o)); };
      if (req.headers["x-api-key"] !== clave) return json({ status: "error", error: "clave de acceso invalida" }, 401);
      if (modo === "error") return json({ status: "error", error: "Router no confirmo almacenamiento HF" });
      const { tool, args } = cuerpo;
      if (tool === "guardar") { almacen.set(args.nombre, args.valor); return json({ status: "ok", result: { nombre: args.nombre, destino: "hf", commit: "abc" } }); }
      if (tool === "leer") return almacen.has(args.nombre) ? json({ status: "ok", result: { nombre: args.nombre, valor: almacen.get(args.nombre) } }) : json({ status: "error", error: "Router no encontrado" });
      json({ status: "error", error: "tool no permitida" });
    });
  });
  await new Promise((ok) => s.listen(0, "127.0.0.1", ok));
  return { url: `http://127.0.0.1:${s.address().port}`, almacen, peticiones, cerrar: () => { s.closeAllConnections?.(); s.close(); } };
}
const envCon = (dir, extra = {}) => ({ BRIDGE_STATE_DIR: dir, ...extra });

test("idValido: solo /^[a-zA-Z0-9_-]{1,64}$/", () => {
  for (const ok of ["a", "tarea_1-A", "x".repeat(64)]) assert.equal(idValido(ok), true, ok);
  for (const mal of ["", "x".repeat(65), "../x", "a b", "a/b", "a.b", "ñ", null, undefined, 5]) assert.equal(idValido(mal), false, String(mal));
});

test("ids invalidos se rechazan al guardar y al leer (nunca salen de checkpoints/)", async () => {
  const dir = tmp();
  for (const id of ["../fuera", "a/b", ""]) {
    await assert.rejects(guardarCheckpoint(id, { x: 1 }, { env: envCon(dir) }), { code: "CHECKPOINT_ID_INVALIDO" });
    await assert.rejects(leerCheckpoint(id, { env: envCon(dir) }), { code: "CHECKPOINT_ID_INVALIDO" });
  }
  assert.equal(fs.existsSync(path.join(dir, "checkpoints")), false);
});

test("sin Harness: degrada a BRIDGE_STATE_DIR/checkpoints/<id>.json (atomico, sin .tmp) y se lee de vuelta", async () => {
  const dir = tmp();
  const r = await guardarCheckpoint("t1", { estado: "RUNNING", n: 2 }, { env: envCon(dir) });
  assert.equal(r.local, true); assert.equal(r.harness, false);
  const f = path.join(dir, "checkpoints", "t1.json");
  assert.ok(fs.existsSync(f));
  assert.deepEqual(fs.readdirSync(path.join(dir, "checkpoints")), ["t1.json"], "sin archivos temporales");
  const ck = await leerCheckpoint("t1", { env: envCon(dir) });
  assert.equal(ck.estado, "RUNNING"); assert.equal(ck.n, 2); assert.ok(ck.ts);
  assert.equal(await leerCheckpoint("no-existe", { env: envCon(dir) }), null);
});

test("un archivo local corrupto se trata como ausente (no rompe)", async () => {
  const dir = tmp(); fs.mkdirSync(path.join(dir, "checkpoints"));
  fs.writeFileSync(path.join(dir, "checkpoints", "roto.json"), "{no es json");
  assert.equal(await leerCheckpoint("roto", { env: envCon(dir) }), null);
});

test("con Harness: usa la ruta, cabecera y formato REALES de /invoke y guarda tambien en local", async () => {
  const h = await harnessFalso(); const dir = tmp();
  try {
    const env = envCon(dir, { RIU_DEEPSEEK_HARNESS_URL: h.url + "/", RIU_API_KEY: CLAVE_HARNESS });
    const r = await guardarCheckpoint("tarea-9", { estado: "RUNNING", parcial: "AAA" }, { env });
    assert.deepEqual([r.local, r.harness], [true, true]);
    assert.equal(h.peticiones.length, 1);
    const p = h.peticiones[0];
    assert.equal(p.method, "POST"); assert.equal(p.url, "/invoke"); assert.equal(p.clave, CLAVE_HARNESS);
    assert.equal(p.cuerpo.action, "invoke"); assert.equal(p.cuerpo.tool, "guardar");
    assert.equal(p.cuerpo.args.nombre, "tareas/swe/tarea-9/checkpoint.json");
    assert.equal(typeof p.cuerpo.args.valor, "string");
    assert.equal(JSON.parse(p.cuerpo.args.valor).parcial, "AAA");
    assert.ok(fs.existsSync(path.join(dir, "checkpoints", "tarea-9.json")), "ambos");
    // reinicio: el disco local se pierde, el Harness conserva el checkpoint
    fs.rmSync(path.join(dir, "checkpoints"), { recursive: true });
    const ck = await leerCheckpoint("tarea-9", { env });
    assert.equal(ck.parcial, "AAA");
    const l = h.peticiones.at(-1).cuerpo; assert.equal(l.tool, "leer"); assert.deepEqual(l.args, { nombre: "tareas/swe/tarea-9/checkpoint.json" });
  } finally { h.cerrar(); }
});

test("RIU_DEEPSEEK_HARNESS_API_KEY y RIU_DEEPSEEK_HARNESS_PATH mandan sobre RIU_API_KEY y /invoke (como plugin.py)", async () => {
  const h = await harnessFalso({ clave: "otra-falsa" }); const dir = tmp();
  try {
    const env = envCon(dir, { RIU_DEEPSEEK_HARNESS_URL: h.url, RIU_API_KEY: "ignorada", RIU_DEEPSEEK_HARNESS_API_KEY: "otra-falsa", RIU_DEEPSEEK_HARNESS_PATH: "/h/invoke" });
    const r = await guardarCheckpoint("t2", { a: 1 }, { env });
    assert.equal(r.harness, true); assert.equal(h.peticiones[0].url, "/h/invoke");
  } finally { h.cerrar(); }
});

test("Harness caido, con error o con clave mala: el checkpoint NO se pierde (queda en local) y no lanza", async () => {
  const dir = tmp();
  const caido = await harnessFalso(); const urlCaida = caido.url; caido.cerrar();
  let r = await guardarCheckpoint("c1", { v: 1 }, { env: envCon(dir, { RIU_DEEPSEEK_HARNESS_URL: urlCaida, RIU_API_KEY: CLAVE_HARNESS }) });
  assert.deepEqual([r.local, r.harness], [true, false]); assert.ok(r.harness_error);
  assert.equal((await leerCheckpoint("c1", { env: envCon(dir, { RIU_DEEPSEEK_HARNESS_URL: urlCaida, RIU_API_KEY: CLAVE_HARNESS }) })).v, 1);
  const err = await harnessFalso({ modo: "error" });
  try {
    r = await guardarCheckpoint("c2", { v: 2 }, { env: envCon(dir, { RIU_DEEPSEEK_HARNESS_URL: err.url, RIU_API_KEY: CLAVE_HARNESS }) });
    assert.deepEqual([r.local, r.harness], [true, false]);
    r = await guardarCheckpoint("c3", { v: 3 }, { env: envCon(dir, { RIU_DEEPSEEK_HARNESS_URL: err.url, RIU_API_KEY: "mala" }) });
    assert.deepEqual([r.local, r.harness], [true, false]);
    assert.ok(!JSON.stringify(r).includes("mala"), "el error no repite la clave");
  } finally { err.cerrar(); }
});

test("timeout: un Harness que no contesta no cuelga (timeoutMs inyectable; por defecto 30 s)", async () => {
  const h = await harnessFalso({ modo: "colgar" }); const dir = tmp();
  try {
    const t0 = Date.now();
    const r = await guardarCheckpoint("lento", { v: 1 }, { env: envCon(dir, { RIU_DEEPSEEK_HARNESS_URL: h.url, RIU_API_KEY: CLAVE_HARNESS }), timeoutMs: 150 });
    assert.ok(Date.now() - t0 < 3000); assert.deepEqual([r.local, r.harness], [true, false]);
    assert.equal(await leerCheckpoint("lento", { env: envCon(dir, { RIU_DEEPSEEK_HARNESS_URL: h.url, RIU_API_KEY: CLAVE_HARNESS }), timeoutMs: 150 }).then((c) => c.v), 1, "lee de local");
  } finally { h.cerrar(); }
  // el valor por defecto es 30 s
  const { TIMEOUT_MS } = await import("../src/checkpoint_hf.js"); assert.equal(TIMEOUT_MS, 30000);
});

test("URL del Harness no segura (http a un host externo, con usuario:clave) se ignora: nada sale, solo local", async () => {
  const dir = tmp();
  for (const u of ["http://harness.ejemplo.com", "http://u:p@127.0.0.1:9", "ftp://x", "no-es-url"]) {
    let llamado = false;
    const r = await guardarCheckpoint("u1", { v: 1 }, { env: envCon(dir, { RIU_DEEPSEEK_HARNESS_URL: u, RIU_API_KEY: CLAVE_HARNESS }), fetch: async () => { llamado = true; throw new Error("no debe salir"); } });
    assert.equal(llamado, false, u); assert.deepEqual([r.local, r.harness], [true, false]);
  }
});

test("lee el mas reciente entre Harness y local (si el local quedo atrasado)", async () => {
  const h = await harnessFalso(); const dir = tmp();
  try {
    const env = envCon(dir, { RIU_DEEPSEEK_HARNESS_URL: h.url, RIU_API_KEY: CLAVE_HARNESS });
    await guardarCheckpoint("n1", { v: "viejo" }, { env: envCon(dir) });  // solo local
    await new Promise((ok) => setTimeout(ok, 15));
    await guardarCheckpoint("n1", { v: "nuevo" }, { env: { ...env, BRIDGE_STATE_DIR: tmp() } });  // otro disco + Harness
    assert.equal((await leerCheckpoint("n1", { env })).v, "nuevo");
  } finally { h.cerrar(); }
});

test("sanear: elimina campos con pinta de clave (authorization, api_key, claves, token...) y valores con forma de clave", () => {
  const limpio = sanear({
    headers: { Authorization: "Bearer gsk_FALSA1234567890", "x-api-key": "k-falsa", "Content-Type": "json" },
    api_key: "abc", apiKey: "abc", claves: { groq: ["gsk_FALSA1234567890"], nvidia: ["nvapi-FALSA1234567890"] }, token: "t", access_token: "t", secret: "s", password: "p",
    max_tokens: 100, modelo: "m",
    texto: "usa gsk_FALSA1234567890 y nvapi-FALSA1234567890 y sk-FALSA123456789012 y hf_FALSA1234567890123456789",
    args: '{"api_key":"valor-secreto","x":1}', lista: [{ authorization: "z", ok: 1 }],
  }, ["literal-secreto-xyz"]);
  const j = JSON.stringify(limpio);
  for (const mal of ["gsk_FALSA", "nvapi-FALSA", "sk-FALSA", "hf_FALSA", "valor-secreto", "k-falsa"]) assert.ok(!j.includes(mal), mal + " -> " + j);
  assert.ok(!("api_key" in limpio) && !("claves" in limpio) && !("token" in limpio) && !("headers" in limpio), "las cabeceras no se guardan");
  assert.equal(limpio.max_tokens, 100); assert.equal(limpio.modelo, "m");
  assert.deepEqual(limpio.lista, [{ ok: 1 }]);
  assert.ok(!JSON.stringify(sanear({ t: "tiene literal-secreto-xyz dentro" }, ["literal-secreto-xyz"])).includes("literal-secreto-xyz"));
  assert.deepEqual(sanear(sanear(limpio)), limpio, "idempotente");
});

test("lo guardado (local y Harness) nunca lleva claves ni cabeceras", async () => {
  const h = await harnessFalso(); const dir = tmp();
  try {
    const env = envCon(dir, { RIU_DEEPSEEK_HARNESS_URL: h.url, RIU_API_KEY: CLAVE_HARNESS });
    await guardarCheckpoint("s1", { estado: "RUNNING", authorization: "Bearer gsk_FALSA1234567890", claves: { groq: ["gsk_FALSA1234567890"] }, token: "t-falso", salida: "mi clave es secreto-literal-7 ok" }, { env, secretos: ["secreto-literal-7"] });
    const local = fs.readFileSync(path.join(dir, "checkpoints", "s1.json"), "utf8");
    const remoto = h.peticiones[0].crudo;
    for (const txt of [local, remoto]) for (const mal of ["gsk_FALSA", "t-falso", "secreto-literal-7", CLAVE_HARNESS]) assert.ok(!txt.includes(mal), mal);
    assert.equal(JSON.parse(local).estado, "RUNNING");
  } finally { h.cerrar(); }
});
