import { expect, test } from "bun:test";
import sharp from "sharp";
import { exportScreenshot } from "../src/daytona/export-image";

test("long full-page captures stay within WebP's dimension limit", async () => {
  const png = await sharp({ create: { width: 100, height: 18000, channels: 3, background: "#abcdef" } }).png().toBuffer();
  const image = await exportScreenshot({ imageBase64: png.toString("base64") });
  const meta = await sharp(Buffer.from(image.imageBase64, "base64")).metadata();
  expect(meta.format).toBe("webp");
  expect(meta.width).toBe(image.width);
  expect(meta.height).toBe(image.height);
  expect(image.height).toBeLessThanOrEqual(16383);
  expect(image.width).toBeGreaterThan(0);
});
