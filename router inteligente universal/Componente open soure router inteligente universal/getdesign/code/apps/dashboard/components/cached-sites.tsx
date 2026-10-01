import Link from "next/link";
import { hasCachedSiteImages } from "@convex/lib/cachedSiteSchema";
import { formatCaptureDate } from "@/lib/cached-sites";

export function CachedSites({
  sites,
  previewCount,
}: {
  sites: import("@/lib/cached-site-schema").CachedSiteSummary[]
  previewCount?: number
}) {
  const catalog = sites.filter(hasCachedSiteImages);
  if (catalog.length === 0) return null;
  const shown =
    previewCount === undefined ? catalog : catalog.slice(0, previewCount);

  return (
    <section aria-labelledby="cached-sites-title" className="min-w-0">
      <div className="mb-4 flex flex-wrap items-end justify-between gap-3">
        <div>
          <h2 id="cached-sites-title" className="text-sm font-medium">Examples</h2>
          <p className="mt-1 text-xs text-muted-foreground">
            Cached design systems from public sites. Open or download without running an extraction.
          </p>
        </div>
        {previewCount === undefined ? (
          <span className="text-xs text-muted-foreground">{catalog.length} available</span>
        ) : (
          <Link
            href="/sites"
            className="text-xs font-medium text-foreground underline-offset-4 hover:underline"
          >
            Browse all examples
          </Link>
        )}
      </div>
      <div className={`grid min-w-0 grid-cols-1 gap-3 sm:grid-cols-2 ${previewCount === undefined ? "xl:grid-cols-3" : "xl:grid-cols-4"}`}>
        {shown.map(site => (
          <Link
            key={site.slug}
            href={`/sites/${site.slug}`}
            className="group flex min-w-0 flex-col overflow-hidden rounded-xl border transition-colors hover:border-foreground/25 hover:bg-muted/20 focus-visible:outline-2 focus-visible:outline-offset-4 focus-visible:outline-ring"
          >
            <img src={site.images[0]!.url} alt={`${site.title} website screenshot`} width={site.images[0]!.width} height={site.images[0]!.height} loading="lazy" className="aspect-[16/10] w-full border-b object-cover object-top" />
            <div className="flex h-2 border-b" aria-label={`${site.title} color palette`}>
              {site.colors.map(color => (
                <span key={color} className="min-w-0 flex-1" style={{ backgroundColor: color }} title={color} />
              ))}
            </div>
            <div className="flex flex-1 flex-col p-4">
              <div className="flex items-baseline justify-between gap-3">
                <h3 className="truncate text-sm font-medium">{site.title}</h3>
                <span className="truncate text-xs text-muted-foreground">{new URL(site.url).hostname}</span>
              </div>
              <p className="mt-2 line-clamp-2 text-xs leading-relaxed text-muted-foreground">{site.summary}</p>
              <div className="mt-auto flex flex-wrap items-center justify-between gap-2 pt-4 text-xs text-muted-foreground">
                <span>Captured <time dateTime={site.capturedAt}>{formatCaptureDate(site.capturedAt)}</time></span>
                <span className="text-foreground">Open design <span aria-hidden="true">↗</span></span>
              </div>
            </div>
          </Link>
        ))}
      </div>
    </section>
  );
}
