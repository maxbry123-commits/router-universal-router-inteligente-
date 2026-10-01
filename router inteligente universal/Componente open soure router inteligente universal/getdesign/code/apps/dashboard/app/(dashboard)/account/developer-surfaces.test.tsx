import { describe, expect, test } from "bun:test";
import { renderToStaticMarkup } from "react-dom/server";
import { docsUrl } from "@getdesign/content";

import { DeveloperSurfaces } from "./developer-surfaces";

describe("Settings developer surfaces", () => {
  test("links API, CLI, SDK, and Skills to docs", () => {
    const html = renderToStaticMarkup(<DeveloperSurfaces />);
    expect(html).toContain("Developers");
    expect(html).toContain("There is no getdesign API key");
    for (const href of [
      docsUrl("/surfaces/api"),
      docsUrl("/surfaces/cli"),
      docsUrl("/surfaces/sdk"),
      docsUrl("/surfaces/skill"),
    ]) {
      expect(html).toContain(`href="${href}"`);
    }
  });
});
