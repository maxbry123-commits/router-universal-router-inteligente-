import type { Metadata } from "next";
import Link from "next/link";
import { notFound, redirect } from "next/navigation";
import { withAuth } from "@workos-inc/authkit-nextjs";
import { DesignDocument } from "@/components/design-document";
import { loadCachedSite, formatCaptureDate } from "@/lib/cached-sites";
import { ScreenshotGallery } from "../../runs/[slug]/gallery-panel";
import { ExportActions } from "../../runs/[slug]/export-actions";

export const metadata: Metadata = { title: "Cached design example" };

export default async function CachedSitePage({ params }: {
  params: Promise<{ slug: string }>;
}) {
  const { user, accessToken } = await withAuth();
  if (!user || !accessToken) redirect("/sign-in");
  const { slug } = await params;
  const site = await loadCachedSite(slug, accessToken);
  if (!site) notFound();

  return (
    <div className="flex min-h-svh flex-1 items-stretch">
      <div className="flex min-w-0 flex-1 flex-col">
      <header className="flex min-h-14 flex-wrap items-center gap-3 border-b px-4 py-3">
        <nav aria-label="Breadcrumb" className="flex min-w-0 items-center gap-2 text-sm">
          <Link href="/sites" className="text-muted-foreground hover:text-foreground">Examples</Link>
          <span aria-hidden="true" className="text-muted-foreground">/</span>
          <span className="truncate">{site.title}</span>
        </nav>
        <div className="ml-auto"><ExportActions content={site.markdown} siteName={site.title} /></div>
      </header>
      <div className="flex flex-wrap items-center justify-between gap-4 border-b bg-muted/20 px-6 py-4">
        <div className="min-w-0 text-xs text-muted-foreground">
          <p>Cached snapshot · <time dateTime={site.capturedAt}>{formatCaptureDate(site.capturedAt)}</time></p>
          <a href={site.url} target="_blank" rel="noreferrer" className="mt-1 inline-block underline underline-offset-4">{new URL(site.url).hostname}</a>
        </div>
        <div className="text-left sm:text-right">
          <Link href={`/agent?refresh=${site.slug}`} className="inline-flex min-h-9 items-center rounded-md border bg-background px-3 text-xs font-medium hover:bg-muted focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-ring">Refresh site</Link>
          <p className="mt-1 text-xs text-muted-foreground">Starts a new run with your provider keys.</p>
        </div>
      </div>
      <DesignDocument content={site.markdown} imagesInGallery />
      </div>
      <ScreenshotGallery runId={`cached-${site.slug}`} tiles={site.images.map(image => ({ file: image.url, url: image.url, width: image.width, height: image.height, label: image.url.endsWith("-hero.webp") ? "Hero viewport" : "Full page" }))} totalExpected={site.images.length} />
    </div>
  );
}
