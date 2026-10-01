import Link from "next/link";
import { HugeiconsIcon } from "@hugeicons/react";
import { Tick02Icon } from "@hugeicons/core-free-icons";

import { buttonVariants } from "@/components/ui/button";
import { cn } from "@/lib/utils";

const PROVIDERS = ["daytona", "openai"] as const;

const STEPS = [
  {
    id: "keys",
    title: "Add provider keys",
    description:
      "Save Daytona and OpenAI keys. Dashboard runs use yours, not a shared pool.",
  },
  {
    id: "url",
    title: "Choose a public URL",
    description:
      "Paste a public site in Agent. Cached examples open without spending keys.",
  },
  {
    id: "extract",
    title: "Open the finished design",
    description:
      "When the run completes, Overview lists it. Open it to read or download design.md.",
  },
] as const;

type StepState = "complete" | "current" | "upcoming";
type ProviderId = (typeof PROVIDERS)[number];

function stepState(index: number, current: number): StepState {
  if (index < current) return "complete";
  if (index === current) return "current";
  return "upcoming";
}

function providerSaved(
  keys: ReadonlyArray<{ provider: string }> | undefined,
  provider: ProviderId,
  credentialsReady: boolean,
) {
  if (keys) return keys.some((key) => key.provider === provider);
  return credentialsReady;
}

export function ExtractionGuide({
  credentialsReady,
  keys,
}: {
  credentialsReady: boolean;
  keys?: ReadonlyArray<{ provider: string }>;
}) {
  const current = credentialsReady ? 1 : 0;

  return (
    <section
      aria-labelledby="extraction-heading"
      className="rounded-xl border bg-card p-5"
    >
      <h1 id="extraction-heading" className="text-base font-medium">
        Turn a website into a design system
      </h1>
      <p className="mt-1 text-sm text-muted-foreground">
        Keys, then a URL, then extract. Overview hides this after your first
        completed run.
      </p>

      <ol aria-label="Setup steps" className="mt-5 divide-y">
        {STEPS.map((step, index) => {
          const state = stepState(index, current);
          return (
            <li
              key={step.id}
              aria-current={state === "current" ? "step" : undefined}
              className="flex gap-3 py-4 first:pt-0 last:pb-0"
            >
              <StepIndex n={index + 1} state={state} />
              <div className="min-w-0 flex-1">
                <div className="flex flex-wrap items-baseline justify-between gap-x-3 gap-y-1">
                  <h2
                    className={cn(
                      "text-sm font-medium",
                      state === "upcoming" && "text-muted-foreground",
                    )}
                  >
                    {step.title}
                  </h2>
                  {state === "complete" ? (
                    <span className="text-xs text-muted-foreground">Done</span>
                  ) : null}
                </div>
                <p
                  className={cn(
                    "mt-1 text-sm text-muted-foreground",
                    state === "upcoming" && "text-muted-foreground/80",
                  )}
                >
                  {step.description}
                </p>
                {index === 0 ? (
                  <ProviderStatus
                    keys={keys}
                    credentialsReady={credentialsReady}
                  />
                ) : null}
                {state === "current" ? (
                  <StepActions credentialsReady={credentialsReady} />
                ) : null}
              </div>
            </li>
          );
        })}
      </ol>
    </section>
  );
}

function StepIndex({ n, state }: { n: number; state: StepState }) {
  return (
    <span
      aria-hidden="true"
      className={cn(
        "mt-0.5 flex size-6 shrink-0 items-center justify-center rounded-full border text-[11px] font-medium",
        state === "complete" &&
          "border-foreground bg-foreground text-background",
        state === "current" && "border-foreground text-foreground",
        state === "upcoming" && "border-border text-muted-foreground",
      )}
    >
      {state === "complete" ? (
        <HugeiconsIcon icon={Tick02Icon} className="size-3.5" />
      ) : (
        n
      )}
    </span>
  );
}

function ProviderStatus({
  keys,
  credentialsReady,
}: {
  keys: ReadonlyArray<{ provider: string }> | undefined;
  credentialsReady: boolean;
}) {
  return (
    <ul className="mt-2 flex flex-wrap gap-2">
      {PROVIDERS.map((provider) => {
        const saved = providerSaved(keys, provider, credentialsReady);
        const label = provider === "daytona" ? "Daytona" : "OpenAI";
        return (
          <li
            key={provider}
            className="rounded-md border px-2 py-0.5 text-xs text-muted-foreground"
          >
            {label} {saved ? "saved" : "needed"}
          </li>
        );
      })}
    </ul>
  );
}

function StepActions({ credentialsReady }: { credentialsReady: boolean }) {
  if (credentialsReady) {
    return (
      <div className="mt-3 flex flex-wrap items-center gap-2">
        <Link
          href="/agent"
          className={buttonVariants({
            size: "lg",
          })}
        >
          Extract a design system
        </Link>
        <Link
          href="/sites"
          className={buttonVariants({
            variant: "outline",
            size: "lg",
          })}
        >
          Open an example
        </Link>
      </div>
    );
  }

  return (
    <div className="mt-3 flex flex-wrap items-center gap-2">
      <Link
        href="/account#provider-keys"
        className={buttonVariants({
          size: "lg",
        })}
      >
        Add provider keys
      </Link>
      <Link
        href="/sites"
        className={buttonVariants({
          variant: "outline",
          size: "lg",
        })}
      >
        Open an example
      </Link>
    </div>
  );
}
