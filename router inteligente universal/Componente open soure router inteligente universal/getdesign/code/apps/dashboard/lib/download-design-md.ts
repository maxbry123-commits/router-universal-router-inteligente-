import { getAnalytics } from "@getdesign/analytics";

export function exportFileStem(siteName: string): string {
  const slug = siteName
    .toLowerCase()
    .replace(/['’]/g, "")
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/^-+|-+$/g, "")
    .slice(0, 80);
  return `getdesign-${slug || "design"}`;
}

export function exportMarkdownFilename(siteName: string): string {
  return `${exportFileStem(siteName)}.md`;
}

export function exportZipFilename(siteName: string): string {
  return `${exportFileStem(siteName)}.zip`;
}

export async function downloadDesignMd(content: string, filename: string) {
  const { markdown } = await prepareDesignDownload(content, false);
  saveDownload(new Blob([markdown], { type: "text/markdown;charset=utf-8" }), filename);
}

export function downloadPlainMarkdown(content: string, filename: string) {
  saveDownload(new Blob([content], { type: "text/markdown;charset=utf-8" }), filename);
}

export async function downloadDesignBundle(
  content: string,
  filename = "getdesign-design.zip",
  markdownName = "getdesign-design.md",
) {
  const { zipSync, strToU8 } = await import("fflate");
  const { markdown, files } = await prepareDesignDownload(content, true);
  const bytes = zipSync({ [markdownName]: strToU8(markdown), ...files }, { level: 0 });
  saveDownload(new Blob([new Uint8Array(bytes)], { type: "application/zip" }), filename);
}

export async function prepareDesignDownload(content: string, bundle: boolean) {
  const files: Record<string, Uint8Array> = {};
  const urls = [...new Set([...content.matchAll(/!\[[^\]]*\]\(([^)]+)\)/g)].map(match => match[1]!))];
  const replacements = await Promise.all(urls.map(async (url, index) => {
    const response = await fetch(url);
    if (!response.ok) throw new Error("Could not download screenshots. Please retry.");
    const type = response.headers.get("content-type")?.split(";")[0];
    if (type !== "image/png" && type !== "image/webp" && type !== "image/jpeg") throw new Error("Screenshot response is not an image.");
    const bytes = new Uint8Array(await response.arrayBuffer());
    const path = `images/${String(index + 1).padStart(3, "0")}.${type === "image/png" ? "png" : type === "image/webp" ? "webp" : "jpg"}`;
    if (bundle) files[path] = bytes;
    let binary = "";
    if (!bundle) for (const byte of bytes) binary += String.fromCharCode(byte);
    return [url, bundle ? path : `data:${type};base64,${btoa(binary)}`] as const;
  }));
  let markdown = content;
  for (const [url, replacement] of replacements) markdown = markdown.replaceAll(`](${url})`, `](${replacement})`);
  return { markdown, files };
}

function saveDownload(blob: Blob, filename: string) {
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = filename;
  document.body.appendChild(link);
  try {
    link.click();
    getAnalytics().capture({ event: "design_md_downloaded", properties: {} });
  } finally {
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
  }
}
