import type { Metadata } from "next";
import { Suspense } from "react";
import { withAuth } from "@workos-inc/authkit-nextjs";
import { UserProfile } from "@workos-inc/widgets";
import { redirect } from "next/navigation";

import { api } from "@convex/_generated/api";
import { WidgetLoadingGate } from "@/components/widget-loading-gate";
import { WorkOsWidgetsProvider } from "@/components/workos-widgets-provider";
import { ProviderKeysSkeleton } from "@/components/dashboard-skeletons";
import { getConvexClient } from "@/lib/convex-server";
import { hasRequiredRunCredentials } from "@/lib/credential-readiness";

import { DeveloperSurfaces } from "./developer-surfaces";
import { ProviderKeysCard } from "./provider-keys-card";
import { SettingsSection, SettingsShell } from "./settings-shell";

async function ProviderKeys({ accessToken }: { accessToken: string }) {
  const keys = await getConvexClient(accessToken).query(
    api.userCredentials.listForUser,
    {},
  );

  return (
    <ProviderKeysCard
      keys={keys}
      credentialsReady={hasRequiredRunCredentials(keys)}
    />
  );
}

export const metadata: Metadata = { title: "Account" };

export default async function AccountPage() {
  const { accessToken, user } = await withAuth();

  if (!user || !accessToken) {
    redirect("/sign-in");
  }

  return (
    <SettingsShell>
      <Suspense fallback={<ProviderKeysSkeleton />}>
        <ProviderKeys accessToken={accessToken} />
      </Suspense>
      <SettingsSection
        id="account"
        title="Account"
        description="Name, email, and password for this dashboard login."
      >
        <WorkOsWidgetsProvider>
          <WidgetLoadingGate>
            <UserProfile authToken={accessToken} />
          </WidgetLoadingGate>
        </WorkOsWidgetsProvider>
      </SettingsSection>
      <DeveloperSurfaces />
    </SettingsShell>
  );
}
