import { el } from "../dom.js";

export function messageStream(context) {
  const stream = el("div", { class: "messages", role: "log", "aria-label": "Mensajes" });
  for (const message of context.messages) {
    stream.append(el("article", { class: `message ${message.role}`, text: message.text }));
  }
  return stream;
}
