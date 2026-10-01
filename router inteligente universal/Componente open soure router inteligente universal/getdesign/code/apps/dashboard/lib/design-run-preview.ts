import type { ConvexHttpClient } from "convex/browser";
import { api } from "@convex/_generated/api";
import { parseDesignMd } from "@convex/lib/designMdPreview";

export const OVERVIEW_RUN_QUERY_LIMIT = 12;
export const OVERVIEW_RUN_DISPLAY_LIMIT = 6;
export const RUNS_PAGE_QUERY_LIMIT = 48;

export type RunStatus = "queued" | "running" | "completed" | "failed";

export type ListedDesignRun = {
  _id: string;
  domain: string;
  status: RunStatus;
  mode?: "visual" | "text_only";
};

export type DesignRunPreview = {
  slug: string;
  domain: string;
  status: RunStatus;
  title: string;
  theme: string;
  accent: string;
  image: string | null;
  textOnly: boolean;
  visibility: "public" | "private";
};

export type RunVisibilityFilter = "all" | DesignRunPreview["visibility"];

export function parseRunVisibilityFilter(value?: string): RunVisibilityFilter {
  return value === "public" || value === "private" ? value : "all";
}

export function filterRunPreviews<T extends { visibility: DesignRunPreview["visibility"] }>(
  runs: T[],
  filter: RunVisibilityFilter,
) {
  if (filter === "all") return runs;
  return runs.filter((run) => run.visibility === filter);
}

export function artifactSiteName(value: unknown): string | undefined {
  if (!value || typeof value !== "object" || !("siteName" in value)) return undefined;
  const name = value.siteName;
  return typeof name === "string" && name.trim() ? name.trim() : undefined;
}

export function runPageTitle({
  domain,
  url,
  siteName,
  markdown,
  crawlSiteName,
  docSiteName,
}: {
  domain?: string;
  url?: string;
  siteName?: string;
  markdown?: string | null;
  crawlSiteName?: string;
  docSiteName?: string;
}): string {
  if (markdown) {
    const { title } = parseDesignMd(markdown);
    if (title && title !== "Unknown") return title;
  }
  const named = [docSiteName, crawlSiteName, siteName]
    .map((value) => value?.trim())
    .find(Boolean);
  if (named) return named;
  if (domain?.trim()) return domain.trim();
  if (url) {
    try {
      return new URL(url).hostname.replace(/^www\./, "");
    } catch {
      return url;
    }
  }
  return "Run";
}

export { parseDesignMd };

export function runStatusLabel(status: RunStatus) {
  switch (status) {
    case "queued":
      return "Queued";
    case "running":
      return "Running";
    case "completed":
      return "Completed";
    case "failed":
      return "Failed";
    default: {
      const _exhaustive: never = status;
      return _exhaustive;
    }
  }
}

export async function loadRecentRunPreviews(
  convex: ConvexHttpClient,
  userId: string,
  options: {
    queryLimit: number;
    requireDesignFile?: boolean;
    limit?: number;
  },
): Promise<DesignRunPreview[]> {
  return await convex.query(api.designRuns.listRecentPreviews, {
    userId,
    limit: options.queryLimit,
    ...(options.requireDesignFile ? { requireDesignFile: true } : {}),
    ...(options.limit !== undefined ? { displayLimit: options.limit } : {}),
  });
}
