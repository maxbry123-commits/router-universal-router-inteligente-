// Regresiones de duplicación: un selector real y un solo mensaje de respuesta.
import test from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
const src = (f) => readFileSync(new URL("../" + f, import.meta.url), "utf8");

test("Groq y NVIDIA permanecen en un unico selector de modelos, sin filas duplicadas", () => {
  const s = src("selector-modelos.js"), c = src("selector-modelos.css");
  assert.match(s, /id = "modelo-unificado"/);
  for (const id of ["groq/qwen/qwen3.8-27b", "nvidia/minimaxai/minimax-m3.1-flash",
    "nvidia/meta/muse-glimmer-30b", "nvidia/nvidia/nemotron-3-ultra-550b-a55b", "nvidia/z-ai/glm-5.3"])
    assert.ok(s.includes(id), id);
  assert.match(c, /\.sel-fila\[data-selector="groq"\]/);
  assert.match(c, /\.sel-fila\[data-selector="nvidia-groq-team"\]/);
  assert.match(c, /#sh-selectores #selectores \.sel-resp-global/);
});

test("Una respuesta del proveedor crea un globo, no otro item meta para procedencia", () => {
  const s = src("enviar-mensaje.js");
  assert.match(s, /const respuesta = burbuja\(answer.reply/);
  assert.match(s, /respuesta\.dataset\.procedencia = answer\.nota/);
  assert.doesNotMatch(s, /if \(answer\.nota\) c\.hist\.append\(node\("div", answer\.nota/);
  assert.doesNotMatch(s, /if \(r\.nota\) c\.hist\.append\(node\("div", r\.nota/);
});

test("La ruta de elección del proveedor no activa la lógica de agentes", () => {
  const s = src("selector-modelos.js");
  assert.match(s, /selec\?\.encender\?\.\("groq"\)/);
  assert.match(s, /selec\?\.encender\?\.\("nvidia-groq-team"\)/);
  assert.match(s, /selec\?\.encender\?\.\("swe-code"\)/);
});
