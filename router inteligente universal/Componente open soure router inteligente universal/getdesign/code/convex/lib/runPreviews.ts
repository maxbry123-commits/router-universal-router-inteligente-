import type { Doc, Id } from "../_generated/dataModel";
import type { QueryCtx } from "../_generated/server";
import { parseDesignMd } from "./designMdPreview";

export type RunPreview = {
  slug: string;
  domain: string;
  status: Doc<"designRuns">["status"];
  title: string;
  theme: string;
  accent: string;
  image: string | null;
  textOnly: boolean;
  visibility: "public" | "private";
};

export type TileUrl = {
  file: string;
  width: number;
  height: number;
  url: string;
};

export async function loadArtifactsForRun(
  ctx: QueryCtx,
  runId: Id<"designRuns">,
) {
  const rows = await ctx.db
    .query("designRunArtifacts")
    .withIndex("by_run", (q) => q.eq("runId", runId))
    .collect();

  const artifacts: Record<string, unknown> = {
    crawl: null,
    visual: null,
    description: null,
    tokens: null,
    doc: null,
    markdown: null,
  };

  for (const row of rows) {
    const storageUrl = row.storageId
      ? await ctx.storage.getUrl(row.storageId)
      : null;
    if (row.kind === "description" || row.kind === "markdown") {
      artifacts[row.kind] = row.text ?? storageUrl ?? null;
    } else {
      artifacts[row.kind] =
        row.value && storageUrl
          ? { ...row.value, __storageUrl: storageUrl }
          : (row.value ?? (storageUrl ? { __storageUrl: storageUrl } : null));
    }
  }

  return artifacts;
}

export async function loadTileUrlsForRun(
  ctx: QueryCtx,
  runId: Id<"designRuns">,
): Promise<TileUrl[]> {
  const visual = await ctx.db
    .query("designRunArtifacts")
    .withIndex("by_run_kind", (q) =>
      q.eq("runId", runId).eq("kind", "visual"),
    )
    .unique();

  const tiles = visual?.value?.tiles;
  if (!Array.isArray(tiles)) return [];

  const withUrls = await Promise.all(
    tiles.map(async (tile) => {
      const storageId = tile.storageId;
      if (!storageId) return null;
      const url = await ctx.storage.getUrl(storageId);
      if (!url) return null;
      return {
        file: String(tile.file),
        width: Number(tile.width),
        height: Number(tile.height),
        url,
      };
    }),
  );

  return withUrls.filter((tile): tile is TileUrl => tile !== null);
}

function visibilityOf(run: Doc<"designRuns">): "public" | "private" {
  return run.visibility === "public" ? "public" : "private";
}

function fallbackPreview(run: Doc<"designRuns">): RunPreview {
  return {
    slug: String(run._id),
    domain: run.domain,
    status: run.status,
    title: run.domain,
    theme: "",
    accent: "#888888",
    image: null,
    textOnly: run.mode === "text_only",
    visibility: visibilityOf(run),
  };
}

async function markdownTextForRun(
  ctx: QueryCtx,
  runId: Id<"designRuns">,
): Promise<string | null> {
  const row = await ctx.db
    .query("designRunArtifacts")
    .withIndex("by_run_kind", (q) =>
      q.eq("runId", runId).eq("kind", "markdown"),
    )
    .unique();
  return typeof row?.text === "string" ? row.text : null;
}

async function firstTileUrlForRun(
  ctx: QueryCtx,
  runId: Id<"designRuns">,
): Promise<string | null> {
  const visual = await ctx.db
    .query("designRunArtifacts")
    .withIndex("by_run_kind", (q) =>
      q.eq("runId", runId).eq("kind", "visual"),
    )
    .unique();
  const tiles = visual?.value?.tiles;
  if (!Array.isArray(tiles) || tiles.length === 0) return null;
  const storageId = tiles[0]?.storageId;
  if (!storageId) return null;
  return await ctx.storage.getUrl(storageId);
}

async function previewForRun(
  ctx: QueryCtx,
  run: Doc<"designRuns">,
  requireDesignFile: boolean,
): Promise<RunPreview | null> {
  if (run.status !== "completed") {
    return requireDesignFile ? null : fallbackPreview(run);
  }

  const [markdown, image] = await Promise.all([
    markdownTextForRun(ctx, run._id),
    run.mode === "text_only"
      ? Promise.resolve(null)
      : firstTileUrlForRun(ctx, run._id),
  ]);
  if (!markdown) {
    return requireDesignFile ? null : fallbackPreview(run);
  }

  return {
    slug: String(run._id),
    domain: run.domain,
    status: run.status,
    image,
    textOnly: run.mode === "text_only",
    visibility: visibilityOf(run),
    ...parseDesignMd(markdown),
  };
}

export async function listRecentPreviewsForUser(
  ctx: QueryCtx,
  userId: string,
  args: {
    limit: number;
    requireDesignFile: boolean;
    displayLimit?: number;
  },
): Promise<RunPreview[]> {
  const rows = await ctx.db
    .query("designRuns")
    .withIndex("by_user_updated", (q) => q.eq("userId", userId))
    .order("desc")
    .take(args.limit);

  const mapped = await Promise.all(
    rows
      .filter((run) => !run.deletedAt)
      .map((run) => previewForRun(ctx, run, args.requireDesignFile)),
  );

  return mapped
    .filter((run): run is RunPreview => Boolean(run))
    .slice(0, args.displayLimit);
}
