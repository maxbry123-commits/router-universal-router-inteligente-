import { resourceWindow } from "./resource-window.js";
import { controlLabel } from "../i18n.js";

export const openAgents = context =>
  resourceWindow(controlLabel(context, "agents"), "chat.agents", context);
export const openConversations = context =>
  resourceWindow(controlLabel(context, "conversations"), "chat.conversations", context);
