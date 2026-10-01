import { expect, test } from "bun:test";

test("public run HTTP and UI checks run in isolation", async () => {
  const child = Bun.spawn({
    cmd: [process.execPath, "test", "./tests/public-runs-suite.tsx"],
    cwd: new URL("..", import.meta.url).pathname,
    stdout: "pipe", stderr: "pipe",
  });
  const [stdout, stderr, code] = await Promise.all([
    new Response(child.stdout).text(), new Response(child.stderr).text(), child.exited,
  ]);
  expect(code, `${stdout}\n${stderr}`).toBe(0);
}, 15_000);
