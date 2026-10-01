"use client"

import { useState } from "react"
import { HugeiconsIcon } from "@hugeicons/react"
import {
  ArrowDown01Icon,
  Copy01Icon,
  Download01Icon,
} from "@hugeicons/core-free-icons"

import {
  downloadDesignBundle,
  downloadPlainMarkdown,
  exportMarkdownFilename,
  exportZipFilename,
  prepareDesignDownload,
} from "@/lib/download-design-md"
import { Button } from "@/components/ui/button"
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuGroup,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu"

function clipboardMarkdown(content: string) {
  return content.replace(/(!\[[^\]]*\]\()\/(?!\/)([^)]+)\)/g,
    (_match, prefix: string, path: string) => `${prefix}${window.location.origin}/${path})`)
}

export function ExportActions({
  content,
  siteName,
}: {
  content: string
  siteName: string
}) {
  const [copied, setCopied] = useState(false)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const hasImages = content.includes("![")

  const handleCopy = async (withImages: boolean) => {
    setBusy(true)
    setError(null)
    try {
      const source = clipboardMarkdown(content)
      const text = withImages
        ? (await prepareDesignDownload(source, false)).markdown
        : source
      await navigator.clipboard.writeText(text)
      setCopied(true)
      window.setTimeout(() => setCopied(false), 1500)
    } catch {
      setError("Copy failed. Please retry.")
    } finally {
      setBusy(false)
    }
  }

  const handleDownload = async (withImages: boolean) => {
    setBusy(true)
    setError(null)
    try {
      if (withImages) {
        await downloadDesignBundle(
          content,
          exportZipFilename(siteName),
          exportMarkdownFilename(siteName),
        )
      } else {
        downloadPlainMarkdown(
          clipboardMarkdown(content),
          exportMarkdownFilename(siteName),
        )
      }
    } catch {
      setError("Download failed. Please retry.")
    } finally {
      setBusy(false)
    }
  }

  return (
    <div className="flex items-center gap-2">
      {error ? <span role="alert" className="text-xs text-destructive">{error}</span> : null}
      {copied ? <span className="text-xs text-muted-foreground">Copied</span> : null}
      <DropdownMenu>
        <DropdownMenuTrigger
          disabled={busy}
          render={
            <Button
              variant="outline"
              size="sm"
              aria-label="Download"
            />
          }
        >
          <HugeiconsIcon icon={Download01Icon} />
          Download
          <HugeiconsIcon icon={ArrowDown01Icon} data-icon="inline-end" />
        </DropdownMenuTrigger>
        <DropdownMenuContent align="end" className="w-44">
          <DropdownMenuGroup>
            <DropdownMenuLabel>Download</DropdownMenuLabel>
            <DropdownMenuItem
              disabled={busy}
              onClick={() => void handleDownload(false)}
            >
              <HugeiconsIcon icon={Download01Icon} />
              Without images
            </DropdownMenuItem>
            {hasImages ? (
              <DropdownMenuItem
                disabled={busy}
                onClick={() => void handleDownload(true)}
              >
                <HugeiconsIcon icon={Download01Icon} />
                With images
              </DropdownMenuItem>
            ) : null}
          </DropdownMenuGroup>
          <DropdownMenuSeparator />
          <DropdownMenuGroup>
            <DropdownMenuLabel>Copy</DropdownMenuLabel>
            <DropdownMenuItem
              disabled={busy}
              onClick={() => void handleCopy(false)}
            >
              <HugeiconsIcon icon={Copy01Icon} />
              Without images
            </DropdownMenuItem>
            {hasImages ? (
              <DropdownMenuItem
                disabled={busy}
                onClick={() => void handleCopy(true)}
              >
                <HugeiconsIcon icon={Copy01Icon} />
                With images
              </DropdownMenuItem>
            ) : null}
          </DropdownMenuGroup>
        </DropdownMenuContent>
      </DropdownMenu>
    </div>
  )
}
