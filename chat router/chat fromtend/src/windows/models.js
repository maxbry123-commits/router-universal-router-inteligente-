import { button, el, openWindow } from "../dom.js";
import { controlLabel, t } from "../i18n.js";
import { dispatchLocalAction } from "../bridge.js";

export function openModels(context) {
  const list = el("div", { class: "option-list" });
  if (!context.config.models.length) list.append(el("p", { class: "muted", text: t(context, "modelsEmpty") }));
  const dialog = openWindow(controlLabel(context, "models"), el("div", { class: "window-body" }, list), t(context, "closeWindow"));
  for (const model of context.config.models) {
    list.append(button(model.label, async () => {
      try {
        if (context.config.modelActionId) await context.execute(context.config.modelActionId, { modelId: model.id });
        else dispatchLocalAction("model.select", { modelId: model.id });
        context.selection.modelId = model.id;
        context.refresh();
        context.notice(t(context, context.config.modelActionId ? "selectedRemote" : "selectedLocal", { name: model.label }));
        dialog.close();
      } catch (error) { context.notice(error.message, true); }
    }, model.id === context.selection.modelId ? "option selected" : "option"));
  }
  if (context.config.modelsActionId) {
    const refresh = button(t(context, "modelsRefresh"), async () => {
    refresh.disabled = true;
    try {
      const result = await context.execute(context.config.modelsActionId);
      if (!Array.isArray(result.models)) throw new Error("INVALID_MODELS_RESPONSE");
      context.setModels(result.models);
      dialog.close();
      openModels(context);
    } catch (error) { context.notice(error.message, true); }
    finally { refresh.disabled = false; }
    }, "ghost");
    list.append(refresh);
  }
}
