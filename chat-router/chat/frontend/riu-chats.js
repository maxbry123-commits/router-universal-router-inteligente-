// riu-chats.js — cerrar un chat con confirmación (RUI 18) y contador de anclados (RUI 19). Dividido de chat-riu2.js sin cambiar la lógica.
import { crear, SVG } from "./riu-util.js";
// ---------- POR PANEL ----------
// RUI 18 delete-button: cerrar un chat con confirmacion (basura que abre la tapa -> Cerrar / Mantener). Tambien aria de pestañas.
export function cerrarChats({ root, q }) {
  const tabs = q("#chat-tabs"); if (!tabs) return;
  tabs.setAttribute("role", "tablist");
  let t = 0;
  const poner = () => {
    obs.disconnect();
    try {
      tabs.querySelectorAll(".chip-borrar,.chip-confirmar").forEach((x) => x.remove());
      const chips = [...tabs.querySelectorAll(".chip")].filter((c) => c.textContent.trim() !== "＋");
      chips.forEach((c, i) => {
        c.setAttribute("role", "tab"); c.setAttribute("aria-selected", String(c.classList.contains("on")));
        const b = crear("button", "chip-borrar"); b.type = "button"; b.title = "Borrar este chat"; b.setAttribute("aria-label", "Borrar " + c.textContent.replace("…", "").trim());
        b.innerHTML = SVG('<path d="M6 6l12 12M18 6L6 18"/>', 14);
        c.after(b);
        b.addEventListener("click", () => {
          const cf = crear("span", "chip-confirmar");
          const si = crear("button", "mini rojo", chips.length > 1 ? "Borrar" : "Vaciar"), no = crear("button", "mini", "Mantener");
          si.type = no.type = "button";
          si.addEventListener("click", () => { clearTimeout(t); root.dispatchEvent(new CustomEvent("riu:cerrar-chat", { detail: i })); });
          no.addEventListener("click", () => { clearTimeout(t); poner(); });
          obs.disconnect(); cf.append(si, no); b.replaceWith(cf); obs.observe(tabs, { childList: true });
          clearTimeout(t); t = setTimeout(() => { if (cf.isConnected) poner(); }, 4000);
        });
      });
    } finally { obs.observe(tabs, { childList: true }); }
  };
  let p = 0;
  const obs = new MutationObserver(() => { if (!p) p = requestAnimationFrame(() => { p = 0; poner(); }); });
  poner();
}

// RUI 19 animated-counter: cuantos anclados llevas, en el boton del ancla
export function contadorAncla({ q }) {
  const b = q("#btn-ancla"); if (!b || b.querySelector(".riu-contador")) return;
  const n = crear("span", "riu-contador"); n.hidden = true; b.append(n); b.classList.add("con-contador");
  const act = () => {
    const v = Number(b.dataset.n || 0);
    if (!n.hidden && n.textContent === String(v)) return;
    n.hidden = v < 1; n.textContent = String(v); n.classList.remove("sube"); void n.offsetWidth; n.classList.add("sube");
  };
  new MutationObserver(act).observe(b, { attributes: true, attributeFilter: ["data-n"] }); act();
}
