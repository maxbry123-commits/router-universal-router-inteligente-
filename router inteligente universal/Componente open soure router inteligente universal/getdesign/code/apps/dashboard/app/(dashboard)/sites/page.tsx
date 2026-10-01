import type { Metadata } from "next";
import { withAuth } from "@workos-inc/authkit-nextjs"
import { redirect } from "next/navigation"

import { CachedSites } from "@/components/cached-sites"
import { loadCachedSites } from "@/lib/cached-sites"
import {
  Breadcrumb,
  BreadcrumbItem,
  BreadcrumbList,
  BreadcrumbPage,
} from "@/components/ui/breadcrumb"

export const metadata: Metadata = { title: "Examples" };

export default async function SitesPage() {
  const { user, accessToken } = await withAuth()

  if (!user || !accessToken) {
    redirect("/sign-in")
  }

  const sites = await loadCachedSites(accessToken)

  return (
    <>
      <header className="flex h-14 shrink-0 items-center gap-2 border-b px-4">
        <Breadcrumb>
          <BreadcrumbList>
            <BreadcrumbItem>
              <BreadcrumbPage>Examples</BreadcrumbPage>
            </BreadcrumbItem>
          </BreadcrumbList>
        </Breadcrumb>
      </header>
      <div className="flex flex-1 flex-col gap-6 p-6">
        <CachedSites sites={sites} />
      </div>
    </>
  )
}
