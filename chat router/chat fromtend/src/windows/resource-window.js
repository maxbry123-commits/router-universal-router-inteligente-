import { el, openWindow } from "../dom.js";

export async function resourceWindow(title, actionId, context) {
  const body = el("div", { class: "window-body" }, el("p", { class: "muted", text: "Consultando el backend…" }));
  openWindow(title, body);
  try {
    const result = await context.execute(actionId);
    if (!Array.isArray(result.items)) throw new Error("INVALID_RESOURCE_RESPONSE");
    body.replaceChildren(...result.items.map(item => el("div", { class: "resource" },
      el("strong", { text: String(item.label || item.id || "") }),
      el("span", { class: "muted", text: String(item.description || "") }))));
    if (!result.items.length) body.append(el("p", { class: "muted", text: "El backend no devolvió elementos." }));
  } catch (error) { body.replaceChildren(el("p", { class: "error", text: error.message })); }
}
