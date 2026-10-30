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
