import { beforeEach, describe, expect, mock, test } from "bun:test";
import { renderToStaticMarkup } from "react-dom/server";
import { getFunctionName } from "convex/server";
import { listCachedSites } from "./cached-sites";
import { ExtractionGuide } from "../components/extraction-guide";

type RunFixture = {
  _id: string;
  domain: string;
  status: "queued" | "running" | "completed" | "failed";
  visibility?: "public" | "private";
};

let recent: RunFixture[] = [];
let artifacts: Record<string, { markdown?: string }> = {};

function summarize(runs: RunFixture[]) {
  return {
    total: runs.length,
    completed: runs.filter((run) => run.status === "completed").length,
    failed: runs.filter((run) => run.status === "failed").length,
    active: runs.filter(
      (run) => run.status === "queued" || run.status === "running",
    ).length,
  };
}

const query = mock(async (_reference: unknown, args: Record<string, unknown>) => {
  const name = getFunctionName(_reference as Parameters<typeof getFunctionName>[0]);
  if (name === "cachedSites:list") return listCachedSites();
  if (name === "designRuns:summarizeForUser") return summarize(recent);
  if (name === "userCredentials:listForUser") return [];
  if (name === "designRuns:listRecentPreviews") {
    const requireDesignFile = Boolean(args.requireDesignFile);
    const displayLimit =
      typeof args.displayLimit === "number" ? args.displayLimit : undefined;
    return recent
      .slice(0, Number(args.limit))
      .map((run) => previewFromRun(run, requireDesignFile))
      .filter((run): run is NonNullable<typeof run> => Boolean(run))
      .slice(0, displayLimit);
  }
  throw new Error(`Unexpected query ${name}`);
});

mock.module("@workos-inc/authkit-nextjs", () => ({
  withAuth: async () => ({ user: { id: "overview-test-user" }, accessToken: "overview-token" }),
}));
const getConvexClient = mock(() => ({ query }));
mock.module("./convex-server", () => ({
  getConvexClient,
}));
mock.module("../components/extraction-onboarding", () => ({
  ExtractionOnboarding: () => <ExtractionGuide credentialsReady={false} />,
}));

const { default: Page } = await import("../app/(dashboard)/page");

beforeEach(() => {
  recent = [];
  artifacts = {};
  query.mockClear();
  getConvexClient.mockClear();
});

function completedRun(id: string): RunFixture {
  artifacts[id] = { markdown: `# ${id} Design System\n\nAccent: \`#abcdef\`` };
  return { _id: id, domain: `${id}.example`, status: "completed" };
}

function previewFromRun(run: RunFixture, requireDesignFile: boolean) {
  if (run.status !== "completed") {
    return requireDesignFile
      ? null
      : {
          slug: run._id,
          domain: run.domain,
          status: run.status,
          title: run.domain,
          theme: "",
          accent: "#888888",
          image: null,
          textOnly: false,
          visibility: run.visibility === "public" ? "public" : "private",
        };
  }
  const markdown = artifacts[run._id]?.markdown;
  if (!markdown) {
    return requireDesignFile
      ? null
      : {
          slug: run._id,
          domain: run.domain,
          status: run.status,
          title: run.domain,
          theme: "",
          accent: "#888888",
          image: null,
          textOnly: false,
          visibility: run.visibility === "public" ? "public" : "private",
        };
  }
  return {
    slug: run._id,
    domain: run.domain,
    status: run.status,
    title: idTitle(markdown, run.domain),
    theme: "",
    accent: "#abcdef",
    image: "https://example.com/captured.png",
    textOnly: false,
    visibility: run.visibility === "public" ? "public" : "private",
  };
}

function idTitle(markdown: string, fallback: string) {
  const match = markdown.match(/^# (.+)/m);
  return match
    ? match[1].replace(/\s*Design System\s*$/i, "").trim()
    : fallback;
}

function queryNames() {
  return query.mock.calls.map(
    ([reference]) =>
      getFunctionName(reference as Parameters<typeof getFunctionName>[0]),
  );
}

describe("Overview recent-run summary", () => {
  test("shows catalog stats and an examples preview when there are no runs", async () => {
    const html = renderToStaticMarkup(await Page());
    const catalog = listCachedSites();
    expect(html).toContain("Cached sites");
    expect(html).toContain(String(catalog.length));
    expect(html).toContain("Your runs");
    expect(html).toContain("Browse all examples");
    expect(html).toContain(`href="/sites/${catalog[0]!.slug}"`);
    expect((html.match(/href="\/sites\//g) ?? []).length).toBe(4);
    expect(html).not.toContain("Recent runs");
    expect(html).not.toContain("0 shown");
    expect(html).toContain('href="/account#provider-keys"');
    expect(html).toContain('href="/sites"');
  });

  test("authenticates the server's run queries with the WorkOS access token", async () => {
    await Page();
    expect(getConvexClient).toHaveBeenCalledWith("overview-token");
  });
  test("shows setup onboarding when there are no completed runs", async () => {
    const html = renderToStaticMarkup(await Page());

    expect(html).toContain("Turn a website into a design system");
    expect(html).toContain("Add provider keys");
    expect(html).toContain("Choose a public URL");
    expect(html).toContain("Open the finished design");
    expect(html).toContain('href="/account#provider-keys"');
    expect(html).toContain('href="/sites"');
    expect(html).not.toContain("Recent runs");
    expect(html).not.toContain("No completed design systems yet");
  });

  test("removes unsupported placeholder statistics", async () => {
    const html = renderToStaticMarkup(await Page());

    for (const removed of [
      "3.2M",
      "13k",
      "google.com/s2/favicons",
      "View all",
    ]) {
      expect(html).not.toContain(removed);
    }
    expect(html).not.toContain("Recent runs");
  });

  test("counts only displayed completed runs with design files, scoped to the user", async () => {
    recent = [
      completedRun("visible"),
      { _id: "queued", domain: "queued.example", status: "queued" },
      { _id: "running", domain: "running.example", status: "running" },
      { _id: "failed", domain: "failed.example", status: "failed" },
      { _id: "missing", domain: "missing.example", status: "completed" },
    ];

    const html = renderToStaticMarkup(await Page());

    expect(html).toContain("Browse all runs");
    expect(html).toContain("Completed runs with design files from your latest 12 runs.");
    expect(html).toContain('href="/runs/visible"');
    expect(html).toContain('href="/runs"');
    expect(html).toContain(">5<");
    expect(html).toContain(">2<");
    expect(html).toContain(">1<");
    for (const id of ["queued", "running", "failed", "missing"]) {
      expect(html).not.toContain(`href="/runs/${id}"`);
    }
    expect(html).toContain("Extract");
    expect(html).not.toContain("Turn a website into a design system");
    expect(queryNames()).toContain("designRuns:listRecentPreviews");
    expect(queryNames()).toContain("designRuns:summarizeForUser");
    expect(queryNames()).toContain("cachedSites:list");
    expect(queryNames()).toContain("userCredentials:listForUser");
    expect(queryNames()).not.toContain("designRuns:listRecent");
    expect(queryNames()).not.toContain("designRunArtifacts:getForRun");
    expect(
      query.mock.calls.map(([, args]) => args),
    ).toContainEqual({
      userId: "overview-test-user",
      limit: 12,
      requireDesignFile: true,
      displayLimit: 6,
    });
  });

  test("keeps the recent list to six completed runs", async () => {
    recent = Array.from({ length: 25 }, (_, i) => completedRun(`run-${i}`));

    const html = renderToStaticMarkup(await Page());

    expect(html).toContain("Browse all runs");
    expect(html).toContain("from your latest 12 runs.");
    expect(html.match(/href="\/runs\//g)).toHaveLength(6);
    expect(html).not.toContain('href="/runs/run-6"');
    expect(html).toContain(">25<");
  });
});


test("Examples lists shared snapshots without mixing them into private run counts", async () => {
  const { default: SitesPage } = await import("../app/(dashboard)/sites/page");
  const html = renderToStaticMarkup(await SitesPage());
  expect(html).toContain("Examples");
  expect(html).toContain('href="/sites/linear"');
  expect(html).toContain("Captured");
  expect((html.match(/href="\/sites\//g) ?? []).length).toBeGreaterThanOrEqual(10);
});

test("a legacy cached row cannot crash the catalog or display an image-free card", async () => {
  const { CachedSites } = await import("../components/cached-sites");
  const site = listCachedSites()[0]!;
  const broken = { ...site, slug: "legacy", images: [] };
  const html = renderToStaticMarkup(<CachedSites sites={[broken, site]} />);
  expect(html).toContain(`href="/sites/${site.slug}"`);
  expect(html).not.toContain('href="/sites/legacy"');
  expect(html).toContain("1 available");
});

test("Overview examples preview links to the full catalog", async () => {
  const { CachedSites } = await import("../components/cached-sites");
  const sites = listCachedSites();
  const html = renderToStaticMarkup(
    <CachedSites sites={sites} previewCount={4} />,
  );
  expect(html).toContain("Browse all examples");
  expect((html.match(/href="\/sites\//g) ?? []).length).toBe(4);
  expect(html).not.toContain("available");
});

test("Runs lists every recent status without mixing in cached sites", async () => {
  const { default: RunsPage } = await import("../app/(dashboard)/runs/page");
  recent = [
    { ...completedRun("visible"), visibility: "public" },
    { _id: "queued", domain: "queued.example", status: "queued" },
    { _id: "failed", domain: "failed.example", status: "failed" },
  ];
  const html = renderToStaticMarkup(await RunsPage({ searchParams: Promise.resolve({}) }));
  expect(html).toContain("Recent runs");
  expect(html).toContain("3 available");
  expect(html).toContain('href="/runs?visibility=public"');
  expect(html).toContain('href="/runs?visibility=private"');
  expect(html).toContain('href="/runs/visible"');
  expect(html).toContain('href="/runs/queued"');
  expect(html).toContain('href="/runs/failed"');
  expect(html).toContain("Public");
  expect(html).toContain("Private");
  expect(html).toContain("Queued");
  expect(html).toContain("Failed");
  expect(html).toContain("Extract");
  expect(html).not.toContain("Browse all runs");
  expect(html).not.toContain("Turn a website into a design system");
  expect(
    query.mock.calls.map(([, args]) => args),
  ).toContainEqual({ userId: "overview-test-user", limit: 48 });
});

test("Runs can show only public or private extractions", async () => {
  const { default: RunsPage } = await import("../app/(dashboard)/runs/page");
  recent = [
    { ...completedRun("visible"), visibility: "public" },
    { _id: "queued", domain: "queued.example", status: "queued" },
    { _id: "failed", domain: "failed.example", status: "failed" },
  ];
  const publicHtml = renderToStaticMarkup(
    await RunsPage({ searchParams: Promise.resolve({ visibility: "public" }) }),
  );
  expect(publicHtml).toContain('href="/runs/visible"');
  expect(publicHtml).not.toContain('href="/runs/queued"');
  expect(publicHtml).not.toContain('href="/runs/failed"');
  expect(publicHtml).toContain("1 public");
  expect(publicHtml).toContain('aria-current="page"');

  const privateHtml = renderToStaticMarkup(
    await RunsPage({ searchParams: Promise.resolve({ visibility: "private" }) }),
  );
  expect(privateHtml).not.toContain('href="/runs/visible"');
  expect(privateHtml).toContain('href="/runs/queued"');
  expect(privateHtml).toContain("2 private");
});

test("Runs shows an empty state when the user has no extractions", async () => {
  const { default: RunsPage } = await import("../app/(dashboard)/runs/page");
  const html = renderToStaticMarkup(await RunsPage({ searchParams: Promise.resolve({}) }));
  expect(html).toContain("No runs yet");
  expect(html).toContain("Start an extraction from Agent.");
  expect(html).toContain('href="/agent"');
  expect(html).not.toContain("Recent runs");
});

test("Overview recent-run preview links to the Runs page", async () => {
  const { RecentRuns } = await import("../components/recent-runs");
  const html = renderToStaticMarkup(
    <RecentRuns
      preview
      runs={[
        {
          slug: "visible",
          domain: "visible.example",
          status: "completed",
          title: "Visible",
          theme: "Clean",
          accent: "#abcdef",
          image: null,
          textOnly: false,
          visibility: "private",
        },
      ]}
    />,
  );
  expect(html).toContain("Browse all runs");
  expect(html).toContain('href="/runs"');
  expect(html).toContain('href="/runs/visible"');
  expect(html).toContain("Private");
  expect(html).not.toContain("available");
});
