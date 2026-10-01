import { v } from "convex/values";
import { internalMutation, query } from "./_generated/server";
import { requireWorkOsUserId } from "./workosAuth";
import { cachedSiteFields, cachedSiteSummaryFields } from "./lib/cachedSiteFields";
import snapshots from "./seedData/cached-sites.json";
import { cachedSiteSchema, hasCachedSiteImages } from "./lib/cachedSiteSchema";
import type { Doc } from "./_generated/dataModel";

function summary(site: Doc<"cachedSites">) {
  return {
    slug: site.slug, title: site.title, url: site.url, capturedAt: site.capturedAt,
    images: site.images ?? [],
    summary: site.summary, colors: site.colors, mode: site.mode, tiles: site.tiles,
  };
}

// Shared across accounts. No user ID filter and no private run data.
export const list = query({
  args: {},
  returns: v.array(v.object(cachedSiteSummaryFields)),
  handler: async ctx => {
    await requireWorkOsUserId(ctx);
    const sites = await ctx.db.query("cachedSites").collect();
    return sites.filter(hasCachedSiteImages).sort((a, b) => a.title.localeCompare(b.title)).map(summary);
  },
});

export const get = query({
  args: { slug: v.string() },
  returns: v.union(v.null(), v.object(cachedSiteFields)),
  handler: async (ctx, { slug }) => {
    await requireWorkOsUserId(ctx);
    const site = await ctx.db.query("cachedSites").withIndex("by_slug", q => q.eq("slug", slug)).unique();
    return site && hasCachedSiteImages(site) ? { ...summary(site), markdown: site.markdown } : null;
  },
});

// Deploy-only entry point. Users cannot write to or replace the shared library.
export const seed = internalMutation({
  args: {},
  returns: v.object({ inserted: v.number(), updated: v.number(), unchanged: v.number(), total: v.number() }),
  handler: async ctx => {
    const catalog = snapshots.map(site => cachedSiteSchema.parse(site));
    if (catalog.length < 10 || new Set(catalog.map(site => site.slug)).size !== catalog.length) {
      throw new Error("The shared catalog needs at least ten distinct sites");
    }
    let inserted = 0, updated = 0, unchanged = 0;
    for (const site of catalog) {
      const existing = await ctx.db.query("cachedSites").withIndex("by_slug", q => q.eq("slug", site.slug)).unique();
      if (!existing) {
        await ctx.db.insert("cachedSites", { ...site, updatedAt: Date.now() });
        inserted++;
      } else if ((hasCachedSiteImages(existing) && Date.parse(existing.capturedAt) > Date.parse(site.capturedAt)) ||
        Object.entries(site).every(([key, value]) => JSON.stringify(existing[key as keyof typeof existing]) === JSON.stringify(value))) {
        unchanged++;
      } else {
        await ctx.db.patch(existing._id, { ...site, updatedAt: Date.now() });
        updated++;
      }
    }
    return { inserted, updated, unchanged, total: catalog.length };
  },
});
