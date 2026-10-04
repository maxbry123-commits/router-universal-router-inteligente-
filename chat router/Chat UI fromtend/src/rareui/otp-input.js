import { el } from "../dom.js";
// 10 otp-input: N casillas con avance automático y pegado completo.
export function otpInput({ length = 6, onComplete } = {}) {
  const root = el("div", { class: "rui-otp", role: "group", "aria-label": "otp-input" });
  const cells = [];
  const value = () => cells.map(c => c.value).join("");
  for (let i = 0; i < length; i++) {
    const cell = el("input", { type: "text", inputmode: "numeric", maxlength: "1", "aria-label": "otp " + (i + 1) });
    cell.addEventListener("input", () => {
      cell.value = cell.value.replace(/\D/g, "").slice(-1);
      if (cell.value && cells[i + 1]) cells[i + 1].focus();
      if (value().length === length) onComplete?.(value());
    });
    cell.addEventListener("keydown", e => { if (e.key === "Backspace" && !cell.value && cells[i - 1]) cells[i - 1].focus(); });
    cell.addEventListener("paste", e => {
      e.preventDefault();
      const text = (e.clipboardData?.getData("text") || "").replace(/\D/g, "").slice(0, length);
      text.split("").forEach((ch, j) => { if (cells[j]) cells[j].value = ch; });
      if (value().length === length) onComplete?.(value());
    });
    cells.push(cell);
    root.append(cell);
  }
  return root;
}
