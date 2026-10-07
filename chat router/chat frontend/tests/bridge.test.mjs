import assert from "node:assert/strict";
import test from "node:test";

const store = new Map();
globalThis.sessionStorage = {
  getItem: key => store.get(key) ?? null,
  setItem: (key, value) => store.set(key, String(value))
};
globalThis.window = {
  RIU_CONFIG: {
    apiBase: "https://aaaaaaaaaaaaaaaaaaaaaaaa--8000.hf.jobs",
    liveUrl: "https://raw.example.test/LIVE_URL.json",
    harnessUrl: "https://aaaaaaaaaaaaaaaaaaaaaaaa--8000.hf.jobs/plugins/puente_chat/call"
  }
};
let answer;
let last;
globalThis.fetch = async (url, options = {}) => {
  if (url.startsWith(window.RIU_CONFIG.liveUrl))
    return Response.json({ LIVE_URL: window.RIU_CONFIG.apiBase });
  last = { url, options, payload: JSON.parse(options.body || "{}") };
  return Response.json({ status: "ok", result: answer });
};

const { accion } = await import("../api.js");

test("acciones del plugin fallan cerrado si el resultado contiene error", async () => {
  answer = { error: "ARCHIVO_MUY_GRANDE" };
  await assert.rejects(accion("subir", { sesion: "chat-1" }), /ARCHIVO_MUY_GRANDE/);
  assert.equal(last.payload.sesion, "chat-1");
  answer = { ok: false };
  await assert.rejects(accion("sandbox", { sesion: "chat-2" }), /ACCION_SIN_CONFIRMACION/);
});

test("chat.send del bridge conserva sesión y anclas sin modelo DeepSeek", async () => {
  answer = { choices: [{ message: { content: "confirmado" } }], herramientas: [] };
  const result = await window.YAIWES_PLUGIN_BRIDGE.execute("chat.send", {
    model: "nv-nemotron-super", message: "consulta", sesion: "chat-3", task_id: "tarea-3",
    anclados: ["archivo.txt", "handoff:skill"], max_tokens: 512
  });
  assert.equal(result.reply, "confirmado");
  assert.match(last.url, /\/plugins\/puente_chat\/call\/chat_async$/);
  assert.deepEqual(last.payload.anclados, ["archivo.txt", "handoff:skill"]);
  assert.equal(last.payload.sesion, "chat-3");
  assert.equal(last.payload.task_id, "tarea-3");
  assert.equal(last.payload.model, "nv-nemotron-super");
});

test("detener cancela el polling local; no afirma cancelación remota", async () => {
  answer = { estado: "procesando", proceso_id: "prueba" };
  const controller = new AbortController();
  const pending = window.YAIWES_PLUGIN_BRIDGE.execute("chat.send", {
    model: "nv-nemotron-super", message: "consulta", sesion: "chat-4",
    signal: controller.signal
  });
  setTimeout(() => controller.abort(), 20);
  await assert.rejects(pending, { name: "AbortError" });
});
