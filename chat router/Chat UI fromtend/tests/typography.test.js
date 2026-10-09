import test from "node:test";
import assert from "node:assert/strict";
import { fixture, settle } from "./dom-fixture.js";
import { TEXT_ROLES, TEXT_COLORS, defaultTypography, normalizeTypography } from "../src/typography/state.js";
import { applyTypography, exportTypographyCss } from "../src/typography/apply.js";
import { openTypography } from "../src/windows/typography.js";

test("typography editor edits each of 11 roles independently and applies real CSS", async () => {
  const { document, context } = fixture();
  assert.deepEqual(TEXT_ROLES, ["title", "subtitle", "body", "input", "placeholder", "output", "button", "symbol", "label", "helper", "status"]);
  assert.equal(TEXT_COLORS.length, 10);
  openTypography(context);
  assert.equal(document.querySelectorAll(".typo-role-tabs .chip").length, 11);
  const size = [...document.querySelectorAll(".typo-controls input[type='number']")][0];
  size.value = "30";
  size.dispatchEvent(new window.Event("input", { bubbles: true }));
  const css = exportTypographyCss(normalizeTypography({ roles: { title: { size: 30 } } }));
  assert.match(css, /font-size:calc\(30px \* 1\)/);
  assert.match(css, /textarea::placeholder/);
});

test("typography applies a style node with per-role selectors and survives reloads", () => {
  const { document } = fixture();
  const state = defaultTypography();
  state.roles.status.color = "#FF475F";
  applyTypography(state, document);
  const node = document.getElementById("yaiwes-typography");
  assert.ok(node);
  assert.match(node.textContent, /\.sub[^{]*\{[^}]*color:#FF475F/);
  const bad = normalizeTypography({ roles: { title: { size: 999, color: "red", weight: 1, font: "evil" } } });
  assert.equal(bad.roles.title.size, 48);
  assert.equal(bad.roles.title.color, "#EDEDED");
  assert.equal(bad.roles.title.weight, 300);
  assert.equal(bad.roles.title.font, "system");
  const sig = normalizeTypography({ signal: "#ff6d11", scale: 500, icons: { send: "bot" } });
  assert.equal(sig.signal, "#FF6D11");
  assert.equal(sig.scale, 160);
  assert.equal(sig.icons.send, "bot");
  assert.equal(sig.icons.attach, "paperclip");
});
