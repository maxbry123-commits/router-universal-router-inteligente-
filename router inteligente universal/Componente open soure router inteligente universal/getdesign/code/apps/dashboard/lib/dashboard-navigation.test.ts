import { describe, expect, test } from "bun:test"
import { existsSync } from "node:fs"
import path from "node:path"
import { docsUrl, SITE_GITHUB_URL } from "@getdesign/content"
import {
  NAV_COMMANDS,
  NAV_MAIN,
  NAV_SECONDARY,
  matchesNavigation,
  navItemHint,
  navigateNavItem,
} from "./dashboard-navigation"
import { isApplePlatform, isNavigationShortcut } from "./navigation-shortcuts"

const dashboardPages = path.join(import.meta.dir, "../app/(dashboard)")

describe("dashboard navigation commands", () => {
  test("keeps product pages internal and sends docs off-site", () => {
    expect(NAV_COMMANDS).toEqual([...NAV_MAIN, ...NAV_SECONDARY])
    expect(NAV_MAIN.map((item) => item.title)).toEqual([
      "Overview",
      "Agent",
      "Runs",
      "Examples",
    ])
    expect(NAV_SECONDARY.map((item) => item.title)).toEqual([
      "Docs",
      "Settings",
    ])
    expect(new Set(NAV_COMMANDS.map((item) => item.url)).size).toBe(
      NAV_COMMANDS.length,
    )
    for (const item of NAV_COMMANDS) {
      if (item.external) {
        expect(item.url.startsWith("https://")).toBe(true)
        continue
      }
      expect(item.url.startsWith("/")).toBe(true)
      expect(
        existsSync(
          path.join(dashboardPages, item.url.replace(/^\//, ""), "page.tsx"),
        ),
      ).toBe(true)
    }
  })

  test("blank searches show all commands", () => {
    expect(
      NAV_COMMANDS.filter((item) => matchesNavigation(item, "  ")),
    ).toEqual(NAV_COMMANDS)
  })

  test("routes SDK and API searches to Docs", () => {
    expect(
      NAV_COMMANDS.filter((item) => matchesNavigation(item, " sDk ")).map(
        (item) => item.url,
      ),
    ).toEqual([docsUrl()])
    expect(
      NAV_COMMANDS.filter((item) => matchesNavigation(item, "api")).map(
        (item) => item.url,
      ),
    ).toEqual([docsUrl()])
  })

  test("matches routes and multiple keyword tokens", () => {
    for (const query of [
      "/account",
      "provider keys",
      "keys settings",
      "ACCOUNT",
    ]) {
      expect(
        NAV_COMMANDS.filter((item) => matchesNavigation(item, query)).map(
          (item) => item.url,
        ),
      ).toEqual(["/account"])
    }
    expect(
      NAV_COMMANDS.filter((item) => matchesNavigation(item, "cached sites")).map(
        (item) => item.url,
      ),
    ).toEqual(["/sites"])
    expect(
      NAV_COMMANDS.filter((item) => matchesNavigation(item, "recent")).map(
        (item) => item.url,
      ),
    ).toEqual(["/runs"])
  })

  test("unmatched text returns no commands", () => {
    expect(
      NAV_COMMANDS.filter((item) => matchesNavigation(item, "no-such-page")),
    ).toEqual([])
  })

  test("opens external destinations instead of pushing in-app routes", () => {
    const pushed: string[] = []
    const opened: string[] = []
    const actions = {
      push: (url: string) => {
        pushed.push(url)
      },
      open: (url: string) => {
        opened.push(url)
      },
    }
    navigateNavItem(
      { title: "Agent", url: "/agent", icon: NAV_MAIN[1]!.icon },
      actions,
    )
    navigateNavItem(
      {
        title: "Docs",
        url: docsUrl(),
        icon: NAV_SECONDARY[0]!.icon,
        external: true,
      },
      actions,
    )
    expect(pushed).toEqual(["/agent"])
    expect(opened).toEqual([docsUrl()])
    expect(navItemHint({ title: "Docs", url: docsUrl(), icon: NAV_SECONDARY[0]!.icon, external: true })).toBe(
      "docs.getdesign.app",
    )
  })
})

describe("retired surface routes", () => {
  test("redirect exact dashboard docs pages to the docs site", async () => {
    const { default: config } = await import("../next.config.mjs")
    if (!config.redirects) throw new Error("next.config is missing redirects")
    const redirects = await config.redirects()
    const bySource = Object.fromEntries(
      redirects.map((redirect) => [redirect.source, redirect]),
    )
    expect(bySource["/api"]).toEqual({
      source: "/api",
      destination: docsUrl("/surfaces/api"),
      permanent: true,
    })
    expect(bySource["/cli"]).toEqual({
      source: "/cli",
      destination: docsUrl("/surfaces/cli"),
      permanent: true,
    })
    expect(bySource["/sdk"]).toEqual({
      source: "/sdk",
      destination: docsUrl("/surfaces/sdk"),
      permanent: true,
    })
    expect(bySource["/skills"]).toEqual({
      source: "/skills",
      destination: docsUrl("/surfaces/skill"),
      permanent: true,
    })
    expect(bySource["/docs"]).toEqual({
      source: "/docs",
      destination: docsUrl(),
      permanent: true,
    })
    expect(bySource["/support"]).toEqual({
      source: "/support",
      destination: `${SITE_GITHUB_URL}/issues`,
      permanent: true,
    })
    expect(redirects.some((redirect) => redirect.source.includes(":path"))).toBe(
      false,
    )
  })
})

describe("navigation shortcuts", () => {
  const event = {
    key: "k",
    metaKey: true,
    ctrlKey: false,
    altKey: false,
    shiftKey: false,
    repeat: false,
    isComposing: false,
    defaultPrevented: false,
  }

  test("supports Cmd+K and Ctrl+K", () => {
    expect(isNavigationShortcut(event, "k")).toBe(true)
    expect(
      isNavigationShortcut({ ...event, metaKey: false, ctrlKey: true }, "k"),
    ).toBe(true)
  })

  test("normalizes the key and leaves the sidebar shortcut distinct", () => {
    expect(isNavigationShortcut({ ...event, key: "K" }, "k")).toBe(true)
    expect(isNavigationShortcut({ ...event, key: "b" }, "k")).toBe(false)
    expect(isNavigationShortcut({ ...event, key: "b" }, "b")).toBe(true)
  })

  for (const flag of [
    "altKey",
    "shiftKey",
    "repeat",
    "isComposing",
    "defaultPrevented",
  ] as const) {
    test(`ignores ${flag}`, () => {
      expect(isNavigationShortcut({ ...event, [flag]: true }, "k")).toBe(false)
    })
  }

  test("leaves unmodified K alone", () => {
    expect(isNavigationShortcut({ ...event, metaKey: false }, "k")).toBe(false)
  })

  test("shows the Mac shortcut only on Apple platforms", () => {
    for (const platform of ["MacIntel", "iPhone", "iPad"])
      expect(isApplePlatform(platform)).toBe(true)
    for (const platform of ["Win32", "Linux x86_64", ""])
      expect(isApplePlatform(platform)).toBe(false)
  })
})
