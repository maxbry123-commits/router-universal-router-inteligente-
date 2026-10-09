import { button, el } from "../dom.js";
import { t } from "../i18n.js";
import { THEME_PALETTES, THEME_TOKENS, palettePreview } from "./theme-palette.js";

export function themePicker(context, draft) {
  const options = el("div", { class: "theme-options", role: "group", "aria-label": t(context, "theme") });
  for (const { id, label, reference } of THEME_PALETTES) {
    const node = button("", () => {
      draft.theme = id;
      for (const option of options.children) option.setAttribute("aria-pressed", String(option === node));
    }, "theme-option");
    node.setAttribute("aria-pressed", String(draft.theme === id));
    node.setAttribute("data-theme-option", id);
    node.append(palettePreview(id),
      el("span", { class: "theme-label" }, el("strong", { text: t(context, label) }),
        el("small", { text: t(context, reference ? "themeReference" : "themeCanonical") })));
    options.append(node);
  }
  const copyStatus = el("small", { class: "muted", role: "status" });
  const copy = button(t(context, "themeCopy") || "Copiar colores de este tema", async () => {
    const data = THEME_TOKENS[draft.theme] || {};
    const text = Object.entries(data).map(([k, v]) => k + ": " + v).join("\n");
    try { await navigator.clipboard.writeText(text); copyStatus.textContent = "Paleta " + draft.theme + " copiada."; }
    catch { copyStatus.textContent = text; }
  }, "ghost");
  return el("div", { class: "setting-field" }, el("span", { text: t(context, "theme") }), options,
    el("div", { class: "theme-copy" }, copy, copyStatus));
}
