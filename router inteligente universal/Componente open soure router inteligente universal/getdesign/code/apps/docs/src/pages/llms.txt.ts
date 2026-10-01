import type { APIRoute } from "astro";
import {
  API_ORIGIN,
  DASHBOARD_ORIGIN,
  DOCS_ORIGIN,
  GITHUB_ORIGIN,
  MARKETING_ORIGIN,
} from "../lib/site";

export const GET: APIRoute = () => {
  const body = `# getdesign docs

> Documentation for getdesign: the design system for any URL. Paste a URL; an agent opens it in a real browser, extracts palette, typography, and components, and returns a production-grade \`design.md\`. Visual runs also capture companion screenshots.

The web, API, CLI, and SDK share the \`@getdesign/agent\` core. The Skill uses your coding agent's own tools.

## Canonical URLs

- Marketing: ${MARKETING_ORIGIN}
- Dashboard: ${DASHBOARD_ORIGIN}
- Docs: ${DOCS_ORIGIN}
- API: ${API_ORIGIN}
- Repo: ${GITHUB_ORIGIN}

## Surfaces

- Web: sign in at ${DASHBOARD_ORIGIN}, save Daytona and OpenAI keys in Settings, then run a URL from Agent
- API: \`GET ${API_ORIGIN}/v1/design?url=<absolute-url>\` with \`Authorization: Bearer <WorkOS access token>\` plus \`x-daytona-api-key\` and \`x-openai-api-key\`. Use \`format=json\` for a structured result; \`/v1/design/stream\` returns SSE progress then a result or error
- CLI: \`bunx @getdesign/cli <url>\` on Bun with \`DAYTONA_API_KEY\` and \`OPENAI_API_KEY\`. Writes \`./getdesign-runs/<slug>/design.md\` by default. No REPL
- SDK: \`bun add @getdesign/sdk\`. \`getDesign(url, options)\` returns markdown plus \`images[]\`; \`streamDesign\` yields progress, result, or error events. Local Bun execution, not the hosted API
- Skill: \`npx skills add MohtashamMurshid/getdesign\`. Runs inside Claude Code, Codex, or Cursor using the host agent's tools

## Setup and costs

Dashboard sign-in uses WorkOS. Hosted design endpoints need a WorkOS bearer token. There is no getdesign API key in v1. Visual runs need your Daytona and OpenAI keys; you pay those providers directly. CLI and SDK run locally and do not need a WorkOS token. The SDK is not a browser or edge-runtime client.

## Docs

- [Quickstart](${DOCS_ORIGIN}/quickstart/)
- [Concepts](${DOCS_ORIGIN}/concepts/)
- [Web surface](${DOCS_ORIGIN}/surfaces/web/)
- [API surface](${DOCS_ORIGIN}/surfaces/api/)
- [CLI surface](${DOCS_ORIGIN}/surfaces/cli/)
- [SDK surface](${DOCS_ORIGIN}/surfaces/sdk/)
- [Skill surface](${DOCS_ORIGIN}/surfaces/skill/)
- [SDK reference](${DOCS_ORIGIN}/reference/sdk/)
- [CLI reference](${DOCS_ORIGIN}/reference/cli/)
- [FAQ](${DOCS_ORIGIN}/resources/faq/)
- [Changelog](${DOCS_ORIGIN}/resources/changelog/)

## Full corpus

- [${DOCS_ORIGIN}/llms-full.txt](${DOCS_ORIGIN}/llms-full.txt)
`;

  return new Response(body, {
    headers: {
      "Content-Type": "text/plain; charset=utf-8",
      "Cache-Control": "public, max-age=3600, s-maxage=3600",
    },
  });
};
