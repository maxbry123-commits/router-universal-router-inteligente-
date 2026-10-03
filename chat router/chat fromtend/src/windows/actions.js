import { button, el, openWindow } from "../dom.js";
import { controlLabel, slotLabel, t } from "../i18n.js";

export function openActions(context) {
  const list = el("div", { class: "option-list" });
  const dialog = openWindow(controlLabel(context, "functions"), el("div", { class: "window-body" }, list), t(context, "closeWindow"));
  for (const action of context.config.actions) {
    const node = button(slotLabel(context, action), async () => {
      try {
        await context.execute(action.actionId, { functionId: action.id, modelId: context.selection.modelId });
        context.notice(t(context, "backendConfirmed", { name: slotLabel(context, action) }));
        dialog.close();
      } catch (error) { context.notice(error.message, true); }
    }, "option");
    if (action.description) node.title = action.description;
    list.append(node);
  }
}
