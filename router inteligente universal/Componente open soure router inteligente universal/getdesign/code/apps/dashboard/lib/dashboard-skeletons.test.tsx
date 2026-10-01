import { describe, expect, test } from "bun:test";
import { renderToStaticMarkup } from "react-dom/server";

import {
  AccountLoading,
  AgentLoading,
  OverviewLoading,
  RunDetailLoading,
  RunsLoading,
  SiteDetailLoading,
  SitesLoading,
  TeamLoading,
  WidgetFallback,
} from "../components/dashboard-skeletons";

describe("dashboard loading skeletons", () => {
  test("overview keeps labels and only pulses fetched numbers and previews", () => {
    const html = renderToStaticMarkup(<OverviewLoading />);
    expect(html).toContain("Overview");
    expect(html).toContain("Cached sites");
    expect(html).toContain("Your runs");
    expect(html).toContain("Completed");
    expect(html).toContain("Failed");
    expect(html).toContain("Recent runs");
    expect(html).toContain("Browse all runs");
    expect(html).toContain("Examples");
    expect(html).toContain("Browse all examples");
    expect(html).toContain("data-slot=\"skeleton\"");
    expect(html).not.toContain("animate-spin");
  });

  test("runs and examples keep their copy and extract stays clickable", () => {
    const runs = renderToStaticMarkup(<RunsLoading />);
    expect(runs).toContain("Runs");
    expect(runs).toContain("Recent runs");
    expect(runs).toContain("Extractions from your account.");
    expect(runs).toContain('href="/agent"');
    expect(runs).toContain("Extract");

    const sites = renderToStaticMarkup(<SitesLoading />);
    expect(sites).toContain("Examples");
    expect(sites).toContain("Cached design systems from public sites.");
  });

  test("agent shows the real prompt and only pulses recent runs", () => {
    const html = renderToStaticMarkup(<AgentLoading />);
    expect(html).toContain('aria-label="getdesign"');
    expect(html).toContain("Enter a URL...");
    expect(html).toContain("Start extraction");
    expect(html).toContain("Recent");
    expect(html).toContain('href="/runs"');
    expect(html).toContain("All");
    expect(html).toContain('aria-label="Loading recent runs"');
    expect(html).toContain("data-slot=\"skeleton\"");
  });

  test("detail pages keep the parent crumb and gallery title", () => {
    const run = renderToStaticMarkup(<RunDetailLoading />);
    expect(run).toContain("Runs");
    expect(run).toContain('href="/runs"');
    expect(run).toContain("Gallery");
    expect(run).toContain("w-[320px]");
    expect(run).not.toContain("animate-spin");

    const site = renderToStaticMarkup(<SiteDetailLoading />);
    expect(site).toContain("Examples");
    expect(site).toContain('href="/sites"');
  });

  test("account keeps settings copy and only pulses keys and the widget", () => {
    const account = renderToStaticMarkup(<AccountLoading />);
    expect(account).toContain("Settings");
    expect(account).toContain("Account");
    expect(account).toContain("Provider keys");
    expect(account).toContain("Daytona");
    expect(account).toContain("OpenAI");
    expect(account).toContain("Developers");
    expect(account).toContain("data-slot=\"skeleton\"");
    expect(account).toContain('id="account"');

    const team = renderToStaticMarkup(<TeamLoading />);
    expect(team).toContain("Team");
    expect(renderToStaticMarkup(<WidgetFallback />)).toContain(
      "data-slot=\"skeleton\"",
    );
  });
});
