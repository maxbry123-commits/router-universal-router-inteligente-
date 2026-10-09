import { el } from "../dom.js";
import { t } from "../i18n.js";

export function messageStream(context) {
  const stream = el("div", { class: "messages", role: "log", "aria-label": t(context, "messagesAria") });
  for (const message of context.messages) {
    stream.append(el("article", { class: `message ${message.role}`, text: message.text }));
  }
  return stream;
}
