import { createHash } from "node:crypto";
import { readFile } from "node:fs/promises";
import { resolve } from "node:path";
import sharp from "../packages/tools/node_modules/sharp";
import snapshots from "../convex/seedData/cached-sites.json";
import { cachedSiteSchema } from "../convex/lib/cachedSiteSchema";

export async function validateCachedSiteImages() {
  for (const raw of snapshots) {
    const site = cachedSiteSchema.parse(raw);
    for (const image of site.images) {
      const data = await readFile(resolve(import.meta.dir, `../apps/dashboard/public${image.url}`));
      const hash = createHash("sha256").update(data).digest("hex").slice(0, 12);
      const meta = await sharp(data).metadata();
      if (!image.url.includes(`/${hash}-`) || meta.format !== "webp" || meta.width !== image.width || meta.height !== image.height || !site.markdown.includes(`](${image.url})`)) {
        throw new Error(`Invalid or unreferenced screenshot: ${site.slug}`);
      }
    }
  }
}
