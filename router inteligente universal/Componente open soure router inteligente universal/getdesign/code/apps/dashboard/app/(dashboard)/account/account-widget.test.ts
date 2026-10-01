import { describe, expect, test } from "bun:test";
import { readFileSync } from "node:fs";

describe("account UserProfile widget", () => {
  test("sizes to the profile rows instead of filling the settings pane", () => {
    const css = readFileSync(new URL("../../globals.css", import.meta.url), "utf8");
    expect(css).toContain("#account .woswidgets-root .rt-Card");
    expect(css).toContain("padding: 0");
    expect(css).toContain("align-content: start");
  });
});
