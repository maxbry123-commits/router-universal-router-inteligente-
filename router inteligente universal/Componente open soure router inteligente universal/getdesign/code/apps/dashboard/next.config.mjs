import { buildAnalyticsConfig } from "@getdesign/analytics/config"

const DOCS_BASE_URL = "https://docs.getdesign.app"
const SUPPORT_URL = "https://github.com/MohtashamMurshid/getdesign/issues"

/** @type {import('next').NextConfig} */
const nextConfig = {
  env: { NEXT_PUBLIC_POSTHOG_CONFIG: buildAnalyticsConfig(process.env) },
  // Shared runs are accessible by link; the dashboard is not a search index.
  async headers() {
    return [{
      source: "/:path*",
      headers: [{ key: "X-Robots-Tag", value: "noindex, nofollow" }],
    }]
  },
  // Exact paths only. `/api` must not use `:path*`, or credential and run
  // route handlers under `app/api/` would be redirected to docs.
  async redirects() {
    return [
      { source: "/api", destination: `${DOCS_BASE_URL}/surfaces/api`, permanent: true },
      { source: "/cli", destination: `${DOCS_BASE_URL}/surfaces/cli`, permanent: true },
      { source: "/sdk", destination: `${DOCS_BASE_URL}/surfaces/sdk`, permanent: true },
      { source: "/skills", destination: `${DOCS_BASE_URL}/surfaces/skill`, permanent: true },
      { source: "/docs", destination: DOCS_BASE_URL, permanent: true },
      { source: "/support", destination: SUPPORT_URL, permanent: true },
    ]
  },
}

export default nextConfig
