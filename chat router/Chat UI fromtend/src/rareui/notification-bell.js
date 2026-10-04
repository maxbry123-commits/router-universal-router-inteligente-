import { el, button } from "../dom.js";
// 14 notification-bell: campana con contador real de notificaciones entregadas al componente.
export function notificationBell({ count = 0, onOpen } = {}) {
  let n = count;
  const badge = el("span", { class: "rui-bell-badge", text: String(n), hidden: n === 0 });
  const b = button("🔔", () => { n = 0; badge.hidden = true; badge.textContent = "0"; onOpen?.(); }, "icon-btn rui-bell");
  b.append(badge);
  b.notify = () => { n++; badge.hidden = false; badge.textContent = String(n); };
  return b;
}
