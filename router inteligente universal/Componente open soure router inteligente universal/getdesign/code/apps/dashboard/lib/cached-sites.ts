import snapshots from "@convex/seedData/cached-sites.json";
import { canUseBundledCatalog } from "./cached-site-fallback";
import { api } from "@convex/_generated/api";
import { getConvexClient } from "./convex-server";
import { cachedSiteSchema, type CachedSiteSummary } from "./cached-site-schema";

// Curated public-site snapshots only. Never derived from users' private runs.
const sites = snapshots.map(snapshot => cachedSiteSchema.parse(snapshot));

export function listCachedSites(): CachedSiteSummary[] {
  return sites.map(site => ({
    slug: site.slug, title: site.title, url: site.url, capturedAt: site.capturedAt,
    images: site.images,
    summary: site.summary, colors: site.colors, mode: site.mode, tiles: site.tiles,
  }));
}

export function getCachedSite(slug: string) {
  return sites.find(site => site.slug === slug) ?? null;
}

export function formatCaptureDate(value: string) {
  return new Intl.DateTimeFormat("en", {
    month: "short", day: "numeric", year: "numeric", timeZone: "UTC",
  }).format(new Date(value));
}

export function pickRandomItems<T>(items: readonly T[], count: number): T[] {
  if (count >= items.length) return items.slice();
  const pool = items.slice();
  for (let i = 0; i < count; i++) {
    const j = i + Math.floor(Math.random() * (pool.length - i));
    const current = pool[i]!;
    pool[i] = pool[j]!;
    pool[j] = current;
  }
  return pool.slice(0, count);
}


/** Production always reads the seeded database. Old local/preview backends can
 * still display the curated bundle until their schema and functions deploy. */
export async function loadCachedSites(accessToken: string) {
  try {
    const rows = await getConvexClient(accessToken).query(api.cachedSites.list, {});
    return rows.length === 0 && canUseBundledCatalog(process.env) ? listCachedSites() : rows;
  } catch (error) {
    if (canUseBundledCatalog(process.env, error)) return listCachedSites();
    throw error;
  }
}

export async function loadCachedSite(slug: string, accessToken: string) {
  try {
    const site = await getConvexClient(accessToken).query(api.cachedSites.get, { slug });
    return !site && canUseBundledCatalog(process.env) ? getCachedSite(slug) : site;
  } catch (error) {
    if (canUseBundledCatalog(process.env, error)) return getCachedSite(slug);
    throw error;
  }
}
