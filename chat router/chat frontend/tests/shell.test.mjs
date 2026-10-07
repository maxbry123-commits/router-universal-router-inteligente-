import assert from "node:assert/strict";
import test from "node:test";
import { readFileSync } from "node:fs";
import { runInNewContext } from "node:vm";

const source = readFileSync(new URL("../shell.js", import.meta.url), "utf8")
  .replace(/^import .*;\n/gm, "");

test("cada vista abre por URL, navega sin recarga y respeta volver", async () => {
  const routes = ["chat", "archivos", "seguimiento", "canvas", "connectors", "templates", "engineering"];
  const links = routes.map(view => ({
    dataset: { view }, href: `https://example.test/chat/ui/shell.html?view=${view}`,
    setAttribute(name, value) { this[name] = value; },
    removeAttribute(name) { delete this[name]; }
  }));
  const mounted = [];
  const listeners = {};
  const elements = {
    "#panel": { innerHTML: "" }, "#notice": { textContent: "" },
    "#connection": { textContent: "" }, "#view-title": { textContent: "" },
    "#connect": { addEventListener() {} },
    "#navigation": { addEventListener(type, fn) { listeners.navigation = fn; } },
    "#theme": { value: "", addEventListener() {} }
  };
  const location = { href: links[3].href };
  const window = {
    location,
    history: { pushState(_, __, url) { location.href = url; } },
    addEventListener(name, fn) { listeners[name] = fn; }
  };
  const document = {
    documentElement: { dataset: {} },
    querySelector(selector) { return elements[selector]; },
    querySelectorAll(selector) { assert.equal(selector, "[data-view]"); return links; }
  };
  const modules = Object.fromEntries(routes.map(view => [view, async (_, context) => {
    mounted.push(context.view);
  }]));
  const context = {
    window, document, URL, localStorage: { getItem: () => null, setItem() {} },
    fetch: async url => ({ ok: true, text: async () => `contenido ${url}` }),
    api: {}, chat: modules.chat, archivos: modules.archivos,
    seguimiento: modules.seguimiento, canvas: modules.canvas,
    organization: modules.connectors
  };
  runInNewContext(source, context);
  const flush = () => new Promise(resolve => setImmediate(resolve));
  await flush();
  assert.equal(mounted.at(-1), "canvas");
  assert.equal(elements["#view-title"].textContent, "Canvas");
  assert.equal(links[3]["aria-current"], "page");
  let prevented = false;
  listeners.navigation({
    target: { closest: () => links[1] }, button: 0,
    preventDefault() { prevented = true; }
  });
  await flush();
  assert.equal(prevented, true);
  assert.equal(window.location.href, links[1].href);
  assert.equal(mounted.at(-1), "archivos");
  assert.equal(links[3]["aria-current"], undefined);
  location.href = links[3].href;
  listeners.popstate();
  await flush();
  assert.equal(mounted.at(-1), "canvas");
});
