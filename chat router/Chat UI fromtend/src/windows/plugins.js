import { resourceWindow } from "./resource-window.js";
import { controlLabel } from "../i18n.js";

export const openPlugins = context => resourceWindow(controlLabel(context, "plugins"), "chat.plugins", context);
