import test from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";

const read = path => readFileSync(new URL(path, import.meta.url), "utf8");

test("gris V07 is primary while the three older Maxbry themes remain intact", () => {
  const tokens = read("../styles/tokens.css");
  const css = read("../styles/chat.css");
  for (const hex of ["#1C1B1A", "#2A2927", "#F5F4F0", "#A8A29E", "#C65D3B", "#0a0a0d", "#141417", "#202025", "#2563eb", "#ff5500", "#f4f4f5", "#18181b", "#3f3f46"]) assert.ok(tokens.includes(hex));
  for (const hex of ["#1B1B1B", "#202020", "#252525", "#2A2A2A", "#3C3C3C", "#484848", "#3A3A3A", "#525252", "#FAFAFA", "#EDEDED", "#BFBFBF", "#A0A0A0"]) assert.ok(tokens.includes(hex));
  assert.deepEqual(Array.from(tokens.matchAll(/\[data-theme="([^"]+)"\]/g), match => match[1]), ["gris", "little", "matte", "blanco"]);
  assert.match(tokens, /--selection-fill: var\(--module-selected\)/);
  assert.match(css, /\.pending, #status\.pending/);
  assert.match(css, /\.progress, #status\.progress/);
  assert.doesNotMatch(css, /#[0-9a-f]{3,8}\b/i);
  assert.doesNotMatch(css, /var\(--orange\)/);
  assert.match(css, /\.primary \{[^}]*background: var\(--accent\)/);
  assert.match(css, /\.option\.selected \{[^}]*var\(--selection-border\)/);
  assert.match(css, /\.switch\[aria-checked="true"\][^}]*var\(--status-blue\)/);
});

test("mobile source has no horizontal control scroller and uses canonical geometry", () => {
  const css = read("../styles/chat.css");
  assert.doesNotMatch(css, /overflow-x:\s*auto|\.selector-row|\.toggle-row/);
  assert.match(css, /grid-template-rows: auto minmax\(0, 1fr\) auto/);
  assert.match(css, /\.composer \{[^}]*border-radius: 12px/);
  assert.match(css, /button \{[^}]*border-radius: 10px/);
  assert.match(css, /border-radius: 28px 28px 0 0/);
  assert.match(css, /border-radius: 24px/);
  assert.match(css, /\[hidden\] \{ display: none !important; \}/);
  assert.match(css, /prefers-reduced-motion/);
  assert.match(css, /#status \{[^}]*top:/);
  assert.doesNotMatch(read("../src/actions/record-voice.js"), /buttonNode\.textContent/);
});
