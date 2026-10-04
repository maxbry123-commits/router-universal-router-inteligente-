import { el, button, openWindow } from "../dom.js";
import { t } from "../i18n.js";
import { ICON_META, V12_COLORS, v12Svg } from "../icons-v12.js";

const CATS = Object.freeze([
  { id: "all", label: "catAll" }, { id: "general", label: "catGeneral" },
  { id: "files", label: "catFiles" }, { id: "ai", label: "catAi" },
  { id: "connect", label: "catConnect" }, { id: "media", label: "catMedia" },
  { id: "status", label: "catStatus" },
]);

export function openIconLibrary(context) {
  let cat = "all", color = "white";
  const grid = el("div", { class: "icon-grid" });
  const status = el("p", { class: "muted", role: "status" });
  const cats = el("div", { class: "chip-row" });
  const colors = el("div", { class: "chip-row" });

  const paint = () => {
    grid.replaceChildren();
    for (const meta of ICON_META.filter(i => cat === "all" || i.cat === cat)) {
      const hex = V12_COLORS.find(c => c.id === color)?.hex || "#F8F8F8";
      const cell = button("", async () => {
        const svg = `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="${hex}" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round">${v12Svg(meta.id).innerHTML}</svg>`;
        try { await navigator.clipboard.writeText(svg); status.textContent = t(context, "iconCopied", { name: meta.name }); }
        catch { status.textContent = t(context, "iconCopyFailed"); }
      }, "icon-cell");
      const glyph = v12Svg(meta.id, "svg-icon");
      glyph.style.color = hex;
      cell.append(glyph, el("span", { class: "name", text: meta.name }), el("span", { class: "sub", text: meta.use }));
      cell.setAttribute("data-icon", meta.id);
      grid.append(cell);
    }
    cats.querySelectorAll("button").forEach(b => b.setAttribute("aria-pressed", String(b.dataset.cat === cat)));
    colors.querySelectorAll("button").forEach(b => b.setAttribute("aria-pressed", String(b.dataset.color === color)));
  };

  for (const c of CATS) {
    const b = button(t(context, c.label), () => { cat = c.id; paint(); }, "chip");
    b.dataset.cat = c.id;
    cats.append(b);
  }
  for (const c of V12_COLORS) {
    const b = button(c.name, () => { color = c.id; paint(); }, "chip");
    b.dataset.color = c.id;
    b.style.setProperty("--chip-accent", c.hex);
    colors.append(b);
  }
  paint();
  const dialog = openWindow(t(context, "iconLibrary"),
    el("div", { class: "window-body" },
      el("p", { class: "muted", text: t(context, "iconLibraryDesc") }),
      cats, colors, grid, status),
    t(context, "closeWindow"));
  return dialog;
}
