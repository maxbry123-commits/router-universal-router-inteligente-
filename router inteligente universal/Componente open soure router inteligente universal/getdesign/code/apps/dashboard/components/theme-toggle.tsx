"use client"

import { useTheme } from "next-themes"
import { HugeiconsIcon } from "@hugeicons/react"
import { Moon02Icon, Sun01Icon } from "@hugeicons/core-free-icons"

import { nextColorTheme } from "@/lib/theme"
import {
  SidebarMenu,
  SidebarMenuButton,
  SidebarMenuItem,
} from "@/components/ui/sidebar"

export function ThemeToggle() {
  const { setTheme } = useTheme()

  return (
    <SidebarMenu>
      <SidebarMenuItem>
        <SidebarMenuButton
          tooltip="Toggle theme"
          aria-label="Toggle theme"
          aria-keyshortcuts="d"
          onClick={() =>
            setTheme(nextColorTheme(document.documentElement.classList))
          }
        >
          <HugeiconsIcon
            icon={Moon02Icon}
            strokeWidth={1.75}
            className="size-[18px] shrink-0 dark:hidden"
          />
          <HugeiconsIcon
            icon={Sun01Icon}
            strokeWidth={1.75}
            className="hidden size-[18px] shrink-0 dark:block"
          />
          <span className="flex-1 text-left text-sm">Theme</span>
          <kbd className="font-mono text-xs opacity-60">D</kbd>
        </SidebarMenuButton>
      </SidebarMenuItem>
    </SidebarMenu>
  )
}
