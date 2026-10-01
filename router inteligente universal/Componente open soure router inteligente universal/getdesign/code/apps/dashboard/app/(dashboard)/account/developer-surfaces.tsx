import { ArrowRight01Icon } from "@hugeicons/core-free-icons";
import { HugeiconsIcon } from "@hugeicons/react";
import { docsUrl } from "@getdesign/content";

import { SettingsGroup, SettingsSection } from "./settings-shell";

const SURFACES = [
  {
    title: "API",
    href: docsUrl("/surfaces/api"),
    description: "HTTP endpoint at api.getdesign.app",
  },
  {
    title: "CLI",
    href: docsUrl("/surfaces/cli"),
    description: "bunx @getdesign/cli",
  },
  {
    title: "SDK",
    href: docsUrl("/surfaces/sdk"),
    description: "@getdesign/sdk",
  },
  {
    title: "Skills",
    href: docsUrl("/surfaces/skill"),
    description: "Cursor, Claude Code, and Codex",
  },
] as const;

export function DeveloperSurfaces() {
  return (
    <SettingsSection
      id="developers"
      title="Developers"
      description="There is no getdesign API key. Dashboard runs use the keys above. Other surfaces take Daytona and OpenAI keys in the request or environment."
    >
      <SettingsGroup>
        <ul className="divide-y">
          {SURFACES.map((surface) => (
            <li key={surface.href}>
              <a
                href={surface.href}
                target="_blank"
                rel="noreferrer"
                className="flex items-center justify-between gap-4 px-4 py-3 transition-colors hover:bg-muted/40"
              >
                <div className="min-w-0">
                  <p className="text-sm font-medium text-foreground">
                    {surface.title}
                  </p>
                  <p className="mt-0.5 text-xs text-muted-foreground">
                    {surface.description}
                  </p>
                </div>
                <HugeiconsIcon
                  icon={ArrowRight01Icon}
                  strokeWidth={2}
                  className="size-4 shrink-0 text-muted-foreground"
                />
              </a>
            </li>
          ))}
        </ul>
      </SettingsGroup>
    </SettingsSection>
  );
}
