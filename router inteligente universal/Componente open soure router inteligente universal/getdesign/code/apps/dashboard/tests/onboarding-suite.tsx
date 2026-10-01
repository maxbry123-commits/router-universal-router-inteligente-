// Run through onboarding.test.ts. Bun's module mocks are process-wide.
import { beforeEach, describe, expect, mock, test } from "bun:test";
import { readFileSync } from "node:fs";
import { renderToStaticMarkup } from "react-dom/server";

import { getFunctionName } from "convex/server";
import { hasRequiredRunCredentials } from "../lib/credential-readiness";
import { listCachedSites } from "../lib/cached-sites";
import type { ProviderKeyMeta } from "../app/(dashboard)/account/provider-keys-card";

type RecentRunFixture = {
  _id: string;
  domain: string;
  status: "queued" | "running" | "completed" | "failed";
};

let auth: { user: { id: string } | null; accessToken?: string };
let storedKeys: ProviderKeyMeta[] = [];
let recentRuns: RecentRunFixture[] = [];
let convexAuthenticated = true;
let cachedSites = listCachedSites();
let catalogError: Error | null = null;
const query = mock(async (reference: unknown, args: Record<string, unknown> = {}) => {
  const name = getFunctionName(reference as Parameters<typeof getFunctionName>[0]);
  if (name === "userCredentials:listForUser") return storedKeys;
  if (name === "cachedSites:list") {
    if (catalogError) throw catalogError;
    return cachedSites;
  }
  if (name === "designRuns:listRecent") return recentRuns.slice(0, Number(args.limit ?? 3));
  throw new Error(`Unexpected query ${name}`);
});
const getConvexClient = mock(() => ({ query }));

mock.module("@workos-inc/authkit-nextjs", () => ({
  withAuth: async () => auth,
}));
mock.module("next/navigation", () => ({
  redirect: (path: string) => {
    throw new Error(`redirect:${path}`);
  },
  useRouter: () => ({ refresh() {}, push() {} }),
}));
mock.module("@/lib/convex-server", () => ({ getConvexClient }));
mock.module("../lib/convex-server", () => ({ getConvexClient }));
mock.module("convex/react", () => ({
  useMutation: () => mock(),
  useQuery: (reference: unknown, args: Record<string, unknown> | "skip") => {
    if (args === "skip") return undefined;
    const name = getFunctionName(reference as Parameters<typeof getFunctionName>[0]);
    if (name === "userCredentials:listForUser") return storedKeys;
    if (name === "designRuns:listRecent") {
      return recentRuns.slice(0, Number(args.limit ?? 3));
    }
    return undefined;
  },
  useConvexAuth: () => ({ isAuthenticated: convexAuthenticated, isLoading: !convexAuthenticated }),
}));

const { ExtractionOnboarding } =
  await import("../components/extraction-onboarding");
const { ExtractionGuide } =
  await import("../components/extraction-guide");
const { ProviderKeysCard } =
  await import("../app/(dashboard)/account/provider-keys-card");
const { AgentCommand } = await import("../app/(dashboard)/agent/agent-command");
const { default: AgentPage } = await import("../app/(dashboard)/agent/page");
const { AgentRecentRunsLoader } = await import(
  "../app/(dashboard)/agent/agent-recent-runs"
);
const { ExportActions } =
  await import("../app/(dashboard)/runs/[slug]/export-actions");

const key = (provider: ProviderKeyMeta["provider"]): ProviderKeyMeta => ({
  provider,
  keySuffix: "demo",
  updatedAt: 1,
});

beforeEach(() => {
  auth = { user: { id: "fixture-user" }, accessToken: "fixture-token" };
  storedKeys = [];
  recentRuns = [];
  convexAuthenticated = true;
  cachedSites = listCachedSites();
  catalogError = null;
  getConvexClient.mockClear();
  query.mockClear();
});

describe("extraction onboarding", () => {
  test("Agent waits for Convex authentication even when provider keys are saved", () => {
    convexAuthenticated = false;
    const html = renderToStaticMarkup(
      <AgentCommand credentialsReady user={{ id: "fixture-user" }} />,
    );
    expect(html).toMatch(/<textarea[^>]*disabled/);
  });
  for (const providers of [
    [],
    ["daytona"],
    ["openai"],
    ["daytona", "openai"],
  ] as ProviderKeyMeta["provider"][][]) {
    test(`server readiness and Account guidance with ${providers.join(" + ") || "no keys"}`, async () => {
      storedKeys = providers.map(key);
      const ready = hasRequiredRunCredentials(storedKeys);
      const html = renderToStaticMarkup(await ExtractionOnboarding());
      expect(getConvexClient).toHaveBeenCalledWith("fixture-token");
      expect(query).toHaveBeenCalledWith(expect.anything(), {});
      expect(html).toContain("Turn a website into a design system");
      expect(html).toContain("Add provider keys");
      expect(html).toContain("Choose a public URL");
      expect(html).toContain("Open the finished design");
      expect(html).toContain('aria-current="step"');
      expect(html.includes("Daytona saved")).toBe(providers.includes("daytona"));
      expect(html.includes("Daytona needed")).toBe(!providers.includes("daytona"));
      expect(html.includes("OpenAI saved")).toBe(providers.includes("openai"));
      expect(html.includes("OpenAI needed")).toBe(!providers.includes("openai"));
      expect(html.includes('href="/agent"')).toBe(ready);
      expect(html.includes("Extract a design system")).toBe(ready);
      expect(html.includes('href="/account#provider-keys"')).toBe(!ready);
      expect(html).toContain('href="/sites"');
      expect(html).toContain("Open an example");
      expect(html).not.toContain("fixture-token");
      expect(html).not.toContain("demo");

      const account = renderToStaticMarkup(
        <ProviderKeysCard keys={storedKeys} credentialsReady={ready} />,
      );
      expect(account).toContain('id="provider-keys"');
      expect(account).toContain(ready ? "Continue to Agent" : "Back to Agent");
      for (const provider of ["daytona", "openai"] as const) {
        expect(account.includes(`id="${provider}-key"`)).toBe(
          !providers.includes(provider),
        );
      }
      if (providers.length === 1) {
        expect(account).toContain(
          `Save your ${providers[0] === "daytona" ? "OpenAI" : "Daytona"} key above`,
        );
      }
    });
  }

  for (const session of [{ user: null }, { user: { id: "fixture-user" } }]) {
    test(`requires an authenticated user and access token: ${JSON.stringify(session)}`, async () => {
      auth = session;
      await expect(ExtractionOnboarding()).rejects.toThrow("redirect:/sign-in");
      expect(getConvexClient).not.toHaveBeenCalled();
    });
  }

  test("Overview can pass saved keys without a second credentials query", async () => {
    storedKeys = [key("daytona")];
    const html = renderToStaticMarkup(
      await ExtractionOnboarding({ keys: storedKeys }),
    );
    expect(getConvexClient).not.toHaveBeenCalled();
    expect(html).toContain("Daytona saved");
    expect(html).toContain("OpenAI needed");
    expect(html).toContain('href="/account#provider-keys"');
    expect(html).not.toContain('href="/agent"');
  });

  test("Overview shows onboarding only without completed runs and hides the empty recent-run list", () => {
    const page = readFileSync(
      new URL("../app/(dashboard)/page.tsx", import.meta.url),
      "utf8",
    );
    expect(page).toContain(
      "{runs.length === 0 ? <ExtractionOnboarding keys={keys} /> : null}",
    );
    expect(page).toContain("<RecentRuns");
    expect(page).toContain('href="/runs"');
    expect(page).toContain("<CachedSites");
    expect(page).not.toContain("EmptyDesignRuns");
    const setup = renderToStaticMarkup(
      <ExtractionGuide credentialsReady={false} />,
    );
    expect(setup).toContain("Open an example");
    expect(setup).toContain("Daytona needed");
    expect(setup).toContain("OpenAI needed");
    expect(setup).not.toContain('href="/agent"');
    const ready = renderToStaticMarkup(<ExtractionGuide credentialsReady />);
    expect(ready).toContain('href="/agent"');
    expect(ready).toContain("Extract a design system");
    expect(ready).toContain("Daytona saved");
    expect(ready).toContain("OpenAI saved");
    expect(ready).toContain("Open an example");
    expect(ready).not.toContain('href="/account#provider-keys"');
  });

  test("the Agent allows URL lookup without keys and explains new extraction requirements", () => {
    for (const ready of [false, true]) {
      const html = renderToStaticMarkup(
        <AgentCommand credentialsReady={ready} user={{ id: "fixture-user" }} />,
      );
      expect(html).not.toContain("download design.md");
      expect(html).not.toContain("Set up provider keys");
      expect(/<textarea[^>]*disabled=""/.test(html)).toBe(false);
      expect(html.includes("Add provider keys")).toBe(!ready);
      expect(html).not.toContain("Cached sites are ready to open.");
      expect(html).not.toContain("Examples");
      expect(html).not.toContain("Recent");
      expect(html).toContain('aria-label="Start extraction"');
    }
  });

  test("the Agent shows three cached-site prompt suggestions and only the last three runs", () => {
    const html = renderToStaticMarkup(
      <AgentCommand
        credentialsReady
        user={{ id: "fixture-user" }}
        cachedSites={[
          { slug: "linear", title: "Linear", url: "https://linear.app" },
          { slug: "stripe", title: "Stripe", url: "https://stripe.com" },
          { slug: "vercel", title: "Vercel", url: "https://vercel.com" },
          { slug: "clerk", title: "Clerk", url: "https://clerk.com" },
        ]}
        exampleSuggestions={[
          { slug: "linear", title: "Linear", url: "https://linear.app" },
          { slug: "stripe", title: "Stripe", url: "https://stripe.com" },
          { slug: "vercel", title: "Vercel", url: "https://vercel.com" },
        ]}
        recentRuns={[
          { id: "newest", domain: "newest.example", status: "running" },
          { id: "middle", domain: "middle.example", status: "completed" },
          { id: "oldest", domain: "oldest.example", status: "failed" },
          { id: "hidden", domain: "hidden.example", status: "queued" },
        ]}
      />,
    );
    expect(html).not.toContain("Examples");
    expect(html).not.toContain('href="/sites/linear"');
    expect(html).toContain("Linear");
    expect(html).toContain("Stripe");
    expect(html).toContain("Vercel");
    expect(html).not.toContain("Clerk");
    expect(html).toContain("Recent");
    expect(html).toContain('href="/runs"');
    expect(html).toContain('href="/runs/newest"');
    expect(html).toContain('href="/runs/oldest"');
    expect(html).not.toContain('href="/runs/hidden"');
  });

  test("Agent loads three random cached-site suggestions and only the last three private runs", async () => {
    recentRuns = [
      { _id: "newest", domain: "newest.example", status: "running" },
      { _id: "middle", domain: "middle.example", status: "completed" },
      { _id: "oldest", domain: "oldest.example", status: "failed" },
      { _id: "hidden", domain: "hidden.example", status: "queued" },
    ];
    const html = renderToStaticMarkup(
      await AgentPage({ searchParams: Promise.resolve({}) }),
    );
    expect(html).not.toContain("Examples");
    expect(html).not.toContain('href="/sites/linear"');
    const suggested = listCachedSites().filter(site => html.includes(`>${site.title}</button>`));
    expect(suggested).toHaveLength(3);
    expect(html).toContain("Recent");
    expect(html).toContain('href="/runs"');

    getConvexClient.mockClear();
    query.mockClear();
    const runs = renderToStaticMarkup(
      await AgentRecentRunsLoader({
        userId: "fixture-user",
        accessToken: "fixture-token",
      }),
    );
    expect(getConvexClient).toHaveBeenCalledWith("fixture-token");
    expect(query.mock.calls.map(([reference, args]) => [
      getFunctionName(reference as Parameters<typeof getFunctionName>[0]),
      args,
    ])).toEqual([
      ["designRuns:listRecent", { userId: "fixture-user", limit: 3 }],
    ]);
    expect(runs).toContain("Recent");
    expect(runs).toContain('href="/runs/newest"');
    expect(runs).toContain("Running");
    expect(runs).toContain('href="/runs/oldest"');
    expect(runs).not.toContain('href="/runs/hidden"');
    expect(runs).not.toContain("hidden.example");
  });

  test("Agent matches and refreshes database-only cached sites instead of the bundled seed", async () => {
    cachedSites = [{
      ...listCachedSites()[0]!,
      slug: "database-only", title: "Database only", url: "https://database-only.example",
    }];
    const page = await AgentPage({ searchParams: Promise.resolve({ refresh: "database-only" }) });
    const expected = { slug: "database-only", title: "Database only", url: "https://database-only.example" };
    expect(page.props.cachedSites).toEqual([expected]);
    expect(page.props.exampleSuggestions).toEqual([expected]);
    expect(page.props.refreshSite).toEqual(expected);
    expect(getConvexClient).toHaveBeenCalledWith("fixture-token");
    expect(query.mock.calls.map(([reference]) => getFunctionName(reference as Parameters<typeof getFunctionName>[0])))
      .toContain("cachedSites:list");
  });

  test("Agent does not advertise bundled sites when the production catalog is empty or unavailable", async () => {
    const previous = process.env.VERCEL_ENV;
    process.env.VERCEL_ENV = "production";
    try {
      cachedSites = [];
      const page = await AgentPage({ searchParams: Promise.resolve({ refresh: listCachedSites()[0]!.slug }) });
      expect(page.props.cachedSites).toEqual([]);
      expect(page.props.exampleSuggestions).toEqual([]);
      expect(page.props.refreshSite).toBeNull();
      catalogError = new Error("Could not find public function cachedSites:list");
      await expect(AgentPage({ searchParams: Promise.resolve({}) })).rejects.toThrow("cachedSites:list");
    } finally {
      if (previous === undefined) delete process.env.VERCEL_ENV;
      else process.env.VERCEL_ENV = previous;
    }
  });

  test("completed runs have a visible, keyboard-accessible design export menu", () => {
    const html = renderToStaticMarkup(
      <ExportActions content="# Fixture" siteName="Fixture" />,
    );
    expect(html).toContain('aria-label="Download"');
    expect(html).toContain('aria-haspopup="menu"');
    const actions = readFileSync(
      new URL(
        "../app/(dashboard)/runs/[slug]/export-actions.tsx",
        import.meta.url,
      ),
      "utf8",
    );
    expect(actions).toContain("Without images");
    expect(actions).toContain("With images");
    expect(actions).toContain(">Copy</DropdownMenuLabel>");
    const shell = readFileSync(
      new URL(
        "../app/(dashboard)/runs/[slug]/run-page-shell.tsx",
        import.meta.url,
      ),
      "utf8",
    );
    expect(shell).toContain("siteName={siteName}");
    expect(shell).toContain("{exportMarkdown ? (");
  });
});
