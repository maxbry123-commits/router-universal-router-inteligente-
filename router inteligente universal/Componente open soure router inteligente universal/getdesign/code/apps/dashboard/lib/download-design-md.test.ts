import { expect, test } from "bun:test";
import { exportFileStem, exportMarkdownFilename, exportZipFilename, prepareDesignDownload } from "./download-design-md";

test("export files are named with getdesign branding and the site", () => {
  expect(exportFileStem("Mohtasham's Portfolio")).toBe("getdesign-mohtashams-portfolio");
  expect(exportMarkdownFilename("Linear")).toBe("getdesign-linear.md");
  expect(exportZipFilename("Linear")).toBe("getdesign-linear.zip");
  expect(exportFileStem("   ")).toBe("getdesign-design");
});

test("image downloads remain usable offline and fail instead of omitting unavailable captures", async () => {
  const original = globalThis.fetch;
  const bytes = new Uint8Array([137, 80, 78, 71, 13, 10, 26, 10]);
  try {
    globalThis.fetch = (async () => new Response(bytes, { headers: { "content-type": "image/png" } })) as unknown as typeof fetch;
    const content = "# Example\n\n![Hero](https://storage.example/hero)";
    const bundle = await prepareDesignDownload(content, true);
    expect(bundle.markdown).toContain("](images/001.png)");
    expect(bundle.files["images/001.png"]).toEqual(bytes);
    const standalone = await prepareDesignDownload(content, false);
    expect(standalone.markdown).toContain("](data:image/png;base64,iVBORw0KGgo=)");
    globalThis.fetch = (async () => new Response("missing", { status: 404 })) as unknown as typeof fetch;
    await expect(prepareDesignDownload(content, true)).rejects.toThrow("Could not download screenshots");
  } finally { globalThis.fetch = original; }
});
