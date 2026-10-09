import { button } from "../dom.js";
import { controlLabel, t } from "../i18n.js";
import { dispatchLocalAction } from "../bridge.js";
import { selectionWindow } from "../components/selection-window.js";

export function openModels(context) {
  const dialog = selectionWindow(context, {
    title: controlLabel(context, "models"), selectedId: context.selection.modelId,
    items: context.config.models.filter(model => !/deepseek|(^|\/)auto(\/|$)/i.test(model.id)),
    emptyText: t(context, "modelsEmpty"), searchable: true,
    onApply: async model => {
      if (context.config.modelActionId) {
        context.notice(t(context, "backendLoading"), false, true);
        await context.execute(context.config.modelActionId, { modelId: model.id });
      }
      else dispatchLocalAction("model.select", { modelId: model.id });
      context.selection.modelId = model.id;
      return t(context, context.config.modelActionId ? "selectedRemote" : "selectedLocal", { name: model.label });
    },
  });
  if (context.config.modelsActionId) {
    const refresh = button(t(context, "modelsRefresh"), async () => {
      const buttons = Array.from(dialog.querySelectorAll("button"));
      const disabled = buttons.map(node => node.disabled);
      buttons.forEach(node => { node.disabled = true; });
      dialog.setAttribute("aria-busy", "true");
      context.notice(t(context, "backendLoading"), false, true);
      try {
        const result = await context.execute(context.config.modelsActionId);
        if (!Array.isArray(result.models)) throw new Error("INVALID_MODELS_RESPONSE");
        context.setModels(result.models);
        dialog.close(); openModels(context);
      } catch (error) { context.notice(error.message, true); }
      finally { dialog.removeAttribute("aria-busy"); buttons.forEach((node, index) => { node.disabled = disabled[index]; }); }
    }, "ghost");
    dialog.querySelector(".window-body").prepend(refresh);
  }
  return dialog;
}
