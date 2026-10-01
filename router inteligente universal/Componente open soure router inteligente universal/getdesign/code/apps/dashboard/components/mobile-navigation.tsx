"use client"

import Link from "next/link"

import { BrandMark } from "@/components/brand-mark"
import { SidebarTrigger, useSidebar } from "@/components/ui/sidebar"

export function MobileNavigation() {
  const { openMobile } = useSidebar()

  return (
    <header className="sticky top-0 z-30 flex shrink-0 items-center gap-3 border-b bg-background px-3 pt-[env(safe-area-inset-top)] md:hidden">
      <SidebarTrigger
        aria-label="Open navigation"
        aria-expanded={openMobile}
        aria-haspopup="dialog"
        className="my-1.5 size-11"
      />
      <Link href="/" className="flex min-h-11 items-center gap-2 text-sm font-semibold">
        <BrandMark size={20} />
        <span>getdesign</span>
      </Link>
    </header>
  )
}
