import { FONTS, TEXT_ROLES } from "./state.js";

const SELECTORS = {
  title: ".brand h1, .welcome h2",
  subtitle: ".welcome p, .composer-model .selection-label",
  body: ".conversation, .option-copy .name",
  input: ".composer textarea",
  output: ".message.assistant",
  button: "button",
  symbol: ".icon svg, .svg-icon, .icon",
  label: ".eyebrow, .preview-label, .window-heading .eyebrow, [data-control-label]",
  helper: ".helper, .preview-helper, .attachment, .result-note",
  status: ".sub, .muted, #status, .panel-state, .state",
};

const props = (row, scale) => [
  ["color", row.color],
  ["font-family", FONTS[row.font]],
  ["font-size", "calc(" + row.size + "px * " + scale + ")"],
  ["font-weight", String(row.weight)],
  ["letter-spacing", row.tracking + "px"],
  ["line-height", String(row.lineHeight)],
  ["font-style", row.italic ? "italic" : "normal"],
  ["text-decoration", row.underline ? "underline" : "none"],
  ["text-transform", row.uppercase ? "uppercase" : "none"],
  ["text-align", row.align],
];

let styleNode;
export function applyTypography(state, doc = document) {
  if (!styleNode || !styleNode.isConnected || styleNode.ownerDocument !== doc) {
    styleNode = doc.createElement("style");
    styleNode.id = "yaiwes-typography";
    (doc.head || doc.documentElement).append(styleNode);
  }
  const roles = state.roles || state;
  const scale = (state.scale || 100) / 100;
  const rules = [":root{--status-blue:" + state.signal + ";--blue:" + state.signal + ";--on:" + state.signal + "}"];
  for (const role of TEXT_ROLES.filter(r => r !== "placeholder")) {
    if (!SELECTORS[role]) continue;
    const declaration = props(roles[role], scale).map(([name, value]) => name + ":" + value).join(";");
    rules.push(SELECTORS[role] + "{" + declaration + "}");
  }
  const ph = props(roles.placeholder, scale).filter(([name]) => name !== "text-decoration" && name !== "text-align");
  rules.push(".composer textarea::placeholder{" + ph.map(([n, v]) => n + ":" + v).join(";") + "}");
  styleNode.textContent = rules.join("\n");
  return styleNode;
}

export function exportTypographyCss(state) {
  const node = applyTypography(state);
  return "/* Tipografia YAIWES exportada */\n" + node.textContent;
}
