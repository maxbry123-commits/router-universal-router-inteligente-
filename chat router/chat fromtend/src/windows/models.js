import { button, el, openWindow } from "../dom.js";

export function openModels(context) {
  const list = el("div", { class: "option-list" });
  if (!context.config.models.length) list.append(el("p", { class: "muted", text: "No hay modelos configurados. Añádelos en Configuración o conecta el catálogo del backend." }));
  const dialog = openWindow(context.config.labels.models, el("div", { class: "window-body" }, list));
  for (const model of context.config.models) {
    list.append(button(model.label, async () => {
      try {
        if (context.config.modelActionId) await context.execute(context.config.modelActionId, { modelId: model.id });
        context.selection.modelId = model.id;
        context.refresh();
        context.notice(context.config.modelActionId ? `${model.label} confirmado` : `${model.label} elegido localmente; el backend se comprobará al enviar.`);
        dialog.close();
      } catch (error) { context.notice(error.message, true); }
    }, model.id === context.selection.modelId ? "option selected" : "option"));
  }
  if (context.config.modelsActionId) list.append(button("Actualizar desde backend", async () => {
    try {
      const result = await context.execute(context.config.modelsActionId);
      if (!Array.isArray(result.models)) throw new Error("INVALID_MODELS_RESPONSE");
      context.setModels(result.models);
      dialog.close();
      openModels(context);
    } catch (error) { context.notice(error.message, true); }
  }, "ghost"));
}
