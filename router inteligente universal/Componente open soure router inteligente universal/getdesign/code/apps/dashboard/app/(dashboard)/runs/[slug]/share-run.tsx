"use client";

import { useState } from "react";
import { useMutation } from "convex/react";
import { useRouter } from "next/navigation";
import { HugeiconsIcon } from "@hugeicons/react";
import {
  ArrowDown01Icon,
  ArrowUpRight01Icon,
  CircleLock01Icon,
  Copy01Icon,
  Globe02Icon,
} from "@hugeicons/core-free-icons";
import { api } from "@convex/_generated/api";
import type { Id } from "@convex/_generated/dataModel";
import { Button } from "@/components/ui/button";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuRadioGroup,
  DropdownMenuRadioItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";

export function ShareRun({ runId, isPublic }: { runId: string; isPublic: boolean }) {
  const setVisibility = useMutation(api.publicRuns.setVisibility);
  const router = useRouter();
  const [busy, setBusy] = useState(false);
  const [copied, setCopied] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const path = `/r/${encodeURIComponent(runId)}`;
  const visibility = isPublic ? "public" : "private";

  async function changeVisibility(next: string) {
    if (next !== "public" && next !== "private") return;
    if (next === visibility) return;
    setBusy(true);
    setError(null);
    try {
      await setVisibility({ id: runId as Id<"designRuns">, visibility: next });
      setCopied(false);
      router.refresh();
    } catch {
      setError("Could not update sharing. Please retry.");
    } finally {
      setBusy(false);
    }
  }

  async function copyLink() {
    try {
      await navigator.clipboard.writeText(new URL(path, window.location.origin).href);
      setError(null);
      setCopied(true);
    } catch {
      setError("Could not copy the link. Open the public page and copy its address.");
    }
  }

  return (
    <>
      {error ? <span role="alert" className="text-xs text-destructive">{error}</span> : null}
      <DropdownMenu>
        <DropdownMenuTrigger
          disabled={busy}
          render={
            <Button
              variant="outline"
              size="sm"
              aria-label="Visibility"
            />
          }
        >
          <HugeiconsIcon icon={isPublic ? Globe02Icon : CircleLock01Icon} />
          {busy ? "Saving…" : isPublic ? "Public" : "Private"}
          <HugeiconsIcon icon={ArrowDown01Icon} data-icon="inline-end" />
        </DropdownMenuTrigger>
        <DropdownMenuContent align="end" className="w-44">
          <DropdownMenuRadioGroup
            value={visibility}
            onValueChange={(value) => void changeVisibility(value)}
          >
            <DropdownMenuRadioItem disabled={busy} value="private">
              <HugeiconsIcon icon={CircleLock01Icon} />
              Private
            </DropdownMenuRadioItem>
            <DropdownMenuRadioItem disabled={busy} value="public">
              <HugeiconsIcon icon={Globe02Icon} />
              Public
            </DropdownMenuRadioItem>
          </DropdownMenuRadioGroup>
          {isPublic ? (
            <>
              <DropdownMenuSeparator />
              <DropdownMenuItem onClick={() => void copyLink()}>
                <HugeiconsIcon icon={Copy01Icon} />
                {copied ? "Link copied" : "Copy link"}
              </DropdownMenuItem>
              <DropdownMenuItem
                render={<a href={path} target="_blank" rel="noreferrer" />}
              >
                <HugeiconsIcon icon={ArrowUpRight01Icon} />
                Open public page
              </DropdownMenuItem>
            </>
          ) : null}
        </DropdownMenuContent>
      </DropdownMenu>
    </>
  );
}
