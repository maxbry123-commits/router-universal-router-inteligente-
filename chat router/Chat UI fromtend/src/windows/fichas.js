import { button, el, openWindow } from "../dom.js";
import { controlLabel, t } from "../i18n.js";

export function openFichas(context) {
  const list = el("div", { class: "option-list" });
  const detail = el("div", { role: "status" });
  const reload = button(t(context, "modelsRefresh"), () => load(), "ghost");
  const body = el("div", { class: "window-body" }, reload, list, detail);
  openWindow(controlLabel(context, "fichas"), body, t(context, "closeWindow"));

  async function load() {
    reload.disabled = true;
    list.replaceChildren(el("p", { class: "muted", text: t(context, "backendLoading") }));
    detail.replaceChildren();
    try {
      const result = await context.execute("chat.fichas");
      if (!Array.isArray(result.items)) throw new Error("INVALID_FICHAS_RESPONSE");
      list.replaceChildren();
      for (const item of result.items) {
        const node = button(item.label, async () => {
          node.disabled = true;
          detail.replaceChildren(el("p", { class: "muted", text: t(context, "backendLoading") }));
          try {
            const result = await context.execute("chat.ficha", { id: item.id });
            const ficha = result.ficha;
            if (!ficha || ficha.id !== item.id) throw new Error("INVALID_FICHA_RESPONSE");
            detail.replaceChildren(el("strong", { text: ficha.id }),
              el("p", { class: "muted", text: `${ficha.status || "UNKNOWN"} · ${ficha.version || ""} · ${ficha.kind || ""}` }));
          } catch (error) { detail.replaceChildren(el("p", { class: "error", text: error.message })); }
          finally { node.disabled = false; }
        }, "option");
        list.append(node);
      }
      if (!result.items.length) list.append(el("p", { class: "muted", text: t(context, "resourcesEmpty") }));
    } catch (error) { list.replaceChildren(el("p", { class: "error", text: error.message })); }
    finally { reload.disabled = false; }
  }
  load();
}
