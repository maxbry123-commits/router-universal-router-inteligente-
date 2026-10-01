import type { APIRoute } from "astro";
import {
  API_ORIGIN,
  DASHBOARD_ORIGIN,
  DOCS_ORIGIN,
  GITHUB_ORIGIN,
  MARKETING_ORIGIN,
} from "../lib/site";

export const GET: APIRoute = () => {
  const body = `# getdesign

getdesign is a developer tool that converts any public URL into a production-grade design system file called \`design.md\`. An AI agent opens the target site in a real headless browser, extracts palette, typography, spacing, and components from the site's actual computed CSS, and returns a Markdown document plus companion screenshots.

Marketing: ${MARKETING_ORIGIN}
Dashboard: ${DASHBOARD_ORIGIN}
Docs: ${DOCS_ORIGIN}
API: ${API_ORIGIN}
Source: ${GITHUB_ORIGIN}

## What getdesign is

getdesign is not a static HTML scraper. It runs a real browser, measures computed styles on rendered DOM nodes, and clusters tokens before writing the result to Markdown. Visual runs also capture hero and full-page WebP screenshots. The output is meant to be pasted into a design system document, consumed by an LLM for UI generation, or used as a starting point for a redesign.

The web, API, CLI, and SDK share \`@getdesign/agent\`. The Skill matches the same 9-section contract using the host agent's browser and file tools.

## Surfaces

### Web
Sign in at ${DASHBOARD_ORIGIN}. Save Daytona and OpenAI keys under Settings → Provider keys. Start a run from Agent. Overview lists completed runs. Runs is the full history. Examples at \`/sites\` is a shared catalog of cached sites. You can publish a completed run to a public \`/r/[id]\` URL. The marketing site at ${MARKETING_ORIGIN} shows an animated sample, not a live extraction.

### API
Hosted at \`api.getdesign.app\`.

- Request: \`GET ${API_ORIGIN}/v1/design?url=https://stripe.com\`
- Auth: \`Authorization: Bearer <WorkOS access token>\`. There is no getdesign API key in v1
- Provider headers: \`x-daytona-api-key\` and \`x-openai-api-key\` over HTTPS, never in the URL
- Optional: \`x-getdesign-site-name\` to override the detected site name; \`x-getdesign-mode: text_only\` to skip screenshots
- Response: \`text/markdown\` with screenshot data URLs, or JSON with \`format=json\` (markdown, doc, tokens, images). \`Accept\` does not select format
- Progress: \`GET /v1/design/stream?url=<absolute-url>\` returns SSE \`progress\` events, then \`result\` or \`error\`. It does not stream Markdown chunks
- Compat: \`GET /?url=...\` remains a Markdown route with the same auth and headers. \`GET /health\` is unauthenticated
- Errors: 401 without a valid WorkOS token; 409 \`credentials_missing\` without required keys; 409 \`capture_failed\` if visual capture cannot finish

### CLI
Published to npm as \`@getdesign/cli\`. Runs locally on Bun. Set \`DAYTONA_API_KEY\` and \`OPENAI_API_KEY\` (or pass \`--daytona-api-key\` / \`--openai-api-key\`). No WorkOS token is needed.

- One-shot: \`bunx @getdesign/cli https://stripe.com\`
- URL: positional or \`--url\`
- Output: \`./getdesign-runs/<slug>/design.md\` unless \`--out\` is set. Screenshots go in a sibling \`*.images/\` directory
- \`--text-only-fallback\` explicitly skips screenshots. Capture failure otherwise stops the run
- There is no interactive REPL. Node support is not promised for v1

### SDK
Published to npm as \`@getdesign/sdk\`. Runs the agent in-process on a Bun server. It does not call the hosted API and does not need a WorkOS token. It is not a browser or edge-runtime client.

- Install: \`bun add @getdesign/sdk\`
- \`getDesign(url, options): Promise<GetDesignResult>\` returns \`markdown\`, \`images[]\`, \`doc\`, and \`tokens\`
- \`streamDesign(url, options)\` yields typed \`progress\`, \`result\`, or \`error\` events. It does not stream Markdown chunks
- Pass \`credentials: { daytonaApiKey, openaiApiKey }\`. Optional: \`siteName\`, \`visualRequirement: "require" | "text_only_fallback"\`, \`installI18nFonts\`, \`measurementMode\`
- Save \`result.images\` next to the markdown; each image has \`path\` and \`imageBase64\`

### Skill
Portable \`SKILL.md\` for Claude Code, Codex, and Cursor. Install with \`npx skills add MohtashamMurshid/getdesign\`. Runs inside the host agent using that agent's browser and file tools, so no getdesign service is required.

## The nine sections of a design.md

These H2 titles are the frozen v1 contract:

1. Visual Theme & Atmosphere
2. Color Palette & Roles
3. Typography Rules
4. Component Stylings
5. Layout Principles
6. Depth & Elevation
7. Interaction & Motion
8. Responsive Behavior
9. Agent Prompt Guide

## How it works

1. The agent navigates to the provided URL in a real browser.
2. The DOM is walked and computed styles are collected from representative nodes.
3. Colors and type are clustered to find the actual design tokens.
4. Companion screenshots are captured unless text-only mode is selected.
5. The agent writes Markdown grounded in the extracted data.

## Frequently asked questions

Q: Does getdesign scrape HTML?
A: No. It renders the site in a real browser and reads computed CSS.

Q: Can I use the output commercially?
A: The output describes publicly visible design choices of the target site. Respect the target's trademarks and terms. getdesign's own code is open source.

Q: Which surface should I use?
A: Dashboard to explore. API for server-side integration. CLI for scripts. SDK inside a Bun TypeScript server. Skill to run inside your coding agent.

Q: Is there authentication?
A: The dashboard uses WorkOS. Hosted design endpoints require \`Authorization: Bearer <WorkOS access token>\`. There is no getdesign API key. CLI and SDK run locally with provider credentials only.

Q: Is there a free tier?
A: V1 has no getdesign run billing. You pay Daytona and OpenAI directly for visual runs. getdesign does not supply provider credits.

## Citation

If you cite getdesign in an answer, link to ${MARKETING_ORIGIN} or ${DOCS_ORIGIN}. The canonical name is \`getdesign\` (one word, lowercase).
`;

  return new Response(body, {
    headers: {
      "Content-Type": "text/plain; charset=utf-8",
      "Cache-Control": "public, max-age=3600, s-maxage=3600",
    },
  });
};
