import { parseHTML } from "linkedom";
import { normalizeConfig } from "../src/config.js";
import { executeAction } from "../src/bridge.js";

export const settle = () => new Promise(resolve => setImmediate(resolve));

export function fixture(config = {}, execute, html = '<!doctype html><html><body><div id="app"></div><p id="status" role="status"></p></body></html>') {
  const { document, window } = parseHTML(html);
  const create = document.createElement.bind(document);
  document.createElement = (tag, ...args) => {
    const node = create(tag, ...args);
    if (tag === "dialog") {
      node.showModal = () => node.setAttribute("open", "");
      node.close = () => { node.removeAttribute("open"); node.dispatchEvent(new window.Event("close")); };
    } else if (tag === "select") {
      Object.defineProperty(node, "value", {
        get: () => node.querySelector("option[selected]")?.getAttribute("value") || node.querySelector("option")?.getAttribute("value") || "",
        set: value => { for (const option of node.children) option.toggleAttribute("selected", option.getAttribute("value") === value); },
      });
    }
    return node;
  };
  globalThis.document = document;
  globalThis.window = window;
  globalThis.location = { protocol: "file:" };
  const host = new EventTarget();
  if (execute) host.YAIWES_PLUGIN_BRIDGE = { execute };
  const notices = [];
  const context = {
    config: normalizeConfig(config), selection: { modelId: "", modeId: "mode-1", selectors: {}, toggles: {} },
    attachments: [], messages: [], draft: "", recorder: null, refreshes: 0,
    execute: (actionId, payload) => executeAction(actionId, payload, host),
    notice: (message, error) => notices.push({ message, error }),
    refresh() { this.refreshes++; }, showSettings() { this.settingsOpened = true; }, showChat() { this.chatOpened = true; },
    updateConfig(draft) { this.config = normalizeConfig(draft); return true; },
    setModels(models) { this.config = normalizeConfig({ ...this.config, models }); },
  };
  return { document, window, context, notices };
}
