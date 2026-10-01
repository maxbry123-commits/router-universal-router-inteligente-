export async function waitForStepGroup<Step>(
  steps: readonly Step[],
  runStep: (step: Step) => Promise<void>
): Promise<void> {
  const results = await Promise.allSettled(steps.map((step) => runStep(step)))
  const failure = results.find(
    (result): result is PromiseRejectedResult => result.status === "rejected"
  )
  if (failure) throw failure.reason
}


/** Join a step claimed by another tab without scheduling another paid request. */
export async function waitForRunningStep(
  step: import("./runs-store").RunStep,
  readRun: () => Promise<import("./runs-store").RunState | null>,
  pause: () => Promise<void> = () => new Promise(resolve => setTimeout(resolve, 1500)),
  now: () => number = Date.now,
): Promise<void> {
  const { runRecoveryState } = await import("../../../convex/designRunPolicy");
  while (true) {
    const run = await readRun();
    if (!run) throw new Error("Run not found.");
    const status = run.steps[step];
    if (status === "ok" || status === "skipped") return;
    if (status !== "running") throw new Error(typeof run.error === "string" ? run.error : run.error?.message ?? `${step} failed.`);
    if (runRecoveryState(run, now()) === "stalled") throw new Error("This run stopped reporting progress. You can start a new run.");
    await pause();
  }
}
