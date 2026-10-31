import test from "node:test";
import assert from "node:assert/strict";
import fs from "node:fs";
import os from "node:os";
import path from "node:path";

process.env.BRIDGE_STATE_DIR = fs.mkdtempSync(path.join(os.tmpdir(), "bridge-rec-"));
const B = await import("../src/bloques.js");
const CK = path.join(process.env.BRIDGE_STATE_DIR, "checkpoints");

test("el checkpoint guarda tokens/secciones, tarea, paso, estado, proveedor/modelo y sobrevive a 'reinicio' (releer del disco)", () => {
  B.checkpointGuardar("rec-1", {
    modo: "solucion", total: 4, enviados: 2, huella: B.huella("T"),
    tarea: "arreglar login", paso: "revisa", estado: "WAIT_TOOLS",
    tokens_recibidos: 1234, secciones_recibidas: [1, 2],
    proveedor: "groq", modelo: "qwen/qwen3.8-27b",
  });
  const c = B.checkpointCrudo("rec-1");
  assert.equal(c.tarea, "arreglar login"); assert.equal(c.paso, "revisa"); assert.equal(c.estado, "WAIT_TOOLS");
  assert.equal(c.tokens_recibidos, 1234); assert.deepEqual(c.secciones_recibidas, [1, 2]);
  assert.equal(c.proveedor, "groq"); assert.equal(c.modelo, "qwen/qwen3.8-27b");
  assert.equal(B.checkpointLeer("rec-1", B.huella("T")).enviados, 2);
  const l = B.listarCheckpoints().find((s) => s.conv_id === "rec-1");
  assert.equal(l.estado, "WAIT_TOOLS"); assert.equal(l.paso, "revisa"); assert.equal(l.proveedor, "groq");
});

test("estado invalido se normaliza; sin estado: CONTINUAR, o DONE si completo", () => {
  B.checkpointGuardar("rec-2", { enviados: 1, total: 2, estado: "banana" });
  assert.equal(B.checkpointCrudo("rec-2").estado, "CONTINUAR");
  B.checkpointGuardar("rec-3", { enviados: 2, total: 2, completo: true });
  assert.equal(B.checkpointCrudo("rec-3").estado, "DONE");
  B.checkpointGuardar("rec-4", { enviados: 1, total: 2, estado: "error" });
  assert.equal(B.checkpointCrudo("rec-4").estado, "ERROR");
});

test("un checkpoint en estado DONE no se retoma aunque no traiga completo", () => {
  B.checkpointGuardar("rec-5", { enviados: 2, total: 2, estado: "DONE", huella: B.huella("Z") });
  assert.equal(B.checkpointLeer("rec-5", B.huella("Z")), null);
});

test("herramienta con ID: confirmar una vez, consultar si ya se ejecuto, no se pisa el primer resultado", () => {
  B.checkpointGuardar("tool-1", { enviados: 1, total: 3, huella: B.huella("H") });
  assert.equal(B.herramientaEjecutada("tool-1", "call_abc"), false);
  assert.equal(B.herramientaConfirmar("tool-1", "call_abc", { ok: true, salida: "hecho" }), true);
  assert.equal(B.herramientaEjecutada("tool-1", "call_abc"), true);
  assert.deepEqual(B.herramientaResultado("tool-1", "call_abc"), { ok: true, salida: "hecho" });
  assert.equal(B.herramientaConfirmar("tool-1", "call_abc", { ok: false, salida: "otra" }), false);  // idempotente
  assert.equal(B.herramientaResultado("tool-1", "call_abc").salida, "hecho");
  assert.equal(B.herramientaEjecutada("tool-1", "call_otro"), false);
  assert.equal(B.herramientaEjecutada("sin-checkpoint", "x"), false);
  assert.equal(B.herramientaEjecutada("tool-1", ""), false);
});

test("las herramientas confirmadas sobreviven a un checkpointGuardar posterior con estado en memoria viejo", () => {
  B.checkpointGuardar("tool-2", { enviados: 1, total: 3, huella: B.huella("H2") });
  B.herramientaConfirmar("tool-2", "id-1", "r1");
  B.checkpointGuardar("tool-2", { enviados: 2, total: 3, huella: B.huella("H2") });  // el motor guarda su ck sin herramientas
  assert.equal(B.herramientaEjecutada("tool-2", "id-1"), true);
  assert.equal(B.checkpointCrudo("tool-2").enviados, 2);
  // tarea distinta (otra huella) con el mismo conv_id: no hereda herramientas viejas
  B.checkpointGuardar("tool-2", { enviados: 0, total: 5, huella: B.huella("OTRA") });
  assert.equal(B.herramientaEjecutada("tool-2", "id-1"), false);
});

test("confirmar sin checkpoint previo crea uno y el conv_id se sanea", () => {
  assert.equal(B.herramientaConfirmar("../../evil", "t1", "x"), true);
  assert.ok(!fs.existsSync(path.join(process.env.BRIDGE_STATE_DIR, "evil.json")));
  assert.equal(B.herramientaEjecutada("../../evil", "t1"), true);
});

test("el checkpoint NUNCA guarda claves, cabeceras ni tokens de autenticacion (ni en anidados ni en texto)", () => {
  const secreto = "gsk_" + "A".repeat(30), nv = "nvapi-" + "B".repeat(30);
  B.checkpointGuardar("sec-1", {
    modo: "m", enviados: 1, total: 2, tokens_recibidos: 77,
    authorization: "Bearer " + secreto, api_key: secreto, apiKey: secreto, GROQ_API_KEY: secreto,
    headers: { Authorization: "Bearer " + nv, "x-api-key": nv }, cabeceras: { a: 1 },
    token: "tok", access_token: "tok", clave: "c", cookie: "sid=1",
    anidado: { dentro: { password: "p", secret: "s", ok: "visible" } },
    ultima_salida: "usa Authorization: Bearer " + secreto + " y " + nv + " fin",
  });
  B.herramientaConfirmar("sec-1", "tc1", { salida: "ok", headers: { Authorization: "Bearer " + secreto }, api_key: nv });
  const crudo = fs.readFileSync(path.join(CK, "sec-1.json"), "utf8");
  for (const mal of [secreto, nv, "Bearer ", "sid=1", '"tok"', '"p"']) assert.ok(!crudo.includes(mal), "no debe aparecer: " + mal);
  const c = JSON.parse(crudo);
  assert.equal(c.tokens_recibidos, 77, "los contadores de tokens recibidos si se guardan");
  assert.equal(c.anidado.dentro.ok, "visible");
  assert.equal(B.herramientaResultado("sec-1", "tc1").salida, "ok");
  assert.ok(!("headers" in c) && !("authorization" in c));
});

test("escritura atomica: si falla el rename el checkpoint anterior queda intacto y no queda .tmp", () => {
  B.checkpointGuardar("atom-1", { enviados: 1, total: 3, ultima_salida: "BUENO" });
  const orig = fs.renameSync;
  fs.renameSync = () => { throw new Error("corte simulado"); };
  try { assert.throws(() => B.checkpointGuardar("atom-1", { enviados: 2, total: 3, ultima_salida: "NUEVO" }), /corte/); }
  finally { fs.renameSync = orig; }
  assert.equal(B.checkpointCrudo("atom-1").ultima_salida, "BUENO");
  assert.deepEqual(fs.readdirSync(CK).filter((f) => !f.endsWith(".json")), []);
});

test("la carpeta de estado es absoluta, sigue a BRIDGE_STATE_DIR y no depende del cwd", () => {
  assert.equal(B.estadoDir(), path.resolve(process.env.BRIDGE_STATE_DIR));
  const cwd = process.cwd(), otro = fs.mkdtempSync(path.join(os.tmpdir(), "cwd-"));
  try {
    process.chdir(otro);
    B.checkpointGuardar("cwd-1", { enviados: 1, total: 2 });
    assert.ok(fs.existsSync(path.join(CK, "cwd-1.json")));
    assert.ok(!fs.existsSync(path.join(otro, "state")));
  } finally { process.chdir(cwd); }
});

test("sin BRIDGE_STATE_DIR el defecto es relativo al modulo, no al cwd, y se marca como no persistente si cae en tmp", () => {
  const prev = process.env.BRIDGE_STATE_DIR;
  try {
    delete process.env.BRIDGE_STATE_DIR;
    const d = B.estadoDir();
    assert.ok(path.isAbsolute(d)); assert.ok(d.endsWith(path.join("web-bridge", "state")));
    process.env.BRIDGE_STATE_DIR = "/tmp/x-estado";
    assert.equal(B.estadoEfimero(), true);
    process.env.BRIDGE_STATE_DIR = "/data/estado";
    assert.equal(B.estadoEfimero(), false);
  } finally { process.env.BRIDGE_STATE_DIR = prev; }
});
