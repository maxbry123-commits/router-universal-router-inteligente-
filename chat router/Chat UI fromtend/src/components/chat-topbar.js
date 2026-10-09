import { el } from "../dom.js";
import { brandMark } from "./mark.js";
import { iconButton } from "./icon-button.js";
import { openChatMenu } from "../windows/chat-menu.js";

export function chatTopbar(context) {
  const menu = iconButton(context, "chatMenu", "more", () => openChatMenu(context));
  menu.setAttribute("aria-haspopup", "dialog");
  return el("header", { class: "topbar" },
    el("div", { class: "brand" }, brandMark("brand-mark"), el("h1", { text: context.config.title })),
    el("div", { class: "top-actions" }, iconButton(context, "configure", "settings", () => context.showSettings()), menu));
}
