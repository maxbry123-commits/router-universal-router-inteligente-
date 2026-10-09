import { el } from "../dom.js";
// 06 duration-picker: selector de duración con valores reales devueltos al callback.
export function durationPicker({ minutes = [5, 15, 30, 60], onPick } = {}) {
  const out = el("output", { class: "rui-duration-out", text: String(minutes[0]) + " min" });
  const input = el("input", { type: "range", min: "0", max: String(minutes.length - 1), step: "1", value: "0" });
  input.addEventListener("input", () => {
    const value = minutes[Number(input.value)];
    out.textContent = value + " min";
    onPick?.(value);
  });
  return el("div", { class: "rui-duration" }, input, out);
}
