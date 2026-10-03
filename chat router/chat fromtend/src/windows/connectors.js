import { resourceWindow } from "./resource-window.js";
import { controlLabel } from "../i18n.js";
export const openConnectors = context => resourceWindow(controlLabel(context, "connectors"), context.config.connectorsActionId, context);
