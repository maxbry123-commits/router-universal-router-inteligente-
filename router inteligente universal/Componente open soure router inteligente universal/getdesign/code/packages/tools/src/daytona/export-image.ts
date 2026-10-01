import sharp from "sharp";
import type { ScreenshotArtifact } from "./types.js";

/** Compact, portable evidence files. Original PNG tiles remain available to analysis. */
export async function exportScreenshot(image: ScreenshotArtifact) {
  const { data, info } = await sharp(Buffer.from(image.imageBase64, "base64"))
    .resize({ width: 16383, height: 16383, fit: "inside", withoutEnlargement: true })
    .webp({ quality: 82 }).toBuffer({ resolveWithObject: true });
  return { imageBase64: data.toString("base64"), width: info.width, height: info.height };
}
