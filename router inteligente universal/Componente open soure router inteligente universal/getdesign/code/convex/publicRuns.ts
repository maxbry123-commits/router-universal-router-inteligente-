import { ConvexError, v } from "convex/values";
import { action, internalQuery, mutation, query, type QueryCtx } from "./_generated/server";
import { internal } from "./_generated/api";
import { requireWorkOsUserId } from "./workosAuth";

async function publishedRun(ctx: QueryCtx, id: string) {
  const runId = ctx.db.normalizeId("designRuns", id);
  if (!runId) return null;
  const run = await ctx.db.get(runId);
  return run && !run.deletedAt && run.status === "completed" && run.visibility === "public"
    ? run : null;
}

export const setVisibility = mutation({
  args: { id: v.id("designRuns"), visibility: v.union(v.literal("private"), v.literal("public")) },
  returns: v.null(),
  handler: async (ctx, { id, visibility }) => {
    const userId = await requireWorkOsUserId(ctx);
    const run = await ctx.db.get(id);
    if (!run || run.deletedAt || run.userId !== userId) throw new ConvexError("Run not found.");
    if (visibility === "public") {
      if (run.status !== "completed") throw new ConvexError("Only completed runs can be published.");
      const markdown = await ctx.db.query("designRunArtifacts")
        .withIndex("by_run_kind", q => q.eq("runId", id).eq("kind", "markdown")).unique();
      if (!markdown?.text?.trim()) throw new ConvexError("The design document is unavailable.");
    }
    await ctx.db.patch(id, {
      visibility,
      publishedAt: visibility === "public" ? (run.publishedAt ?? Date.now()) : undefined,
      updatedAt: Date.now(),
    });
    return null;
  },
});

/** Anonymous reads deliberately omit owner data, crawl payloads, traces and storage IDs. */
export const get = query({
  args: { id: v.string() },
  handler: async (ctx, { id }) => {
    const run = await publishedRun(ctx, id);
    if (!run) return null;
    const rows = await ctx.db.query("designRunArtifacts")
      .withIndex("by_run", q => q.eq("runId", run._id)).collect();
    const markdown = rows.find(row => row.kind === "markdown")?.text;
    if (!markdown?.trim()) return null;
    const visual = rows.find(row => row.kind === "visual")?.value;
    const tiles: { storageId?: string; width: number; height: number }[] =
      run.mode !== "text_only" && Array.isArray(visual?.tiles) ? visual.tiles : [];
    // Stored Markdown uses direct storage links. Public output uses checked image routes.
    const content = markdown.replace(/!\[Captured page tile \d+\]\([^\n]*\)/g, "").trim();
    return {
      id: String(run._id), url: run.url, domain: run.domain,
      mode: run.mode ?? "visual", completedAt: run.completedAt ?? null,
      publishedAt: run.publishedAt ?? null, markdown: content,
      doc: rows.find(row => row.kind === "doc")?.value ?? null,
      tokens: rows.find(row => row.kind === "tokens")?.value ?? null,
      visualDescription: rows.find(row => row.kind === "description")?.text ?? null,
      images: tiles.flatMap((tile, index) =>
        tile.storageId ? [{ index, width: tile.width, height: tile.height }] : []),
    };
  },
});

export const imageStorageId = internalQuery({
  args: { id: v.string(), index: v.number() },
  returns: v.union(v.id("_storage"), v.null()),
  handler: async (ctx, { id, index }) => {
    if (!Number.isSafeInteger(index) || index < 0) return null;
    const run = await publishedRun(ctx, id);
    if (!run || run.mode === "text_only") return null;
    const visual = await ctx.db.query("designRunArtifacts")
      .withIndex("by_run_kind", q => q.eq("runId", run._id).eq("kind", "visual")).unique();
    const storageId = visual?.value?.tiles?.[index]?.storageId;
    return typeof storageId === "string" ? ctx.db.system.normalizeId("_storage", storageId) : null;
  },
});

/** Return bytes, never permanent storage URLs, so unpublishing also closes image reads. */
export const image = action({
  args: { id: v.string(), index: v.number() },
  returns: v.union(v.object({ bytes: v.bytes(), contentType: v.string() }), v.null()),
  handler: async (ctx, args): Promise<{ bytes: ArrayBuffer; contentType: string } | null> => {
    const storageId = await ctx.runQuery(internal.publicRuns.imageStorageId, args);
    if (!storageId) return null;
    const blob = await ctx.storage.get(storageId);
    if (!blob || !["image/png", "image/webp", "image/jpeg"].includes(blob.type)) return null;
    return { bytes: await blob.arrayBuffer(), contentType: blob.type };
  },
});
