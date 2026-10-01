import { expect, test } from "bun:test";

// Run against a local `next start` after building the dashboard:
// GETDESIGN_RUNTIME_BASE_URL=http://localhost:4398 bun test tests/agent-loading-runtime.test.ts
// No session, database connection, or provider usage is needed.
const baseUrl = process.env.GETDESIGN_RUNTIME_BASE_URL;

test.skipIf(!baseUrl)("Agent's loading tree serializes across the server/client boundary", async () => {
  const url = new URL("/agent", baseUrl);
  if (!["localhost", "127.0.0.1", "[::1]"].includes(url.hostname)) {
    throw new Error("Run this smoke test against a local dashboard server.");
  }
  const response = await fetch(url, { headers: { RSC: "1" }, redirect: "manual" });
  expect(response.status).toBe(200);
  expect(response.headers.get("content-type")).toContain("text/x-component");
  const body = await response.text();
  expect(body).toContain("Loading recent runs");
  // RSC failures can be embedded alongside an otherwise valid auth redirect.
  const errors = [...body.matchAll(/^[\da-f]+:E(\{[^\n]+\})$/gm)]
    .map(match => JSON.parse(match[1]!) as { digest?: string; message?: string });
  expect(errors.length).toBeGreaterThan(0);
  expect(errors.some(error => error.digest?.includes(";/sign-in;"))).toBe(true);
  expect(errors.filter(error => !error.digest?.startsWith("NEXT_REDIRECT;"))).toEqual([]);
}, 15_000);
