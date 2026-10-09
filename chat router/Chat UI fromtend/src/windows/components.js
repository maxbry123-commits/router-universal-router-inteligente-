import { el, openWindow } from "../dom.js";
import { t } from "../i18n.js";
import { rareFolder, bounceSidebar, hookSidebar, familyDrawer, proximitySidebar,
  durationPicker, fluidOrb, scrollProgress, codeBlock, otpInput, gravityLetters,
  githubActivity, emojiReaction, notificationBell, stepPlayer, gridReveal,
  gooeyNav, deleteButton, animatedCounter, matrixOrb, taskList, voiceNote } from "../rareui/index.js";

// Catálogo vivo de los 22 componentes Rare UI portados desde la skill Maxbry.
// Los componentes son interacciones reales; los que consumen datos arrancan vacíos
// o con el estado local de la sesión, nunca con datos falsos.
export function openComponents(context) {
  const host = el("div", { class: "rui-catalog" });
  const mount = (name, node) => host.append(
    el("div", { class: "rui-demo", "data-component": name },
      el("p", { class: "muted", text: name }), node));

  mount("folder-component", rareFolder({ label: "Archivos", items: [] }));
  const bounce = bounceSidebar({ items: ["A", "B", "C"] });
  mount("bounce-sidebar", el("div", {},
    el("button", { type: "button", text: "toggle", onClick: () => bounce.classList.contains("open") ? bounce.close() : bounce.open() }), bounce));
  mount("hook-sidebar", hookSidebar({ items: ["A", "B"] }));
  mount("family-drawer", familyDrawer({ groups: [{ label: "Grupo", children: [{ label: "Opción" }] }] }));
  mount("proximity-sidebar", proximitySidebar({ items: [{ label: "1" }, { label: "2" }, { label: "3" }] }));
  mount("duration-picker", durationPicker({}));
  mount("fluid-orb", fluidOrb());
  const scrollBox = el("div", { class: "rui-scroll-box" },
    ...Array.from({ length: 20 }, (_, i) => el("p", { text: "línea " + (i + 1) })));
  mount("scroll-progress", el("div", {}, scrollProgress(scrollBox), scrollBox));
  mount("code-block", codeBlock({ code: "echo yaiwes", lang: "sh" }));
  mount("otp-input", otpInput({ length: 6 }));
  mount("gravity-letters", gravityLetters({ text: "YAIWES" }));
  mount("github-activity", githubActivity({ data: {} }));
  mount("emoji-reaction", emojiReaction({}));
  mount("notification-bell", notificationBell({ count: 0 }));
  mount("step-player", stepPlayer({ steps: [] }));
  mount("grid-reveal", gridReveal({ items: [] }));
  mount("gooey-nav", gooeyNav({ items: [{ label: "Uno" }, { label: "Dos" }] }));
  mount("delete-button", deleteButton({ onDelete: () => {} }));
  mount("animated-counter", animatedCounter({ value: context.messages?.length || 0 }));
  mount("matrix-orb", matrixOrb({}));
  mount("task-list", taskList({ tasks: [] }));
  mount("voice-note", voiceNote({}));

  return openWindow(t(context, "components"), el("div", { class: "window-body" },
    el("p", { class: "muted", text: t(context, "componentsDesc") }), host),
    t(context, "closeWindow"));
}
