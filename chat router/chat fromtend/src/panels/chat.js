import { el } from "../dom.js";
import { messageStream } from "../components/message-stream.js";
import { brandMark } from "../components/mark.js";
import { chatTopbar } from "../components/chat-topbar.js";
import { chatComposer } from "../components/chat-composer.js";
import { chatDescription, t } from "../i18n.js";

export function renderChat(context) {
  const root = el("section", { class: "chat-panel panel", "aria-label": t(context, "chatAria") });
  const conversation = el("main", { class: "conversation" });
  if (!context.messages.length) conversation.append(el("div", { class: "welcome" },
    brandMark("welcome-icon"), el("h2", { text: t(context, "emptyTitle") }),
    el("p", { class: "muted", text: chatDescription(context) })));
  conversation.append(messageStream(context));
  root.append(chatTopbar(context), conversation, chatComposer(context));
  return root;
}
