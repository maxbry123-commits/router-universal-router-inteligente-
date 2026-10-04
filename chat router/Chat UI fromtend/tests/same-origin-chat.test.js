import test from "node:test";
import assert from "node:assert/strict";
import { createSameOriginChatBridge, installSameOriginChatBridge } from "../src/plugins/same-origin-chat.js";

const response = (body, status = 200) => ({ ok: status < 400, status, json: async () => body });

test("the HTTP plugin uses only verified same-origin paths and explicit non-DeepSeek models", async () => {
  const calls = [];
  const fetchImpl = async (path, options) => {
    calls.push({ path, options });
    if (path === "/chat/providers") return response({ providers: [
      { id: "auto", configured: true }, { id: "hf", configured: true, label: "HF" }, { id: "deepseek", configured: true },
    ] });
    if (path === "/chat/providers/hf/models") return response({ models: [
      { model_id: "some/real-model", label: "Real", selectable: true },
      { model_id: "deepseek/v4", selectable: true }, { model_id: "unavailable", selectable: false },
    ] });
    if (path === "/chat/documents") return response({ document: { id: "doc-42" } });
    if (path === "/chat/send") return response({ reply: "Respuesta real", conversation_id: "conv-42", provider: "hf", model: "some/real-model" });
    throw Error(`UNEXPECTED_PATH:${path}`);
  };
  const bridge = createSameOriginChatBridge(fetchImpl);
  assert.deepEqual(await bridge.execute("chat.models"), { ok: true, models: [{ id: "hf/some/real-model", label: "HF · Real" }] });
  const file = new Blob(["contenido real"], { type: "text/plain" });
  assert.equal((await bridge.execute("chat.attach", { file, name: "file.txt" })).attachmentId, "doc-42");
  assert.deepEqual(await bridge.execute("chat.send", { message: "Lee el archivo", modelId: "hf/some/real-model", modeId: "mode-1", attachments: [{ attachmentId: "doc-42" }] }),
    { ok: true, reply: "Respuesta real", conversationId: "conv-42" });
  assert.equal(calls.every(call => call.options.credentials === "same-origin" && call.options.cache === "no-store"), true);
  const docBody = JSON.parse(calls.find(call => call.path === "/chat/documents").options.body);
  assert.equal(Buffer.from(docBody.data_b64, "base64").toString(), "contenido real");
  const sendBody = JSON.parse(calls.at(-1).options.body);
  assert.deepEqual(sendBody, { message: "Lee el archivo", provider: "hf", model: "some/real-model", mode: "direct", conversation_id: null, doc_ids: ["doc-42"] });
  await bridge.execute("chat.send", { message: "siguiente", modelId: "hf/some/real-model", modeId: "mode-1" });
  assert.equal(JSON.parse(calls.at(-1).options.body).conversation_id, "conv-42");
  bridge.resetSession();
  await bridge.execute("chat.send", { message: "nuevo", modelId: "hf/some/real-model", modeId: "mode-1" });
  assert.equal(JSON.parse(calls.at(-1).options.body).conversation_id, null);
});

test("unsupported operations, providers, upload state and backend failures stay closed", async () => {
  let count = 0;
  const bridge = createSameOriginChatBridge(async () => { count++; return response({ reply: "", conversation_id: "x" }); });
  const base = { message: "hello", modelId: "hf/gpt", modeId: "mode-1" };
  for (const modelId of ["auto/gpt", "hf/deepseek-v4", "deepseek/model", "gpt", ""]) {
    await assert.rejects(bridge.execute("chat.send", { ...base, modelId }), /MODEL_PROVIDER_REQUIRED_OR_FORBIDDEN/);
  }
  await assert.rejects(bridge.execute("chat.send", { ...base, modeId: "mode-8" }), /MODE_NOT_SUPPORTED/);
  await assert.rejects(bridge.execute("chat.send", { ...base, attachments: [{ file: new Blob(["x"]) }] }), /ATTACHMENT_NOT_UPLOADED/);
  await assert.rejects(bridge.execute("chat.attach", { file: new Blob(["x".repeat(10 * 1024 * 1024 + 1)]) }), /DOCUMENT_EMPTY_OR_TOO_LARGE/);
  await assert.rejects(bridge.execute("power.router.on"), /ACTION_UNCONFIGURED/);
  assert.equal(count, 0);
  await assert.rejects(bridge.execute("chat.send", base), /INVALID_CHAT_RESPONSE/);
  const mismatch = createSameOriginChatBridge(async () => response({ reply: "incompatible", provider: "deepseek", model: "v4" }));
  await assert.rejects(mismatch.execute("chat.send", base), /BACKEND_MODEL_MISMATCH/);
  const denied = createSameOriginChatBridge(async () => response({ detail: "Unauthorized" }, 401));
  await assert.rejects(denied.execute("chat.send", base), /BACKEND_HTTP_401/);
  const deniedHtml = createSameOriginChatBridge(async () => ({
    ok: false, status: 401, json: async () => { throw new SyntaxError("Not JSON"); },
  }));
  await assert.rejects(deniedHtml.execute("chat.send", base), /BACKEND_HTTP_401/);
});

test("an in-flight old reply cannot attach to a newly reset chat", async () => {
  let finish;
  const bridge = createSameOriginChatBridge(() => new Promise(resolve => { finish = resolve; }));
  const send = bridge.execute("chat.send", { message: "anterior", modelId: "hf/gpt", modeId: "mode-1" });
  bridge.resetSession();
  finish(response({ reply: "tardía", conversation_id: "old", provider: "hf", model: "gpt" }));
  await assert.rejects(send, /CHAT_SESSION_CHANGED/);
});

test("host bridge wins; file protocol never installs HTTP transport", () => {
  const host = { location: { protocol: "file:" }, fetch: async () => {} };
  assert.equal(installSameOriginChatBridge(host), false);
  assert.equal(host.YAIWES_PLUGIN_BRIDGE, undefined);
  const existing = { execute: async () => ({ ok: true }) };
  host.location.protocol = "https:";
  host.YAIWES_PLUGIN_BRIDGE = existing;
  assert.equal(installSameOriginChatBridge(host), false);
  assert.equal(host.YAIWES_PLUGIN_BRIDGE, existing);
  delete host.YAIWES_PLUGIN_BRIDGE;
  assert.equal(installSameOriginChatBridge(host), true);
  assert.equal(typeof host.YAIWES_PLUGIN_BRIDGE.execute, "function");
});
