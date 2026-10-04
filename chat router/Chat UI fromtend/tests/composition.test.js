import test from "node:test";
import assert from "node:assert/strict";
import { fixture, settle } from "./dom-fixture.js";
import { renderChat } from "../src/panels/chat.js";
import { openTools } from "../src/windows/tools.js";
import { openSelectors } from "../src/windows/selectors.js";
import { openControls } from "../src/windows/controls.js";
import { openActions } from "../src/windows/actions.js";
import { renderSettings } from "../src/panels/settings.js";
import { openFichas } from "../src/windows/fichas.js";

test("chat uses a compact header and composer, not permanent selector/toggle strips", () => {
  const { document, context } = fixture();
  const chat = renderChat(context);
  document.body.append(chat);
  assert.equal(chat.querySelectorAll("button").length, 8);
  assert.equal(chat.querySelectorAll(".top-actions button").length, 2);
  assert.equal(chat.querySelector(".selector-row, .toggle-row"), null);
  assert.equal(chat.querySelectorAll(".selection-button[aria-haspopup='dialog']").length, 2);
  assert.equal(chat.querySelector(".composer").children.length, 5);
  assert.equal(chat.querySelector(".composer textarea").getAttribute("rows"), "2");
  for (const button of chat.querySelectorAll(".icon-btn")) assert.ok(button.getAttribute("aria-label"));
  chat.querySelector('[data-control="configure"]').click();
  assert.equal(context.settingsOpened, true);
  chat.querySelector('[data-control="chatMenu"]').click();
  assert.equal(document.querySelectorAll("dialog[open]").length, 1);
  assert.equal(document.querySelectorAll("dialog .option").length, 2);
});

test("plus menu exposes distinct document and attachment commands without stacked dialogs", () => {
  const { document, context } = fixture({ attachActionId: "files.attach", documentsActionId: "documents.upload" });
  const commands = [];
  const first = openTools(context, actionId => commands.push(actionId));
  assert.equal(first.querySelectorAll(".option").length, 9);
  assert.ok(first.querySelector('[data-control="plugins"]'));
  assert.ok(first.querySelector('[data-control="fichas"]'));
  first.querySelector('[data-control="documents"]').click();
  assert.deepEqual(commands, ["documents.upload"]);
  assert.equal(document.querySelectorAll("dialog[open]").length, 0);
  openTools(context, actionId => commands.push(actionId)).querySelector('[data-control="attach"]').click();
  assert.deepEqual(commands, ["documents.upload", "files.attach"]);
  openTools(context, () => {}).querySelector('[data-control="selectors"]').click();
  assert.equal(document.querySelectorAll("dialog[open]").length, 1);
  assert.equal(document.querySelectorAll("[data-selector]").length, 5);
});

test("ficha picker reads and refreshes live entries, then reads the selected ficha", async () => {
  const calls = [];
  let items = [{ id: "ficha.1", label: "ficha.1" }];
  const { document, context } = fixture({}, async (action, payload) => {
    calls.push([action, payload]);
    if (action === "chat.fichas") return { ok: true, items };
    if (action === "chat.ficha") return { ok: true, ficha: { id: payload.id, status: "testing" } };
    throw new Error("NOT_CONFIGURED");
  });
  openFichas(context);
  await settle();
  assert.equal(document.querySelectorAll("dialog .option").length, 1);
  document.querySelector("dialog .option").click();
  await settle();
  assert.ok(document.querySelector("dialog .window-body [role='status']").textContent.includes("ficha.1"));
  items = [{ id: "ficha.2", label: "ficha.2" }];
  document.querySelector("dialog .window-body .ghost").click();
  await settle();
  assert.equal(document.querySelector("dialog .option").textContent, "ficha.2");
  assert.deepEqual(calls.map(([action]) => action), ["chat.fichas", "chat.ficha", "chat.fichas"]);
});

test("all five selector launchers open their own named window with configured descriptions", () => {
  const { document, context } = fixture({ selectors: Array.from({ length: 5 }, (_, index) => ({ label: `Custom ${index + 1}`, description: `Description ${index + 1}` })) });
  for (let index = 0; index < 5; index++) {
    const directory = openSelectors(context);
    directory.querySelector(`[data-selector="selector-${index + 1}"]`).click();
    const dialog = document.querySelector("dialog[open]");
    assert.equal(dialog.getAttribute("aria-label"), `Custom ${index + 1}`);
    assert.ok(dialog.textContent.includes(`Description ${index + 1}`));
    assert.equal(dialog.querySelector(".primary").disabled, true);
    assert.equal(document.querySelectorAll("dialog[open]").length, 1);
    dialog.close();
  }
});

test("eight switches remain off on failure and only change after bridge confirmation", async () => {
  let confirm;
  let calls = 0;
  const { context } = fixture({ toggles: [{ label: "Search", description: "Configured description", actionId: "search.toggle" }] }, () => {
    calls++;
    return new Promise(resolve => { confirm = resolve; });
  });
  const dialog = openControls(context);
  assert.equal(dialog.querySelectorAll('[role="switch"]').length, 8);
  const first = dialog.querySelector('[role="switch"]');
  first.click();
  assert.equal(calls, 1);
  assert.equal(first.disabled, true);
  assert.equal(first.getAttribute("aria-checked"), "false");
  confirm({ ok: true });
  await settle();
  assert.equal(first.getAttribute("aria-checked"), "true");
  assert.equal(context.selection.toggles["toggle-1"], true);
  assert.equal(first.disabled, false);
  const failed = fixture({ toggles: [{ actionId: "fail" }] }, async () => ({ ok: false }));
  const switchNode = openControls(failed.context).querySelector('[role="switch"]');
  switchNode.click(); await settle();
  assert.equal(switchNode.getAttribute("aria-checked"), "false");
  assert.equal(failed.context.selection.toggles["toggle-1"], undefined);
  assert.match(failed.notices.at(-1).message, /ACTION_FAILED/);
});

test("all twelve functions retain their configured commands and visible descriptions", async () => {
  const calls = [];
  const { context } = fixture({ actions: Array.from({ length: 12 }, (_, index) => ({ label: `Function ${index}`, description: `Purpose ${index}`, actionId: `function.${index}` })) }, async (actionId, payload) => {
    calls.push({ actionId, payload }); return { ok: true };
  });
  const dialog = openActions(context);
  assert.equal(dialog.querySelectorAll(".option").length, 12);
  assert.ok(dialog.textContent.includes("Purpose 11"));
  dialog.querySelectorAll(".option")[11].click(); await settle();
  assert.deepEqual(calls, [{ actionId: "function.11", payload: { functionId: "action-12", modelId: "" } }]);
});

test("settings preserves every slot, command and editable name with seven palette panels", () => {
  const { document, context } = fixture();
  const settings = renderSettings(context);
  document.body.append(settings);
  assert.deepEqual(Array.from(settings.querySelectorAll("[data-theme-option]")).map(node => node.getAttribute("data-theme-option")), ["gris", "little", "matte", "blanco", "crystal", "orange", "blue"]);
  assert.equal(settings.querySelectorAll(".theme-sample").length, 7);
  assert.equal(settings.querySelectorAll(".theme-color").length, 35);
  assert.ok(settings.textContent.includes("Paleta de referencia · no aprobada"));
  assert.equal(settings.querySelectorAll("details").length, 33 + Object.keys(context.config.labels).length);
  assert.ok(settings.querySelector('[aria-label="Subir documentos · actionId"]'));
  settings.querySelector('[data-theme-option="blue"]').click();
  assert.equal(context.config.theme, "gris");
  assert.equal(settings.querySelector('[data-theme-option="blue"]').getAttribute("aria-pressed"), "true");
  settings.querySelector('[aria-label="Título del chat"]').value = "Mi chat";
  settings.querySelector('[aria-label="Título del chat"]').dispatchEvent(new document.defaultView.Event("input"));
  settings.querySelector(".primary").click();
  assert.equal(context.config.theme, "blue");
  assert.equal(context.config.title, "Mi chat");
  assert.equal(context.chatOpened, true);
  assert.deepEqual([context.config.selectors.length, context.config.toggles.length, context.config.modes.length, context.config.actions.length], [5, 8, 8, 12]);
});

test("settings reset requires confirmation and replaces saved commands without removing the panel", () => {
  const { document, window, context } = fixture({ theme: "little", sendActionId: "custom.send" });
  context.selection.toggles["toggle-1"] = true;
  window.confirm = () => false;
  const settings = renderSettings(context);
  document.body.append(settings);
  const reset = [...settings.querySelectorAll("button")].find(node => node.textContent === "Restablecer configuración");
  reset.click();
  assert.equal(context.config.sendActionId, "custom.send");
  window.confirm = () => true;
  reset.click();
  assert.equal(context.config.sendActionId, "chat.send");
  assert.equal(context.config.theme, "gris");
  assert.deepEqual(context.selection.toggles, {});
  assert.equal(context.settingsOpened, true);
});

test("settings import requires confirmation and replaces the selection only after a valid file", async () => {
  const { document, window, context } = fixture({ sendActionId: "custom.send" });
  const settings = renderSettings(context);
  document.body.append(settings);
  const fileInput = settings.querySelector('input[type="file"]');
  const data = JSON.stringify({ format: "yaiwes-chat-settings", version: 1, config: context.config });
  Object.defineProperty(fileInput, "files", { value: [{ size: data.length, text: async () => data }] });
  window.confirm = () => false;
  fileInput.dispatchEvent(new window.Event("change")); await settle();
  assert.equal(context.settingsOpened, undefined);
  window.confirm = () => true;
  fileInput.dispatchEvent(new window.Event("change")); await settle();
  assert.equal(context.settingsOpened, true);
  assert.equal(context.config.sendActionId, "custom.send");
});

test("app surfaces errors inside the active sheet and expires its toast", async t => {
  t.mock.timers.enable({ apis: ["setTimeout"] });
  const { document } = fixture();
  await import("../src/app.js");
  document.querySelector('[data-control="tools"]').click();
  document.querySelector('[data-control="controls"]').click();
  document.querySelector('[role="switch"]').click(); await settle();
  assert.equal(document.querySelector(".window-status").textContent, "ACTION_UNCONFIGURED");
  assert.equal(document.querySelector("#status").className, "error");
  t.mock.timers.tick(8000);
  assert.equal(document.querySelector("#status").textContent, "");
});
