import { beforeEach, expect, mock, test } from "bun:test";
import { getFunctionName } from "convex/server";

type Fixture = {
  normalizedUrl: string;
  status: string;
  mode?: string;
  startedAt?: number;
  error?: { step: string; message: string };
  steps: Record<string, string>;
};
let run: Fixture;
let failRender = false;
let missingImages = false;
let failFinalRead = false;
let denyStepClaim = false;
let savedMarkdown = false;
let reads = 0;
const query = mock(async (reference: Parameters<typeof getFunctionName>[0]) => {
  const name = getFunctionName(reference);
  if (name === "designRunArtifacts:getForRun")
    return {
      doc: {},
      crawl: { sourceUrl: "https://secret.test", stylesheets: [] },
    };
  if (name === "designRunArtifacts:getTileUrls") return missingImages ? [] : [{ url: "https://storage.test/tile.png" }];
  reads++;
  if (failFinalRead && reads > 1) throw new Error("read unavailable");
  return structuredClone(run);
});
const mutation = mock(
  async (
    reference: Parameters<typeof getFunctionName>[0],
    args: Record<string, any>,
  ) => {
    const name = getFunctionName(reference);
    if (name === "designRuns:beginStep") {
      if (denyStepClaim) return false;
      run.status = "running";
      run.startedAt ??= 123;
      run.steps[args.step] = "running";
    }
    if (name === "designRunArtifacts:upsertValue" && args.kind === "markdown")
      savedMarkdown = true;
    if (name === "designRuns:finishStep") {
      if (args.step === "render") expect(savedMarkdown).toBe(true);
      run.steps[args.step] = args.status;
      Object.assign(run, args.patch);
    }
    if (name === "designRuns:failStep") {
      run.status = "failed";
      run.error = { step: args.step, message: args.message };
      run.steps[args.step] = "failed";
    }
    return null;
  },
);
mock.module("@workos-inc/authkit-nextjs", () => ({
  withAuth: async () => ({
    user: { id: "user_01ARZ3NDEKTSV4RRFFQ69G5FAV" },
    accessToken: "fixture-auth",
  }),
}));
mock.module("@/lib/convex-server", () => ({
  getConvexClient: () => ({ query, mutation }),
}));
mock.module("@getdesign/agent", () => ({
  resolveModel: mock(),
  runCrawl: mock(),
  runDescribe: mock(),
  runExtractTokens: mock(),
  runSynthesize: mock(),
  runVisual: mock(),
}));
mock.module("@getdesign/tools/render", () => ({
  withDesignImages: (markdown: string) => markdown,
  renderDesignMd: () => {
    if (failRender)
      throw new Error("SECRET provider error https://secret.test");
    return "# PRIVATE generated markdown";
  },
}));
const { runStepHandler } = await import("../app/api/runs/[id]/_run-step");
const invoke = () =>
  runStepHandler("render")(
    new Request("http://localhost:3014/api/runs/fixture/render", {
      method: "POST",
    }),
    { params: Promise.resolve({ id: "fixture" }) },
  );

beforeEach(() => {
  run = {
    normalizedUrl: "https://secret.test",
    status: "running",
    startedAt: 123,
    steps: { crawl: "ok", capture: "ok", extract: "ok", describe: "ok", synthesize: "ok", render: "pending" },
  };
  failRender = false;
  missingImages = false;
  failFinalRead = false;
  denyStepClaim = false;
  savedMarkdown = false;
  reads = 0;
  query.mockClear();
  mutation.mockClear();
});

test("completion receipt exists only after markdown storage and final persistence", async () => {
  const response = await invoke();
  expect(response.status).toBe(200);
  const body = await response.json();
  expect(body.analytics).toEqual({
    started: false,
    completed: true,
    mode: "visual",
  });
  expect(JSON.stringify(body.analytics)).not.toMatch(
    /PRIVATE|secret.test|fixture-auth/,
  );
});

test("a lost step claim returns conflict without overwriting another request's run", async () => {
  denyStepClaim = true;
  const response = await invoke();
  expect(response.status).toBe(409);
  expect(run.status).toBe("running");
  expect(run.error).toBeUndefined();
  expect(savedMarkdown).toBe(false);
  expect(mutation.mock.calls.map(([reference]) => getFunctionName(reference))).toEqual(["designRuns:beginStep"]);
});

test("a direct render request cannot turn capture failure into unmarked text-only output", async () => {
  run.steps.capture = "failed";
  run.status = "failed";
  const response = await invoke();
  expect(response.status).toBe(409);
  expect(run.status).toBe("failed");
  expect(mutation).not.toHaveBeenCalled();
  expect(savedMarkdown).toBe(false);
});

test("first actual step transition acknowledges start; queued alone never does", async () => {
  run.status = "queued";
  delete run.startedAt;
  const response = await invoke();
  expect((await response.json()).analytics.started).toBe(true);
});

test("skipped/completed step requests produce no historical completion receipt", async () => {
  run.status = "completed";
  run.steps.render = "ok";
  expect(await (await invoke()).json()).toEqual({ ok: true, skipped: true });
  expect(mutation).not.toHaveBeenCalled();
});

test("persisted failure receipt has an allowlisted step, never the raw error", async () => {
  failRender = true;
  const response = await invoke();
  expect(response.status).toBe(500);
  const body = await response.json();
  expect(body.analytics).toEqual({
    started: false,
    completed: false,
    failedStep: "render",
    mode: "visual",
  });
  expect(JSON.stringify(body.analytics)).not.toMatch(/SECRET|secret.test/);
  expect(savedMarkdown).toBe(false);
});

test("analytics-only read failures do not change completed runs into failed runs", async () => {
  failFinalRead = true;
  const response = await invoke();
  expect(response.status).toBe(200);
  expect(run.status).toBe("completed");
  expect(await response.json()).toEqual({ ok: true });
});


test("missing stored images fail render, release its claim, and retry without recapturing", async () => {
  missingImages = true;
  expect((await invoke()).status).toBe(500);
  expect(run.steps.render).toBe("failed");
  expect(run.steps.capture).toBe("ok");
  expect(run.error?.step).toBe("render");
  expect(savedMarkdown).toBe(false);
  missingImages = false;
  expect((await invoke()).status).toBe(200);
  expect(run.steps.render).toBe("ok");
  expect(run.status).toBe("completed");
  expect(mutation.mock.calls.filter(([reference]) => getFunctionName(reference) === "designRuns:beginStep").map(([,args]) => args.step)).toEqual(["render", "render"]);
});
