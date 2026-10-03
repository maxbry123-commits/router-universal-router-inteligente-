import { normalizeConfig, readConfig, saveConfig } from "./config.js";
import { executeAction } from "./bridge.js";
import { renderChat } from "./panels/chat.js";
import { renderSettings } from "./panels/settings.js";

const app = document.getElementById("app");
const status = document.getElementById("status");
const context = {
  config: readConfig(),
  selection: { modelId: "", modeId: "mode-1", selectors: {}, toggles: {} },
  attachments: [], messages: [], draft: "", recorder: null,
  execute: (actionId, payload) => executeAction(actionId, payload),
  notice(message, error = false) {
    status.textContent = message;
    status.className = error ? "error" : "";
  },
  refresh() { document.documentElement.dataset.theme = context.config.theme; app.replaceChildren(renderChat(context)); },
  showChat() { context.refresh(); },
  showSettings() { app.replaceChildren(renderSettings(context)); },
  updateConfig(draft) {
    context.config = saveConfig(draft);
    if (!context.config.models.some(model => model.id === context.selection.modelId)) context.selection.modelId = "";
  },
  setModels(models) {
    context.updateConfig(normalizeConfig({ ...context.config, models }));
    context.notice("Catálogo actualizado desde el backend.");
  },
};

document.documentElement.dataset.theme = context.config.theme;
context.refresh();
