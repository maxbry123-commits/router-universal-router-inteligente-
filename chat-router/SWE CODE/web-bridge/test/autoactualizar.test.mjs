import test from "node:test";
import assert from "node:assert/strict";
import fs from "node:fs";
import os from "node:os";
import path from "node:path";
import { execFileSync } from "node:child_process";
import { revisar, RUTAS } from "../src/autoactualizar.js";

const git = (dir, ...a) => execFileSync("git", ["-C", dir, "-c", "user.email=t@t", "-c", "user.name=t", ...a], { encoding: "utf8" }).trim();
function repo() {
  const d = fs.mkdtempSync(path.join(os.tmpdir(), "auto-"));
  git(d, "init", "-q"); fs.mkdirSync(path.join(d, "chat-router", "SWE CODE", "web-bridge"), { recursive: true });
  fs.mkdirSync(path.join(d, "chat-router", "chat", "frontend"), { recursive: true });
  fs.writeFileSync(path.join(d, "chat-router", "SWE CODE", "web-bridge", "a.js"), "1"); git(d, "add", "-A"); git(d, "commit", "-qm", "base");
  return d;
}
const commit = (d, rel, txt) => { fs.writeFileSync(path.join(d, rel), txt); git(d, "add", "-A"); git(d, "commit", "-qm", txt); };

test("un cambio en SWE CODE o SWE CODE free hace que el bridge se relance solo", async () => {
  const d = repo(); const estado = { cabeza: git(d, "rev-parse", "HEAD") }; let relanzado = 0;
  await revisar({ repo: d, estado, relanzar: async () => { relanzado++; } });
  assert.equal(relanzado, 0, "sin cambios no se relanza");
  commit(d, "chat-router/SWE CODE/web-bridge/a.js", "2");
  await revisar({ repo: d, estado, relanzar: async () => { relanzado++; } });
  assert.equal(relanzado, 1);
});

test("un cambio que no es del bridge (frontend, docs) no lo relanza pero se da por visto", async () => {
  const d = repo(); const estado = { cabeza: git(d, "rev-parse", "HEAD") }; let relanzado = 0;
  commit(d, "chat-router/chat/frontend/x.js", "x");
  await revisar({ repo: d, estado, relanzar: async () => { relanzado++; } });
  assert.equal(relanzado, 0); assert.equal(estado.cabeza, git(d, "rev-parse", "HEAD"));
  await revisar({ repo: d, estado, relanzar: async () => { relanzado++; } });
  assert.equal(relanzado, 0);
});

test("si el directorio no es un repo git no hace nada ni lanza", async () => {
  const d = fs.mkdtempSync(path.join(os.tmpdir(), "nogit-")); let relanzado = 0;
  await revisar({ repo: d, estado: { cabeza: "x" }, relanzar: async () => { relanzado++; } });
  assert.equal(relanzado, 0);
});

test("vigila las rutas del bridge, de SWE CODE free y el formato de salida", () => {
  for (const r of ["chat-router/SWE CODE/", "chat-router/SWE CODE free/", "chat-router/chat/backend/mvp/prompts/"]) assert.ok(RUTAS.includes(r), r);
});
