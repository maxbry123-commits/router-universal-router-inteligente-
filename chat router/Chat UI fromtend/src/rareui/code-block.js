import { el, button } from "../dom.js";
// 09 code-block: código con botón copiar real (portapapeles, error visible si el navegador lo niega).
export function codeBlock({ code = "", lang = "" } = {}) {
  const status = el("span", { class: "muted" });
  const pre = el("pre", { class: "rui-code" }, el("code", { text: code }));
  const copy = button("Copiar", async () => {
    try { await navigator.clipboard.writeText(code); status.textContent = "copiado"; }
    catch { status.textContent = "COPY_FAILED"; status.className = "error"; }
  }, "ghost");
  return el("div", { class: "rui-code-block" }, el("div", { class: "rui-code-head" },
    el("span", { class: "muted", text: lang }), copy, status), pre);
}
