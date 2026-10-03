import test from "node:test";
import assert from "node:assert/strict";
import { LANGUAGES, STRINGS, t, controlLabel, slotLabel } from "../src/i18n.js";
import { normalizeConfig } from "../src/config.js";
import { closeChat } from "../src/actions/chat-session.js";

test("every interface key exists in es/en/fr/pt and configured names remain editable", () => {
  for (const locale of LANGUAGES) {
    assert.deepEqual(Object.keys(STRINGS[locale]).sort(), Object.keys(STRINGS.es).sort());
    const context = { config: normalizeConfig({ locale }) };
    assert.ok(t(context, "backendSending"));
    assert.ok(controlLabel(context, "send"));
    assert.ok(slotLabel(context, context.config.modes[0]));
  }
  const custom = { config: normalizeConfig({ locale: "fr", labels: { send: "Mon bouton" } }) };
  assert.equal(controlLabel(custom, "send"), "Mon bouton");
  assert.equal(normalizeConfig({ locale: "invalid" }).locale, "es");
});

test("new chat discards local state, resets bridge session and emits a local action", () => {
  const events = [];
  const host = new EventTarget();
  host.addEventListener("yaiwes:ui-action", event => events.push(event.detail));
  let resets = 0;
  host.YAIWES_PLUGIN_BRIDGE = { resetSession: () => { resets++; } };
  const context = { messages: [{ text: "Private" }], attachments: [{ file: {} }], draft: "Private", selection: { modelId: "hf/gpt" }, refresh: () => {} };
  closeChat(context, host);
  assert.deepEqual(context.messages, []);
  assert.deepEqual(context.attachments, []);
  assert.equal(context.draft, "");
  assert.equal(context.sessionVersion, 1);
  assert.equal(resets, 1);
  assert.deepEqual(events, [{ actionId: "chat.close", payload: {} }]);
});
