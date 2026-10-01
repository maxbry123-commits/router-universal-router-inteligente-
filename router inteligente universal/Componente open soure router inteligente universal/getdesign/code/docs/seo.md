# Search indexing and metadata

The marketing site at `https://www.getdesign.app` owns search discovery. Its
homepage and `/design` are canonical, indexable production pages listed in the
sitemap. Preview, development, and custom staging deployments stay blocked from
indexing. `VERCEL_TARGET_ENV` takes precedence over `VERCEL_ENV`; `NODE_ENV` alone
does not enable indexing.

The dashboard uses a site-wide `X-Robots-Tag: noindex, nofollow` header and root
robots metadata. Production robots.txt allows crawling so search engines can
read that header. WorkOS still protects private pages. Publishing a run makes
it accessible by link, not eligible for indexing. Shared-page titles and social
metadata use the anonymous published-run lookup, with request-local caching;
unpublishing closes subsequent metadata reads as well as page reads.

Google explains why blocking crawling prevents it from reading `noindex` in its
[indexing documentation](https://developers.google.com/search/docs/crawling-indexing/block-indexing).

Homepage FAQ answers and FAQ structured data share `HOME_FAQ` in
`apps/web/app/_lib/faq.ts`. Keep answers accurate and visible in the page.
The FAQ adds useful product information; it does not promise a Google rich
result. Google [retired FAQ rich results in May 2026](https://developers.google.com/search/updates#may-2026).

## Local checks

```sh
bun test scripts/seo.test.ts apps/web/test/launch-copy.test.tsx apps/dashboard/tests/public-runs.test.ts
bun run --cwd apps/web typecheck
bun run --cwd apps/dashboard typecheck
VERCEL_ENV=production bun run --cwd apps/web build
SEO_BUILD_ENV=production SEO_WEB_ONLY=1 bun test scripts/seo-build.test.ts
VERCEL_ENV=preview bun run --cwd apps/web build
SEO_BUILD_ENV=preview SEO_WEB_ONLY=1 bun test scripts/seo-build.test.ts
```

Unset `VERCEL_TARGET_ENV` for these examples, or set it to the same environment.
Omit `SEO_WEB_ONLY=1` when checking the documentation site's build too; that
build must match `SEO_BUILD_ENV`.

## After deployment

Check the live sitemap and canonical tags, then submit
`https://www.getdesign.app/sitemap.xml` in the site's Google Search Console
property. Inspect the homepage and `/design` URLs to confirm that Google can
fetch their production HTML. Check a published dashboard URL for its `noindex`
header. Track impressions, clicks, and indexed pages in Search Console; a local
build cannot verify Google's index or measure ranking changes.
