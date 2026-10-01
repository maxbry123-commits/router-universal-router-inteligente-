import { describe, expect, test } from "bun:test";
import { getCachedSite, listCachedSites, pickRandomItems } from "./cached-sites";
import { canUseBundledCatalog } from "./cached-site-fallback";
import { findCachedSite } from "./cached-site-url";

describe("Curated cached sites", () => {
  test("ships at least ten distinct completed visual snapshots with downloadable documents", () => {
    const sites = listCachedSites();
    expect(sites.length).toBeGreaterThanOrEqual(10);
    expect(new Set(sites.map(site => site.slug)).size).toBe(sites.length);
    expect(new Set(sites.map(site => site.url)).size).toBe(sites.length);
    for (const site of sites) {
      expect(site).not.toHaveProperty("markdown");
      expect(site.mode).toBe("visual");
      expect(site.tiles).toBeGreaterThan(0);
      expect(Date.parse(site.capturedAt)).toBeLessThanOrEqual(Date.now());
      const cached = getCachedSite(site.slug)!;
      expect(cached.markdown).toContain("Design System");
      expect(cached.markdown).toContain("Color Palette");
      expect(cached.markdown).toContain("Typography");
      expect(cached.markdown.toLowerCase()).not.toContain("text-only mode");
    }
    expect(getCachedSite("../../.env.local")).toBeNull();
    expect(getCachedSite("not-in-the-catalog")).toBeNull();
  });

  test("reuses the exact cached page but preserves query, path and scheme differences", () => {
    const sites = [{ slug: "linear", url: "https://linear.app" }];
    expect(findCachedSite("linear.app", sites)?.slug).toBe("linear");
    expect(findCachedSite(" https://linear.app/#features ", sites)?.slug).toBe("linear");
    for (const url of ["https://linear.app/pricing", "https://linear.app/?locale=fr", "http://linear.app", "https://linear.app.evil.test", "https://linear.app@evil.test", "bad url", ""]) {
      expect(findCachedSite(url, sites)).toBeUndefined();
    }
  });

  test("picks a unique random subset from the cached catalog", () => {
    const slugs = listCachedSites().map(site => site.slug);
    expect(pickRandomItems([], 3)).toEqual([]);
    expect(pickRandomItems(slugs, 20)).toEqual(slugs);
    const original = Math.random;
    Math.random = () => 0;
    try {
      expect(pickRandomItems(slugs, 3)).toEqual(slugs.slice(0, 3));
    } finally {
      Math.random = original;
    }
    const picked = pickRandomItems(slugs, 3);
    expect(picked).toHaveLength(3);
    expect(new Set(picked).size).toBe(3);
    expect(picked.every(slug => slugs.includes(slug))).toBe(true);
  });
});


test("production never silently replaces database data with the bundled catalog", () => {
  const missing = new Error("Could not find public function for 'cachedSites:list'");
  for (const error of [undefined, missing, new Error("Unauthorized"), new Error("Network failure")]) {
    expect(canUseBundledCatalog({ VERCEL_ENV: "production" }, error)).toBe(false);
    expect(canUseBundledCatalog({ NODE_ENV: "production" }, error)).toBe(false);
  }
  expect(canUseBundledCatalog({ VERCEL_ENV: "preview", NODE_ENV: "production" }, missing)).toBe(true);
  expect(canUseBundledCatalog({ NODE_ENV: "development" }, missing)).toBe(true);
  expect(canUseBundledCatalog({ VERCEL_ENV: "preview" }, new Error("Unauthorized"))).toBe(false);
  expect(canUseBundledCatalog({ VERCEL_ENV: "preview" }, new Error("Network failure"))).toBe(false);
});


test("all seeded images decode at the declared dimensions and match their document and content hash", async () => {
  const { validateCachedSiteImages } = await import("../../../scripts/validate-cached-site-images");
  await validateCachedSiteImages();
  for (const site of listCachedSites()) expect(site.images.length).toBeGreaterThanOrEqual(2);
});
