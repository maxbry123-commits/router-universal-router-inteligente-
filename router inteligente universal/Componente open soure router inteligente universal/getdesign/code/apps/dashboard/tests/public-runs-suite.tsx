// Run through public-runs.test.ts to isolate Bun's module mocks.
import { beforeEach, expect, mock, test } from "bun:test";
import { readFileSync } from "node:fs";
import { renderToStaticMarkup } from "react-dom/server";
import { getFunctionName } from "convex/server";

const published = {
  id: "published-run", domain: "example.com", url: "https://example.com", mode: "visual" as const,
  completedAt: 1, publishedAt: 2, markdown: "# Example design\n\n## Palette\nBlue",
  doc: { title: "Example" }, tokens: { colors: ["blue"] }, visualDescription: "A blue page",
  images: [{ index: 0, width: 1024, height: 768 }],
};
let available = true;
const query = mock(async (ref: Parameters<typeof getFunctionName>[0]) => {
  expect(getFunctionName(ref)).toBe("publicRuns:get");
  return available ? published : null;
});
const action = mock(async (ref: Parameters<typeof getFunctionName>[0]) => {
  expect(getFunctionName(ref)).toBe("publicRuns:image");
  return available ? { bytes: new TextEncoder().encode("image").buffer, contentType: "image/png" } : null;
});
const getConvexClient = mock(() => ({ query, action }));
mock.module("@/lib/convex-server", () => ({ getConvexClient }));
mock.module("../lib/convex-server", () => ({ getConvexClient }));
mock.module("next/navigation", () => ({
  notFound: () => { throw new Error("notFound"); },
  useRouter: () => ({ refresh() {} }),
}));
mock.module("convex/react", () => ({
  useMutation: () => mock(), useQuery: () => undefined,
  useConvexAuth: () => ({ isAuthenticated: false }),
}));

const { GET: markdown } = await import("../app/r/[id]/design.md/route");
const { GET: json } = await import("../app/r/[id]/design.json/route");
const { GET: image } = await import("../app/r/[id]/images/[index]/route");
const { default: Page, generateMetadata } = await import("../app/r/[id]/page");
const { ShareRun } = await import("../app/(dashboard)/runs/[slug]/share-run");
const request = new Request("https://app.example/r/published-run/design.md");
const context = { params: Promise.resolve({ id: "published-run" }) };

beforeEach(() => { available = true; query.mockClear(); action.mockClear(); getConvexClient.mockClear(); });

test("anonymous Markdown and JSON use absolute checked screenshot URLs and no cache", async () => {
  const md = await markdown(request, context);
  expect(md.status).toBe(200);
  expect(md.headers.get("content-type")).toContain("text/markdown");
  expect(md.headers.get("cache-control")).toBe("no-store");
  expect(md.headers.get("access-control-allow-origin")).toBe("*");
  expect(await md.text()).toContain("![Captured page tile 1](https://app.example/r/published-run/images/0)");
  const data = await json(request, context);
  const result = await data.json();
  expect(result.schemaVersion).toBe(1);
  expect(result.links.markdown).toBe("https://app.example/r/published-run/design.md");
  expect(result.images[0].url).toBe("https://app.example/r/published-run/images/0");
  expect(result.doc).toEqual(published.doc);
  for (const args of getConvexClient.mock.calls) expect(args).toEqual([]);
  expect(action).not.toHaveBeenCalled();
});

test("missing or unpublished runs return 404 for every download", async () => {
  available = false;
  for (const handler of [markdown, json]) {
    const response = await handler(request, context);
    expect(response.status).toBe(404);
    expect(response.headers.get("cache-control")).toBe("no-store");
    expect(response.headers.has("location")).toBe(false);
  }
  const response = await image(request, { params: Promise.resolve({ id: "published-run", index: "0" }) });
  expect(response.status).toBe(404);
  await expect(Page(context)).rejects.toThrow("notFound");
  await expect(generateMetadata(context)).rejects.toThrow("notFound");
});

test("agent links retain the public HTTPS host behind a reverse proxy", async () => {
  const proxied = new Request("http://localhost:3000/r/published-run/design.json", {
    headers: { host: "internal.local", "x-forwarded-host": "app.getdesign.app", "x-forwarded-proto": "https" },
  });
  const result = await (await json(proxied, context)).json();
  expect(result.links.page).toBe("https://app.getdesign.app/r/published-run");
  expect(result.images[0].url).toBe("https://app.getdesign.app/r/published-run/images/0");
});

test("screenshots return bytes rather than redirects to permanent storage URLs", async () => {
  const response = await image(request, { params: Promise.resolve({ id: "published-run", index: "0" }) });
  expect(response.status).toBe(200);
  expect(response.headers.get("content-type")).toBe("image/png");
  expect(response.headers.get("cache-control")).toBe("no-store");
  expect(response.headers.has("location")).toBe(false);
  expect(await response.text()).toBe("image");
  for (const index of ["-1", "1.1", "oops", "9007199254740992"]) {
    expect((await image(request, { params: Promise.resolve({ id: "published-run", index }) })).status).toBe(404);
  }
  expect(action).toHaveBeenCalledTimes(1);
});

test("public page renders the design and download links without owner-only controls", async () => {
  const html = renderToStaticMarkup(await Page(context));
  expect(html).toContain("Example design");
  expect(html).toContain('href="/r/published-run/design.md"');
  expect(html).toContain('href="/r/published-run/design.json"');
  expect(html).toContain('/r/published-run/images/0');
  expect(html).not.toContain("Publish run");
  expect(html).not.toContain("Make private");
});

test("owner controls are a public/private dropdown with a copyable link when published", () => {
  const privateHtml = renderToStaticMarkup(<ShareRun runId="run" isPublic={false} />);
  expect(privateHtml).toContain('aria-label="Visibility"');
  expect(privateHtml).toContain('aria-haspopup="menu"');
  expect(privateHtml).toContain("Private");
  expect(privateHtml).not.toContain("anyone view and download");
  const publicHtml = renderToStaticMarkup(<ShareRun runId="run" isPublic />);
  expect(publicHtml).toContain("Public");
  const share = readFileSync(
    new URL("../app/(dashboard)/runs/[slug]/share-run.tsx", import.meta.url),
    "utf8",
  );
  expect(share).toContain('value="private"');
  expect(share).toContain('value="public"');
  expect(share).toContain("Copy link");
  expect(share).toContain("href={path}");
  const shell = readFileSync(
    new URL("../app/(dashboard)/runs/[slug]/run-page-shell.tsx", import.meta.url),
    "utf8",
  );
  expect(shell.indexOf("<ExportActions")).toBeLessThan(shell.indexOf("<ShareRun"));
});


test("shared metadata describes only a published run and keeps it out of search", async () => {
  const metadata = await generateMetadata(context);
  expect(metadata.title).toBe("Example design");
  expect(metadata.robots).toEqual({ index: false, follow: false });
  expect(metadata.alternates?.canonical).toBe("https://dashboard.getdesign.app/r/published-run");
  expect(metadata.openGraph).toMatchObject({
    title: "Example design · getdesign",
    url: "https://dashboard.getdesign.app/r/published-run",
    description: "View Example design on getdesign. Download the published design document and screenshots.",
  });
  expect(metadata.twitter).toMatchObject({ card: "summary", title: "Example design · getdesign" });
  for (const args of getConvexClient.mock.calls) expect(args).toEqual([]);
  expect(action).not.toHaveBeenCalled();
});
