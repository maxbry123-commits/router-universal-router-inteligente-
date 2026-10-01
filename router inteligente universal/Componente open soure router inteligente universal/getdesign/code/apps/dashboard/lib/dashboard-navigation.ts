import type { IconSvgElement } from "@hugeicons/react"
import {
  DashboardBrowsingIcon,
  SparklesIcon,
  Clock01Icon,
  GridViewIcon,
  BookOpen02Icon,
  Settings05Icon,
} from "@hugeicons/core-free-icons"
import { docsUrl } from "@getdesign/content"

export type NavItem = {
  title: string
  url: string
  icon: IconSvgElement
  keywords?: string
  external?: boolean
}

export const NAV_MAIN: NavItem[] = [
  {
    title: "Overview",
    url: "/",
    icon: DashboardBrowsingIcon,
    keywords: "home dashboard",
  },
  { title: "Agent", url: "/agent", icon: SparklesIcon },
  {
    title: "Runs",
    url: "/runs",
    icon: Clock01Icon,
    keywords: "recent history extractions",
  },
  {
    title: "Examples",
    url: "/sites",
    icon: GridViewIcon,
    keywords: "cached sites catalog library",
  },
]

export const NAV_SECONDARY: NavItem[] = [
  {
    title: "Docs",
    url: docsUrl(),
    icon: BookOpen02Icon,
    keywords: "documentation help support api cli sdk skill surfaces",
    external: true,
  },
  {
    title: "Settings",
    url: "/account",
    icon: Settings05Icon,
    keywords: "account provider keys",
  },
]

export const NAV_COMMANDS = [...NAV_MAIN, ...NAV_SECONDARY]

export function matchesNavigation(item: NavItem, query: string) {
  const text = `${item.title} ${item.url} ${item.keywords ?? ""}`.toLowerCase()
  return query
    .trim()
    .toLowerCase()
    .split(/\s+/)
    .every((word) => text.includes(word))
}

export function navItemHint(item: NavItem) {
  if (!item.external) return item.url
  try {
    return new URL(item.url).host
  } catch {
    return item.url
  }
}

export function navigateNavItem(
  item: NavItem,
  actions: { push: (url: string) => void; open: (url: string) => void },
) {
  if (item.external) {
    actions.open(item.url)
    return
  }
  actions.push(item.url)
}
