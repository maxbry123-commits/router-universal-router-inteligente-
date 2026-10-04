import test from "node:test";
import assert from "node:assert/strict";
import { executeAction } from "../src/bridge.js";

test("missing command and bridge fail closed", async () => {
  await assert.rejects(executeAction("", {}, {}), { code: "ACTION_UNCONFIGURED" });
  await assert.rejects(executeAction("chat.send", { message: "real" }, {}), { code: "BRIDGE_MISSING" });
});

test("bridge result, refusal and rejection are distinct", async () => {
  const host = { YAIWES_PLUGIN_BRIDGE: { execute: async (id, payload) => ({ ok: true, reply: `${id}:${payload.message}` }) } };
  assert.deepEqual(await executeAction("chat.send", { message: "hi" }, host), { ok: true, reply: "chat.send:hi" });
  host.YAIWES_PLUGIN_BRIDGE.execute = async () => ({ ok: false, error: "denied" });
  await assert.rejects(executeAction("chat.send", {}, host), { code: "ACTION_FAILED" });
  host.YAIWES_PLUGIN_BRIDGE.execute = async () => undefined;
  await assert.rejects(executeAction("chat.send", {}, host), { code: "ACTION_FAILED" });
  host.YAIWES_PLUGIN_BRIDGE.execute = async () => ({});
  await assert.rejects(executeAction("chat.send", {}, host), { code: "ACTION_FAILED" });
  host.YAIWES_PLUGIN_BRIDGE.execute = async () => { throw Error("offline"); };
  await assert.rejects(executeAction("chat.send", {}, host), { code: "ACTION_FAILED" });
});

test("action bus emits the exact command and payload before the bridge call", async () => {
  const events = [];
  const host = new EventTarget();
  host.addEventListener("yaiwes:ui-action", event => events.push(event.detail));
  host.YAIWES_PLUGIN_BRIDGE = { execute: async () => ({ ok: true }) };
  await executeAction("control.on", { enabled: true }, host);
  assert.deepEqual(events, [{ actionId: "control.on", payload: { enabled: true } }]);
});
