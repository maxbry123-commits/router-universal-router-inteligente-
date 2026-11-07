import type { Metadata } from "next";
import type { ReactNode } from "react";
import Link from "next/link";
import Footer from "@/components/Footer";
import GooeyNavbar from "@/components/GooeyNavbar";
import McpAsk from "@/components/mcp/McpAsk";
import McpClients from "@/components/mcp/McpClients";
import McpCode from "@/components/mcp/McpCode";
import McpText from "@/components/mcp/McpText";
import CodeBlock from "@/components/ui/code-block";
import { fetchStarCount } from "@/lib/github";
import { MCP_CLI, MCP_COMPONENTS_JSON } from "@/lib/mcp";
import { SITE_NAME } from "@/lib/site";

const DESCRIPTION =
  "Add Rare UI from Claude Code, Cursor, Codex, or VS Code. One registry in components.json, then ask for any component.";

export const metadata: Metadata = {
  title: "MCP",
  description: DESCRIPTION,
  alternates: {
    canonical: "/mcp",
  },
  openGraph: {
    title: `MCP | ${SITE_NAME}`,
    description: DESCRIPTION,
    url: "/mcp",
    siteName: SITE_NAME,
    locale: "en_US",
    type: "website",
  },
};

const STEPS: { heading: string; content: ReactNode }[] = [
  {
    heading: "Add the registry",
    content: (
      <>
        <McpText>
          {
            "Your project needs shadcn set up first: `components.json`, Tailwind, and the `cn` helper. Add this to `components.json` and keep `{name}` as written."
          }
        </McpText>
        <CodeBlock
          code={MCP_COMPONENTS_JSON}
          language="json"
          showFrame={false}
          showLineNumbers={false}
          className="rounded-lg bg-muted p-3"
        />
      </>
    ),
  },
  {
    heading: "Connect your editor",
    content: <McpClients />,
  },
  {
    heading: "Ask for a component",
    content: (
      <>
        <McpText>
          {
            "Prefix the name with `@rare-ui`, or ask in plain words. The file lands in `components/ui`, and it's yours from there."
          }
        </McpText>
        <McpAsk />
      </>
    ),
  },
];

export default async function McpPage() {
  const stars = await fetchStarCount();

  return (
    <>
      <GooeyNavbar stars={stars} />

      <main className="mx-auto w-full max-w-3xl flex-1 px-5 pb-24 pt-32 sm:px-6 md:pt-40">
        <header className="flex flex-col gap-3">
          <h1 className="font-runde text-3xl font-bold tracking-tight sm:text-4xl">
            MCP
          </h1>
          <p className="font-medium text-muted-foreground">{DESCRIPTION}</p>
        </header>

        <ol className="mt-12 flex flex-col">
          {STEPS.map((step, index) => (
            <li
              key={step.heading}
              className="grid grid-cols-[1.5rem_minmax(0,1fr)] gap-x-4 pb-12 last:pb-0"
            >
              <span className="flex size-6 items-center justify-center rounded-full bg-[#FC4C01]/10 font-mono text-xs font-medium text-[#FC4C01]">
                {index + 1}
              </span>
              <section className="flex flex-col gap-3">
                <h2 className="font-runde text-lg font-bold leading-6 tracking-tight">
                  {step.heading}
                </h2>
                {step.content}
              </section>
            </li>
          ))}
        </ol>

        <section className="mt-16 flex flex-col gap-3 border-t border-foreground/10 pt-10">
          <h2 className="font-runde text-lg font-bold tracking-tight">
            Without MCP
          </h2>
          <p className="text-[15px] leading-relaxed text-muted-foreground">
            The shadcn CLI installs the same files. Browse everything on the{" "}
            <Link
              href="/components"
              className="text-foreground underline decoration-foreground/25 underline-offset-4 transition-colors duration-150 ease-out hover:decoration-foreground"
            >
              components
            </Link>{" "}
            page.
          </p>
          <McpCode value={MCP_CLI} />
        </section>
      </main>

      <Footer />
    </>
  );
}
