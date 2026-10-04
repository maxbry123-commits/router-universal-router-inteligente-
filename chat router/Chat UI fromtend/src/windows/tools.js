import { el, openWindow } from "../dom.js";
import { controlLabel, t } from "../i18n.js";
import { windowOption } from "../components/window-option.js";
import { icon } from "../components/icon.js";
import { openActions } from "./actions.js";
import { openSelectors } from "./selectors.js";
import { openControls } from "./controls.js";
import { openSkills } from "./skills.js";
import { openConnectors } from "./connectors.js";
import { openPlugins } from "./plugins.js";
import { openFichas } from "./fichas.js";
import { openComponents } from "./components.js";
import { openAgents, openConversations } from "./agents.js";

export function openTools(context, pickFiles) {
  const list = el("div", { class: "option-list" });
  const dialog = openWindow(controlLabel(context, "tools"), el("div", { class: "window-body" }, list), t(context, "closeWindow"));
  for (const [name, glyph, action, isWindow] of [
    ["attach", "attach", () => pickFiles(context.config.attachActionId), false],
    ["documents", "file", () => pickFiles(context.config.documentsActionId), false],
    ["skills", "grid", () => openSkills(context), true],
    ["connectors", "connectors", () => openConnectors(context), true],
    ["plugins", "connectors", () => openPlugins(context), true],
    ["fichas", "grid", () => openFichas(context), true],
    ["components", "grid", () => openComponents(context), true],
    ["agents", "connectors", () => openAgents(context), true],
    ["conversations", "file", () => openConversations(context), true],
    ["selectors", "grid", () => openSelectors(context), true],
    ["controls", "controls", () => openControls(context), true],
    ["functions", "plus", () => openActions(context), true],
  ]) {
    const node = windowOption(controlLabel(context, name), context.config.descriptions[name], () => { dialog.close(); action(); }, glyph);
    node.setAttribute("data-control", name);
    if (isWindow) { node.setAttribute("aria-haspopup", "dialog"); node.append(icon("chevron")); }
    list.append(node);
  }
  return dialog;
}
