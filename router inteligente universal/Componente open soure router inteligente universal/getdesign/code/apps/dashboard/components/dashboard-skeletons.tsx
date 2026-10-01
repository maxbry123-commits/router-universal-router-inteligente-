import Link from "next/link";

import { DeveloperSurfaces } from "@/app/(dashboard)/account/developer-surfaces";
import {
  SettingsGroup,
  SettingsSection,
  SettingsShell,
} from "@/app/(dashboard)/account/settings-shell";
import { AgentInputPlaceholder } from "@/components/agent-input-placeholder";
import { BrandMark } from "@/components/brand-mark";
import { buttonVariants } from "@/components/ui/button";
import {
  Breadcrumb,
  BreadcrumbItem,
  BreadcrumbLink,
  BreadcrumbList,
  BreadcrumbPage,
  BreadcrumbSeparator,
} from "@/components/ui/breadcrumb";
import { Skeleton } from "@/components/ui/skeleton";
import { OVERVIEW_RUN_QUERY_LIMIT } from "@/lib/design-run-preview";

function PageHeader({
  title,
  parent,
  parentHref,
  action,
  tall,
}: {
  title?: string;
  parent?: string;
  parentHref?: string;
  action?: React.ReactNode;
  tall?: boolean;
}) {
  return (
    <header
      className={`flex shrink-0 items-center gap-2 border-b px-4 ${tall ? "h-16" : "h-14"}`}
    >
      <Breadcrumb className="min-w-0">
        <BreadcrumbList>
          {parent && parentHref ? (
            <>
              <BreadcrumbItem>
                <BreadcrumbLink href={parentHref}>{parent}</BreadcrumbLink>
              </BreadcrumbItem>
              <BreadcrumbSeparator />
              <BreadcrumbItem>
                <Skeleton className="h-3 w-28" />
              </BreadcrumbItem>
            </>
          ) : (
            <BreadcrumbItem>
              <BreadcrumbPage>{title}</BreadcrumbPage>
            </BreadcrumbItem>
          )}
        </BreadcrumbList>
      </Breadcrumb>
      {action}
    </header>
  );
}

function StatCard({
  label,
  href,
}: {
  label: string;
  href?: string;
}) {
  const body = (
    <>
      <p className="text-xs text-muted-foreground">{label}</p>
      <Skeleton className="mt-1 h-7 w-10" />
    </>
  );
  const className = "rounded-xl border px-4 py-3";
  if (!href) {
    return <div className={className}>{body}</div>;
  }
  return (
    <Link href={href} className={`${className} transition-colors hover:bg-muted/30`}>
      {body}
    </Link>
  );
}

function RunRowSkeleton() {
  return (
    <div className="flex items-center gap-3 px-4 py-2">
      <Skeleton className="h-10 w-16 shrink-0 rounded-md sm:w-20" />
      <div className="min-w-0 flex-1 space-y-1.5">
        <Skeleton className="h-4 w-40 max-w-full" />
        <Skeleton className="h-3 w-24" />
      </div>
      <Skeleton className="h-3 w-12" />
      <Skeleton className="hidden h-3 w-16 sm:block" />
    </div>
  );
}

function SiteCardSkeleton() {
  return (
    <div className="overflow-hidden rounded-xl border">
      <Skeleton className="aspect-[16/10] w-full rounded-none" />
      <Skeleton className="h-2 w-full rounded-none" />
      <div className="space-y-2 p-4">
        <div className="flex items-baseline justify-between gap-3">
          <Skeleton className="h-4 w-28" />
          <Skeleton className="h-3 w-20" />
        </div>
        <Skeleton className="h-3 w-full" />
        <Skeleton className="h-3 w-2/3" />
      </div>
    </div>
  );
}

function ExtractAction() {
  return (
    <Link
      href="/agent"
      className={buttonVariants({
        size: "lg",
        className: "ml-auto",
      })}
    >
      Extract
    </Link>
  );
}

export function OverviewLoading() {
  return (
    <>
      <PageHeader title="Overview" />
      <div className="flex flex-1 flex-col gap-6 p-6">
        <section aria-label="Overview stats" className="grid grid-cols-2 gap-3 sm:grid-cols-4">
          <StatCard label="Cached sites" href="/sites" />
          <StatCard label="Your runs" href="/runs" />
          <StatCard label="Completed" />
          <StatCard label="Failed" />
        </section>
        <section aria-busy="true" aria-label="Loading recent runs" className="rounded-xl border">
          <div className="flex flex-wrap items-center justify-between gap-x-4 gap-y-2 border-b px-4 py-2.5">
            <div className="min-w-0">
              <h2 className="text-sm font-medium">Recent runs</h2>
              <p className="mt-0.5 text-xs text-muted-foreground">
                Completed runs with design files from your latest {OVERVIEW_RUN_QUERY_LIMIT} runs.
              </p>
            </div>
            <Link
              href="/runs"
              className="shrink-0 text-xs font-medium text-foreground underline-offset-4 hover:underline"
            >
              Browse all runs
            </Link>
          </div>
          <div className="divide-y">
            {Array.from({ length: 6 }, (_, index) => (
              <RunRowSkeleton key={index} />
            ))}
          </div>
        </section>
        <section>
          <div className="mb-4 flex flex-wrap items-end justify-between gap-3">
            <div>
              <h2 className="text-sm font-medium">Examples</h2>
              <p className="mt-1 text-xs text-muted-foreground">
                Cached design systems from public sites. Open or download without running an extraction.
              </p>
            </div>
            <Link
              href="/sites"
              className="text-xs font-medium text-foreground underline-offset-4 hover:underline"
            >
              Browse all examples
            </Link>
          </div>
          <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 xl:grid-cols-4">
            {Array.from({ length: 4 }, (_, index) => (
              <SiteCardSkeleton key={index} />
            ))}
          </div>
        </section>
      </div>
    </>
  );
}

export function RunsLoading() {
  return (
    <>
      <PageHeader title="Runs" action={<ExtractAction />} />
      <div className="flex flex-1 flex-col gap-6 p-6">
        <section aria-busy="true" aria-label="Loading runs" className="rounded-xl border">
          <div className="flex flex-wrap items-center justify-between gap-x-4 gap-y-2 border-b px-4 py-2.5">
            <div className="min-w-0">
              <h2 className="text-sm font-medium">Recent runs</h2>
              <p className="mt-0.5 text-xs text-muted-foreground">
                Extractions from your account.
              </p>
            </div>
          </div>
          <div className="divide-y">
            {Array.from({ length: 8 }, (_, index) => (
              <RunRowSkeleton key={index} />
            ))}
          </div>
        </section>
      </div>
    </>
  );
}

export function SitesLoading() {
  return (
    <>
      <PageHeader title="Examples" />
      <div className="flex flex-1 flex-col gap-6 p-6">
        <section aria-busy="true" aria-label="Loading examples">
          <div className="mb-4">
            <h2 className="text-sm font-medium">Examples</h2>
            <p className="mt-1 text-xs text-muted-foreground">
              Cached design systems from public sites. Open or download without running an extraction.
            </p>
          </div>
          <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 xl:grid-cols-3">
            {Array.from({ length: 6 }, (_, index) => (
              <SiteCardSkeleton key={index} />
            ))}
          </div>
        </section>
      </div>
    </>
  );
}

export function AgentRecentRunsSkeleton() {
  return (
    <section aria-busy="true" aria-label="Loading recent runs" className="mt-8">
      <div className="mb-1 flex items-center gap-2">
        <h2 className="text-xs font-medium text-muted-foreground">Recent</h2>
        <Link href="/runs" className="text-xs text-muted-foreground hover:text-foreground">
          All
        </Link>
      </div>
      <ul>
        {Array.from({ length: 3 }, (_, index) => (
          <li key={index} className="flex items-center justify-between gap-3 py-1.5">
            <Skeleton className="h-3 w-36" />
            <Skeleton className="h-3 w-14" />
          </li>
        ))}
      </ul>
    </section>
  );
}

export function AgentLoading() {
  return (
    <div className="mx-auto flex min-h-[calc(100svh-3.5rem)] w-full max-w-xl flex-col justify-center px-4 py-8">
      <div className="mb-8 flex justify-center">
        <BrandMark size={34} />
      </div>
      <AgentInputPlaceholder />
      <AgentRecentRunsSkeleton />
    </div>
  );
}

function DocumentColumnSkeleton({
  parent,
  parentHref,
}: {
  parent: string;
  parentHref: string;
}) {
  return (
    <div className="flex min-h-svh flex-1 items-stretch">
      <div className="flex min-w-0 flex-1 flex-col">
        <PageHeader parent={parent} parentHref={parentHref} />
        <div className="flex min-w-0 flex-1 justify-center p-6">
          <div className="mx-auto w-full max-w-3xl space-y-4">
            <Skeleton className="h-8 w-64 max-w-full" />
            <Skeleton className="h-4 w-full" />
            <Skeleton className="h-4 w-full" />
            <Skeleton className="h-4 w-5/6" />
            <Skeleton className="mt-8 h-5 w-40" />
            <Skeleton className="h-4 w-full" />
            <Skeleton className="h-4 w-4/5" />
            <Skeleton className="mt-8 aspect-[16/10] w-full" />
          </div>
        </div>
      </div>
      <aside
        aria-busy="true"
        aria-label="Loading gallery"
        className="sticky top-0 hidden h-svh w-[320px] shrink-0 self-start border-l lg:flex lg:flex-col"
      >
        <div className="flex h-12 items-center gap-2 border-b px-3">
          <p className="text-xs font-semibold tracking-tight">Gallery</p>
        </div>
        <div className="flex flex-col gap-2 p-2">
          {Array.from({ length: 4 }, (_, index) => (
            <Skeleton key={index} className="aspect-[16/10] w-full" />
          ))}
        </div>
      </aside>
    </div>
  );
}

export function RunDetailLoading() {
  return <DocumentColumnSkeleton parent="Runs" parentHref="/runs" />;
}

export function SiteDetailLoading() {
  return <DocumentColumnSkeleton parent="Examples" parentHref="/sites" />;
}

export function ProviderKeysSkeleton() {
  return (
    <SettingsSection
      id="provider-keys"
      title="Provider keys"
      description="Dashboard runs use these keys. They are encrypted at rest and never shown again after you save."
    >
      <SettingsGroup>
        <div
          aria-busy="true"
          aria-label="Loading provider keys"
          className="divide-y"
        >
          <div className="px-4 py-3">
            <p className="text-sm font-medium">Daytona</p>
            <Skeleton className="mt-2 h-7 max-w-sm" />
          </div>
          <div className="px-4 py-3">
            <p className="text-sm font-medium">OpenAI</p>
            <Skeleton className="mt-2 h-7 max-w-sm" />
          </div>
        </div>
      </SettingsGroup>
    </SettingsSection>
  );
}

export function WidgetFallback() {
  return (
    <SettingsGroup>
      <div aria-busy="true" aria-label="Loading" className="divide-y">
        {Array.from({ length: 5 }, (_, index) => (
          <div key={index} className="px-4 py-3">
            <Skeleton className="h-5 w-full" />
          </div>
        ))}
      </div>
    </SettingsGroup>
  );
}

export function AccountLoading() {
  return (
    <SettingsShell>
      <ProviderKeysSkeleton />
      <SettingsSection
        id="account"
        title="Account"
        description="Name, email, and password for this dashboard login."
      >
        <WidgetFallback />
      </SettingsSection>
      <DeveloperSurfaces />
    </SettingsShell>
  );
}

export function TeamLoading() {
  return (
    <>
      <PageHeader title="Team" tall />
      <div className="flex flex-1 flex-col gap-4 p-4 pt-0">
        <WidgetFallback />
      </div>
    </>
  );
}
