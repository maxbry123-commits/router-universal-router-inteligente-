import { z } from "zod";

export const cachedSiteSchema = z.strictObject({
  slug: z.string().regex(/^[a-z0-9]+(?:-[a-z0-9]+)*$/),
  title: z.string().min(1),
  url: z.url().refine(value => new URL(value).protocol === "https:"),
  capturedAt: z.iso.datetime(),
  summary: z.string().min(1),
  colors: z.array(z.string().regex(/^#[0-9a-f]{6}$/i)).min(1).max(8),
  images: z.array(z.strictObject({
    url: z.string().regex(/^\/cached-sites\/[a-z0-9-]+\/[a-f0-9]{12}-(hero|full-page)\.webp$/),
    alt: z.string().min(1), width: z.number().int().positive(), height: z.number().int().positive(),
  })).length(2).refine(images =>
    images.some(image => image.url.endsWith("-hero.webp")) &&
    images.some(image => image.url.endsWith("-full-page.webp")),
    "A hero and full-page screenshot are required",
  ),
  markdown: z.string().min(1000),
  mode: z.literal("visual"),
  tiles: z.number().int().positive(),
});
export type CachedSite = z.infer<typeof cachedSiteSchema>;
export type CachedSiteSummary = Omit<CachedSite, "markdown">;

/** Legacy rows may predate image metadata; they are not publishable snapshots. */
export function hasCachedSiteImages(site: { images?: unknown }): boolean {
  return cachedSiteSchema.shape.images.safeParse(site.images).success;
}
