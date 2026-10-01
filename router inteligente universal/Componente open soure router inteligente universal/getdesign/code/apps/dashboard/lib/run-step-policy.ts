import type { RunState, RunStep } from "./runs-store";

export function runStepRejection(run: Pick<RunState, "steps" | "mode">, step: RunStep): string | null {
  if (run.steps[step] === "running") return "This step is already running.";
  if (step === "crawl") return null;
  if (run.steps.crawl !== "ok") return "Wait for the site crawl to complete.";
  if (step === "capture" || step === "extract") return null;
  const visualReady = run.steps.capture === "ok";
  const textOnly = run.mode === "text_only" && run.steps.capture === "skipped";
  if (!visualReady && !textOnly) {
    return "Capture must succeed, or you must explicitly continue with text-only.";
  }
  if (step === "describe") return null;
  if (run.steps.extract !== "ok") return "Wait for token extraction to complete.";
  if (run.steps.describe !== "ok" && !(textOnly && run.steps.describe === "skipped")) {
    return "Wait for the visual description to complete.";
  }
  if (step === "render" && run.steps.synthesize !== "ok") {
    return "Wait for design synthesis to complete.";
  }
  return null;
}
