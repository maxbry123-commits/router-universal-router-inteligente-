import test from "node:test";
import assert from "node:assert/strict";
import { execFileSync } from "node:child_process";
import { mkdtempSync, cpSync, readdirSync, readFileSync, rmSync } from "node:fs";
import { tmpdir } from "node:os";
import { join, dirname } from "node:path";
import { fileURLToPath } from "node:url";

const AQUI = join(dirname(fileURLToPath(import.meta.url)), "..");
const SHA = "abcdef123456";

function construir() {
  const d = mkdtempSync(join(tmpdir(), "riu-build-"));
  cpSync(AQUI, d, { recursive: true });
  const env = { ...process.env, VERCEL_GIT_COMMIT_SHA: SHA + "7890" };
  execFileSync("sh", ["build.sh"], { cwd: d, env });
  return d;
}
// en .js solo los imports (build.sh no toca el ?v= del css que pone pensando-3d.js a mano); en .html js y css
const versiones = (txt, f) => [...txt.matchAll(f.endsWith(".html") ? /\.(?:js|css)\?v=([0-9a-f]+)/g : /\.js\?v=([0-9a-f]+)/g)].map((m) => m[1]);

test("Vercel: ninguna URL del chat queda con un ?v= viejo; todas llevan el commit actual", () => {
  const d = construir();
  try {
    const malos = [];
    for (const f of readdirSync(d).filter((x) => /\.(js|html)$/.test(x))) {
      for (const v of versiones(readFileSync(join(d, f), "utf8"), f)) if (v !== SHA) malos.push(f + ":" + v);
    }
    assert.deepEqual(malos, []);
    const shell = readFileSync(join(d, "shell.html"), "utf8");
    assert.match(shell, new RegExp("/chat/ui/shell\\.js\\?v=" + SHA + '"'));
  } finally { rmSync(d, { recursive: true, force: true }); }
});

test("build.sh es idempotente: correrlo dos veces deja los mismos archivos", () => {
  const d = construir();
  try {
    const antes = readFileSync(join(d, "shell.js"), "utf8") + readFileSync(join(d, "shell.html"), "utf8");
    execFileSync("sh", ["build.sh"], { cwd: d, env: { ...process.env, VERCEL_GIT_COMMIT_SHA: SHA + "7890" } });
    assert.equal(readFileSync(join(d, "shell.js"), "utf8") + readFileSync(join(d, "shell.html"), "utf8"), antes);
  } finally { rmSync(d, { recursive: true, force: true }); }
});

test("el fuente de git no trae ?v= fijos (Hugging Face sirve el fuente tal cual, Vercel pone el commit)", () => {
  const fijos = [];
  for (const f of readdirSync(AQUI).filter((x) => /\.(js|html)$/.test(x))) {
    if (versiones(readFileSync(join(AQUI, f), "utf8"), f).length) fijos.push(f);
  }
  assert.deepEqual(fijos, []);
});
