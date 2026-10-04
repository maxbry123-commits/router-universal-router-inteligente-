import { button, el, openWindow } from "../dom.js";
import { controlLabel, slotLabel, t } from "../i18n.js";

export function openControls(context) {
  const body = el("div", { class: "window-body" });
  for (const slot of context.config.toggles) {
    const state = el("span", { class: "sub", text: t(context, context.selection.toggles[slot.id] ? "on" : "off") });
    const node = button("", async () => {
      const enabled = !context.selection.toggles[slot.id];
      node.disabled = true;
      node.setAttribute("aria-busy", "true");
      context.notice(t(context, "backendLoading"), false, true);
      try {
        await context.execute(slot.actionId, { controlId: slot.id, enabled });
        context.selection.toggles[slot.id] = enabled;
        node.setAttribute("aria-checked", String(enabled));
        state.textContent = t(context, enabled ? "on" : "off");
        context.notice(t(context, "toggleConfirmed", { name: slotLabel(context, slot), state: state.textContent }));
      } catch (error) { context.notice(error.message, true); }
      finally { node.disabled = false; node.removeAttribute("aria-busy"); }
    }, "switch");
    node.setAttribute("role", "switch");
    node.setAttribute("aria-label", slotLabel(context, slot));
    node.setAttribute("aria-checked", String(!!context.selection.toggles[slot.id]));
    node.append(el("span", { class: "switch-knob" }));
    body.append(el("div", { class: "toggle-card" },
      el("div", { class: "option-copy" }, el("span", { class: "name", text: slotLabel(context, slot) }),
        ...(slot.description ? [el("span", { class: "sub", text: slot.description })] : []), state), node));
  }
  return openWindow(controlLabel(context, "controls"), body, t(context, "closeWindow"));
}
