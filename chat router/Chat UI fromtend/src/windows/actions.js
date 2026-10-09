import { el, openWindow } from "../dom.js";
import { controlLabel, slotLabel, t } from "../i18n.js";
import { windowOption } from "../components/window-option.js";

export function openActions(context) {
  const list = el("div", { class: "option-list" });
  const dialog = openWindow(controlLabel(context, "functions"), el("div", { class: "window-body" }, list), t(context, "closeWindow"));
  for (const action of context.config.actions) {
    const node = windowOption(slotLabel(context, action), action.description, async () => {
      node.disabled = true;
      context.notice(t(context, "backendLoading"), false, true);
      try {
        await context.execute(action.actionId, { functionId: action.id, modelId: context.selection.modelId });
        context.notice(t(context, "backendConfirmed", { name: slotLabel(context, action) }));
        dialog.close();
      } catch (error) { context.notice(error.message, true); }
      finally { node.disabled = false; }
    });
    list.append(node);
  }
  return dialog;
}
