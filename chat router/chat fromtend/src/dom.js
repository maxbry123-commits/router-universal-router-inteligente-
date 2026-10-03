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
  const dialog = el("dialog", { class: "window", "aria-label": title });
  dialog.append(el("header", { class: "window-header" }, el("h2", { text: title }), button(closeLabel, () => dialog.close(), "ghost")), content);
  dialog.addEventListener("close", () => dialog.remove());
  document.body.append(dialog);
  dialog.showModal();
  return dialog;
}
