"use client";

import { useState, type ChangeEvent } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";

import { Button, buttonVariants } from "@/components/ui/button";
import { Input } from "@/components/ui/input";

import { SettingsGroup, SettingsSection } from "./settings-shell";

export type ProviderKeyMeta = {
  provider: "daytona" | "openai";
  keySuffix: string;
  updatedAt: number;
};

type ProviderId = ProviderKeyMeta["provider"];

const PROVIDERS: Array<{
  id: ProviderId;
  label: string;
  placeholder: string;
}> = [
  { id: "daytona", label: "Daytona", placeholder: "Daytona API key" },
  { id: "openai", label: "OpenAI", placeholder: "OpenAI API key" },
];

function formatUpdatedAt(timestamp: number) {
  return new Date(timestamp).toLocaleDateString(undefined, {
    year: "numeric",
    month: "short",
    day: "numeric",
  });
}

export function ProviderKeysCard({
  keys,
  credentialsReady,
}: {
  keys: ProviderKeyMeta[];
  credentialsReady: boolean;
}) {
  const missingProviders = PROVIDERS.filter(
    (provider) => !keys.some((key) => key.provider === provider.id),
  ).map((provider) => provider.label);

  return (
    <SettingsSection
      id="provider-keys"
      title="Provider keys"
      description="Dashboard runs use these keys. They are encrypted at rest and never shown again after you save."
    >
      <SettingsGroup>
        <div className="divide-y">
          {PROVIDERS.map((provider) => (
            <ProviderKeyRow
              key={provider.id}
              provider={provider}
              stored={keys.find((entry) => entry.provider === provider.id)}
            />
          ))}
        </div>
        <div className="flex flex-col items-start gap-3 border-t bg-muted/30 px-4 py-3 sm:flex-row sm:items-center sm:justify-between">
          <p role="status" className="text-xs text-muted-foreground">
            {credentialsReady
              ? "Both provider keys are saved. Continue to Agent and enter a public URL to extract a design system."
              : `Save your ${missingProviders.join(" and ")} ${missingProviders.length === 1 ? "key" : "keys"} above, then return to Agent.`}
          </p>
          <Link
            href="/agent"
            className={buttonVariants({
              variant: credentialsReady ? "default" : "outline",
            })}
          >
            {credentialsReady ? "Continue to Agent" : "Back to Agent"}
          </Link>
        </div>
      </SettingsGroup>
    </SettingsSection>
  );
}

function ProviderKeyRow({
  provider,
  stored,
}: {
  provider: (typeof PROVIDERS)[number];
  stored?: ProviderKeyMeta;
}) {
  const router = useRouter();
  const [draft, setDraft] = useState("");
  const [replacing, setReplacing] = useState(false);
  const [optimistic, setOptimistic] = useState<{
    stored: ProviderKeyMeta | undefined;
    value: ProviderKeyMeta | null;
  }>();
  const [pending, setPending] = useState<"save" | "remove" | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);

  // A refreshed server prop takes precedence over the last save/remove response.
  const current =
    optimistic && optimistic.stored === stored
      ? (optimistic.value ?? undefined)
      : stored;
  const showForm = !current || replacing;

  async function save() {
    setError(null);
    setNotice(null);
    setPending("save");
    try {
      const response = await fetch("/api/credentials", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ provider: provider.id, key: draft }),
      });
      const payload = (await response.json()) as {
        error?: string;
        keySuffix?: string;
      };
      if (!response.ok || !payload.keySuffix) {
        setError(payload.error ?? "Could not save key.");
        return;
      }
      setDraft("");
      setReplacing(false);
      setNotice(`${provider.label} key saved.`);
      setOptimistic({
        stored,
        value: {
          provider: provider.id,
          keySuffix: payload.keySuffix,
          updatedAt: Date.now(),
        },
      });
      router.refresh();
    } catch {
      setError("Could not save key.");
    } finally {
      setPending(null);
    }
  }

  async function remove() {
    setError(null);
    setNotice(null);
    setPending("remove");
    try {
      const response = await fetch("/api/credentials", {
        method: "DELETE",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ provider: provider.id }),
      });
      const payload = (await response.json()) as { error?: string };
      if (!response.ok) {
        setError(payload.error ?? "Could not remove key.");
        return;
      }
      setDraft("");
      setReplacing(false);
      setOptimistic({ stored, value: null });
      setNotice(`${provider.label} key removed.`);
      router.refresh();
    } catch {
      setError("Could not remove key.");
    } finally {
      setPending(null);
    }
  }

  return (
    <div className="px-4 py-3">
      {showForm ? (
        <>
          <label htmlFor={`${provider.id}-key`} className="text-sm font-medium">
            {provider.label}
          </label>
          <form
            onSubmit={(event) => {
              event.preventDefault();
              if (pending === null && draft.trim()) void save();
            }}
            className="mt-2 flex flex-wrap items-center gap-2"
          >
            <Input
              id={`${provider.id}-key`}
              aria-label={`${provider.label} API key`}
              aria-invalid={Boolean(error)}
              aria-describedby={error ? `${provider.id}-key-error` : undefined}
              type="password"
              autoComplete="off"
              spellCheck={false}
              value={draft}
              placeholder={provider.placeholder}
              disabled={pending !== null}
              onChange={(event: ChangeEvent<HTMLInputElement>) =>
                setDraft(event.target.value)
              }
              className="min-w-0 flex-1 sm:max-w-sm"
            />
            <Button
              type="submit"
              disabled={pending !== null || !draft.trim()}
              aria-label={`Save ${provider.label} key`}
            >
              {pending === "save" ? "Saving" : "Save"}
            </Button>
            {current ? (
              <Button
                type="button"
                variant="ghost"
                disabled={pending !== null}
                onClick={() => {
                  setDraft("");
                  setReplacing(false);
                  setError(null);
                }}
              >
                Cancel
              </Button>
            ) : null}
          </form>
        </>
      ) : (
        <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
          <div className="min-w-0">
            <p className="text-sm font-medium">{provider.label}</p>
            <p className="mt-0.5 font-mono text-xs text-muted-foreground">
              ••••{current.keySuffix}
              <span className="font-sans">
                {" "}
                · Updated {formatUpdatedAt(current.updatedAt)}
              </span>
            </p>
          </div>
          <div className="flex gap-1">
            <Button
              variant="outline"
              disabled={pending !== null}
              onClick={() => {
                setDraft("");
                setReplacing(true);
                setError(null);
              }}
            >
              Replace
            </Button>
            <Button
              variant="destructive"
              disabled={pending !== null}
              onClick={() => void remove()}
            >
              {pending === "remove" ? "Removing" : "Remove"}
            </Button>
          </div>
        </div>
      )}
      {error ? (
        <p
          id={`${provider.id}-key-error`}
          role="alert"
          className="mt-2 text-xs text-destructive"
        >
          {error}
        </p>
      ) : null}
      {notice ? (
        <p role="status" className="mt-2 text-xs text-muted-foreground">
          {notice}
        </p>
      ) : null}
    </div>
  );
}
