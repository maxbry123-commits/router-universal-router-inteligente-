import { button, el, openWindow } from "../dom.js";
import { controlLabel, slotLabel, t } from "../i18n.js";
import { dispatchLocalAction } from "../bridge.js";

export function openModes(context) {
  const list = el("div", { class: "option-list" });
  const dialog = openWindow(controlLabel(context, "modes"), el("div", { class: "window-body" }, list), t(context, "closeWindow"));
  for (const mode of context.config.modes) {
    list.append(button(`${slotLabel(context, mode)}${mode.description ? ` · ${mode.description}` : ""}`, async () => {
      try {
        if (mode.actionId) await context.execute(mode.actionId, { modeId: mode.id });
        else dispatchLocalAction("mode.select", { modeId: mode.id });
        context.selection.modeId = mode.id;
        context.refresh();
        context.notice(t(context, mode.actionId ? "selectedRemote" : "selectedLocal", { name: slotLabel(context, mode) }));
        dialog.close();
      } catch (error) { context.notice(error.message, true); }
    }, mode.id === context.selection.modeId ? "option selected" : "option"));
  }
}
