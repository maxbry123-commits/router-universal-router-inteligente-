import type { Metadata } from "next";
import Link from "next/link"
import { withAuth } from "@workos-inc/authkit-nextjs"
import { redirect } from "next/navigation"
import {
  Breadcrumb,
  BreadcrumbItem,
  BreadcrumbList,
  BreadcrumbPage,
} from "@/components/ui/breadcrumb"
import { buttonVariants } from "@/components/ui/button"
import { CachedSites } from "@/components/cached-sites"
import { ExtractionOnboarding } from "@/components/extraction-onboarding"
import { RecentRuns } from "@/components/recent-runs"
import { loadCachedSites } from "@/lib/cached-sites"
import { getConvexClient } from "@/lib/convex-server"
import {
  loadRecentRunPreviews,
  OVERVIEW_RUN_DISPLAY_LIMIT,
  OVERVIEW_RUN_QUERY_LIMIT,
} from "@/lib/design-run-preview"
import { api } from "@convex/_generated/api"

const EXAMPLE_PREVIEW_COUNT = 4

export const metadata: Metadata = { title: "Overview" };

export default async function Page() {
  const { user, accessToken } = await withAuth()

  if (!user || !accessToken) {
    redirect("/sign-in")
  }

  const convex = getConvexClient(accessToken)
  const [runs, summary, sites, keys] = await Promise.all([
    loadRecentRunPreviews(convex, user.id, {
      queryLimit: OVERVIEW_RUN_QUERY_LIMIT,
      requireDesignFile: true,
      limit: OVERVIEW_RUN_DISPLAY_LIMIT,
    }),
    convex.query(api.designRuns.summarizeForUser, {
      userId: user.id,
    }),
    loadCachedSites(accessToken),
    convex.query(api.userCredentials.listForUser, {}),
  ])

  return (
    <>
      <header className="flex h-14 shrink-0 items-center gap-2 border-b px-4">
        <Breadcrumb>
          <BreadcrumbList>
            <BreadcrumbItem>
              <BreadcrumbPage>Overview</BreadcrumbPage>
            </BreadcrumbItem>
          </BreadcrumbList>
        </Breadcrumb>
        {runs.length > 0 ? (
          <Link
            href="/agent"
            className={buttonVariants({
              size: "lg",
              className: "ml-auto",
            })}
          >
            Extract
          </Link>
        ) : null}
      </header>

      <div className="flex flex-1 flex-col gap-6 p-6">
        <section aria-label="Overview stats" className="grid grid-cols-2 gap-3 sm:grid-cols-4">
          <Link
            href="/sites"
            className="rounded-xl border px-4 py-3 transition-colors hover:bg-muted/30"
          >
            <p className="text-xs text-muted-foreground">Cached sites</p>
            <p className="mt-1 text-lg font-medium tabular-nums">{sites.length}</p>
          </Link>
          <Link
            href="/runs"
            className="rounded-xl border px-4 py-3 transition-colors hover:bg-muted/30"
          >
            <p className="text-xs text-muted-foreground">Your runs</p>
            <p className="mt-1 text-lg font-medium tabular-nums">{summary.total}</p>
          </Link>
          <div className="rounded-xl border px-4 py-3">
            <p className="text-xs text-muted-foreground">Completed</p>
            <p className="mt-1 text-lg font-medium tabular-nums">{summary.completed}</p>
          </div>
          <div className="rounded-xl border px-4 py-3">
            <p className="text-xs text-muted-foreground">Failed</p>
            <p className="mt-1 text-lg font-medium tabular-nums">{summary.failed}</p>
          </div>
        </section>

        {runs.length === 0 ? <ExtractionOnboarding keys={keys} /> : null}

        <RecentRuns runs={runs} preview />

        <CachedSites sites={sites} previewCount={EXAMPLE_PREVIEW_COUNT} />
      </div>
    </>
  )
}
