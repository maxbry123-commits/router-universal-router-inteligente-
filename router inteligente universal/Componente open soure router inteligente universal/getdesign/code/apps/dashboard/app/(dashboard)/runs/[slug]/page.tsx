import type { Metadata } from "next";
import { withDesignImages } from "@getdesign/tools/render"
import { notFound, redirect } from "next/navigation"
import { withAuth } from "@workos-inc/authkit-nextjs"
import { DesignDocument } from "@/components/design-document"
import { getConvexClient } from "@/lib/convex-server"
import { artifactSiteName, runPageTitle } from "@/lib/design-run-preview"
import { toRunState } from "@/lib/runs-store"
import { api } from "@convex/_generated/api"
import type { Id } from "@convex/_generated/dataModel"
import { RunPageShell } from "./run-page-shell"

export const metadata: Metadata = { title: "Design run" };

export default async function RunPage({
  params,
}: {
  params: Promise<{ slug: string }>
}) {
  const { slug } = await params
  const { user, accessToken } = await withAuth()

  if (!user) {
    redirect("/sign-in")
  }

  const convex = getConvexClient(accessToken)
  const page = await convex.query(api.designRuns.getPage, {
    id: slug as Id<"designRuns">,
    userId: user.id,
  })

  if (!page) notFound()

  const { run, artifacts, tiles } = page
  const runState = toRunState(run)

  const storedContent =
    runState.status === "completed" && typeof artifacts.markdown === "string"
      ? artifacts.markdown
      : null

  const content = storedContent && runState.mode !== "text_only" && !storedContent.includes("![Captured page tile")
    ? withDesignImages(storedContent, tiles.filter(tile => tile.url).map((tile, index) => ({ url: tile.url!, alt: `Captured page tile ${index + 1}` })))
    : storedContent

  const markdownContent = content ? (
    <DesignDocument content={content} imagesInGallery />
  ) : null

  const siteName = runPageTitle({
    domain: typeof run.domain === "string" ? run.domain : undefined,
    url: runState.url,
    siteName: runState.siteName,
    markdown: storedContent,
    crawlSiteName: artifactSiteName(artifacts.crawl),
    docSiteName: artifactSiteName(artifacts.doc),
  })

  return (
    <RunPageShell
      key={slug}
      runId={slug}
      siteName={siteName}
      userId={user.id}
      isPublic={run.visibility === "public"}
      initialTiles={tiles}
      totalExpected={runState.tiles}
      exportMarkdown={content}
      markdownContent={markdownContent}
      runState={markdownContent ? null : runState}
    />
  )
}
