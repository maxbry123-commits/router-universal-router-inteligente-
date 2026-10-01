# Cached site library

Every signed-in dashboard user can browse and download the same 12 public-site snapshots. They live in the shared Convex `cachedSites` table, with no owner/user ID. Provider keys are not required to read them. Public catalog queries require authentication and return only the curated documents and display metadata. Users cannot modify the catalog: seeding is an internal mutation, callable by deployment tooling rather than browser clients.

Private extraction history remains in the separate, owner-scoped `designRuns` and `designRunArtifacts` tables. **Refresh site** prefills Agent and creates a new private extraction using the requesting user's keys when submitted. It does not publish that run or overwrite the shared catalog.

## Production deployment

The dashboard's checked-in `vercel.json` runs `bun run build:dashboard:vercel` from the repository root. `scripts/build-dashboard.ts` performs these steps in order:

1. Require a production `CONVEX_DEPLOY_KEY` in the Vercel Production environment. A missing, preview or development key stops the build before deployment.
2. Build the dashboard's generated workspace dependencies in order: types, content, tools, agent and SDK. These packages export `dist` files that are absent in a fresh checkout. A dependency failure stops the build before any deployment.
3. Copy Vercel's `WORKOS_CLIENT_ID` into the Convex deployment selected by the production key. Convex reads its own environment when evaluating `auth.config.ts`. A missing Vercel client ID stops the build before any work; a failed copy prevents deployment and seeding.
4. Run `convex deploy` with the dashboard build command and `--cmd-url-env-var-name NEXT_PUBLIC_CONVEX_URL`. This connects the built frontend to the deployment selected by that key and deploys the backend/schema.
5. Run the internal `cachedSites:seed` mutation using the same deployment key. A seed failure fails the Vercel build, preventing publication of the frontend.

Configure `CONVEX_DEPLOY_KEY` with permission to set deployment environment variables, deploy and execute the internal seed function. Set `WORKOS_CLIENT_ID` in Vercel Production, along with the existing dashboard WorkOS and encryption settings. Each production build synchronizes that client ID to Convex before deploying. Configure the client ID separately for development and preview Convex deployments. The deployment key is server-only and is never passed to browser code.

The seed source is `convex/seedData/cached-sites.json`. A seed transaction inserts missing slugs, updates older or changed snapshots, and leaves identical or newer database snapshots untouched. Repeated deployments create no duplicate rows. It never deletes extra catalog entries or touches private runs, credentials or users. No model calls or new captures occur during deployment.

Vercel previews with a Preview Deploy Key deploy an isolated backend and use `--preview-run cachedSites:seed`. Preview builds reject production/development deploy keys. Local builds and previews without a deploy key do not mutate a backend; they can still display the committed bundle if the cached-site functions are not deployed or the catalog is empty. Authentication and network errors are not hidden by this fallback. Production always reads the database and never falls back to the bundle.

Convex's [Vercel deployment guide](https://docs.convex.dev/production/hosting/vercel) documents deployment URL injection and preview seeding. `--preview-run` does not seed production, which is why our production hook explicitly runs the seed after deployment.

## Refresh the source snapshots

From the repository root, with the approved local environment file:

```sh
bun --env-file=apps/dashboard/.env.local scripts/cache-sites.ts
```

This runs three visual extractions concurrently across 12 public sites using Daytona and OpenAI, incurring provider usage. Only completed visual results whose palettes are grounded in source CSS enter the seed catalog. A secret-value check and strict metadata schema run before writing. The script replaces the seed file atomically only after at least ten sites pass; otherwise the previous file remains intact. Intermediate snapshots and the batch report stay in ignored `getdesign-runs/cached-sites/`. Sandboxes follow the existing pipeline's cleanup lifecycle.

Review the generated catalog diff and run the dashboard checks. The next production deployment upserts the new snapshots automatically. For a configured local development backend, `bun x convex dev --once` deploys the schema/functions and `bun x convex run cachedSites:seed` seeds it. Shared snapshots display their capture date and are not presented as live site data.

## Image evidence

Every new seed record requires a hero image and a full-page image, with dimensions and versioned paths. The recapture script writes WebP files to `apps/dashboard/public/cached-sites/<slug>/` and links them in the Markdown. The database seed includes this metadata and those references; Vercel ships the matching files with the frontend. These are curated public-site captures. Private run screenshots stay in owner-scoped Convex storage and are never copied into the public catalog.

The deployment hook checks every seed image's content hash, dimensions, and document reference before starting deployment. Image paths contain content hashes; keep older files when refreshing the catalog so older shared rows can still resolve their images. Every signed-in account receives the same seeded image metadata. There are no provider calls during deployment or when opening the catalog.

Overview cards show real hero screenshots. Detail pages include both captures. **Download with images** saves a ZIP with `design.md` and relative image files for offline use, including Markdown viewers that block data URLs. **Download design.md** embeds the image bytes in the one file. If an image cannot be downloaded, export reports an error instead of silently omitting it.

Legacy rows without a valid hero/full-page image pair are withheld from catalog reads and cards until repaired. The seed restores the complete versioned snapshot for an incomplete curated row even if that row carries a newer timestamp; valid newer snapshots are preserved. This avoids combining old image evidence with a different document or date. Desktop cached pages use the same collapsible right-side gallery as private runs. Mobile pages keep inline previews, and exported files keep their images.
