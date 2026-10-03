import { resourceWindow } from "./resource-window.js";
export const openConnectors = context => resourceWindow(context.config.labels.connectors, context.config.connectorsActionId, context);
