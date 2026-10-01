import { expect, test } from "bun:test";
import {
  artifactSiteName,
  filterRunPreviews,
  parseDesignMd,
  parseRunVisibilityFilter,
  runPageTitle,
} from "./design-run-preview";

test("run page title uses the design heading, then crawl name, then domain", () => {
  expect(
    runPageTitle({
      domain: "example.com",
      markdown: "# Mohtasham's Portfolio Design System\n",
    }),
  ).toBe("Mohtasham's Portfolio");
  expect(
    runPageTitle({
      domain: "example.com",
      crawlSiteName: "Example",
    }),
  ).toBe("Example");
  expect(runPageTitle({ domain: "example.com" })).toBe("example.com");
  expect(artifactSiteName({ siteName: " Linear " })).toBe("Linear");
});

test("parseDesignMd still exports from the dashboard helper", () => {
  expect(
    parseDesignMd("# Linear Design System\n\n## 1. Visual Theme & Atmosphere\n\nClean.\n\n`#3366FF`"),
  ).toEqual({
    title: "Linear",
    theme: "Clean.",
    accent: "#3366FF",
  });
});

test("run visibility filters ignore unknown values and keep public or private rows", () => {
  expect(parseRunVisibilityFilter()).toBe("all");
  expect(parseRunVisibilityFilter("nope")).toBe("all");
  expect(parseRunVisibilityFilter("public")).toBe("public");
  const runs = [
    { slug: "open", visibility: "public" as const },
    { slug: "mine", visibility: "private" as const },
  ];
  expect(filterRunPreviews(runs, "all").map((run) => run.slug)).toEqual(["open", "mine"]);
  expect(filterRunPreviews(runs, "public").map((run) => run.slug)).toEqual(["open"]);
  expect(filterRunPreviews(runs, "private").map((run) => run.slug)).toEqual(["mine"]);
});
