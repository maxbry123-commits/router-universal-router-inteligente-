import { ConvexError, v } from "convex/values";

import { mutation, query, type QueryCtx } from "./_generated/server";
import type { Id } from "./_generated/dataModel";
import { requireMatchingWorkOsUserId } from "./workosAuth";
import {
  loadArtifactsForRun,
  loadTileUrlsForRun,
} from "./lib/runPreviews";

const artifactKindSchema = v.union(
  v.literal("crawl"),
  v.literal("visual"),
  v.literal("description"),
  v.literal("tokens"),
  v.literal("doc"),
  v.literal("markdown"),
);

async function assertOwnedRun(ctx: QueryCtx, runId: Id<"designRuns">, userId: string) {
  await requireMatchingWorkOsUserId(ctx, userId);
  const run = await ctx.db.get(runId);
  if (!run || run.userId !== userId || run.deletedAt) {
    throw new ConvexError({
      code: "NOT_FOUND",
      message: "Run not found.",
    });
  }
  return run;
}

export const getForRun = query({
  args: {
    runId: v.id("designRuns"),
    userId: v.string(),
  },
  returns: v.any(),
  handler: async (ctx, args) => {
    await assertOwnedRun(ctx, args.runId, args.userId);
    return await loadArtifactsForRun(ctx, args.runId);
  },
});

export const getTileUrls = query({
  args: {
    runId: v.id("designRuns"),
    userId: v.string(),
  },
  returns: v.array(
    v.object({
      file: v.string(),
      width: v.number(),
      height: v.number(),
      url: v.string(),
    }),
  ),
  handler: async (ctx, args) => {
    await assertOwnedRun(ctx, args.runId, args.userId);
    return await loadTileUrlsForRun(ctx, args.runId);
  },
});

export const generateUploadUrl = mutation({
  args: {
    runId: v.id("designRuns"),
    userId: v.string(),
  },
  returns: v.string(),
  handler: async (ctx, args) => {
    await assertOwnedRun(ctx, args.runId, args.userId);
    return await ctx.storage.generateUploadUrl();
  },
});

export const upsertValue = mutation({
  args: {
    runId: v.id("designRuns"),
    userId: v.string(),
    kind: artifactKindSchema,
    value: v.optional(v.any()),
    text: v.optional(v.string()),
    storageId: v.optional(v.id("_storage")),
    contentType: v.optional(v.string()),
  },
  returns: v.null(),
  handler: async (ctx, args) => {
    await assertOwnedRun(ctx, args.runId, args.userId);
    const now = Date.now();
    const existing = await ctx.db
      .query("designRunArtifacts")
      .withIndex("by_run_kind", (q) =>
        q.eq("runId", args.runId).eq("kind", args.kind),
      )
      .unique();

    const patch: {
      value?: unknown;
      text?: string;
      storageId?: typeof args.storageId;
      contentType?: string;
      updatedAt: number;
    } = { updatedAt: now };
    if (args.value !== undefined) patch.value = args.value;
    if (args.text !== undefined) patch.text = args.text;
    if (args.storageId !== undefined) patch.storageId = args.storageId;
    if (args.contentType !== undefined) patch.contentType = args.contentType;

    if (existing) {
      await ctx.db.patch(existing._id, patch);
      return null;
    }

    await ctx.db.insert("designRunArtifacts", {
      runId: args.runId,
      kind: args.kind,
      ...patch,
      createdAt: now,
    });
    return null;
  },
});
