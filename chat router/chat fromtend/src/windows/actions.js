import { button, el, openWindow } from "../dom.js";

export function openActions(context) {
  const list = el("div", { class: "option-list" });
  const dialog = openWindow(context.config.labels.functions, el("div", { class: "window-body" }, list));
  for (const action of context.config.actions) {
    const node = button(action.label, async () => {
      try {
        await context.execute(action.actionId, { functionId: action.id, modelId: context.selection.modelId });
        context.notice(`${action.label}: confirmado por el backend`);
        dialog.close();
      } catch (error) { context.notice(error.message, true); }
    }, "option");
    if (action.description) node.title = action.description;
    list.append(node);
  }
}
