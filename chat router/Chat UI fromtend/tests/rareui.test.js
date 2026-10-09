import test from "node:test";
import assert from "node:assert/strict";
import { fixture, settle } from "./dom-fixture.js";
import * as rareui from "../src/rareui/index.js";
import { openComponents } from "../src/windows/components.js";

const NAMES = ["folder-component", "bounce-sidebar", "hook-sidebar", "family-drawer",
  "proximity-sidebar", "duration-picker", "fluid-orb", "scroll-progress", "code-block",
  "otp-input", "gravity-letters", "github-activity", "emoji-reaction", "notification-bell",
  "step-player", "grid-reveal", "gooey-nav", "delete-button", "animated-counter",
  "matrix-orb", "task-list", "voice-note"];

test("all 22 Rare UI components render in the catalog", async () => {
  const { document, context } = fixture();
  openComponents(context);
  await settle();
  const demos = document.querySelectorAll(".rui-demo");
  assert.equal(demos.length, 22);
  assert.deepEqual([...demos].map(d => d.dataset.component), NAMES);
});

test("component interactions are real, not placeholders", async () => {
  const { document } = fixture();
  const otp = rareui.otpInput({ length: 4 });
  document.body.append(otp);
  const cells = otp.querySelectorAll("input");
  for (const [i, c] of [...cells].entries()) {
    c.value = String(i + 1);
    c.dispatchEvent(new window.Event("input", { bubbles: true }));
  }
  let picked;
  const dur = rareui.durationPicker({ minutes: [5, 15, 30], onPick: v => { picked = v; } });
  const range = dur.querySelector("input");
  range.value = "2";
  range.dispatchEvent(new window.Event("input", { bubbles: true }));
  assert.equal(picked, 30);
  let deleted = false;
  const del = rareui.deleteButton({ onDelete: () => { deleted = true; } });
  del.click();
  assert.equal(deleted, false);
  del.click();
  await settle();
  assert.equal(deleted, true);
  const bell = rareui.notificationBell({ count: 0 });
  bell.notify();
  assert.equal(bell.querySelector(".rui-bell-badge").textContent, "1");
  bell.click();
  assert.equal(bell.querySelector(".rui-bell-badge").textContent, "0");
  const voice = rareui.voiceNote({});
  voice.querySelector("button").click();
  await settle();
  assert.match(voice.querySelector(".muted, .error").textContent, /VOICE_UNAVAILABLE/);
});
