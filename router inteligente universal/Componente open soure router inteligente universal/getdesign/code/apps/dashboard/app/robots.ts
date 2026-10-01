import type { MetadataRoute } from "next";

export default function robots(): MetadataRoute.Robots {
  const production = (process.env.VERCEL_TARGET_ENV ?? process.env.VERCEL_ENV) === "production";
  // Crawlers must fetch production URLs to see the site-wide noindex header.
  // Private pages remain protected by WorkOS; public runs remain unindexed.
  return { rules: production
    ? { userAgent: "*", allow: "/" }
    : { userAgent: "*", disallow: "/" }
  };
}
