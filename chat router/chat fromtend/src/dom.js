export function el(tag, attributes = {}, ...children) {
  const node = tag === "svg" || tag === "path"
    ? document.createElementNS("http://www.w3.org/2000/svg", tag)
    : document.createElement(tag);
  for (const [name, value] of Object.entries(attributes)) {
    if (name === "class") node.setAttribute("class", value);
    else if (name === "text") node.textContent = value;
    else if (name === "onClick") node.addEventListener("click", value);
    else if (name === "onChange") node.addEventListener("change", value);
    else if (value !== undefined && value !== null) node.setAttribute(name, String(value));
  }
  node.append(...children);
  return node;
}

export function button(label, onClick, className = "") {
  return el("button", { type: "button", class: className, onClick, text: label });
}

export function openWindow(title, content, closeLabel = "Cerrar") {
  const opener = document.activeElement;
  const dialog = el("dialog", { class: "window", "aria-label": title });
  dialog.append(el("div", { class: "sheet-handle", "aria-hidden": "true" }),
    el("header", { class: "window-header" }, el("h2", { text: title }), button(closeLabel, () => dialog.close(), "ghost")),
    el("p", { class: "window-status", role: "status", "aria-live": "polite" }), content);
  dialog.addEventListener("click", event => {
    if (event.target !== dialog || dialog.getAttribute("aria-busy") === "true") return;
    const rect = dialog.getBoundingClientRect();
    if (event.clientX < rect.left || event.clientX > rect.right || event.clientY < rect.top || event.clientY > rect.bottom) dialog.close();
  });
  dialog.addEventListener("close", () => {
    dialog.remove();
    const target = opener?.isConnected ? opener : document.querySelector('[data-control="tools"]');
    target?.focus();
  });
  document.body.append(dialog);
  dialog.showModal();
  return dialog;
}
