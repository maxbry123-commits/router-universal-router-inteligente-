import { controlLabel, slotLabel, t } from "../i18n.js";
import { dispatchLocalAction } from "../bridge.js";
import { selectionWindow } from "../components/selection-window.js";

export function openModes(context) {
  return selectionWindow(context, {
    title: controlLabel(context, "modes"), selectedId: context.selection.modeId,
    items: context.config.modes.map(mode => ({ ...mode, label: slotLabel(context, mode) })),
    onApply: async mode => {
      if (mode.actionId) {
        context.notice(t(context, "backendLoading"), false, true);
        await context.execute(mode.actionId, { modeId: mode.id });
      }
      else dispatchLocalAction("mode.select", { modeId: mode.id });
      context.selection.modeId = mode.id;
      return t(context, mode.actionId ? "selectedRemote" : "selectedLocal", { name: mode.label });
    },
  });
}
