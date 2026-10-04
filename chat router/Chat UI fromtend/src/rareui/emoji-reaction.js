import { el, button } from "../dom.js";
// 13 emoji-reaction: reacciones con contadores reales de la sesión local.
export function emojiReaction({ emojis = ["👍", "❤️", "🔥"], counts = {} } = {}) {
  const root = el("div", { class: "rui-reactions" });
  for (const emoji of emojis) {
    let count = Number(counts[emoji] || 0);
    const b = button(emoji + " " + count, () => { count++; b.textContent = emoji + " " + count; b.setAttribute("aria-pressed", "true"); }, "chip");
    root.append(b);
  }
  return root;
}
