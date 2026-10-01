import { describe, expect, test } from "bun:test"
import { renderToStaticMarkup } from "react-dom/server"

import { ThemeProvider } from "../components/theme-provider"
import { ThemeToggle } from "../components/theme-toggle"
import { SidebarProvider } from "../components/ui/sidebar"

import { nextColorTheme } from "./theme"

describe("nextColorTheme", () => {
  test("flips the document class between light and dark", () => {
    expect(nextColorTheme({ contains: (token) => token === "dark" })).toBe(
      "light",
    )
    expect(nextColorTheme({ contains: () => false })).toBe("dark")
  })
})

describe("ThemeToggle", () => {
  test("renders a labeled control that advertises the D shortcut", () => {
    const html = renderToStaticMarkup(
      <ThemeProvider defaultTheme="light">
        <SidebarProvider>
          <ThemeToggle />
        </SidebarProvider>
      </ThemeProvider>,
    )

    expect(html).toContain('aria-label="Toggle theme"')
    expect(html).toContain('aria-keyshortcuts="d"')
    expect(html).toContain("Theme")
    expect(html).toContain(">D</kbd>")
  })
})
