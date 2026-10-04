import { el } from "../dom.js";
// 11 gravity-letters: letras que caen con retardo; texto real dado por el llamador.
export function gravityLetters({ text = "" } = {}) {
  const root = el("span", { class: "rui-gravity", "aria-label": text });
  [...text].forEach((ch, i) => {
    const s = el("span", { text: ch === " " ? "\u00a0" : ch, "aria-hidden": "true" });
    s.style.animationDelay = (i * 40) + "ms";
    root.append(s);
  });
  return root;
}
