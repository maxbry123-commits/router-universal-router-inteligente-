import { describe, expect, mock, test } from "bun:test";
import * as publicRuns from "./publicRuns";

process.env.WORKOS_CLIENT_ID ??= "client_test";

function invoke(operation: unknown, ctx: unknown, args: unknown): Promise<any> {
  return (operation as { _handler: (ctx: unknown, args: unknown) => Promise<unknown> })._handler(ctx, args);
}

function fixture(subject: string | null = "owner") {
  const run: Record<string, any> = {
    _id: "run", userId: "owner", userEmail: "private@example.com", url: "https://example.com",
    domain: "example.com", status: "completed", mode: "visual", traceEvents: [{ secret: "trace" }],
  };
  const artifacts = [
    { kind: "markdown", text: "# Design\n\n![Captured page tile 1](https://private-storage/image)\n\n## Palette\nBlue" },
    { kind: "visual", value: { tiles: [{ storageId: "storage", width: 1024, height: 768 }], secret: "sandbox" } },
    { kind: "doc", value: { title: "Design" } },
    { kind: "tokens", value: { colors: ["#fff"] } },
    { kind: "description", text: "A blue page" },
    { kind: "crawl", value: { private: "raw crawl" }, storageId: "private-crawl" },
  ];
  const ctx = {
    auth: { getUserIdentity: async () => subject ? { subject } : null },
    db: {
      system: { normalizeId: (_table: string, id: string) => id === "storage" ? id : null },
      normalizeId: (_table: string, id: string) => ["run", "storage"].includes(id) ? id : null,
      get: mock(async () => run),
      patch: mock(async (_id: string, patch: object) => Object.assign(run, patch)),
      query: mock(() => {
        let kind: string | undefined;
        const filter = { eq: (field: string, value: string) => { if (field === "kind") kind = value; return filter; } };
        const query = {
          withIndex: (_index: string, cb: (q: typeof filter) => unknown) => { cb(filter); return query; },
          collect: async () => artifacts,
          unique: async () => artifacts.find(artifact => artifact.kind === kind) ?? null,
        };
        return query;
      }),
    },
    storage: { get: mock(async () => new Blob(["image bytes"], { type: "image/png" })) },
    runQuery: mock(async (_ref: unknown, args: unknown): Promise<any> => invoke(publicRuns.imageStorageId, ctx, args)),
  };
  return { ctx, run, artifacts };
}

describe("public runs", () => {
  test("existing and explicitly private runs reveal neither output nor images", async () => {
    const { ctx, run } = fixture(null);
    for (const visibility of [undefined, "private"]) {
      run.visibility = visibility;
      expect(await invoke(publicRuns.get, ctx, { id: "run" })).toBeNull();
      expect(await invoke(publicRuns.image, ctx, { id: "run", index: 0 })).toBeNull();
    }
    expect(ctx.db.query).not.toHaveBeenCalled();
    expect(ctx.storage.get).not.toHaveBeenCalled();
  });

  test("only the authenticated owner can publish or unpublish", async () => {
    for (const subject of [null, "attacker"]) {
      for (const visibility of ["public", "private"]) {
        const { ctx } = fixture(subject);
        await expect(invoke(publicRuns.setVisibility, ctx, { id: "run", visibility })).rejects.toThrow();
        expect(ctx.db.patch).not.toHaveBeenCalled();
      }
    }
  });

  test("publication requires a completed, undeleted run with a design document", async () => {
    for (const status of ["queued", "running", "failed"]) {
      const { ctx, run } = fixture();
      run.status = status;
      await expect(invoke(publicRuns.setVisibility, ctx, { id: "run", visibility: "public" })).rejects.toThrow("completed");
    }
    const { ctx, run, artifacts } = fixture();
    artifacts[0]!.text = " ";
    await expect(invoke(publicRuns.setVisibility, ctx, { id: "run", visibility: "public" })).rejects.toThrow("unavailable");
    run.deletedAt = 1;
    await expect(invoke(publicRuns.setVisibility, ctx, { id: "run", visibility: "public" })).rejects.toThrow("not found");
  });

  test("anonymous readers receive only the selected output fields", async () => {
    const { ctx, run } = fixture();
    await invoke(publicRuns.setVisibility, ctx, { id: "run", visibility: "public" });
    ctx.auth.getUserIdentity = async () => null;
    const result = await invoke(publicRuns.get, ctx, { id: "run" });
    expect(result.markdown).toContain("## Palette");
    expect(result.images).toEqual([{ index: 0, width: 1024, height: 768 }]);
    expect(result.doc).toEqual({ title: "Design" });
    const serialized = JSON.stringify(result);
    for (const secret of ["owner", "private@example", "trace", "sandbox", "private-storage", "storageId", "crawl"]) {
      expect(serialized).not.toContain(secret);
    }
    expect(run.visibility).toBe("public");
    const image = await invoke(publicRuns.image, ctx, { id: "run", index: 0 });
    expect(new TextDecoder().decode(image.bytes)).toBe("image bytes");
  });

  test("unpublishing, deletion and incomplete status revoke output and image access", async () => {
    for (const change of [{ visibility: "private" }, { deletedAt: 1 }, { status: "running" }]) {
      const { ctx, run } = fixture();
      await invoke(publicRuns.setVisibility, ctx, { id: "run", visibility: "public" });
      Object.assign(run, change);
      expect(await invoke(publicRuns.get, ctx, { id: "run" })).toBeNull();
      expect(await invoke(publicRuns.image, ctx, { id: "run", index: 0 })).toBeNull();
      expect(ctx.storage.get).not.toHaveBeenCalled();
    }
  });

  test("owner can unpublish and republish at the same run ID", async () => {
    const { ctx } = fixture();
    for (const visibility of ["public", "private", "public"]) {
      await invoke(publicRuns.setVisibility, ctx, { id: "run", visibility });
      const result = await invoke(publicRuns.get, ctx, { id: "run" });
      if (visibility === "private") expect(result).toBeNull();
      else expect(result.id).toBe("run");
    }
  });

  test("text-only runs have no image access even if old tiles exist", async () => {
    const { ctx, run } = fixture(null);
    Object.assign(run, { visibility: "public", mode: "text_only" });
    expect((await invoke(publicRuns.get, ctx, { id: "run" })).images).toEqual([]);
    expect(await invoke(publicRuns.image, ctx, { id: "run", index: 0 })).toBeNull();
  });

  test("invalid run IDs and image indices are ordinary misses", async () => {
    const { ctx, run } = fixture(null);
    run.visibility = "public";
    expect(await invoke(publicRuns.get, ctx, { id: "malformed" })).toBeNull();
    for (const index of [-1, 0.5, 1, Number.MAX_SAFE_INTEGER + 1]) {
      expect(await invoke(publicRuns.image, ctx, { id: "run", index })).toBeNull();
    }
    expect(ctx.storage.get).not.toHaveBeenCalled();
  });
});
