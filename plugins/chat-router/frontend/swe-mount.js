// swe-mount.js — monta los controles de SWE CODE free cerca del panel de selectores
// cuando el selector 'swe-code-free' se enciende. No toca Configuración.
import { mountSweCodeFree } from "./swe-code-free.js";

function ensureMount() {
  let host = document.getElementById("swe-host");
  if (host) return host;
  const panel = document.getElementById("selectores-panel");
  if (!panel) return null;
  host = document.createElement("div");
  host.id = "swe-host";
  host.style.marginTop = "8px";
  panel.insertAdjacentElement("afterend", host);
  return host;
}

function onSelector(e) {
  const act = (e && e.detail && e.detail.activo) || "";
  const host = ensureMount();
  if (!host) return;
  if (act === "swe-code-free") {
    host.hidden = false;
    if (!host.querySelector("#swe-code-free-sel")) {
      mountSweCodeFree(host, {
        tell: (t) => {
          try { if (window.RIU_CHAT && window.RIU_CHAT.avisa) window.RIU_CHAT.avisa(t); } catch {}
        },
      });
    }
  } else {
    host.hidden = true;
  }
}

if (document.readyState === "loading") {
  document.addEventListener("DOMContentLoaded", () => {
    window.addEventListener("riu:selector-activo", onSelector);
    if (window.RIU_SELECTORES && window.RIU_SELECTORES.activo === "swe-code-free") onSelector({ detail: { activo: "swe-code-free" } });
  });
} else {
  window.addEventListener("riu:selector-activo", onSelector);
  if (window.RIU_SELECTORES && window.RIU_SELECTORES.activo === "swe-code-free") onSelector({ detail: { activo: "swe-code-free" } });
}
