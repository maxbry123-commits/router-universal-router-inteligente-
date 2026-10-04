import test from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { execFileSync } from "node:child_process";
import { fileURLToPath } from "node:url";
import { runInNewContext } from "node:vm";
import { fixture } from "./dom-fixture.js";

const build = fileURLToPath(new URL("../scripts/build-review.mjs", import.meta.url));
execFileSync(process.execPath, [build]);
const html = readFileSync(new URL("../chat Yaiwes fromtend.revisar.html", import.meta.url), "utf8");

test("standalone review contains only the real bundled source, with no external modules or test fixtures", () => {
  assert.equal(Array.from(html.matchAll(/<style>/g)).length, 5);
  assert.equal(Array.from(html.matchAll(/<script>/g)).length, 1);
  assert.doesNotMatch(html, /<script[^>]*src=|<link[^>]*stylesheet|type="module"/);
  assert.doesNotMatch(html, /linkedom|Configured description|Purpose 11|Function 11/);
  assert.match(html, /ACTION_UNCONFIGURED/);
  assert.match(html, /BRIDGE_MISSING/);
  assert.match(html, /#C65D3B/);
});

test("standalone bundled JavaScript initializes chat and settings in a Node DOM even if storage is denied", () => {
  const { document, window } = fixture({}, undefined, html);
  const script = document.querySelector("script").textContent;
  const host = { document, window, location: { protocol: "file:" }, structuredClone, CustomEvent, console, setTimeout, clearTimeout };
  Object.defineProperty(host, "localStorage", { get() { throw new Error("STORAGE_BLOCKED"); } });
  runInNewContext(script, host, { timeout: 1000, filename: "chat-review-bundle.js" });
  assert.equal(document.documentElement.dataset.theme, "gris");
  assert.equal(document.querySelectorAll(".chat-panel button").length, 8);
  assert.equal(document.querySelector("#app > p[role='alert']"), null);
  document.querySelector('[data-control="configure"]').click();
  assert.ok(document.querySelector(".settings"));
  assert.equal(document.querySelectorAll("[data-theme-option]").length, 7);
});
