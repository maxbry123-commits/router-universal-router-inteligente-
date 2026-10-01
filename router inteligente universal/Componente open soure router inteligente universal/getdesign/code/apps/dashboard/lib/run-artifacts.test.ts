import { expect, test } from "bun:test";
import { selectRunArtifacts } from "../app/(dashboard)/runs/[slug]/use-run-artifacts";
import type { RunState, StoredVisual } from "./runs-store";

const run: RunState = {
  id: "run", url: "https://example.test", userId: "owner", status: "running",
  createdAt: 1, updatedAt: 2,
  steps: { crawl: "ok", capture: "ok", describe: "running", extract: "ok", synthesize: "pending", render: "pending" },
};

test("artifacts arriving after completed step flags appear on the next query update", () => {
  expect(selectRunArtifacts(run, undefined).visual).toBeNull();
  const visual: StoredVisual = {
    status: "captured",
    tiles: [
      { file: "000.png", width: 1024, height: 768, format: "png" },
      { file: "001.png", width: 1024, height: 768, format: "png" },
    ],
  };
  const selected = selectRunArtifacts(run, { visual }, [{ file: "001.png", url: "https://tiles.example/second" }]);
  expect(selected.visual?.tiles[0]?.url).toBeUndefined();
  expect(selected.visual?.tiles[1]?.url).toBe("https://tiles.example/second");
  expect(selectRunArtifacts(run, { description: "First" }).description).toBe("First");
  expect(selectRunArtifacts(run, { description: "Updated" }).description).toBe("Updated");
});

test("pending steps and a different run do not retain previous artifacts", () => {
  const next = { ...run, id: "next", steps: { ...run.steps, describe: "pending" as const } };
  expect(selectRunArtifacts(next, { description: "Old" }).description).toBeNull();
  expect(selectRunArtifacts(next, undefined).visual).toBeNull();
});
