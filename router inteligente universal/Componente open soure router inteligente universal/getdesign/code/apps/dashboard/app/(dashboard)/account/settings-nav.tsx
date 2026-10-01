"use client";

import { useSyncExternalStore } from "react";

import { cn } from "@/lib/utils";

export const SETTINGS_SECTIONS = [
  { id: "provider-keys", label: "Provider keys" },
  { id: "account", label: "Account" },
  { id: "developers", label: "Developers" },
] as const;

function subscribe(onChange: () => void) {
  window.addEventListener("hashchange", onChange);
  return () => window.removeEventListener("hashchange", onChange);
}

function currentHash() {
  return window.location.hash.slice(1);
}

export function SettingsNav() {
  const hash = useSyncExternalStore(subscribe, currentHash, () => "");
  const active = hash || "provider-keys";

  return (
    <nav
      aria-label="Settings sections"
      className="hidden w-48 shrink-0 border-r px-3 py-6 lg:block"
    >
      <ul className="sticky top-6 space-y-0.5">
        {SETTINGS_SECTIONS.map((section) => (
          <li key={section.id}>
            <a
              href={`#${section.id}`}
              aria-current={active === section.id ? "true" : undefined}
              className={cn(
                "block rounded-md px-2.5 py-1.5 text-sm",
                active === section.id
                  ? "bg-muted font-medium text-foreground"
                  : "text-muted-foreground hover:bg-muted/50 hover:text-foreground",
              )}
            >
              {section.label}
            </a>
          </li>
        ))}
      </ul>
    </nav>
  );
}
