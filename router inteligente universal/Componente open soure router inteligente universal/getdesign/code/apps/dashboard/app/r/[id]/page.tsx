import type { Metadata } from "next";
import { cache } from "react";
import { notFound } from "next/navigation";
import { DesignDocument } from "@/components/design-document";
import { loadPublicRun } from "@/lib/public-runs";
import { artifactSiteName, runPageTitle } from "@/lib/design-run-preview";
import { ExportActions } from "@/app/(dashboard)/runs/[slug]/export-actions";
import { ScreenshotGallery } from "@/app/(dashboard)/runs/[slug]/gallery-panel";

export const dynamic = "force-dynamic";
// Deduplicate the anonymous lookup within a render, without caching across requests.
const getPublicRun = cache(loadPublicRun);

export async function generateMetadata({ params }: { params: Promise<{ id: string }> }): Promise<Metadata> {
  const { id } = await params;
  const run = await getPublicRun(id);
  if (!run) notFound();
  const siteName = runPageTitle({
    domain: run.domain, url: run.url, markdown: run.markdown, docSiteName: artifactSiteName(run.doc),
  });
  const title = siteName;
  const description = `View ${siteName} on getdesign. Download the published design document${run.images.length > 0 ? " and screenshots" : ""}.`;
  const url = `https://dashboard.getdesign.app/r/${encodeURIComponent(run.id)}`;
  return {
    title,
    description,
    robots: { index: false, follow: false },
    alternates: { canonical: url },
    openGraph: { title: `${title} · getdesign`, description, url, siteName: "getdesign", type: "website" },
    twitter: { card: "summary", title: `${title} · getdesign`, description },
  };
}

export default async function PublicRunPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  const run = await getPublicRun(id);
  if (!run) notFound();
  const siteName = runPageTitle({
    domain: run.domain, url: run.url, markdown: run.markdown, docSiteName: artifactSiteName(run.doc),
  });

  return (
    <main className="flex min-h-svh items-stretch">
      <div className="flex min-w-0 flex-1 flex-col">
        <header className="flex flex-wrap items-center gap-3 border-b px-4 py-3">
          <a href="https://www.getdesign.app" className="text-sm font-semibold">getdesign</a>
          <span className="min-w-0 truncate text-sm text-muted-foreground" title={siteName}>{siteName}</span>
          <ExportActions content={run.markdown} siteName={siteName} />
        </header>
        <div className="flex flex-wrap items-center justify-between gap-3 border-b bg-muted/20 px-6 py-4 text-xs text-muted-foreground">
          <p>Public design · {run.mode === "text_only" ? "Text-only" : "Includes screenshots"}. Viewing and downloading use no provider keys.</p>
          <nav aria-label="Download formats" className="flex gap-4">
            <a className="underline underline-offset-4" href={run.links.markdown}>Raw Markdown</a>
            <a className="underline underline-offset-4" href={run.links.json}>JSON</a>
          </nav>
        </div>
        <DesignDocument content={run.markdown} imagesInGallery={run.images.length > 0} />
      </div>
      {run.images.length > 0 ? <ScreenshotGallery
        runId={`public-${run.id}`}
        tiles={run.images.map(image => ({ ...image, file: image.url }))}
        totalExpected={run.images.length}
      /> : null}
    </main>
  );
}
