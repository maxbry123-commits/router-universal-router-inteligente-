export const TYPOGRAPHY_KEY = "yaiwes.chat.typography.v1";
// Roles y paletas copiados del editor V09 del usuario (FROMTED-YAIWES-COLORES-ICONOS-V09.html).
export const TEXT_ROLES = ["title", "subtitle", "body", "input", "placeholder", "output",
  "button", "symbol", "label", "helper", "status"];
export const ROLE_LABELS = {
  title: "Títulos", subtitle: "Subtítulos", body: "Escritura general", input: "Texto de entrada",
  placeholder: "Placeholder", output: "Salidas y respuestas", button: "Texto de botones",
  symbol: "Símbolos 2D", label: "Etiquetas", helper: "Ayudas / notas", status: "Texto de estado",
};
export const PALETTE = [
  ["Blanco", "#FFFFFF"], ["Azul eléctrico", "#0848F7"], ["Verde intenso", "#00D760"],
  ["Rojo vivo", "#FF3650"], ["Naranja vivo", "#FF6D11"], ["Gris claro", "#DADADA"],
  ["Cian", "#05C7FF"], ["Violeta", "#895DFA"], ["Dorado", "#FFBF36"], ["Rosa", "#FF54AD"],
];
export const TEXT_COLORS = PALETTE.map(([, hex]) => hex);
export const SIGNAL_COLORS = PALETTE.slice(0, 6);
export const PRESETS = [
  ["Neutro", { title: "#FFFFFF", subtitle: "#DADADA", body: "#E6E6E6", input: "#FFFFFF", placeholder: "#A9A9A9", output: "#E2E2E2", button: "#F2F2F2", symbol: "#F4F4F4", label: "#F0F0F0", helper: "#A9A9A9", status: "#D0D0D0" }],
  ["Blanco y azul", { title: "#FFFFFF", subtitle: "#DADADA", button: "#FFFFFF", symbol: "#FFFFFF", output: "#DADADA" }],
  ["Blanco y verde", { title: "#FFFFFF", subtitle: "#DADADA", output: "#00D760", button: "#FFFFFF", symbol: "#FFFFFF" }],
  ["Naranja activo", { title: "#FFFFFF", subtitle: "#DADADA", output: "#FF6D11", button: "#FFFFFF", symbol: "#FF6D11" }],
  ["Azul + naranja", { title: "#FFFFFF", subtitle: "#DADADA", output: "#0848F7", button: "#FFFFFF", symbol: "#FF6D11" }],
  ["Grises puros", { title: "#FFFFFF", subtitle: "#DADADA", output: "#F0F0F0", button: "#DADADA", symbol: "#DADADA" }],
];
export const GRAY_SURFACES = [["Fondo", "--bg"], ["Panel", "--surface"], ["Módulo", "--module"],
  ["Seleccionado", "--marked"], ["Máscara", "--mask"]];
export const ICON_SLOTS = { send: "Enviar", attach: "Adjuntar", tools: "Herramientas", back: "Volver" };
export const DEFAULT_ICONS = { send: "send", attach: "paperclip", tools: "settings", back: "x" };
export const FONTS = {
  system: "system-ui, -apple-system, 'Segoe UI', Roboto, Arial, sans-serif",
  sans: "Inter, Arial, Helvetica, sans-serif",
  serif: "Georgia, 'Times New Roman', serif",
  mono: "ui-monospace, Consolas, monospace",
};
const SAMPLES = {
  title: "Diseño inteligente", subtitle: "Subtítulo de ejemplo", body: "Texto de escritura editable",
  input: "Escribe aquí", placeholder: "Texto de ayuda", output: "Resultado local: sin respuesta IA",
  button: "Acción de ejemplo", symbol: "★", label: "ETIQUETA", helper: "Nota auxiliar de ayuda",
  status: "En curso · estado",
};
const SIZES = { title: 28, subtitle: 18, body: 14, input: 14, placeholder: 14, output: 14,
  button: 14, symbol: 16, label: 11, helper: 11, status: 11 };

const roleDefaults = role => ({
  color: "#EDEDED", font: "system", size: SIZES[role], weight: role === "title" || role === "subtitle" ? 700 : 400,
  tracking: 0, lineHeight: 1.5, italic: false, underline: false, uppercase: false,
  align: "left", sample: SAMPLES[role],
});

export const defaultTypography = () => ({
  roles: Object.fromEntries(TEXT_ROLES.map(role => [role, roleDefaults(role)])),
  signal: "#0848F7", scale: 100, icons: { ...DEFAULT_ICONS },
});

const bounded = (value, fallback, min, max) => Number.isFinite(Number(value))
  ? Math.max(min, Math.min(max, Number(value))) : fallback;

export function normalizeTypography(value) {
  const defaults = defaultTypography();
  const source = value && typeof value === "object" ? value : {};
  const rolesSource = source.roles && typeof source.roles === "object" ? source.roles : source;
  const roles = Object.fromEntries(TEXT_ROLES.map(role => {
    const row = rolesSource[role] && typeof rolesSource[role] === "object" ? rolesSource[role] : {};
    const base = defaults.roles[role];
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
  const icons = { ...DEFAULT_ICONS };
  if (source.icons && typeof source.icons === "object") {
    for (const slot of Object.keys(DEFAULT_ICONS)) {
      if (typeof source.icons[slot] === "string" && /^[a-z0-9-]{1,40}$/.test(source.icons[slot])) icons[slot] = source.icons[slot];
    }
  }
  return {
    roles,
    signal: /^#[0-9a-f]{6}$/i.test(source.signal) ? source.signal.toUpperCase() : defaults.signal,
    scale: bounded(source.scale, defaults.scale, 70, 160),
    icons,
  };
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
