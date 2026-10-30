import test from "node:test";
import assert from "node:assert/strict";
import fs from "node:fs";

import os from "node:os";
import path from "node:path";
const dir = fs.mkdtempSync(path.join(os.tmpdir(), "memo-"));
fs.writeFileSync(path.join(dir, "fake.sh"), '#!/bin/sh\necho "$@" >> "$FAKE_LOG"; cat >> "$FAKE_LOG"; echo \'{"ok": true}\'\n', { mode: 0o755 });
process.env.FAKE_LOG = path.join(dir, "log.txt");
process.env.RIU_MEMORIA_CMD = path.join(dir, "fake.sh");
process.env.HF_TOKEN = "hf-prueba";
const { guardarTurno, scopeDe } = await import("../src/memoria.js");

test("el scope es el mismo esquema del historial del chat (chat-ui:hist:<sesion>)", () => {
  assert.equal(scopeDe("Mi Proyecto"), "chat-ui:hist:openclaw-mi-proyecto");
  assert.equal(scopeDe(null), null);
});

test("guarda el turno (usuario y respuesta) con la forma que usa el chat", async () => {
  fs.rmSync(process.env.FAKE_LOG, { force: true });
  const ok = await guardarTurno("chat-2", "hola", "respuesta", "web-qwen38max");
  assert.ok(ok);
  const log = fs.readFileSync(process.env.FAKE_LOG, "utf8");
  assert.match(log, /save chat-ui:hist:openclaw-chat-2 m-\d+-user/); assert.match(log, /save chat-ui:hist:openclaw-chat-2 m-\d+-bot/);
  assert.match(log, /"rol":\s*"bot"/); assert.match(log, /"texto":\s*"respuesta"/);
});

test("sin sesion o sin HF_TOKEN no hace nada ni lanza", async () => {
  assert.equal(await guardarTurno(null, "a", "b", "m"), false);
  const t = process.env.HF_TOKEN; delete process.env.HF_TOKEN;
  assert.equal(await guardarTurno("x", "a", "b", "m"), false);
  process.env.HF_TOKEN = t;
});
