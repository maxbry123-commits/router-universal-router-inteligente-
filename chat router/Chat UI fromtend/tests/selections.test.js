import test from "node:test";
import assert from "node:assert/strict";
import { fixture, settle } from "./dom-fixture.js";
import { openModes } from "../src/windows/modes.js";
import { openModels } from "../src/windows/models.js";
import { openSelector1 } from "../src/windows/selector-1.js";
import { openSelector5 } from "../src/windows/selector-5.js";

test("eight reasoning levels are draft selections until Apply; Cancel does not run commands", async () => {
  const calls = [];
  const { context } = fixture({}, async (...args) => { calls.push(args); return { ok: true }; });
  let dialog = openModes(context);
  assert.equal(dialog.querySelectorAll('[role="option"]').length, 8);
  dialog.querySelector('[data-option="mode-8"]').click();
  assert.equal(context.selection.modeId, "mode-1");
  dialog.querySelector(".window-footer .ghost").click();
  assert.equal(context.selection.modeId, "mode-1");
  assert.deepEqual(calls, []);
  dialog = openModes(context);
  dialog.querySelector('[data-option="mode-8"]').click();
  dialog.querySelector(".primary").click(); await settle();
  assert.equal(context.selection.modeId, "mode-8");
  assert.deepEqual(calls, []);
  assert.equal(context.refreshes, 1);
});

test("a rejected reasoning command preserves the old selection and keeps the sheet open", async () => {
  const { context, notices } = fixture({ modes: [{}, { actionId: "mode.advanced" }] }, async () => ({ ok: false }));
  const dialog = openModes(context);
  dialog.querySelector('[data-option="mode-2"]').click();
  dialog.querySelector(".primary").click(); await settle();
  assert.equal(context.selection.modeId, "mode-1");
  assert.equal(dialog.hasAttribute("open"), true);
  assert.equal(dialog.querySelector(".primary").disabled, false);
  assert.match(notices.at(-1).message, /ACTION_FAILED/);
});

test("selector commits the configured option command only after Apply and acknowledgment", async () => {
  const calls = [];
  const { context } = fixture({ selectors: [{ actionId: "selector.default", options: [{ id: "one", label: "First", actionId: "option.one" }, { id: "two", label: "Second" }] }] }, async (actionId, payload) => {
    calls.push({ actionId, payload }); return { ok: true };
  });
  const dialog = openSelector1(context);
  dialog.querySelector('[data-option="two"]').click();
  assert.deepEqual(context.selection.selectors, {});
  assert.deepEqual(calls, []);
  dialog.querySelector(".primary").click(); await settle();
  assert.deepEqual(calls, [{ actionId: "selector.default", payload: { selectorId: "selector-1", optionId: "two" } }]);
  assert.equal(context.selection.selectors["selector-1"], "two");
});

test("an unconfigured fifth selector fails closed and never saves a selection", async () => {
  const { context, notices } = fixture({ selectors: [{}, {}, {}, {}, { options: [{ id: "five", label: "Fifth" }] }] });
  const dialog = openSelector5(context);
  dialog.querySelector('[data-option="five"]').click();
  dialog.querySelector(".primary").click(); await settle();
  assert.deepEqual(context.selection.selectors, {});
  assert.equal(notices.at(-1).message, "ACTION_UNCONFIGURED");
});

test("model search filters configured models, excludes DeepSeek/auto, and applies a local draft", async () => {
  const { document, window, context } = fixture({ models: [
    { id: "hf/first", label: "First model" }, { id: "hf/second", label: "Second model" },
    { id: "deepseek/chat", label: "Forbidden" }, { id: "auto/model", label: "Auto" },
  ] });
  const dialog = openModels(context);
  assert.equal(dialog.querySelectorAll('[role="option"]').length, 2);
  const search = dialog.querySelector('input[type="search"]');
  search.value = "second";
  search.dispatchEvent(new window.Event("input"));
  assert.equal(dialog.querySelector('[data-option="hf/first"]').hidden, true);
  assert.equal(dialog.querySelector('[data-option="hf/second"]').hidden, false);
  dialog.querySelector('[data-option="hf/second"]').click();
  assert.equal(context.selection.modelId, "");
  dialog.querySelector(".primary").click(); await settle();
  assert.equal(context.selection.modelId, "hf/second");
  assert.equal(document.querySelector("dialog[open]"), null);
});

test("arrow keys select only within the draft; applying a pending command locks cancellation", async () => {
  let confirm;
  const { window, context } = fixture({ modes: [{}, { actionId: "mode.second" }] }, () => new Promise(resolve => { confirm = resolve; }));
  const dialog = openModes(context);
  const event = new window.Event("keydown", { cancelable: true });
  event.key = "ArrowDown";
  dialog.querySelector('[data-option="mode-1"]').dispatchEvent(event);
  assert.equal(dialog.querySelector('[data-option="mode-2"]').getAttribute("aria-selected"), "true");
  assert.equal(context.selection.modeId, "mode-1");
  dialog.querySelector(".primary").click();
  const cancel = new window.Event("cancel", { cancelable: true });
  dialog.dispatchEvent(cancel);
  assert.equal(cancel.defaultPrevented, true);
  assert.equal(dialog.querySelector(".window-header button").disabled, true);
  confirm({ ok: true }); await settle();
  assert.equal(context.selection.modeId, "mode-2");
});
