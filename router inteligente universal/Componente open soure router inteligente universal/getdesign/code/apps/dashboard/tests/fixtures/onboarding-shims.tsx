import type { ComponentProps } from "react";
import { getFunctionName } from "convex/server";
import { ExtractionGuide } from "../../components/extraction-guide";
import { hasRequiredRunCredentials } from "../../lib/credential-readiness";
import { getCachedSite, listCachedSites } from "../../lib/cached-sites";
import { parseDesignMd } from "@convex/lib/designMdPreview";
import { fixture, navigate, refresh } from "./onboarding-state";

function fixtureRunPreviews() {
  if (!fixture.populated) return [];
  const parsed = parseDesignMd(fixture.markdown);
  return [
    {
      slug: "fixture-completed-run",
      domain: "example.test",
      status: "completed" as const,
      title: parsed.title,
      theme: parsed.theme,
      accent: parsed.accent,
      image: null,
      textOnly: false,
      visibility: "public" as const,
    },
    {
      slug: "fixture-running-run",
      domain: "linear.app",
      status: "running" as const,
      title: "linear.app",
      theme: "",
      accent: "#888888",
      image: null,
      textOnly: false,
      visibility: "private" as const,
    },
    {
      slug: "fixture-failed-run",
      domain: "stripe.com",
      status: "failed" as const,
      title: "stripe.com",
      theme: "",
      accent: "#888888",
      image: null,
      textOnly: false,
      visibility: "private" as const,
    },
  ];
}

export default function Link({
  href,
  children,
  ...props
}: ComponentProps<"a">) {
  return (
    <a
      {...props}
      href={href}
      onClick={(event) => {
        event.preventDefault();
        navigate(href ?? "/");
      }}
    >
      {children}
    </a>
  );
}

export function useRouter() {
  return { refresh, push: navigate };
}
export function redirect(path: string): never {
  throw new Error(`Unexpected fixture redirect: ${path}`);
}
export function notFound(): never {
  throw new Error("notFound");
}
export async function withAuth() {
  return { user: { id: "fixture-user" }, accessToken: "fixture-token" };
}
export function ExtractionOnboarding() {
  return (
    <ExtractionGuide
      credentialsReady={hasRequiredRunCredentials(fixture.keys)}
      keys={fixture.keys}
    />
  );
}
export function useMutation() {
  return async () => "fixture-completed-run";
}
export function useConvexAuth() {
  return { isAuthenticated: true, isLoading: false };
}
export function useQuery(
  reference: Parameters<typeof getFunctionName>[0],
  args: Record<string, unknown> | "skip" = {},
) {
  if (args === "skip") return undefined;
  switch (getFunctionName(reference)) {
    case "userCredentials:listForUser":
      return fixture.keys;
    case "designRuns:listRecent":
      return fixture.populated
        ? [
            {
              _id: "fixture-completed-run",
              domain: "example.test",
              status: "completed",
            },
            {
              _id: "fixture-running-run",
              domain: "linear.app",
              status: "running",
            },
            {
              _id: "fixture-failed-run",
              domain: "stripe.com",
              status: "failed",
            },
          ]
        : [];
    case "cachedSites:list":
      return listCachedSites();
    default:
      return [];
  }
}
export function useConvex() {
  return { query: async () => null };
}
export function getConvexClient() {
  return {
    async query(
      reference: Parameters<typeof getFunctionName>[0],
      args: Record<string, unknown> = {},
    ) {
      switch (getFunctionName(reference)) {
        case "designRuns:listRecent":
          return fixture.populated
            ? [
                {
                  _id: "fixture-completed-run",
                  domain: "example.test",
                  status: "completed",
                },
                {
                  _id: "fixture-running-run",
                  domain: "linear.app",
                  status: "running",
                },
                {
                  _id: "fixture-failed-run",
                  domain: "stripe.com",
                  status: "failed",
                },
              ]
            : [];
        case "designRuns:listRecentPreviews": {
          const previews = fixtureRunPreviews();
          if (args.requireDesignFile) {
            return previews
              .filter((run) => run.status === "completed")
              .slice(0, Number(args.displayLimit ?? previews.length));
          }
          return previews.slice(0, Number(args.limit ?? previews.length));
        }
        case "designRuns:summarizeForUser":
          return fixture.populated
            ? { total: 3, completed: 1, failed: 1, active: 1 }
            : { total: 0, completed: 0, failed: 0, active: 0 };
        case "designRuns:getPage":
          return {
            run: {
              _id: "fixture-completed-run",
              domain: "example.test",
              status: "completed",
              url: "https://example.test",
              mode: "visual",
            },
            artifacts: { markdown: fixture.markdown },
            tiles: [],
          };
        case "designRunArtifacts:getForRun":
          return { markdown: fixture.markdown };
        case "designRunArtifacts:getTileUrls":
          return [];
        case "userCredentials:listForUser":
          return fixture.keys;
        case "cachedSites:list":
          return listCachedSites();
        case "cachedSites:get":
          return getCachedSite(String(args.slug));
        default:
          throw new Error("Unexpected query in local fixture");
      }
    },
  };
}

