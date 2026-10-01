import { expect, test } from "bun:test";
import { runStepRejection } from "./run-step-policy";
import type { RunState } from "./runs-store";

const run: Pick<RunState, "steps" | "mode"> = {
  steps: { crawl: "ok", capture: "failed", extract: "ok", describe: "pending", synthesize: "pending", render: "pending" },
};

test("a direct downstream request cannot bypass failed capture or text-only consent", () => {
  for (const step of ["describe", "synthesize", "render"] as const) {
    expect(runStepRejection(run, step)).toContain("explicitly continue");
    expect(runStepRejection({ ...run, mode: "text_only" }, step)).toContain("explicitly continue");
  }
});

test("explicit text-only continuation permits synthesis only after tokens are ready", () => {
  const continued = { mode: "text_only" as const, steps: { ...run.steps, capture: "skipped" as const, describe: "skipped" as const } };
  expect(runStepRejection(continued, "synthesize")).toBeNull();
  expect(runStepRejection({ ...continued, steps: { ...continued.steps, extract: "running" } }, "synthesize")).toContain("token extraction");
  expect(runStepRejection(continued, "render")).toContain("synthesis");
});

test("duplicate step requests are rejected while the step is running", () => {
  expect(runStepRejection({ steps: { ...run.steps, capture: "running" } }, "capture")).toContain("already running");
});
