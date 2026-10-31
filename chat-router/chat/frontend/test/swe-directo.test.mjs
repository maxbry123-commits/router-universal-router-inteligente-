import test from "node:test";
import assert from "node:assert/strict";
import { esSwe, armar, enviarSwe } from "../swe-directo.js";

test("reconoce los ids SWE del selector y deja pasar a los demas modelos por el Router", () => {
  for (const m of ["web-qwen38max", "swecode-asesoria", "hf-liquid-lfm25", "swe-agent-lfm25", "lfm2.5-350m"]) assert.ok(esSwe(m), m);
  for (const m of ["qwen3.8-max", "glm-5.3", "deepseek-v4-pro", "groq/llama-3.3-70b-versatile", "", null]) assert.ok(!esSwe(m), String(m));
});

test("arma el POST OpenAI con el historial, la sesion y el proyecto; los alias hf-* se traducen al id real", () => {
  const b = armar({ model: "hf-liquid-lfm25", historial: [{ role: "user", content: "a" }, { role: "assistant", content: "b" }], mensaje: "c", sesion: "s1", proyecto: "P" });
  assert.equal(b.model, "lfm2.5-350m"); assert.equal(b.conv_id, "s1"); assert.equal(b.proyecto, "P");
  assert.deepEqual(b.messages.map((m) => m.content), ["a", "b", "c"]);
});

test("enviarSwe usa /v1/chat/completions y devuelve la forma que pinta el chat", async () => {
  let visto;
  const api = async (ruta, op) => { visto = { ruta, op }; return { modelo_usado: "web-qwen38max", via_respaldo: "groq", choices: [{ message: { content: "listo" }, finish_reason: "stop" }] }; };
  const r = await enviarSwe(api, { model: "web-qwen38max", historial: [], mensaje: "hola", sesion: "s" });
  assert.equal(visto.ruta, "/v1/chat/completions"); assert.equal(visto.op.method, "POST");
  assert.equal(r.reply, "listo"); assert.equal(r.finish_reason, "stop"); assert.match(r.nota, /groq/);
});

test("si la respuesta no trae texto lo dice en vez de quedarse en silencio", async () => {
  const r = await enviarSwe(async () => ({ error: { code: "RESPALDO_AGOTADO", message: "nada responde" } }), { model: "web-qwen38max", historial: [], mensaje: "x", sesion: "s" });
  assert.match(r.reply, /GAP: .*RESPALDO_AGOTADO/);
});
