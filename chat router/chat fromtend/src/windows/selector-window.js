import { button, el, openWindow } from "../dom.js";
import { slotLabel, t } from "../i18n.js";

export function selectorWindow(index, context) {
  const slot = context.config.selectors[index];
  const list = el("div", { class: "option-list" });
  if (!slot.options.length) list.append(el("p", { class: "muted", text: t(context, "selectorEmpty") }));
  for (const option of slot.options) {
    list.append(button(option.label, async () => {
      const command = option.actionId || slot.actionId;
      try {
        await context.execute(command, { selectorId: slot.id, optionId: option.id });
        context.selection.selectors[slot.id] = option.id;
        context.notice(`${slotLabel(context, slot)}: ${option.label}`);
        dialog.close();
      } catch (error) { context.notice(error.message, true); }
    }, "option"));
  }
  const dialog = openWindow(slotLabel(context, slot), el("div", { class: "window-body" }, el("p", { class: "muted", text: slot.description }), list), t(context, "closeWindow"));
}
