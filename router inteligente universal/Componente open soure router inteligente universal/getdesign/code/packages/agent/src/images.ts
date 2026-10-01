import { exportScreenshot } from "@getdesign/tools/daytona";
import type { VisualResult } from "./agents/visual.js";

/** Portable captured files. Write these beside markdown using their relative paths. */
export type DesignImage = {
  path: string;
  alt: string;
  imageBase64: string;
  mimeType: "image/webp";
  width: number;
  height: number;
};

export async function getDesignImages(visual: VisualResult): Promise<DesignImage[]> {
  if (visual.status !== "captured") return [];
  return Promise.all([
    { path: "images/hero.webp", alt: "Captured hero viewport", ...visual.hero },
    { path: "images/full-page.webp", alt: "Captured full page", ...visual.fullPage },
  ].map(async ({ path, alt, ...artifact }) => ({
    path, alt, ...await exportScreenshot(artifact), mimeType: "image/webp" as const,
  })));
}

/** A single-file Markdown response, for clients that cannot save companion assets. */
export function embedDesignImages(markdown: string, images: DesignImage[]): string {
  for (const image of images) {
    markdown = markdown.replaceAll(`](${image.path})`, `](data:${image.mimeType};base64,${image.imageBase64})`);
  }
  return markdown;
}
