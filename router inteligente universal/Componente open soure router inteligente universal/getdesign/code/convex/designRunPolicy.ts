export type TextOnlyResumeRun = {
  status: "queued" | "running" | "completed" | "failed";
  steps: Record<
    "crawl" | "capture" | "describe" | "extract" | "synthesize" | "render",
    "pending" | "running" | "ok" | "skipped" | "failed"
  >;
  traceEvents?: Array<Record<string, unknown>>;
};

export function textOnlyResumeRejection(run: TextOnlyResumeRun) {
  if (run.status === "completed") {
    return {
      code: "ALREADY_COMPLETED",
      message: "Run already completed.",
    } as const;
  }
  if (run.steps.capture === "ok") {
    return {
      code: "CAPTURE_ALREADY_OK",
      message: "Visual capture already succeeded.",
    } as const;
  }
  if (Object.values(run.steps).some((status) => status === "running")) {
    return {
      code: "STEP_RUNNING",
      message:
        "Wait for the active run steps to finish before continuing without screenshots.",
    } as const;
  }
  return null;
}

export function textOnlyResumePatch(run: TextOnlyResumeRun, now: number) {
  return {
    status: "running" as const,
    currentStep: "extract" as const,
    message: "Continuing without screenshots",
    mode: "text_only" as const,
    error: undefined,
    steps: { ...run.steps, capture: "skipped" as const },
    traceEvents: [
      ...(run.traceEvents ?? []),
      {
        step: "capture",
        status: "skipped",
        message: "Continuing without screenshots",
        at: now,
      },
    ],
    updatedAt: now,
  };
}

// Longer than the dashboard's 60-second request limit, with time for late writes.
export const RUN_STALL_TIMEOUT_MS = 5 * 60_000;

export function runRecoveryState(run: { steps: Record<string, string>; updatedAt: number }, now = Date.now()): "idle" | "active" | "stalled" {
  if (!Object.values(run.steps).includes("running")) return "idle";
  return now - run.updatedAt >= RUN_STALL_TIMEOUT_MS ? "stalled" : "active";
}
