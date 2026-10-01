import { describe, expect, mock, test } from "bun:test";

import * as runs from "./designRuns";
import * as artifacts from "./designRunArtifacts";

process.env.WORKOS_CLIENT_ID ??= "client_test";

// Exercise registered handlers directly, with auth and database boundaries mocked.
const operations = [
  ["create", runs.create, { userId: "owner", url: "https://example.com" }],
  ["get", runs.get, { userId: "owner", id: "run" }],
  ["listRecent", runs.listRecent, { userId: "owner" }],
  ["listRecentPreviews", runs.listRecentPreviews, { userId: "owner" }],
  ["getPage", runs.getPage, { userId: "owner", id: "run" }],
  ["summarizeForUser", runs.summarizeForUser, { userId: "owner" }],
  ["markDeleted", runs.markDeleted, { userId: "owner", id: "run" }],
  ["beginStep", runs.beginStep, { userId: "owner", id: "run", step: "crawl", message: "Reading" }],
  ["finishStep", runs.finishStep, { userId: "owner", id: "run", step: "crawl", status: "ok", message: "Read" }],
  ["failStep", runs.failStep, { userId: "owner", id: "run", step: "crawl", message: "Failed" }],
  ["getForRun", artifacts.getForRun, { userId: "owner", runId: "run" }],
  ["getTileUrls", artifacts.getTileUrls, { userId: "owner", runId: "run" }],
  ["generateUploadUrl", artifacts.generateUploadUrl, { userId: "owner", runId: "run" }],
  ["upsertValue", artifacts.upsertValue, { userId: "owner", runId: "run", kind: "markdown", text: "private" }],
] as const;

function context(subject: string | null) {
  const row = { _id: "run", userId: "owner", status: "queued", updatedAt: 0, steps: {}, traceEvents: [] };
  const rows = {
    withIndex: () => rows,
    order: () => rows,
    take: async () => [row],
    collect: async () => [],
    unique: async () => null,
  };
  return {
    auth: { getUserIdentity: async () => subject ? { subject } : null },
    db: {
      get: mock(async () => row),
      query: mock(() => rows),
      insert: mock(async () => "new-run"),
      patch: mock(async () => {}),
    },
    storage: {
      generateUploadUrl: mock(async () => "https://upload.example"),
      getUrl: mock(async () => "https://storage.example/file"),
    },
  };
}

function invoke(operation: unknown, ctx: unknown, args: unknown) {
  return (operation as { _handler: (ctx: unknown, args: unknown) => Promise<unknown> })._handler(ctx, args);
}

describe("run and artifact ownership", () => {
  for (const [name, operation, args] of operations) {
    for (const subject of [null, "attacker"]) {
      test(`${name} rejects ${subject ?? "anonymous"} supplying the owner's ID before accessing data`, async () => {
        const ctx = context(subject);
        await expect(invoke(operation, ctx, args)).rejects.toThrow();
        for (const call of Object.values(ctx.db)) expect(call).not.toHaveBeenCalled();
        expect(ctx.storage.generateUploadUrl).not.toHaveBeenCalled();
        expect(ctx.storage.getUrl).not.toHaveBeenCalled();
      });
    }
    test(`${name} permits the authenticated owner`, async () => {
      await invoke(operation, context("owner"), args);
    });
  }

  test("a signed-in user cannot read another user's run using their own ID", async () => {
    expect(await invoke(runs.get, context("attacker"), { id: "run", userId: "attacker" })).toBeNull();
    expect(await invoke(runs.getPage, context("attacker"), { id: "run", userId: "attacker" })).toBeNull();
    await expect(invoke(artifacts.getForRun, context("attacker"), { runId: "run", userId: "attacker" })).rejects.toThrow("Run not found");
  });

  test("step claims are atomic so two tabs cannot start the same paid step", async () => {
    const ctx = context("owner");
    const row = await ctx.db.get();
    ctx.db.patch.mockImplementation(async (_id?: unknown, patch?: unknown) => {
      Object.assign(row, patch);
    });
    const args = { id: "run", userId: "owner", step: "capture", message: "Capturing" };
    expect(await invoke(runs.beginStep, ctx, args)).toBe(true);
    expect(await invoke(runs.beginStep, ctx, args)).toBe(false);
    expect(ctx.db.patch).toHaveBeenCalledTimes(1);
  });

  test("a fresh run can recover an interrupted owned run without changing its claim", async () => {
    const ctx = context("owner");
    const old = await ctx.db.get();
    old.status = "running";
    old.steps = { capture: "running" };
    expect(await invoke(runs.create, ctx, {
      userId: "owner", url: "https://example.com", rerunOf: "run",
    })).toBe("new-run");
    expect(ctx.db.patch).not.toHaveBeenCalled();
    expect(old.steps).toEqual({ capture: "running" });
    expect(ctx.db.insert.mock.calls[0]?.[1]).toMatchObject({
      userId: "owner", status: "queued", rerunOf: "run", steps: { capture: "pending" },
    });
  });

  test("recovery cannot reference another user's run", async () => {
    const ctx = context("attacker");
    await expect(invoke(runs.create, ctx, {
      userId: "attacker", url: "https://example.com", rerunOf: "run",
    })).rejects.toThrow("Run not found");
    expect(ctx.db.insert).not.toHaveBeenCalled();
  });
});


test("recovery rejects a live owned run before creating a second paid run", async () => {
  const ctx = context("owner");
  const original = await ctx.db.get();
  original.status = "running";
  original.steps = { capture: "running" };
  original.updatedAt = Date.now();
  await expect(invoke(runs.create, ctx, { userId: "owner", url: "https://example.com", rerunOf: "run" })).rejects.toThrow("still active");
  expect(ctx.db.insert).not.toHaveBeenCalled();
  expect(ctx.db.patch).not.toHaveBeenCalled();
});

test("summarizeForUser counts live owned runs and ignores deleted rows", async () => {
  const previous = process.env.WORKOS_CLIENT_ID;
  process.env.WORKOS_CLIENT_ID = "client_test";
  try {
    const ctx = context("owner");
    ctx.db.query = mock(() => ({
      withIndex: () => ({
        take: async () => [
          { status: "completed" },
          { status: "failed" },
          { status: "completed", deletedAt: 1 },
          { status: "running" },
          { status: "queued" },
        ],
      }),
    }));
    expect(await invoke(runs.summarizeForUser, ctx, { userId: "owner" })).toEqual({
      total: 4,
      completed: 1,
      failed: 1,
      active: 2,
    });
  } finally {
    if (previous === undefined) delete process.env.WORKOS_CLIENT_ID;
    else process.env.WORKOS_CLIENT_ID = previous;
  }
});

test("listRecentPreviews joins markdown and the first tile without loading every artifact", async () => {
  const ctx = context("owner");
  const live = [
    { _id: "done", userId: "owner", domain: "done.example", status: "completed", mode: "visual", visibility: "public" },
    { _id: "queued", userId: "owner", domain: "queued.example", status: "queued" },
    { _id: "gone", userId: "owner", domain: "gone.example", status: "completed", deletedAt: 1 },
    { _id: "empty", userId: "owner", domain: "empty.example", status: "completed", mode: "visual" },
  ];
  ctx.db.query = mock((table: string) => {
    if (table === "designRuns") {
      return {
        withIndex: () => ({
          order: () => ({
            take: async () => live,
          }),
        }),
      };
    }
    return {
      withIndex: (
        _name: string,
        fn: (q: { eq: (field: string, value: unknown) => unknown }) => void,
      ) => {
        const fields: Record<string, unknown> = {};
        const q = {
          eq(field: string, value: unknown) {
            fields[field] = value;
            return q;
          },
        };
        fn(q);
        return {
          unique: async () => {
            if (fields.kind === "markdown" && fields.runId === "done") {
              return {
                text: "# Done Design System\n\n## 1. Visual Theme & Atmosphere\n\nWarm.\n",
              };
            }
            if (fields.kind === "visual" && fields.runId === "done") {
              return {
                value: {
                  tiles: [{ storageId: "tile-1", file: "1.png", width: 10, height: 10 }],
                },
              };
            }
            return null;
          },
        };
      },
    };
  });

  expect(
    await invoke(runs.listRecentPreviews, ctx, {
      userId: "owner",
      limit: 12,
      requireDesignFile: true,
      displayLimit: 6,
    }),
  ).toEqual([
    {
      slug: "done",
      domain: "done.example",
      status: "completed",
      title: "Done",
      theme: "Warm.",
      accent: "#888888",
      image: "https://storage.example/file",
      textOnly: false,
      visibility: "public",
    },
  ]);
  expect(ctx.db.get).not.toHaveBeenCalled();
});

test("getPage loads artifacts and tiles together and returns null for a missing run", async () => {
  const missing = context("owner");
  missing.db.get = mock(async () => null);
  expect(await invoke(runs.getPage, missing, { id: "run", userId: "owner" })).toBeNull();

  const ctx = context("owner");
  expect(await invoke(runs.getPage, ctx, { id: "run", userId: "owner" })).toEqual({
    run: expect.objectContaining({ _id: "run" }),
    artifacts: {
      crawl: null,
      visual: null,
      description: null,
      tokens: null,
      doc: null,
      markdown: null,
    },
    tiles: [],
  });
});
