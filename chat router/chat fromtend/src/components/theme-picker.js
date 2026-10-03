import { button, el } from "../dom.js";
import { t } from "../i18n.js";

export function themePicker(context, draft) {
  const options = el("div", { class: "theme-options", role: "group", "aria-label": t(context, "theme") });
  for (const [id, key] of [["little", "themeLittle"], ["matte", "themeMatte"], ["blanco", "themeBlanco"]]) {
    const node = button("", () => {
      draft.theme = id;
      for (const option of options.children) option.setAttribute("aria-pressed", String(option === node));
    }, "theme-option");
    node.setAttribute("aria-pressed", String(draft.theme === id));
    node.setAttribute("data-theme-option", id);
    node.append(el("span", { class: "theme-sample", "data-theme": id, "aria-hidden": "true" }, el("span"), el("span")),
      el("span", { class: "theme-label", text: t(context, key) }));
    options.append(node);
  }
  return el("div", { class: "setting-field" }, el("span", { text: t(context, "theme") }), options);
}
