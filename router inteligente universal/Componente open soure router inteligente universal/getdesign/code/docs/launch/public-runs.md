# Public run sharing

On a completed run at `/runs/[id]`, choose **Public** in the visibility menu next to Download, then **Copy link**.
Runs are private until their owner publishes them. Existing runs need no migration.

The public link is `/r/[id]`. Anyone can open it without an account or provider keys,
read the document, view screenshots, copy Markdown with or without embedded images,
or download Markdown or an offline ZIP through the shared Download menu. Files use
the site's name, such as `getdesign-resend.md`. Public runs are shared by link; they are not
added to Examples or a searchable gallery.

## Agent access

Use the public link's host with these GET endpoints:

- `/r/[id]/design.md` returns UTF-8 Markdown with absolute screenshot URLs.
- `/r/[id]/design.json` returns `schemaVersion: 1`, the Markdown, structured `doc`,
  `tokens`, `visualDescription`, source URL, capture/publication times, mode,
  image dimensions/URLs, and links to the other formats.
- `/r/[id]/images/[index]` returns the captured image bytes.

For example, replace the URL below with the copied public link:

```sh
curl --fail 'https://YOUR_DASHBOARD_HOST/r/RUN_ID/design.md' -o design.md
```

```js
const run = await fetch(`${publicRunUrl}/design.json`).then(response => {
  if (!response.ok) throw new Error(`Shared run unavailable: ${response.status}`);
  return response.json();
});
// Use run.markdown, run.doc, run.tokens, or fetch each run.images[i].url.
```

These are ordinary HTTP reads usable by agents, scripts, and browser clients.
They do not invoke the extraction API, CLI, or SDK pipeline, and never use provider
keys. The existing generation commands still start new extractions; they do not
automatically import a public run URL.

## Access and revocation

Only the authenticated owner can change visibility. Publishing requires a completed
run with a saved Markdown document. The public response omits owner identity,
credentials, raw crawl data, traces, errors, and storage IDs. Private run mutations
and artifact queries keep their existing owner checks.

Choosing **Private** or deleting the run returns 404 on subsequent public page,
Markdown, JSON, and screenshot requests. Invalid IDs also return 404. Downloads
use `Cache-Control: no-store`; screenshot routes return bytes rather than permanent
storage links. Copies already downloaded by recipients cannot be recalled.
Republishing restores the same public URL.

Deploy the Convex schema/functions and dashboard together using the existing
dashboard deployment flow. No new environment variables or backfill are required.
