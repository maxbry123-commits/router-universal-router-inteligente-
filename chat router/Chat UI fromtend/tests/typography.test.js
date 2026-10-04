import test from "node:test";
import assert from "node:assert/strict";
import { fixture, settle } from "./dom-fixture.js";
import { TEXT_ROLES, TEXT_COLORS, defaultTypography, normalizeTypography } from "../src/typography/state.js";
import { applyTypography, exportTypographyCss } from "../src/typography/apply.js";
import { openTypography } from "../src/windows/typography.js";

test("typography editor edits each of 8 roles independently and applies real CSS", async () => {
  const { document, context } = fixture();
  assert.deepEqual(TEXT_ROLES, ["title", "subtitle", "body", "input", "placeholder", "output", "button", "meta"]);
  assert.equal(TEXT_COLORS.length, 10);
  openTypography(context);
  assert.equal(document.querySelectorAll(".typo-role-tabs .chip").length, 8);
  const size = [...document.querySelectorAll(".typo-controls input[type='number']")][0];
  size.value = "30";
  size.dispatchEvent(new window.Event("input", { bubbles: true }));
  const css = exportTypographyCss(normalizeTypography({ title: { size: 30 } }));
  assert.match(css, /font-size:30px/);
  assert.match(css, /textarea::placeholder/);
});

test("typography applies a style node with per-role selectors and survives reloads", () => {
  const { document } = fixture();
  const state = defaultTypography();
  state.meta.color = "#FF475F";
  applyTypography(state, document);
  const node = document.getElementById("yaiwes-typography");
  assert.ok(node);
  assert.match(node.textContent, /\.sub[^{]*\{[^}]*color:#FF475F/);
  const bad = normalizeTypography({ title: { size: 999, color: "red", weight: 1, font: "evil" } });
  assert.equal(bad.title.size, 48);
  assert.equal(bad.title.color, "#EDEDED");
  assert.equal(bad.title.weight, 300);
  assert.equal(bad.title.font, "system");
});
