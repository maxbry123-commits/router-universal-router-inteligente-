import type { Metadata } from "next";
import { Suspense } from "react";
import { withAuth } from "@workos-inc/authkit-nextjs";
import { redirect } from "next/navigation";

import { hasCachedSiteImages } from "@convex/lib/cachedSiteSchema";
import { AgentRecentRunsSkeleton } from "@/components/dashboard-skeletons";
import { loadCachedSites, pickRandomItems } from "@/lib/cached-sites";

import { AgentCommand } from "./agent-command";
import { AgentRecentRunsLoader } from "./agent-recent-runs";

export const metadata: Metadata = { title: "Agent" };

export default async function AgentPage({ searchParams }: {
  searchParams: Promise<{ refresh?: string }>;
}) {
  const { accessToken, user } = await withAuth();

  if (!user || !accessToken) {
    redirect("/sign-in");
  }

  const [{ refresh }, cachedSites] = await Promise.all([
    searchParams,
    loadCachedSites(accessToken),
  ]);
  const catalog = cachedSites.filter(hasCachedSiteImages).map(({ slug, title, url }) => ({
    slug,
    title,
    url,
  }));
  const refreshSite = catalog.find((site) => site.slug === refresh) ?? null;

  return (
    <AgentCommand
      key={refreshSite?.slug ?? "agent"}
      cachedSites={catalog}
      exampleSuggestions={pickRandomItems(catalog, 3)}
      refreshSite={refreshSite}
      user={{ id: user.id, email: user.email ?? undefined }}
    >
      <Suspense fallback={<AgentRecentRunsSkeleton />}>
        <AgentRecentRunsLoader userId={user.id} accessToken={accessToken} />
      </Suspense>
    </AgentCommand>
  );
}
