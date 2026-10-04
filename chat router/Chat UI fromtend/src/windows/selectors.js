import { el, openWindow } from "../dom.js";
import { controlLabel, slotLabel, t } from "../i18n.js";
import { windowOption } from "../components/window-option.js";
import { icon } from "../components/icon.js";
import { openSelector1 } from "./selector-1.js";
import { openSelector2 } from "./selector-2.js";
import { openSelector3 } from "./selector-3.js";
import { openSelector4 } from "./selector-4.js";
import { openSelector5 } from "./selector-5.js";

const windows = [openSelector1, openSelector2, openSelector3, openSelector4, openSelector5];

export function openSelectors(context) {
  const list = el("div", { class: "option-list" });
  const dialog = openWindow(controlLabel(context, "selectors"), el("div", { class: "window-body" }, list), t(context, "closeWindow"));
  context.config.selectors.forEach((slot, index) => {
    const node = windowOption(slotLabel(context, slot), slot.description, () => { dialog.close(); windows[index](context); });
    node.setAttribute("aria-haspopup", "dialog");
    node.setAttribute("data-selector", slot.id);
    node.append(icon("chevron"));
    list.append(node);
  });
  return dialog;
}
