import test from "node:test";
import assert from "node:assert/strict";
import { existsSync, readFileSync, readdirSync } from "node:fs";
import { dirname, join, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const root = resolve(dirname(fileURLToPath(import.meta.url)), "..");

test("the named HTML entry points to separately editable CSS and JS modules", () => {
  const html = readFileSync(join(root, "chat Yaiwes fromtend.html"), "utf8");
  for (const file of ["styles/tokens.css", "styles/chat.css", "src/app.js"]) {
    assert.ok(html.includes(`./${file}`));
    assert.ok(existsSync(join(root, file)));
  }
  assert.ok(!html.includes("<style"));
  assert.match(html, /No se cargaron los módulos del chat/);
  assert.deepEqual([...html.matchAll(/<script\b[^>]*>/g)].map(match => match[0]), [
    '<script type="module" src="./src/app.js">'
  ]);
  assert.ok(!existsSync(join(root, "index.html")));
});

test("all frontend module imports resolve inside this folder", () => {
  const visit = directory => {
    for (const entry of readdirSync(directory, { withFileTypes: true })) {
      const file = join(directory, entry.name);
      if (entry.isDirectory()) visit(file);
      else if (entry.name.endsWith(".js")) {
        const source = readFileSync(file, "utf8");
        for (const [, importPath] of source.matchAll(/from ["'](\.[^"']+)["']/g)) {
          const target = resolve(directory, importPath);
          assert.ok(target.startsWith(join(root, "src")), `Import escaped frontend: ${target}`);
          assert.ok(existsSync(target), `Missing import: ${target}`);
        }
      }
    }
  };
  visit(join(root, "src"));
});
