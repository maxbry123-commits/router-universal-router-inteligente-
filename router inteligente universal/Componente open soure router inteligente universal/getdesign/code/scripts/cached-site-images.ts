import { mkdir, writeFile } from "node:fs/promises";
import { createHash } from "node:crypto";
import { resolve } from "node:path";
import sharp from "../packages/tools/node_modules/sharp";
import type { VisualResult } from "../packages/agent/src/agents/visual";

export async function saveCachedImages(slug: string, visual: VisualResult) {
  if (visual.status !== "captured") throw new Error("Cached sites require screenshots");
  return Promise.all(([ ["hero", visual.hero], ["full-page", visual.fullPage] ] as const).map(async ([name, artifact]) => {
    const { data, info } = await sharp(Buffer.from(artifact.imageBase64, "base64")).resize({ width: name === "hero" ? 960 : 1440, height: 16383, fit: "inside", withoutEnlargement: true }).webp({ quality: 82 }).toBuffer({ resolveWithObject: true });
    const hash = createHash("sha256").update(data).digest("hex").slice(0, 12);
    const url = `/cached-sites/${slug}/${hash}-${name}.webp`;
    await mkdir(resolve(`apps/dashboard/public/cached-sites/${slug}`), { recursive: true });
    await writeFile(resolve(`apps/dashboard/public${url}`), data);
    return { url, alt: `${slug} captured ${name === "hero" ? "hero viewport" : "full page"}`, width: info.width, height: info.height };
  }));
}
