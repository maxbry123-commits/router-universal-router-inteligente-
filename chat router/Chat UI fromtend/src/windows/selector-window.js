import { slotLabel, t } from "../i18n.js";
import { selectionWindow } from "../components/selection-window.js";

export function selectorWindow(index, context) {
  const slot = context.config.selectors[index];
  return selectionWindow(context, {
    title: slotLabel(context, slot), description: slot.description, selectedId: context.selection.selectors[slot.id],
    items: slot.options, emptyText: t(context, "selectorEmpty"),
    onApply: async option => {
      context.notice(t(context, "backendLoading"), false, true);
      await context.execute(option.actionId || slot.actionId, { selectorId: slot.id, optionId: option.id });
      context.selection.selectors[slot.id] = option.id;
      return t(context, "selectedRemote", { name: `${slotLabel(context, slot)}: ${option.label}` });
    },
  });
}
