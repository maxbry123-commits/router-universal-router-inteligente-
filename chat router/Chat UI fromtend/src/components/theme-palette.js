import { el } from "../dom.js";

export const THEME_TOKENS = Object.freeze({
  gris: { Fondo: "#1B1B1B", Panel: "#202020", "Módulo": "#2A2A2A", Seleccionado: "#3C3C3C", "Máscara": "#484848" },
  little: { Fondo: "#1C1B1A", Panel: "#2A2927", "Módulo": "#353330", Seleccionado: "#49413D", "Máscara": "#544F4A" },
  matte: { Fondo: "#0A0A0D", Panel: "#141417", "Módulo": "#202025", Seleccionado: "#303039", "Máscara": "#3F3F4E" },
  blanco: { Fondo: "#F4F4F5", Panel: "#FFFFFF", "Módulo": "#FFFFFF", Seleccionado: "#EAEAEA", "Máscara": "#E1E1E1" },
  crystal: { Fondo: "#0C1421", Panel: "rgba(240,249,255,.08)", "Módulo": "rgba(240,249,255,.12)", Seleccionado: "rgba(240,249,255,.23)", "Máscara": "rgba(240,249,255,.32)" },
  orange: { Fondo: "#100E0D", Panel: "#1B1816", "Módulo": "#26211D", Seleccionado: "#3B2F26", "Máscara": "#514032" },
  blue: { Fondo: "#0A1424", Panel: "#122238", "Módulo": "#192C45", Seleccionado: "#294562", "Máscara": "#3B5771" },
});

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
