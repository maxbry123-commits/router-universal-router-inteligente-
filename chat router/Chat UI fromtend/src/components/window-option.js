import { button, el } from "../dom.js";
import { icon } from "./icon.js";

export function windowOption(label, description, onClick, glyph) {
  const node = button("", onClick, "option");
  if (glyph) node.append(icon(glyph));
  node.append(el("span", { class: "option-copy" }, el("span", { class: "name", text: label }),
    ...(description ? [el("span", { class: "sub", text: description })] : [])));
  return node;
}
