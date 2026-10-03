import { normalizeConfig, readConfig, saveConfig } from "./config.js";
import { executeAction } from "./bridge.js";
import { installSameOriginChatBridge } from "./plugins/same-origin-chat.js";
import { renderChat } from "./panels/chat.js";
import { renderSettings } from "./panels/settings.js";
import { t } from "./i18n.js";

const app = document.getElementById("app");
const status = document.getElementById("status");
installSameOriginChatBridge();
let statusTimer;
const context = {
  config: readConfig(),
  selection: { modelId: "", modeId: "mode-1", selectors: {}, toggles: {} },
  attachments: [], messages: [], draft: "", recorder: null,
  execute: (actionId, payload) => executeAction(actionId, payload),
  notice(message, error = false, pending = false) {
    clearTimeout(statusTimer);
    status.textContent = message;
    status.className = error ? "error" : pending ? "pending" : "";
    const windowStatus = document.querySelector("dialog[open] .window-status");
    if (windowStatus) { windowStatus.textContent = message; windowStatus.className = `window-status ${status.className}`; }
    if (!pending) statusTimer = setTimeout(() => { status.textContent = ""; }, error ? 8000 : 3500);
  },
  refresh() {
    const focused = document.activeElement?.getAttribute("data-control");
    document.documentElement.dataset.theme = context.config.theme;
    document.documentElement.lang = context.config.locale;
    app.replaceChildren(renderChat(context));
    if (focused) app.querySelector(`[data-control="${focused}"]`)?.focus();
  },
  showChat() { context.refresh(); app.querySelector('[data-control="configure"]')?.focus(); },
  showSettings() { app.replaceChildren(renderSettings(context)); app.querySelector(".settings-header button")?.focus(); },
  updateConfig(draft) {
    context.config = normalizeConfig(draft);
    let persisted = true;
    try { saveConfig(context.config); }
    catch { persisted = false; }
    if (!context.config.models.some(model => model.id === context.selection.modelId)) context.selection.modelId = "";
    return persisted;
  },
  setModels(models) {
    context.updateConfig(normalizeConfig({ ...context.config, models }));
    context.notice(t(context, "modelsUpdated"));
  },
};

document.documentElement.dataset.theme = context.config.theme;
context.refresh();
