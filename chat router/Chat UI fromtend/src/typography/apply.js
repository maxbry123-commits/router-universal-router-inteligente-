import { FONTS, TEXT_ROLES } from "./state.js";

const SELECTORS = {
  title: ".brand h1, .welcome h2",
  subtitle: ".welcome p, .composer-model .selection-label",
  body: ".conversation, .option-copy .name",
  input: ".composer textarea",
  output: ".message.assistant",
  button: "button",
  meta: ".sub, .muted, #status",
};

const props = row => [
  ["color", row.color],
  ["font-family", FONTS[row.font]],
  ["font-size", row.size + "px"],
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
  const rules = TEXT_ROLES.filter(role => role !== "placeholder").map(role => {
    const declaration = props(state[role]).map(([name, value]) => name + ":" + value).join(";");
    return SELECTORS[role] + "{" + declaration + "}";
  });
  const ph = props(state.placeholder).filter(([name]) => name !== "text-decoration" && name !== "text-align");
  rules.push(".composer textarea::placeholder{" + ph.map(([n, v]) => n + ":" + v).join(";") + "}");
  styleNode.textContent = rules.join("\n");
  return styleNode;
}

export function exportTypographyCss(state) {
  const node = applyTypography(state);
  return "/* Tipografia YAIWES exportada */\n" + node.textContent;
}
