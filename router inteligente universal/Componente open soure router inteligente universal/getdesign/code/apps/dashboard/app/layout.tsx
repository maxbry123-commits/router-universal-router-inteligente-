import type { Metadata } from "next"
import { AnalyticsConsent } from "@getdesign/analytics/react"
import { Geist, Geist_Mono } from "next/font/google"
import { AuthKitProvider } from "@workos-inc/authkit-nextjs/components"

import "@radix-ui/themes/styles.css"
import "@workos-inc/widgets/base.css"
import "@workos-inc/widgets/styles.css"
import "./globals.css"
import { DashboardConvexProvider } from "@/components/convex-provider"
import { ThemeProvider } from "@/components/theme-provider"
import { cn } from "@/lib/utils";

const geist = Geist({subsets:['latin'],variable:'--font-sans'})

const fontMono = Geist_Mono({
  subsets: ["latin"],
  variable: "--font-mono",
})

export const metadata: Metadata = {
  title: { default: "Dashboard · getdesign", template: "%s · getdesign" },
  description: "Extract website design systems, explore cached examples, and manage your design runs with getdesign.",
  metadataBase: new URL("https://dashboard.getdesign.app"),
  robots: { index: false, follow: false },
  applicationName: "getdesign",
  appleWebApp: { title: "getdesign", capable: false },
  referrer: "no-referrer",
}

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode
}>) {
  return (
    <html
      lang="en"
      suppressHydrationWarning
      className={cn("antialiased", fontMono.variable, "font-sans", geist.variable)}
    >
      <body>
        <AuthKitProvider>
          <DashboardConvexProvider>
            <ThemeProvider>{children}</ThemeProvider>
          </DashboardConvexProvider>
        </AuthKitProvider>
        <AnalyticsConsent surface="dashboard" />
      </body>
    </html>
  )
}
