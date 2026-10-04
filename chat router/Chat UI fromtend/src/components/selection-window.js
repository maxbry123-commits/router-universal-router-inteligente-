import { button, el, openWindow } from "../dom.js";
import { t } from "../i18n.js";
import { windowOption } from "./window-option.js";

export function selectionWindow(context, { title, description, items, selectedId, emptyText, onApply, searchable = false }) {
  let draftId = selectedId;
  const list = el("div", { class: "option-list", role: "listbox", "aria-label": title });
  const body = el("div", { class: "window-body" });
  const empty = el("p", { class: "muted", text: items.length ? t(context, "noResults") : emptyText, hidden: items.length ? "" : undefined });
  const dialog = openWindow(title, body, t(context, "closeWindow"));
  const cancel = button(t(context, "cancel"), () => dialog.close(), "ghost");
  const apply = button(t(context, "apply"), async () => {
    const item = items.find(entry => entry.id === draftId);
    if (!item) return;
    dialog.setAttribute("aria-busy", "true");
    const controls = Array.from(dialog.querySelectorAll("button, input"));
    const disabled = controls.map(node => node.disabled);
    controls.forEach(node => { node.disabled = true; });
    try {
      const message = await onApply(item);
      dialog.close();
      context.refresh();
      context.notice(message);
    } catch (error) { context.notice(error.message, true); }
    finally {
      dialog.removeAttribute("aria-busy");
      controls.forEach((node, index) => { node.disabled = disabled[index]; });
    }
  }, "primary");
  apply.disabled = !items.some(item => item.id === draftId);
  dialog.addEventListener("cancel", event => { if (dialog.getAttribute("aria-busy") === "true") event.preventDefault(); });
  const redraw = () => {
    const nodes = Array.from(list.children);
    const focusTarget = nodes.find(node => !node.hidden && node.getAttribute("data-option") === draftId) || nodes.find(node => !node.hidden);
    for (const node of list.children) {
      const selected = node.getAttribute("data-option") === draftId;
      node.classList.toggle("selected", selected);
      node.setAttribute("aria-selected", String(selected));
      node.tabIndex = node === focusTarget ? 0 : -1;
    }
    apply.disabled = !items.some(item => item.id === draftId);
  };
  for (const item of items) {
    const node = windowOption(item.label, item.description, () => { draftId = item.id; redraw(); });
    node.setAttribute("data-option", item.id);
    node.setAttribute("role", "option");
    node.addEventListener("keydown", event => {
      if (!["ArrowDown", "ArrowUp", "Home", "End"].includes(event.key)) return;
      event.preventDefault();
      const nodes = Array.from(list.children).filter(entry => !entry.hidden);
      const index = nodes.indexOf(node);
      const next = event.key === "Home" ? 0 : event.key === "End" ? nodes.length - 1 : (index + (event.key === "ArrowDown" ? 1 : -1) + nodes.length) % nodes.length;
      nodes[next]?.focus(); nodes[next]?.click();
    });
    list.append(node);
  }
  if (description) body.append(el("p", { class: "sub", text: description }));
  if (searchable) {
    const search = el("input", { type: "search", placeholder: t(context, "modelSearch"), "aria-label": t(context, "modelSearch") });
    search.addEventListener("input", () => {
      const query = search.value.trim().toLocaleLowerCase(context.config.locale);
      for (const node of list.children) node.hidden = !node.textContent.toLocaleLowerCase(context.config.locale).includes(query);
      empty.hidden = Array.from(list.children).some(node => !node.hidden);
      redraw();
    });
    body.append(el("div", { class: "search-field" }, search));
  }
  body.append(list, empty);
  dialog.append(el("div", { class: "window-footer" }, cancel, apply));
  redraw();
  return dialog;
}
