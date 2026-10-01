"use client";

import { useConvexAuth, useQuery } from "convex/react";

import type { CrawlSiteResult } from "@getdesign/tools";
import type { DesignDoc, DesignTokens } from "@getdesign/types";

import type { RunState, RunStep, StoredVisual } from "@/lib/runs-store";
import { api } from "@convex/_generated/api";
import type { Id } from "@convex/_generated/dataModel";

export type RunArtifacts = {
  crawl: CrawlSiteResult | null;
  visual: StoredVisual | null;
  description: string | null;
  tokens: DesignTokens | null;
  doc: DesignDoc | null;
};

const SHOULD_FETCH_AFTER: Record<keyof RunArtifacts, RunStep> = {
  crawl: "crawl",
  visual: "capture",
  description: "describe",
  tokens: "extract",
  doc: "synthesize",
};

function shouldFetch(run: RunState, key: keyof RunArtifacts): boolean {
  const step = SHOULD_FETCH_AFTER[key];
  const status = run.steps[step];
  if (status === "ok") return true;
  if (status === "running") return true;
  return false;
}

export function useRunArtifacts(run: RunState, userId: string): RunArtifacts {
  const { isAuthenticated } = useConvexAuth();
  const convexArtifacts = useQuery(api.designRunArtifacts.getForRun, isAuthenticated ? {
    runId: run.id as Id<"designRuns">,
    userId,
  } : "skip") as (RunArtifacts & { markdown?: string | null }) | undefined;
  const tileUrls = useQuery(api.designRunArtifacts.getTileUrls, isAuthenticated ? {
    runId: run.id as Id<"designRuns">,
    userId,
  } : "skip");
  return selectRunArtifacts(run, convexArtifacts, tileUrls);
}

// Derive from the live query so artifacts arriving after their step completes
// remain visible, including after authentication or a run-page refresh.
export function selectRunArtifacts(
  run: RunState,
  values: Partial<RunArtifacts> | undefined,
  tileUrls?: Array<{ file: string; url: string }>,
): RunArtifacts {
  const artifacts: RunArtifacts = {
    crawl: shouldFetch(run, "crawl") ? values?.crawl ?? null : null,
    visual: shouldFetch(run, "visual") ? values?.visual ?? null : null,
    description: shouldFetch(run, "description") ? values?.description ?? null : null,
    tokens: shouldFetch(run, "tokens") ? values?.tokens ?? null : null,
    doc: shouldFetch(run, "doc") ? values?.doc ?? null : null,
  };

  if (artifacts.visual && tileUrls) {
    return {
      ...artifacts,
      visual: {
        ...artifacts.visual,
        tiles: artifacts.visual.tiles.map((tile) => ({
          ...tile,
          url: tileUrls.find((entry) => entry.file === tile.file)?.url ?? tile.url,
        })),
      },
    };
  }

  return artifacts;
}

export function tileUrl(visual: StoredVisual | null, index: number): string | null {
  return visual?.tiles[index]?.url ?? null;
}
