import { button, el, openWindow } from "../dom.js";

export function openModes(context) {
  const list = el("div", { class: "option-list" });
  const dialog = openWindow(context.config.labels.modes, el("div", { class: "window-body" }, list));
  for (const mode of context.config.modes) {
    list.append(button(`${mode.label}${mode.description ? ` · ${mode.description}` : ""}`, async () => {
      try {
        if (mode.actionId) await context.execute(mode.actionId, { modeId: mode.id });
        context.selection.modeId = mode.id;
        context.refresh();
        context.notice(mode.actionId ? `${mode.label} confirmado` : `${mode.label} elegido localmente; el backend se comprobará al enviar.`);
        dialog.close();
      } catch (error) { context.notice(error.message, true); }
    }, mode.id === context.selection.modeId ? "option selected" : "option"));
  }
}
