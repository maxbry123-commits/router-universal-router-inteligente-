import test from "node:test";
import assert from "node:assert/strict";
import fs from "node:fs";
import os from "node:os";
import path from "node:path";

process.env.BRIDGE_STATE_DIR = fs.mkdtempSync(path.join(os.tmpdir(), "bridge-"));
const { checkpointLeer, checkpointGuardar, huella, listarCheckpoints } = await import("../src/bloques.js");

test("un checkpoint completo NO se reutiliza para una tarea nueva con el mismo conv_id", () => {
  checkpointGuardar("chat-2", { modo: "solucion", total: 3, enviados: 3, ultima_salida: "respuesta vieja", completo: true, huella: huella("tarea A") });
  assert.equal(checkpointLeer("chat-2", huella("tarea B")), null);
});

test("un checkpoint completo tampoco se retoma aunque sea la misma tarea (ya termino)", () => {
  checkpointGuardar("chat-3", { modo: "solucion", total: 2, enviados: 2, ultima_salida: "ok", completo: true, huella: huella("X") });
  assert.equal(checkpointLeer("chat-3", huella("X")), null);
});

test("un checkpoint a medias de la MISMA tarea se retoma; de otra tarea, no", () => {
  checkpointGuardar("chat-4", { modo: "revision", total: 4, enviados: 2, ultima_salida: "parcial", huella: huella("T") });
  assert.equal(checkpointLeer("chat-4", huella("T")).enviados, 2);
  assert.equal(checkpointLeer("chat-4", huella("otra")), null);
});

test("listarCheckpoints dice a OpenClaw que secciones hay, en que bloque van y cuales terminaron", () => {
  const l = listarCheckpoints();
  const por = Object.fromEntries(l.map((s) => [s.conv_id, s]));
  assert.equal(por["chat-4"].enviados, 2); assert.equal(por["chat-4"].total, 4); assert.equal(por["chat-4"].completo, false);
  assert.equal(por["chat-2"].completo, true);
  assert.ok(!("ultima_salida" in por["chat-4"]));  // la lista no vuelca contenido
});

test("el bridge registra solo lo que repara (leccion) en el mismo formato que lee evolucion.py", async () => {
  const { registrarLeccion } = await import("../src/bloques.js");
  registrarLeccion({ codigo: "SESSION_EXPIRED", accion: "salud() + reintento", resultado: "PASS", modelo: "web-qwen38max" });
  const f = path.join(process.env.BRIDGE_STATE_DIR, "evolucion", "lecciones.jsonl");
  const l = JSON.parse(fs.readFileSync(f, "utf8").trim().split("\n").pop());
  assert.equal(l.codigo, "SESSION_EXPIRED"); assert.equal(l.resultado, "PASS"); assert.ok(l.ts > 1e9);
  registrarLeccion({ accion: "sin codigo" });  // sin codigo no escribe ni lanza
  assert.equal(fs.readFileSync(f, "utf8").trim().split("\n").length, 1);
});

test("proponerMejoras: lo que se repite 3 veces con exito se promueve al runbook y lo que falla 3 veces cambia de estrategia", async () => {
  const { registrarLeccion, proponerMejoras } = await import("../src/bloques.js");
  for (let i = 0; i < 3; i++) registrarLeccion({ codigo: "AGE_GATE", accion: "click Continuar", resultado: "PASS" });
  for (let i = 0; i < 3; i++) registrarLeccion({ codigo: "SELECTOR_BROKEN", accion: "reintento", resultado: "FAIL" });
  registrarLeccion({ codigo: "RARO", accion: "una vez", resultado: "PASS" });
  const p = proponerMejoras();
  assert.ok(p.some((x) => x.codigo === "AGE_GATE" && x.tipo === "promover_a_runbook" && x.veces >= 3));
  assert.ok(p.some((x) => x.codigo === "SELECTOR_BROKEN" && x.tipo === "cambiar_estrategia"));
  assert.ok(!p.some((x) => x.codigo === "RARO"));
});
