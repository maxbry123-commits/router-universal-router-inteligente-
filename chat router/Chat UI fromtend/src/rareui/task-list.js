import { el, button } from "../dom.js";
// 21 task-list: lista con estado real por elemento; eliminar sólo llama al callback.
export function taskList({ tasks = [], onRemove } = {}) {
  const list = el("ul", { class: "rui-tasks" });
  for (const task of tasks) {
    const row = el("li", { class: "rui-task" },
      el("span", { text: String(task.label ?? task) }),
      button("×", async () => { if (await onRemove?.(task) !== false) row.remove(); }, "ghost"));
    list.append(row);
  }
  if (!tasks.length) list.append(el("li", { class: "muted", text: "—" }));
  return list;
}
