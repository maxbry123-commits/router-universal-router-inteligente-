import { resourceWindow } from "./resource-window.js";
export const openSkills = context => resourceWindow(context.config.labels.skills, context.config.skillsActionId, context);
