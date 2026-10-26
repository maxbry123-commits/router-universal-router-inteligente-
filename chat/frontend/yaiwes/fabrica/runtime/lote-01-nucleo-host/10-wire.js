/* 10-wire.js
 * 1 función: cablear el lote 01 al host. Si mueves la carpeta, cambia solo BASE.
 *
 * HTML mínimo:
 * <link rel="stylesheet" href="./01-design-tokens.css">
 * <div id="yaiwes-host" class="yaiwes-host"></div>
 * <script type="module" src="./10-wire.js"></script>
 *
 * Clave por defecto del panel: YAIWES-CONFIG
 */

import { slots } from "./02-slot-registry.js";
import { actions } from "./03-action-bus.js";
import { manifests } from "./05-manifest-store.js";
import { accessKey } from "./06-access-key.js";
import { createWindow } from "./08-chrome-window.js";
import { paintManifest } from "./09-config-panel.js";

export const BASE = new URL(".", import.meta.url).href;

export async function wire(options) {
  const opts = options || {};
  const host = opts.host || document.getElementById("yaiwes-host") || document.body;

  await accessKey.ensureDefault();

  actions.register("fn.noop", async () => ({ ok: true }));
  actions.register("fn.open-config", async () => {
    let panel = document.querySelector("yaiwes-config-panel");
    if (!panel) {
      panel = document.createElement("yaiwes-config-panel");
      document.body.appendChild(panel);
    }
    panel.attachHost(host);
    panel.open();
    return { ok: true };
  });

  const home = createWindow(
    { id: "window.home", kind: "window", label: "YAIWES", slotId: "window.home.toolbar" },
    host
  );

  slots.scan(home.shadowRoot);

  const openCfg = {
    id: "fn.open-config",
    kind: "button",
    label: "Config",
    icon: "⚙",
    action: "fn.open-config",
    targetSlot: "window.home.toolbar",
    size: "regular"
  };
  const paintedCfg = paintManifest(openCfg, host);

  const replay = [];
  manifests.list().forEach((m) => {
    replay.push(paintManifest(m, host));
  });

  return {
    ok: paintedCfg.ok,
    base: BASE,
    slots: slots.list(),
    actions: actions.list(),
    replay
  };
}

if (typeof document !== "undefined") {
  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", () => wire());
  } else {
    wire();
  }
}
