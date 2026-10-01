"use client";

import { useCallback, useState, type ReactNode } from "react";
import { LayoutGroup } from "motion/react";

import {
  Breadcrumb,
  BreadcrumbItem,
  BreadcrumbLink,
  BreadcrumbList,
  BreadcrumbPage,
  BreadcrumbSeparator,
} from "@/components/ui/breadcrumb";
import type { RunState } from "@/lib/runs-store";

import { ExportActions } from "./export-actions";
import { ShareRun } from "./share-run";
import { GalleryPanel } from "./gallery-panel";
import { RunProgress } from "./run-progress";
import type { LightboxTile } from "./tile-lightbox";

/**
 * Client wrapper for the run detail page. Owns the active-tile focus state
 * (so the describe stage can highlight a tile in the gallery panel) and
 * hosts the Motion `LayoutGroup` that lets capture-stage previews fly into
 * the gallery's slots via shared `layoutId`.
 *
 * Layout: a flex row where the left column is the page header + content,
 * and the right column is a sticky gallery panel.
 */
export function RunPageShell({
  runId,
  siteName,
  userId,
  isPublic = false,
  initialTiles,
  totalExpected,
  exportMarkdown,
  markdownContent,
  runState,
}: {
  runId: string;
  siteName: string;
  userId: string;
  isPublic?: boolean;
  initialTiles: LightboxTile[];
  totalExpected?: number;
  /** Markdown source string used by the export-actions toolbar. */
  exportMarkdown: string | null;
  /** Server-rendered markdown article for completed runs. */
  markdownContent: ReactNode | null;
  /** Run state for in-progress / failed runs. */
  runState: RunState | null;
}) {
  const [focusTileIndex, setFocusTileIndex] = useState<number>(-1);
  const handleActiveTileChange = useCallback((index: number) => {
    setFocusTileIndex(index);
  }, []);

  return (
    <LayoutGroup id={`run-${runId}`}>
      <div className="flex min-h-svh flex-1 items-stretch">
        <div className="flex min-w-0 flex-1 flex-col">
          <header className="flex min-h-14 shrink-0 flex-wrap items-center gap-3 border-b px-4 py-3">
            <Breadcrumb className="min-w-0">
              <BreadcrumbList>
                <BreadcrumbItem>
                  <BreadcrumbLink href="/runs">Runs</BreadcrumbLink>
                </BreadcrumbItem>
                <BreadcrumbSeparator />
                <BreadcrumbItem className="min-w-0 flex-1">
                  <BreadcrumbPage className="max-w-[min(16rem,50vw)] truncate sm:max-w-sm" title={siteName}>
                    {siteName}
                  </BreadcrumbPage>
                </BreadcrumbItem>
              </BreadcrumbList>
            </Breadcrumb>
            {exportMarkdown ? (
              <div className="ml-auto flex items-center gap-2">
                <ExportActions
                  content={exportMarkdown}
                  siteName={siteName}
                />
                <ShareRun runId={runId} isPublic={isPublic} />
              </div>
            ) : null}
          </header>

          {markdownContent
            ? markdownContent
            : runState
              ? (
                <RunProgress
                  initialRun={runState}
                  userId={userId}
                  onActiveTileChange={handleActiveTileChange}
                />
              )
              : null}
        </div>

        <GalleryPanel
          runId={runId}
          userId={userId}
          initialTiles={initialTiles}
          totalExpected={totalExpected}
          highlightIndex={focusTileIndex}
        />
      </div>
    </LayoutGroup>
  );
}
