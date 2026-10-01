# dashboard

Authenticated product dashboard (Next.js + WorkOS AuthKit).

## Terms

- **Provider keys** — per-user Daytona and OpenAI keys saved from Settings, stored as ciphertext in Convex. Dashboard runs decrypt them on the server and never fall back to `process.env`.
- **Developer surfaces** — API, CLI, SDK, and Skills. Their docs live on docs.getdesign.app. Settings lists those pages and notes that v1 has no getdesign API key.

- **Cached site** — A curated snapshot of a public site in the shared Convex `cachedSites` table, readable by every signed-in dashboard user. The production deployment seeds this table from the versioned catalog. Opening or downloading it does not run providers. Refresh starts a private extraction using the requesting user's keys; it does not overwrite the shared catalog.
- **Examples** — Dashboard page at `/sites` that lists cached sites. Overview shows the catalog count and a four-site preview that links to this page. Agent shows three random catalog URLs as prompt suggestions under the field.
- **Runs** — Dashboard page at `/runs` that lists the signed-in user's private extractions. Overview shows a six-run preview of completed design files and links here. Agent shows the last three runs plus a link to this page. `/runs/[id]` is one run.
- **Agent** — `/agent` starts a private extraction from a URL. Three random cached-site chips fill the field like prompt suggestions. The last three private runs sit under the field.
- **Public run** — A completed user-owned extraction explicitly published by its owner. `/r/[id]` and its Markdown, JSON, and screenshot endpoints allow anonymous reads without provider usage. Publishing does not add a cached site. Making the run private or deleting it closes subsequent public reads; downloaded copies remain with recipients.
