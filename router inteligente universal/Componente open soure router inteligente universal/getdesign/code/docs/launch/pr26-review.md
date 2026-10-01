# PR 26 launch review

Reviewed on 2026-09-12, starting from `39302be0ffa99bcc2318312cf4bdf40f94cd062d`.

Implementation commits `3da2c2f` and `0d1380d` were pushed to PR 26.

## Findings and fixes

1. **Run ownership was not authenticated in Convex.** Public run and artifact functions compared records with a caller-supplied user ID. Anonymous callers or a different signed-in user could supply the owner's ID to read runs, obtain artifact URLs, request uploads, and mutate results. All entry points now check the WorkOS token identity before accessing data. A regression suite reproduced 22 unauthorized operations before the fix and rejects all of them afterward. The dashboard now forwards access tokens from its Overview and run server pages and authenticates browser subscriptions and mutations through `ConvexProviderWithAuth`. Client queries wait for authentication.
2. **Concurrent requests could repeat a paid step.** Two tabs could both pass the initial step-status query and start capture or synthesis. `beginStep` now claims the step in a Convex mutation, returning false when it is already running or finished. The losing request returns 409 without marking the active run failed. If a crashed server leaves a claim running, the failure screen offers an explicit “Start new run” action with a provider-usage explanation. This creates a separate owned run linked through `rerunOf`, preserving the original history and preventing its late writes from corrupting the replacement. Navigating to the new run resets the client pipeline state.
3. **Downstream HTTP requests could bypass capture failure.** A direct describe/synthesize/render request did not check its prerequisites. The routes now require successful capture or explicit persisted text-only continuation, plus the relevant completed preceding steps.
4. **Late artifacts could remain invisible.** The dashboard recorded a completed step as fetched before its subscription had returned data. It now derives artifacts from the current query result. Screenshot URLs are matched by filename so a missing URL cannot shift subsequent tiles.
5. **Animated content could prevent readiness indefinitely.** Cursor returned ready content with changing text and geometry signatures. Readiness now requires two consecutive ready observations; a gate button still needs an unchanged signature and safe coordinates before a click. A reappearing loader resets readiness, and the pre-screenshot check still rejects blockers.

The dashboard environment example now lists the required WorkOS, Convex and encryption settings. The onboarding browser fixture explicitly disables analytics configuration instead of referencing an undefined `process` global. Native keyboard checks allow time for the modal focus guards to restore focus.

## Local verification

- Frozen dependency install passed with Bun 1.4.0 and Node 22.22.3. Built workspace declarations before checks.
- Final full suite: 261 passed, zero failures. Its 39 build-dependent SEO cases were run separately with the preview build configuration.
- Marketing and docs preview builds passed. The separate rendered SEO suite passed all 39 cases against those builds.
- The dashboard production build passed using the supplied local configuration.
- All 14 workspace typechecks passed. Dashboard typechecking also passed after the final route and artifact changes.
- Targeted dashboard ESLint and `git diff --check` passed.
- Native Chromium command-menu fixture: 67 checks passed, no skipped keyboard checks. Includes Cmd/Ctrl+K, Tab/Shift+Tab containment, Enter/Space activation, focus restoration and all nine destinations.
- Native Chromium onboarding fixture: key save/removal, Agent readiness, native link/form activation, run navigation and a real `design.md` download to disk passed. Completed-run layouts had no horizontal overflow at 320, 390, 768 and 1280 pixels.
- Live Daytona/Chromium fixtures: ordinary content, a timed loading overlay and an explicit intro gate each produced two capture tiles. The gate was clicked once through Computer Use, and the resulting screenshot shows the underlying page. Sandboxes were deleted afterward.

The browser fixtures use dummy data. They do not establish real credential persistence or authenticated dashboard extraction.

## Launch status

The full 20-brand sweep passed 18 visual extractions and CSS-grounding checks. Cursor initially failed because animated content prevented an identical readiness signature; its separate retry after the fix passed. The combined result is **19 of 20 passed**. OpenAI's homepage returned HTTP 403 during the initial HTML fetch, before capture or model calls. This external failure remains. The initial sweep's median duration was 94.8 seconds, above the aspirational 90-second target.

Results are in `getdesign-runs/brand-smoke/pr26-review/summary-final.json`. The original sweep and Cursor retry are retained separately. `review.html` in the same directory contains the 20 palettes, source links, generated files and a downloadable human-review JSON form. All human ratings remain pending. The 18-of-20 primary-color requirement is a human review gate; CSS grounding alone does not satisfy it.

WorkOS's hosted sign-in page loaded with the supplied configuration. With explicit approval, temporary verified users with random passwords and non-deliverable email addresses were created through WorkOS. Password authentication succeeded, and genuine WorkOS sessions were sealed with the installed AuthKit cookie format for native Chromium. The initial check verified authenticated dashboard behavior using that sealed session. A subsequent native Chromium check completed the real hosted email/password form and returned through `/auth/callback` (HTTP 307) into the dashboard, without injecting a session cookie. No email authentication or verification flow was invoked.

The real Account page returned 200 with empty provider-key metadata. Both supplied provider keys saved through the UI with HTTP 200, persisted across refresh, and enabled Agent. Credential deletion returned 200; the final account's metadata query confirmed zero remaining keys. The initial account check had no browser errors.

A signed-in `https://example.com` run successfully created a run and completed crawl and CSS extraction. Capture failed with `protected_gate`: the browser reported a login, consent, age, payment or verification gate. The pipeline stopped as intended, without clicking the gate or implicitly selecting text-only mode. That attempt produced no download. A subsequent run against `https://linear.app` completed all six stages (crawl, capture, extract, describe, synthesize and render) with HTTP 200. The hosted-login browser downloaded `getdesign-runs/pr26-browser/hosted-account-design.md` (13,355 bytes); content checks confirmed Linear design content, palette and typography sections, and no text-only banner. No supplied environment values appeared in the file. The browser reported zero page errors. The sanitized check record is `getdesign-runs/pr26-browser/hosted-account-report.json`. This completes the authenticated extraction/download verification against the local PR dashboard and configured remote providers. Test runs were soft-deleted using the existing run deletion mutation; this retains records and any stored artifacts. Temporary WorkOS users were deleted after testing.

Review artifacts are under `getdesign-runs/`, which is ignored by Git. Environment files and provider keys are not included in the change.

The Convex functions and dashboard changes must be deployed together for the ownership and step-claim checks to take effect. A read-only check against the configured deployment queried a random nonexistent user ID without a token and received an empty list instead of an authentication rejection. No existing user's data was requested. This confirms that the deployed run functions still need the ownership fix. No production deployment or merge is part of this verification record.

The browser authentication adapter follows the [Convex AuthKit Next.js template](https://github.com/get-convex/templates/blob/main/template-nextjs-authkit/components/ConvexClientProvider.tsx), checked against the installed WorkOS and Convex types.


## Cached sites follow-up (2026-09-13)

Overview now displays a curated library of 12 public-site snapshots: Clerk, Convex, Figma, Framer, Linear, Notion, Raycast, Resend, Stripe, Supabase, Vercel and WorkOS. The fresh batch ran three visual extractions concurrently; all 12 completed and passed CSS palette grounding. The catalog contains generated documents and safe display metadata, with capture dates. It includes no private run records or provider credentials.

Signed-in users can open and download snapshots without provider keys or a new extraction. Agent recognizes exact cached page URLs. Refresh prefills a new private extraction, requires the user's keys, and preserves the shared snapshot. The same document renderer serves private runs and cached sites; its mobile layout now wraps long content without page overflow. See [cached-sites.md](cached-sites.md) for the repeatable batch command and storage behavior.

Final automated suite: 264 passed, 39 build-dependent SEO tests skipped, zero failures. The SEO cases were previously verified separately and are unaffected by this dashboard change. Dashboard production build and TypeScript checks passed. Targeted ESLint found zero errors and one pre-existing image warning in the shared input component.

Native Chromium verification covered all 12 cards and exact downloaded document contents, Overview widths 320/390/768/1440, mobile document layout, cached lookup by pressing Enter without keys, prefilled refresh with submission disabled when keys are missing, and unknown-site handling. No extraction HTTP requests, private runs or stored provider keys were created during the cache browsing check. The temporary WorkOS test account was deleted afterward. Browser artifacts are in `getdesign-runs/cached-sites-browser/`.

The library now reads the shared Convex `cachedSites` table in production. Its seed data is committed in `convex/seedData/cached-sites.json`, and the Vercel production build deploys Convex and runs the internal seed before publication. This does not remove the existing launch requirement for human palette review.


## Shared database and production seed follow-up

The 12 snapshots belong to the application catalog, not to any user. Authenticated catalog queries return the same documents for unrelated accounts without looking up provider credentials or private run data. Only the internal `cachedSites:seed` mutation writes the catalog. It upserts by indexed slug, performs no writes for identical data, updates older snapshots, preserves newer database versions and extra catalog entries, and never touches user tables.

The dashboard's Vercel build configuration now runs `scripts/build-dashboard.ts`. Production requires a production deploy key, builds against that deployment's URL, deploys the Convex schema/functions, and runs the seed using the same key. Any failure stops publication. Isolated previews use a project Preview Deploy Key and the CLI preview seed hook. Local/preview builds without upgraded backend functions can use the committed bundle; production cannot use that fallback.

Verification: 275 automated tests passed, with 39 previously verified SEO cases skipped. New tests cover two account identities sharing all 12 documents, anonymous rejection, internal-only seeding, duplicate-free redeployment, snapshot updates, protection of newer/extra data, production key validation, correct seed order, and failure propagation. The deployment key validation tests passed again after tightening preview-key shape checks. Dashboard production build/TypeScript and targeted lint passed. Native Chromium rechecked all 12 downloads and cache navigation against the current local/preview compatibility path, with no page errors or paid requests; its temporary user was deleted.

No live production database was deployed or seeded in this follow-up. The workspace has no Convex deployment configuration/deploy key for executing the production hook; the registered backend handlers and deployment orchestration were tested locally. Production seeding will execute during the configured Vercel production build.


## Clean deployment build fix

The first deployment-hook revision invoked Next.js before compiling the dashboard's workspace packages. Vercel's fresh checkout therefore could not resolve `@getdesign/agent` and `@getdesign/tools/render`, whose exports point into generated `dist` directories. Previously built local artifacts masked the omission.

Every build mode now compiles types, content, tools, agent and SDK in dependency order before the frontend or Convex deployment command. Key validation still occurs before any production/preview work, and a dependency build failure prevents deployment and seeding.

Verified with Bun 1.3.14, matching Vercel: moved all five package output directories and the dashboard's entire `.next` output out of the checkout, reproduced the reported missing-module errors using the old direct build command, then ran the corrected `build:dashboard:vercel` preview command. It rebuilt every package and completed the Next.js production build and TypeScript checks. All 277 automated tests passed, with 39 previously verified SEO cases skipped. New tests inspect workspace manifests to check package coverage and dependency order in each deployment mode.

## Required image evidence

Visual output now retains its screenshot files end to end. Agent, SDK, and API JSON/SSE results include hero and full-page WebP files with paths, dimensions, MIME type and base64 bytes. Markdown references those files. The CLI writes a sibling image directory; its custom output names keep distinct image directories. The plain Markdown API response embeds the bytes. SDK progress events still omit image data and credentials. Default extraction now rejects missing capture credentials instead of quietly returning text-only; the legacy silent-skip option was removed. Explicit text-only selection remains supported and visibly labeled.

The product skill requires real screenshot files beside the document, working relative image links, and inspection of the saved files. Missing browser capture is no longer an automatic CSS-only fallback.

All 12 shared snapshots were recaptured and CSS-grounded. Their 24 real WebP assets are committed under `apps/dashboard/public/cached-sites/`, and the production database seed includes the image metadata and Markdown references. Overview uses hero screenshots for both shared sites and private runs. Deployment validates image hashes, dimensions and references before proceeding. Existing seed rows can receive image metadata during the seed transaction; private images remain in owned Convex storage.

Dashboard documents display capture evidence and offer an offline ZIP containing Markdown and real image files. The single Markdown download embeds the bytes. Export failure is visible if any required image cannot be fetched. Long screenshots are scaled within WebP's 16,383-pixel dimension limit; the original PNG tiles remain available to the analysis pipeline.

Verification with Bun 1.3.14: the full suite passed 284 tests, with 39 build-dependent SEO cases skipped. A subsequent seed-migration regression also passed. The dashboard production build, docs build and dashboard TypeScript checks passed. Native Chromium verified all 12 Overview images, all 24 detail images, 12 single-file Markdown exports, and 12 ZIPs whose bytes exactly match the captured files. Layouts passed at 320, 390, 768 and 1440 pixels. The shared-site check made no paid requests and stored no keys or private runs. A separate real hosted WorkOS sign-in and private Linear extraction passed all six stages, exported 14 screenshots, and displayed its private Overview thumbnail. Both temporary users were deleted, provider credentials removed, and the private test run soft-deleted.

Browser evidence is in `getdesign-runs/cached-sites-images-browser/` and `getdesign-runs/pr26-browser/private-design-images.zip`. Production has not been deployed or seeded locally; the configured production hook performs that work on deployment.

## Review comments and shared gallery

Checked all six review threads. The text-only continuation race and WorkOS issuer mismatch were already covered by the current code and tests. Interrupted-run recovery existed, but its live-run handling still needed correction. The two new image-related findings were valid.

- Catalog reads and Overview now exclude legacy rows without complete image metadata. Seeding replaces an incomplete curated row with its complete versioned snapshot even if the legacy row has a newer timestamp. Valid newer snapshots remain untouched. Replacing the whole incomplete snapshot keeps the document, images and capture date consistent.
- Missing screenshot URLs during rendering fail the claimed render step. The capture step remains successful, and retrying render can complete without a new capture or a stranded running claim.
- A refreshed or second tab joins an already-running step through authenticated status reads. Step-claim conflicts are distinguished from prerequisite errors. The UI disables recovery while a step is active; a new run is offered after five minutes without a persisted update. The create mutation also rejects recovery of an active original run. Interrupted originals retain their artifacts so late writes remain isolated.
- Cached documents now use the same right-side screenshot gallery and lightbox as private runs. Desktop documents avoid duplicate inline images. Mobile documents retain inline previews, and downloads retain all image files.

Validation: 291 tests passed, 40 build-dependent SEO cases skipped, zero failures. Dashboard production build and TypeScript passed. Targeted ESLint had no errors. Native Chromium checked all 12 cached pages at desktop and mobile widths, 36 decoded images, 12 exact ZIP exports, gallery position, collapse/expand, next-image navigation and Escape dismissal. A separate authenticated two-tab fixture joined and refreshed a live capture without duplicate runs, paid capture requests, or page errors. Temporary users and the test run were cleaned up. Gallery evidence is in `getdesign-runs/cached-sites-gallery-browser/`; joining evidence is in `getdesign-runs/review-live-run-browser/`. New Convex guards and seed behavior were tested through registered handlers locally; deploying them still requires the configured production deployment.
