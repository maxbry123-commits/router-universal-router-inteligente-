import { button, el, openWindow } from "../dom.js";
import { t } from "../i18n.js";
import { openIconLibrary } from "./icon-library.js";
import { TEXT_ROLES, TEXT_COLORS, FONTS, defaultTypography, readTypography, saveTypography } from "../typography/state.js";
import { applyTypography, exportTypographyCss } from "../typography/apply.js";

function field(label, input) {
  return el("label", { class: "setting-field" }, el("span", { text: label }), input);
}
function numberInput(value, min, max, onChange) {
  const input = el("input", { type: "number", min, max, step: "any" });
  input.value = String(value);
  input.addEventListener("input", () => onChange(Number(input.value)));
  return input;
}
function toggle(label, value, onChange) {
  const input = el("input", { type: "checkbox" });
  input.checked = value;
  input.addEventListener("change", () => onChange(input.checked));
  return el("label", { class: "typo-toggle" }, input, el("span", { text: label }));
}
function styleNode(node, row, capSize) {
  node.style.color = row.color;
  node.style.fontFamily = FONTS[row.font];
  node.style.fontSize = Math.min(row.size, capSize) + "px";
  node.style.fontWeight = String(row.weight);
  node.style.letterSpacing = row.tracking + "px";
  node.style.lineHeight = String(row.lineHeight);
  node.style.fontStyle = row.italic ? "italic" : "normal";
  node.style.textDecoration = row.underline ? "underline" : "none";
  node.style.textTransform = row.uppercase ? "uppercase" : "none";
  node.style.textAlign = row.align;
  return node;
}

export function openTypography(context) {
  const state = readTypography();
  let role = "title";
  const status = el("p", { role: "status", class: "muted" });
  const controls = el("div", { class: "typo-controls" });
  const preview = el("div", { class: "typo-preview" });
  const tabs = el("div", { class: "typo-role-tabs" });

  function mobilePreview() {
    return el("div", { class: "typo-mobile" },
      styleNode(el("p", { text: state.title.sample }), state.title, 20),
      styleNode(el("p", { text: state.subtitle.sample }), state.subtitle, 14),
      styleNode(el("p", { text: state.body.sample }), state.body, 13),
      styleNode(el("button", { type: "button", text: state.button.sample }), state.button, 12));
  }

  let updateContrast = () => {};
  function paint() {
    const row = state[role];
    controls.replaceChildren();
    preview.replaceChildren(mobilePreview());
    tabs.querySelectorAll(".chip").forEach(b => b.setAttribute("aria-pressed", String(b.dataset.role === role)));

    const sample = role === "placeholder"
      ? el("input", { type: "text", class: "typo-sample-input" })
      : el("p", { class: "typo-sample", contenteditable: "true", text: row.sample });
    if (role === "placeholder") {
      sample.placeholder = row.sample;
      sample.addEventListener("input", () => { row.sample = sample.value; });
    } else {
      sample.addEventListener("input", () => { row.sample = sample.textContent; });
    }
    const refresh = () => {
      if (role === "placeholder") { sample.placeholder = row.sample; }
      styleNode(sample, row, 48);
      updateContrast();
      preview.replaceChildren(mobilePreview());
    };

    const colorRow = el("div", { class: "chip-row" },
      ...TEXT_COLORS.map(hex => {
        const c = button("", () => { row.color = hex; paint(); }, "chip typo-swatch");
        c.style.setProperty("--chip-accent", hex);
        c.setAttribute("aria-label", hex);
        c.setAttribute("aria-pressed", String(row.color === hex));
        return c;
      }),
      (() => {
        const picker = el("input", { type: "color", "aria-label": t(context, "typoCustomColor") });
        picker.value = row.color;
        picker.addEventListener("input", () => { row.color = picker.value.toUpperCase(); refresh(); });
        return picker;
      })());

    const font = el("select");
    for (const key of Object.keys(FONTS)) font.append(el("option", { value: key, text: key }));
    font.value = row.font;
    font.addEventListener("change", () => { row.font = font.value; refresh(); });

    const align = el("select");
    for (const value of ["left", "center", "right"]) align.append(el("option", { value, text: value }));
    align.value = row.align;
    align.addEventListener("change", () => { row.align = align.value; refresh(); });

    const contrast = el("p", { class: "muted" });
    updateContrast = () => {
      const hex = row.color.replace("#", "");
      const channel = i => parseInt(hex.slice(i, i + 2), 16) / 255;
      const lum = v => v <= 0.03928 ? v / 12.92 : Math.pow((v + 0.055) / 1.055, 2.4);
      const l = 0.2126 * lum(channel(0)) + 0.7152 * lum(channel(2)) + 0.0722 * lum(channel(4));
      const moduleLum = 0.027;
      const ratio = (Math.max(l, moduleLum) + 0.05) / (Math.min(l, moduleLum) + 0.05);
      contrast.textContent = t(context, "typoContrast", { ratio: ratio.toFixed(2) });
      contrast.className = ratio < 4.5 ? "error" : "muted";
    };
    updateContrast();
    refresh();

    controls.append(
      sample, contrast,
      field(t(context, "typoColor"), colorRow),
      field(t(context, "typoFont"), font),
      field(t(context, "typoSize"), numberInput(row.size, 10, 48, v => { row.size = v; refresh(); })),
      field(t(context, "typoWeight"), numberInput(row.weight, 300, 900, v => { row.weight = v; refresh(); })),
      field(t(context, "typoTracking"), numberInput(row.tracking, -1, 4, v => { row.tracking = v; refresh(); })),
      field(t(context, "typoLineHeight"), numberInput(row.lineHeight, 1, 2.3, v => { row.lineHeight = v; refresh(); })),
      el("div", { class: "typo-toggles" },
        toggle(t(context, "typoItalic"), row.italic, v => { row.italic = v; refresh(); }),
        toggle(t(context, "typoUnderline"), row.underline, v => { row.underline = v; refresh(); }),
        toggle(t(context, "typoUppercase"), row.uppercase, v => { row.uppercase = v; refresh(); })),
      field(t(context, "typoAlign"), align));
  }

  for (const r of TEXT_ROLES) {
    const b = button(t(context, "typo_" + r), () => { role = r; paint(); }, "chip");
    b.dataset.role = r;
    tabs.append(b);
  }

  const actions = el("div", { class: "typo-col typo-col-actions" },
    button(t(context, "typoApply"), () => {
      const ok = saveTypography(state);
      applyTypography(state);
      status.textContent = t(context, ok ? "typoSaved" : "settingsTemporary");
      status.className = ok ? "" : "error";
    }, "primary"),
    button(t(context, "typoReset"), () => { Object.assign(state[role], defaultTypography()[role]); paint(); }),
    button(t(context, "typoExport"), () => {
      try {
        const blob = new Blob([exportTypographyCss(state)], { type: "text/css" });
        const url = URL.createObjectURL(blob);
        const a = el("a", { href: url, download: "yaiwes-tipografia.css" });
        document.body.append(a); a.click(); a.remove();
        URL.revokeObjectURL(url);
        status.textContent = t(context, "configExported");
      } catch (error) { status.textContent = error.message; status.className = "error"; }
    }),
    button(t(context, "iconLibrary"), () => openIconLibrary(context), "ghost"),
    status);

  const dialog = openWindow(t(context, "typography"), el("div", { class: "typo-editor" },
    el("div", { class: "typo-col" }, tabs, controls),
    el("div", { class: "typo-col typo-col-preview" },
      el("p", { class: "muted", text: t(context, "typoMobileNote") }),
      preview),
    actions),
    t(context, "closeWindow"));
  dialog.classList.add("typo-window");
  paint();
  return dialog;
}
