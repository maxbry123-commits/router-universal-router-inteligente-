import { expect, test } from "bun:test"

import { waitForStepGroup } from "./run-pipeline"

test("waits for sibling steps before surfacing a group failure", async () => {
  let finishExtract!: () => void
  const extractFinished = new Promise<void>((resolve) => {
    finishExtract = resolve
  })
  const captureError = new Error("capture failed")

  let groupSettled = false
  const failure = waitForStepGroup(["capture", "extract"], async (step) => {
    if (step === "capture") throw captureError
    await extractFinished
  }).then(
    () => null,
    (error: unknown) => error
  )
  void failure.finally(() => {
    groupSettled = true
  })

  await Promise.resolve()
  await Promise.resolve()
  expect(groupSettled).toBe(false)

  finishExtract()
  expect(await failure).toBe(captureError)
  expect(groupSettled).toBe(true)
})


test("joining another tab's capture waits for completion without restarting it", async () => {
  const { waitForRunningStep } = await import("./run-pipeline");
  const run = { steps: { capture: "running" }, updatedAt: 100 } as import("./runs-store").RunState;
  let reads = 0, waits = 0;
  await waitForRunningStep("capture", async () => { reads++; return run; }, async () => { waits++; run.steps.capture = "ok"; }, () => 101);
  expect(reads).toBe(2);
  expect(waits).toBe(1);
});

test("joining a failed or interrupted capture reports failure instead of creating a new run", async () => {
  const { waitForRunningStep } = await import("./run-pipeline");
  const { RUN_STALL_TIMEOUT_MS, runRecoveryState } = await import("../../../convex/designRunPolicy");
  const run = { steps: { capture: "running" }, updatedAt: 100 } as import("./runs-store").RunState;
  expect(runRecoveryState(run, 101)).toBe("active");
  expect(runRecoveryState(run, 100 + RUN_STALL_TIMEOUT_MS)).toBe("stalled");
  await expect(waitForRunningStep("capture", async () => run, async () => {}, () => 100 + RUN_STALL_TIMEOUT_MS)).rejects.toThrow("stopped reporting progress");
  run.steps.capture = "failed";
  run.error = { message: "Capture failed" };
  await expect(waitForRunningStep("capture", async () => run)).rejects.toThrow("Capture failed");
  expect(runRecoveryState(run)).toBe("idle");
});
