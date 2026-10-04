import { button, el, openWindow } from "../dom.js";
import { t } from "../i18n.js";

export async function resourceWindow(title, actionId, context) {
  const content = el("div");
  const reload = button(t(context, "modelsRefresh"), () => load(), "ghost");
  const body = el("div", { class: "window-body" }, reload, content);
  openWindow(title, body, t(context, "closeWindow"));
  async function load() {
    reload.disabled = true;
    content.replaceChildren(el("p", { class: "muted", text: t(context, "backendLoading") }));
    try {
      const result = await context.execute(actionId);
      if (!Array.isArray(result.items)) throw new Error("INVALID_RESOURCE_RESPONSE");
      content.replaceChildren(...result.items.map(item => el("div", { class: "resource" },
        el("strong", { text: String(item.label || item.id || "") }),
        el("span", { class: "muted", text: String(item.description || "") }))));
      if (!result.items.length) content.append(el("p", { class: "muted", text: t(context, "resourcesEmpty") }));
    } catch (error) { content.replaceChildren(el("p", { class: "error", text: error.message })); }
    finally { reload.disabled = false; }
  }
  await load();
}
