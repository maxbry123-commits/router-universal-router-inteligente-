import test from "node:test";
import assert from "node:assert/strict";
import { fixture, settle } from "./dom-fixture.js";
import { ICON_META, V12_COLORS } from "../src/icons-v12.js";
import { openIconLibrary } from "../src/windows/icon-library.js";

test("54 unique V12 icon prototypes can be filtered, recolored and report clipboard failure", async () => {
  const { document, context } = fixture();
  assert.equal(ICON_META.length, 54);
  assert.equal(new Set(ICON_META.map(item => item.id)).size, 54);
  assert.equal(V12_COLORS.length, 6);
  openIconLibrary(context);
  assert.equal(document.querySelectorAll(".icon-cell").length, 54);
  const aiCount = ICON_META.filter(item => item.cat === "ai").length;
  document.querySelector('[data-cat="ai"]').click();
  assert.equal(document.querySelectorAll(".icon-cell").length, aiCount);
  document.querySelector('[data-color="blue"]').click();
  assert.equal(document.querySelector(".icon-cell svg").style.color, "#0647F4");
  document.querySelector(".icon-cell").click();
  await settle();
  assert.match(document.querySelector(".window-body [role='status']").textContent, /no permitió/);
});
