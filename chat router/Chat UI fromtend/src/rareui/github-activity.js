import { el } from "../dom.js";
// 12 github-activity: rejilla de actividad; sin datos propios — recibe {day:intensity} reales.
export function githubActivity({ weeks = 20, data = {} } = {}) {
  const grid = el("div", { class: "rui-activity", role: "img", "aria-label": "github-activity" });
  for (let i = 0; i < weeks * 7; i++) {
    const level = Math.max(0, Math.min(4, Number(data[i] || 0)));
    grid.append(el("span", { class: "rui-activity-cell", "data-level": String(level) }));
  }
  return grid;
}
