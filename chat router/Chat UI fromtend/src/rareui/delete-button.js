import { el, button } from "../dom.js";
// 18 delete-button: confirmación en dos pasos; el callback decide el borrado real.
export function deleteButton({ label = "Eliminar", confirm = "Confirmar", onDelete } = {}) {
  let armed = false;
  const b = button(label, async () => {
    if (!armed) { armed = true; b.textContent = confirm; b.classList.add("armed"); return; }
    b.disabled = true;
    try { await onDelete?.(); }
    finally { armed = false; b.disabled = false; b.textContent = label; b.classList.remove("armed"); }
  }, "rui-delete");
  return b;
}
