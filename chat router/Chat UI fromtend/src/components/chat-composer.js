import { el } from "../dom.js";
import { controlLabel, slotLabel, t } from "../i18n.js";
import { openModels } from "../windows/models.js";
import { openModes } from "../windows/modes.js";
import { openTools } from "../windows/tools.js";
import { sendMessage } from "../actions/send-message.js";
import { toggleRecording } from "../actions/record-voice.js";
import { attachments } from "./attachments.js";
import { iconButton } from "./icon-button.js";
import { selectionButton } from "./selection-button.js";

export function chatComposer(context) {
  const mode = context.config.modes.find(item => item.id === context.selection.modeId);
  const model = context.config.models.find(item => item.id === context.selection.modelId);
  const { input, list, pickFiles } = attachments(context);
  const textarea = el("textarea", { rows: "2", maxlength: "20000", placeholder: t(context, "placeholder"), "aria-label": t(context, "messageAria") });
  textarea.value = context.draft;
  textarea.addEventListener("input", () => { context.draft = textarea.value; });
  const send = iconButton(context, "send", "send", () => sendMessage(context, textarea, send), "primary");
  textarea.addEventListener("keydown", event => {
    if (event.key === "Enter" && !event.shiftKey && !event.isComposing) { event.preventDefault(); send.click(); }
  });
  const voice = iconButton(context, "voice", "voice", () => toggleRecording(context, voice));
  const recording = context.recorder?.state === "recording";
  voice.setAttribute("aria-pressed", String(recording));
  if (recording) voice.setAttribute("aria-label", t(context, "stopRecording", { name: controlLabel(context, "voice") }));
  const watchdog = iconButton(context, "watchdog", "shield", async () => {
    watchdog.disabled = true;
    context.notice(t(context, "backendLoading"), false, true);
    try { await context.execute(context.config.watchdogActionId); context.notice(t(context, "watchdogConfirmed")); }
    catch (error) { context.notice(error.message, true); }
    finally { watchdog.disabled = false; }
  });
  const tools = iconButton(context, "tools", "plus", () => openTools(context, pickFiles));
  tools.setAttribute("aria-haspopup", "dialog");
  return el("div", { class: "composer" }, input,
    el("div", { class: "composer-model" }, selectionButton(context, "models", model?.label || controlLabel(context, "models"), () => openModels(context))),
    list, textarea,
    el("div", { class: "composer-bar" }, tools,
      selectionButton(context, "modes", mode ? slotLabel(context, mode) : controlLabel(context, "modes"), () => openModes(context)),
      el("div", { class: "composer-actions" }, voice, watchdog, send)));
}
