#!/usr/bin/env bun
/** Refresh the curated public-site library. Runs three visual extractions at a time.
 * bun --env-file=apps/dashboard/.env.local scripts/cache-sites.ts
 * Only completed, CSS-grounded results enter the catalog. Existing data remains
 * intact unless at least ten sites pass. No account data or credentials are saved.
 */
import { mkdir, writeFile, rename } from "node:fs/promises";
import { resolve } from "node:path";
import { saveCachedImages } from "./cached-site-images";
import { runDesign } from "../packages/agent/src/runDesign";
import { checkPaletteGrounding, joinStylesheetCss } from "./brand-smoke/grounding";
import { cachedSiteSchema, type CachedSite } from "../convex/lib/cachedSiteSchema";

const targets = [
  ["linear", "Linear", "https://linear.app"],
  ["vercel", "Vercel", "https://vercel.com"],
  ["stripe", "Stripe", "https://stripe.com"],
  ["notion", "Notion", "https://notion.so"],
  ["figma", "Figma", "https://figma.com"],
  ["raycast", "Raycast", "https://raycast.com"],
  ["resend", "Resend", "https://resend.com"],
  ["clerk", "Clerk", "https://clerk.com"],
  ["workos", "WorkOS", "https://workos.com"],
  ["convex", "Convex", "https://convex.dev"],
  ["supabase", "Supabase", "https://supabase.com"],
  ["framer", "Framer", "https://framer.com"],
] as const;

for (const key of ["DAYTONA_API_KEY", "OPENAI_API_KEY"]) {
  if (!process.env[key]) throw new Error(`Missing ${key}`);
}
const startedAt = new Date().toISOString();
const out = resolve("getdesign-runs/cached-sites", startedAt.replace(/[:.]/g, "-"));
await mkdir(out, { recursive: true });
const snapshots: CachedSite[] = [];
const failures: { slug: string; error: string }[] = [];
let next = 0;
await Promise.all(Array.from({ length: 3 }, async () => {
  while (next < targets.length) {
    const [slug, title, url] = targets[next++]!;
    console.log(`${slug}: started`);
    try {
      const result = await runDesign(url, {
        siteName: title,
        visualRequirement: "require",
        credentials: { daytonaApiKey: process.env.DAYTONA_API_KEY, openaiApiKey: process.env.OPENAI_API_KEY },
      });
      const grounding = checkPaletteGrounding(joinStylesheetCss(result.crawl.stylesheets), result.doc.palette);
      if (!grounding.pass) throw new Error("Palette contains colors not grounded in the source CSS");
      const colors = [...new Set([...result.markdown.matchAll(/`(#[A-Fa-f0-9]{6})(?![A-Fa-f0-9])/g)].map(m => m[1]!.toUpperCase()))].slice(0, 8);
      const summary = result.markdown.match(/## 1\. Visual Theme & Atmosphere\s+([^\n]+)/)?.[1]?.trim() ?? `${title}'s color palette, typography, layout and component guidance.`;
      const images = await saveCachedImages(slug, result.visual);
      const markdown = result.markdown.replaceAll("](images/hero.webp)", `](${images[0]!.url})`).replaceAll("](images/full-page.webp)", `](${images[1]!.url})`);
      const snapshot = cachedSiteSchema.parse({ images, slug, title, url, capturedAt: new Date().toISOString(), summary, colors, markdown, mode: result.mode, tiles: result.tiles });
      const serialized = JSON.stringify(snapshot, null, 2) + "\n";
      for (const name of ["DAYTONA_API_KEY", "OPENAI_API_KEY", "WORKOS_API_KEY", "WORKOS_COOKIE_PASSWORD", "GETDESIGN_CREDENTIALS_KEY"]) {
        const value = process.env[name];
        if (value && serialized.includes(value)) throw new Error("Secret detected in generated snapshot");
      }
      await writeFile(resolve(out, `${slug}.json`), serialized);
      snapshots.push(snapshot);
      console.log(`${slug}: saved (${snapshot.tiles} tiles)`);
    } catch (error) {
      // Avoid logging provider error bodies, which may contain request details.
      failures.push({ slug, error: error instanceof Error ? error.name : "UnknownError" });
      console.log(`${slug}: failed; excluded from catalog`);
    }
  }
}));
await writeFile(resolve(out, "summary.json"), JSON.stringify({ startedAt, completedAt: new Date().toISOString(), concurrency: 3, passed: snapshots.map(s => s.slug), failures }, null, 2) + "\n");
if (snapshots.length < 10) throw new Error(`Only ${snapshots.length} sites passed; existing catalog unchanged. Results: ${out}`);
snapshots.sort((a, b) => a.title.localeCompare(b.title));
const destination = resolve("convex/seedData/cached-sites.json");
await writeFile(`${destination}.tmp`, JSON.stringify(snapshots, null, 2) + "\n");
await rename(`${destination}.tmp`, destination);
console.log(`Catalog updated: ${snapshots.length} sites. Results: ${out}`);
