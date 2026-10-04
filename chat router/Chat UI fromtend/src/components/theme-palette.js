import { el } from "../dom.js";

export const THEME_PALETTES = Object.freeze([
  { id: "gris", label: "themeGris", reference: false },
  { id: "little", label: "themeLittle", reference: false },
  { id: "matte", label: "themeMatte", reference: false },
  { id: "blanco", label: "themeBlanco", reference: false },
  { id: "crystal", label: "themeCrystal", reference: true },
  { id: "orange", label: "themeOrange", reference: true },
  { id: "blue", label: "themeBlue", reference: true },
]);

export function palettePreview(id) {
  return el("span", { class: "theme-sample", "data-theme": id, "aria-hidden": "true" },
    el("span", { class: "theme-screen" },
      el("span", { class: "theme-surface" }),
      el("span", { class: "theme-card" }),
      el("span", { class: "theme-selected" }),
      el("span", { class: "theme-accent" })
    ),
    el("span", { class: "theme-colors" },
      ...["bg", "surface", "card", "selection-fill", "accent"].map(color =>
        el("span", { class: "theme-color", "data-color": color }))
    )
  );
}
