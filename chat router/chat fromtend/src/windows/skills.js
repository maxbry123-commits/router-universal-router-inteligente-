import { resourceWindow } from "./resource-window.js";
import { controlLabel } from "../i18n.js";
export const openSkills = context => resourceWindow(controlLabel(context, "skills"), context.config.skillsActionId, context);
