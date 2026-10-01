import { withAuth } from "@workos-inc/authkit-nextjs";
import { redirect } from "next/navigation";

import { api } from "@convex/_generated/api";
import { ExtractionGuide } from "@/components/extraction-guide";
import { hasRequiredRunCredentials } from "@/lib/credential-readiness";
import { getConvexClient } from "@/lib/convex-server";

type CredentialMeta = { provider: "daytona" | "openai" };

export async function ExtractionOnboarding({
  credentialsReady,
  keys: keysProp,
}: {
  credentialsReady?: boolean;
  keys?: ReadonlyArray<CredentialMeta>;
} = {}) {
  if (keysProp !== undefined) {
    return (
      <ExtractionGuide
        credentialsReady={hasRequiredRunCredentials(keysProp)}
        keys={keysProp}
      />
    );
  }

  if (credentialsReady !== undefined) {
    return <ExtractionGuide credentialsReady={credentialsReady} />;
  }

  const { accessToken, user } = await withAuth();
  if (!user || !accessToken) redirect("/sign-in");

  const keys = await getConvexClient(accessToken).query(
    api.userCredentials.listForUser,
    {},
  );

  return (
    <ExtractionGuide
      credentialsReady={hasRequiredRunCredentials(keys)}
      keys={keys}
    />
  );
}
