// No carga la app ni conecta al Space. Contratos estaticos de las dos pantallas integradas.
import test from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
const src = (name) => readFileSync(new URL("../" + name, import.meta.url), "utf8");

test("selector unico: modelos HF, Groq, NVIDIA y + API/SDK usan la ventana existente", () => {
  const s = src("selector-modelos.js");
  for (const model of [
    "hf/qwen2.5-coder-1.5b", "groq/qwen/qwen3.8-27b",
    "nvidia/minimaxai/minimax-m3.1-flash", "nvidia/meta/muse-glimmer-30b",
    "nvidia/nvidia/nemotron-3-ultra-550b-a55b", "nvidia/z-ai/glm-5.3",
  ]) assert.ok(s.includes(model), model);
  assert.match(s, /modelo-unificado/);
  assert.match(s, /anadir-api-sdk/);
  assert.match(s, /RIU_BANCO_CLAVES/);
  assert.match(s, /nvidia-groq-team/);
  assert.match(s, /swe-code/);
  assert.doesNotMatch(s, /if \(btn && composer.contains\(btn\).*pintarCatalogo\(\)/);
});
test("la ventana de claves usa plugin del Router MVP, no almacena el secreto localmente", () => {
  const s = src("ventana-claves.js");
  assert.match(s, /\/plugins\/banco_proveedores\/call\/anadir/);
  assert.match(s, /\/plugins\/banco_proveedores\/call\/catalogo/);
  assert.match(s, /secreta\.value = ""/);
  assert.doesNotMatch(s, /localStorage\.setItem\([^)]*secreta/);
});
