import test from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";

const html = readFileSync(new URL("../panel-apariencia.html", import.meta.url), "utf8");

test("el APK se descarga desde el principio de Configuración, justo después de Control", () => {
  const secciones = [...html.matchAll(/<section class="ap-sec" aria-labelledby="([^"]+)"/g)].map((m) => m[1]);
  assert.equal(secciones[0], "ap-h-ctl");
  assert.equal(secciones[1], "ap-h-apk");
  assert.equal([...html.matchAll(/id="ap-apk"/g)].length, 1);
  assert.match(html, /<a id="ap-apk"[^>]*href="[^"]*\/apk"[^>]*download/);
});
