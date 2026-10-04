import test from "node:test";
import assert from "node:assert/strict";
import { sendMessage } from "../src/actions/send-message.js";

function scenario(execute) {
  const notices = [];
  const context = {
    config: { sendActionId: "chat.send" },
    selection: { modelId: "configured-model", modeId: "mode-3", selectors: { "selector-1": "choice" }, toggles: { "toggle-1": true } },
    draft: "Texto real", attachments: [], messages: [], execute,
    notice: (message, error) => notices.push({ message, error }), refresh: () => {},
  };
  return { context, notices, textarea: { value: "Texto real" }, send: { disabled: false } };
}

test("send keeps draft and produces no assistant message when bridge is missing", async () => {
  const { context, textarea, send, notices } = scenario(async () => { throw Error("BRIDGE_MISSING"); });
  await sendMessage(context, textarea, send);
  assert.equal(context.draft, "Texto real");
  assert.equal(context.messages.length, 0);
  assert.equal(send.disabled, false);
  assert.equal(notices.at(-1).message, "BRIDGE_MISSING");
});

test("send uses configured model and state, and only commits a real reply", async () => {
  let captured;
  const { context, textarea, send } = scenario(async (actionId, payload) => {
    captured = { actionId, payload };
    return { ok: true, reply: "Backend confirmó" };
  });
  await sendMessage(context, textarea, send);
  assert.equal(captured.actionId, "chat.send");
  assert.equal(captured.payload.modeId, "mode-3");
  assert.equal(captured.payload.modelId, "configured-model");
  assert.deepEqual(captured.payload.selectors, { "selector-1": "choice" });
  assert.equal(context.messages[1].text, "Backend confirmó");
  assert.equal(context.draft, "");
});

test("an acknowledgment without reply cannot be displayed as assistant content", async () => {
  const { context, textarea, send } = scenario(async () => ({ ok: true }));
  await sendMessage(context, textarea, send);
  assert.equal(context.messages.length, 0);
  assert.equal(context.draft, "Texto real");
});
