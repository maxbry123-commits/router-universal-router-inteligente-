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

// ---- verificacion previa al relanzamiento: node --check de los .js tocados (copia a .mjs) y npm install; si falla NO se relanza (sin git reset) ----
const conLog = async (fn) => { const lineas = []; const w = console.warn; console.warn = (...a) => lineas.push(a.join(" ")); try { return { r: await fn(), lineas }; } finally { console.warn = w; } };

test("un .js roto en el codigo nuevo: NO se relanza, NO se toca el repo (sin git reset --hard: no hay flapping con el autopull) y el log es corto", async () => {
  const d = repo(); const previa = git(d, "rev-parse", "HEAD"); const estado = { cabeza: previa }; let relanzado = 0;
  commit(d, "chat-router/SWE CODE/web-bridge/a.js", "const = ;;; esto no compila");
  const rota = git(d, "rev-parse", "HEAD");
  const { r, lineas } = await conLog(() => revisar({ repo: d, estado, relanzar: async () => { relanzado++; } }));
  assert.equal(relanzado, 0, "no se relanza con codigo roto"); assert.equal(r, false);
  assert.equal(git(d, "rev-parse", "HEAD"), rota, "el repo queda donde esta: ningun reset");
  assert.equal(fs.readFileSync(path.join(d, "chat-router", "SWE CODE", "web-bridge", "a.js"), "utf8"), "const = ;;; esto no compila", "el archivo no se revierte");
  assert.ok(lineas.length <= 2 && lineas.join("").length < 300, "log corto: " + lineas.join(" | "));
  assert.ok(lineas.join("").includes("rechazado"), "deja la linea de log"); assert.ok(!lineas.join("").includes("reset"), "no menciona reset");
  assert.ok(!lineas.join("").includes("esto no compila"), "no vuelca el codigo");
  // la misma cabeza rota no vuelve a registrar el log ni a relanzar
  const otra = await conLog(() => revisar({ repo: d, estado, relanzar: async () => { relanzado++; } })); assert.equal(otra.lineas.length, 0);
  // un commit que NO toca el archivo roto tampoco relanza (sigue roto en el disco)
  commit(d, "chat-router/SWE CODE/web-bridge/otro.js", "export const y = 1;");
  await conLog(() => revisar({ repo: d, estado, relanzar: async () => { relanzado++; } })); assert.equal(relanzado, 0, "el .js roto sigue en el arbol: no se relanza");
  // un commit que lo ARREGLA si se relanza
  commit(d, "chat-router/SWE CODE/web-bridge/a.js", "3");
  await revisar({ repo: d, estado, relanzar: async () => { relanzado++; } });
  assert.equal(relanzado, 1);
});

test("se revisan solo los .js tocados dentro de las rutas del bridge; un .js roto fuera (frontend) no impide el relanzamiento; los borrados se ignoran", async () => {
  const d = repo(); const estado = { cabeza: git(d, "rev-parse", "HEAD") }; let relanzado = 0;
  fs.writeFileSync(path.join(d, "chat-router", "chat", "frontend", "roto.js"), "const = ;");
  fs.writeFileSync(path.join(d, "chat-router", "SWE CODE", "web-bridge", "b.js"), "export const x = 1;");
  git(d, "add", "-A"); git(d, "commit", "-qm", "dos");
  await revisar({ repo: d, estado, relanzar: async () => { relanzado++; } });
  assert.equal(relanzado, 1);
  fs.rmSync(path.join(d, "chat-router", "SWE CODE", "web-bridge", "b.js")); git(d, "add", "-A"); git(d, "commit", "-qm", "borra");
  await revisar({ repo: d, estado, relanzar: async () => { relanzado++; } });
  assert.equal(relanzado, 2);
});

test("si cambia package.json se ejecuta npm install ANTES de relanzar; si falla: no se relanza ni se hace reset; si pasa se relanza con deps", async () => {
  const d = repo(); const previa = git(d, "rev-parse", "HEAD"); const estado = { cabeza: previa }; const rel = []; const inst = [];
  commit(d, "chat-router/SWE CODE/web-bridge/package.json", "{}");
  const mala = git(d, "rev-parse", "HEAD");
  await conLog(() => revisar({ repo: d, estado, relanzar: async (o) => { rel.push(o); }, instalar: async () => { inst.push(1); return false; } }));
  assert.equal(inst.length, 1); assert.equal(rel.length, 0); assert.equal(git(d, "rev-parse", "HEAD"), mala, "sin reset");
  commit(d, "chat-router/SWE CODE/web-bridge/package.json", '{"name":"x"}');
  await revisar({ repo: d, estado, relanzar: async (o) => { rel.push(o); }, instalar: async () => { inst.push(1); return true; } });
  assert.equal(inst.length, 2); assert.deepEqual(rel, [{ deps: true }]);
});

test("sin cambios de package.json no se ejecuta npm install", async () => {
  const d = repo(); const estado = { cabeza: git(d, "rev-parse", "HEAD") }; let inst = 0, rel = 0;
  commit(d, "chat-router/SWE CODE/web-bridge/a.js", "4");
  await revisar({ repo: d, estado, relanzar: async () => { rel++; }, instalar: async () => { inst++; return true; } });
  assert.equal(inst, 0); assert.equal(rel, 1);
});
