import { button } from "../dom.js";

export function namedButton(context, name, onClick, style, label = context.config.labels[name]) {
  const node = button(label, onClick, style);
  if (context.config.descriptions[name]) node.title = context.config.descriptions[name];
  return node;
}
