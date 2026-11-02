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
  assert.match(s, /\/plugins\/deepseek_harness\/credenciales\/anadir/);
  assert.match(s, /\/plugins\/deepseek_harness\/credenciales\/catalogo/);
  assert.match(s, /secreta\.value = ""/);
  assert.doesNotMatch(s, /localStorage\.setItem\([^)]*secreta/);
});

test("DeepSeek MiniMax y OpenAI aparecen en el selector y sus claves se eligen desde Configuracion", () => {
  const s = src("selector-modelos.js"), banco = src("ventana-claves.js"), router = src("swe-directo.js");
  for (const id of ["deepseek/deepseek-v4-pro", "deepseek/deepseek-flash", "minimax/MiniMax-M3",
    "minimax/MiniMax-M2.7", "openai/gpt-5.6", "openai/gpt-5.5"]) {
    assert.ok(s.includes(id), id);
    assert.ok(router.includes(id), id);
  }
  assert.match(s, /api\("\/web\/v1\/modelos\/disponibilidad"\)/);
  assert.match(s, /encender\?\.\("swen-code-free"\)/);
  for (const p of ["deepseek", "minimax", "openai"]) assert.ok(banco.includes('["' + p + '",'), p);
  assert.doesNotMatch(s, /API_KEY\s*=/);
});

test("El selector YAIWES y el proveedor OpenClaw entran por Harness antes de ambos routers", () => {
  const sw = src("swe-directo.js"), ui = src("selector-modelos.js"), conf = JSON.parse(src("../../SWE CODE free/provider-openclaw.json"));
  assert.match(sw, /rutaSwe = \(_id\) => "\/plugins\/deepseek_harness\/modelos\/v1\/chat\/completions"/);
  assert.ok(ui.includes("/plugins/deepseek_harness/modelos/v1/disponibilidad"));
  assert.equal(conf.base_url, "http://127.0.0.1:7861/plugins/deepseek_harness/modelos/v1");
});
