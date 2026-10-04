import { el, openWindow } from "../dom.js";
import { controlLabel, t } from "../i18n.js";
import { closeChat, exportChat } from "../actions/chat-session.js";
import { windowOption } from "../components/window-option.js";

export function openChatMenu(context) {
  const list = el("div", { class: "option-list" });
  const dialog = openWindow(controlLabel(context, "chatMenu"), el("div", { class: "window-body" }, list), t(context, "closeWindow"));
  list.append(windowOption(controlLabel(context, "close"), context.config.descriptions.close, () => {
    dialog.close(); closeChat(context);
  }, "plus"), windowOption(controlLabel(context, "export"), context.config.descriptions.export, () => {
    try { exportChat(context); dialog.close(); context.notice(t(context, "exportStarted")); }
    catch (error) { context.notice(error.message, true); }
  }, "export"));
  return dialog;
}
