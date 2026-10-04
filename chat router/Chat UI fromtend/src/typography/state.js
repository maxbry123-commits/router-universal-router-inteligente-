export const TYPOGRAPHY_KEY = "yaiwes.chat.typography.v1";
export const TEXT_ROLES = ["title", "subtitle", "body", "input", "placeholder", "output", "button", "meta"];
export const TEXT_COLORS = ["#FFFFFF", "#0848F7", "#10D86B", "#FF475F", "#FF7719", "#DADADA", "#00C8F8", "#8860EA", "#FFC14A", "#FB63AD"];
export const FONTS = {
  system: "system-ui, sans-serif", sans: "Arial, sans-serif", serif: "Georgia, serif",
  mono: "ui-monospace, monospace", verdana: "Verdana, sans-serif",
  trebuch: "'Trebuchet MS', sans-serif", times: "'Times New Roman', serif",
};
const SAMPLES = ["Diseño inteligente", "Subtítulo de ejemplo", "Texto de escritura editable",
  "Escribe aquí", "Texto de ayuda", "Resultado local: sin respuesta IA", "Acción de ejemplo", "Metadatos de estado"];
const SIZES = [28, 20, 14, 14, 14, 14, 14, 12];

export const defaultTypography = () => Object.fromEntries(TEXT_ROLES.map((role, index) => [role, {
  color: "#EDEDED", font: "system", size: SIZES[index], weight: index < 2 ? 700 : 400,
  tracking: 0, lineHeight: 1.5, italic: false, underline: false, uppercase: false,
  align: "left", sample: SAMPLES[index],
}]));

const bounded = (value, fallback, min, max) => Number.isFinite(Number(value))
  ? Math.max(min, Math.min(max, Number(value))) : fallback;

export function normalizeTypography(value) {
  const defaults = defaultTypography();
  return Object.fromEntries(TEXT_ROLES.map(role => {
    const row = value?.[role] || {};
    const base = defaults[role];
    return [role, {
      color: /^#[0-9a-f]{6}$/i.test(row.color) ? row.color.toUpperCase() : base.color,
      font: Object.hasOwn(FONTS, row.font) ? row.font : base.font,
      size: bounded(row.size, base.size, 10, 48), weight: bounded(row.weight, base.weight, 300, 900),
      tracking: bounded(row.tracking, base.tracking, -1, 4),
      lineHeight: bounded(row.lineHeight, base.lineHeight, 1, 2.3),
      italic: row.italic === true, underline: row.underline === true, uppercase: row.uppercase === true,
      align: ["left", "center", "right"].includes(row.align) ? row.align : base.align,
      sample: typeof row.sample === "string" ? row.sample.slice(0, 200) : base.sample,
    }];
  }));
}

export function readTypography(storage = globalThis.localStorage) {
  try { return normalizeTypography(JSON.parse(storage.getItem(TYPOGRAPHY_KEY) || "null")); }
  catch { return defaultTypography(); }
}

export function saveTypography(state, storage = globalThis.localStorage) {
  const normalized = normalizeTypography(state);
  try { storage.setItem(TYPOGRAPHY_KEY, JSON.stringify(normalized)); return true; }
  catch { return false; }
}
