import { describe, expect, test } from "bun:test";
import { buildDashboard, dashboardBuildSteps } from "./build-dashboard";

describe("Dashboard deployment and database seed", () => {
  test("production configures Convex with the dashboard client ID before deploying", () => {
    const steps = dashboardBuildSteps({ VERCEL_ENV: "production", CONVEX_DEPLOY_KEY: "prod:test|fake", WORKOS_CLIENT_ID: "  client_test  " });
    expect(steps.at(-3)!.args).toEqual(["x", "convex", "env", "set", "WORKOS_CLIENT_ID", "client_test"]);
    expect(steps.at(-2)!.args.slice(0, 3)).toEqual(["x", "convex", "deploy"]);
  });
  test("production refuses a missing WorkOS client ID before any work", async () => {
    for (const clientId of [undefined, "", "   "]) {
      let calls = 0;
      await expect(buildDashboard({ VERCEL_ENV: "production", CONVEX_DEPLOY_KEY: "prod:test|fake", WORKOS_CLIENT_ID: clientId }, async () => { calls++; return 0; })).rejects.toThrow("Production requires WORKOS_CLIENT_ID");
      expect(calls).toBe(0);
    }
  });
  test("failed WorkOS configuration prevents deployment and seeding", async () => {
    const commands: string[][] = [];
    await expect(buildDashboard({ VERCEL_ENV: "production", CONVEX_DEPLOY_KEY: "prod:test|fake", WORKOS_CLIENT_ID: "client_test" }, async args => {
      commands.push(args);
      return args.includes("set") ? 1 : 0;
    })).rejects.toThrow("Configure production Convex WorkOS client failed");
    expect(commands.at(-1)!.slice(0, 5)).toEqual(["x", "convex", "env", "set", "WORKOS_CLIENT_ID"]);
    expect(commands.some(args => args.includes("deploy") || args.includes("cachedSites:seed"))).toBe(false);
  });
  test("production runs the seed after successful deployment", async () => {
    const commands: string[][] = [];
    await buildDashboard({ VERCEL_ENV: "production", CONVEX_DEPLOY_KEY: "prod:test|fake", WORKOS_CLIENT_ID: "client_test" }, async args => { commands.push(args); return 0; });
    expect(commands.slice(-2)).toEqual([
      ["x", "convex", "deploy", "--cmd", "bun run --cwd apps/dashboard build", "--cmd-url-env-var-name", "NEXT_PUBLIC_CONVEX_URL"],
      ["x", "convex", "run", "cachedSites:seed", "{}"],
    ]);
  });
  test("production refuses missing or non-production keys before any work", async () => {
    for (const key of [undefined, "", "dev:test|fake", "preview:test|fake"]) {
      let calls = 0;
      await expect(buildDashboard({ VERCEL_ENV: "production", CONVEX_DEPLOY_KEY: key }, async () => { calls++; return 0; })).rejects.toThrow("Production requires");
      expect(calls).toBe(0);
    }
  });
  test("failed deployment skips seed and failed seed fails the build", async () => {
    const env = { VERCEL_ENV: "production", CONVEX_DEPLOY_KEY: "prod:test|fake", WORKOS_CLIENT_ID: "client_test" };
    const dependencies = dashboardBuildSteps(env).length - 2;
    let calls = 0;
    await expect(buildDashboard(env, async () => ++calls <= dependencies ? 0 : 1)).rejects.toThrow("must not publish");
    expect(calls).toBe(dependencies + 1);
    calls = 0;
    await expect(buildDashboard(env, async () => ++calls <= dependencies + 1 ? 0 : 1)).rejects.toThrow("Seed shared sites in production failed");
    expect(calls).toBe(dependencies + 2);
  });
  test("preview seeds only its isolated deployment and cannot use a production key", () => {
    const steps = dashboardBuildSteps({ VERCEL_ENV: "preview", CONVEX_DEPLOY_KEY: "preview:team:project|fake" });
    expect(steps).toHaveLength(6);
    expect(steps.at(-1)!.args.slice(-2)).toEqual(["--preview-run", "cachedSites:seed"]);
    for (const key of ["prod:test|fake", "dev:test|fake", "preview:shared-backend|fake"]) {
      expect(() => dashboardBuildSteps({ VERCEL_ENV: "preview", CONVEX_DEPLOY_KEY: key })).toThrow("refusing to deploy");
    }
    expect(dashboardBuildSteps({ VERCEL_ENV: "preview" }).at(-1)!.args).toEqual(["run", "--cwd", "apps/dashboard", "build"]);
  });
});


test("all build modes compile exported workspace packages before the dashboard", async () => {
  for (const env of [
    {}, { VERCEL_ENV: "preview" },
    { VERCEL_ENV: "preview", CONVEX_DEPLOY_KEY: "preview:team:project|fake" },
    { VERCEL_ENV: "production", CONVEX_DEPLOY_KEY: "prod:test|fake", WORKOS_CLIENT_ID: "client_test" },
  ]) {
    const commands: string[][] = [];
    await buildDashboard(env, async args => { commands.push(args); return 0; });
    const builtPackages = commands.filter(args => args[0] === "run" && args[2]?.startsWith("packages/")).map(args => args[2]!);
    const dashboard = await Bun.file(new URL("../apps/dashboard/package.json", import.meta.url)).json();
    for (const [name, version] of Object.entries(dashboard.dependencies)) {
      if (version !== "workspace:*" || !name.startsWith("@getdesign/")) continue;
      const path = `packages/${name.split("/")[1]}`;
      const manifest = await Bun.file(new URL(`../${path}/package.json`, import.meta.url)).json();
      if (!manifest.main?.startsWith("./dist/")) continue;
      expect(builtPackages).toContain(path);
      for (const dependency of Object.keys(manifest.dependencies ?? {})) {
        if (!dependency.startsWith("@getdesign/")) continue;
        const dependencyPath = `packages/${dependency.split("/")[1]}`;
        if (builtPackages.includes(dependencyPath)) {
          expect(builtPackages.indexOf(dependencyPath)).toBeLessThan(builtPackages.indexOf(path));
        }
      }
    }
    expect(commands.findIndex(args => args.includes("apps/dashboard") || args.includes("convex"))).toBe(builtPackages.length);
  }
});

test("a failed dependency build prevents both frontend build and deployment", async () => {
  const commands: string[][] = [];
  await expect(buildDashboard({ VERCEL_ENV: "production", CONVEX_DEPLOY_KEY: "prod:test|fake", WORKOS_CLIENT_ID: "client_test" }, async args => { commands.push(args); return 1; })).rejects.toThrow("Build @getdesign/types failed");
  expect(commands).toEqual([["run", "--cwd", "packages/types", "build"]]);
});
