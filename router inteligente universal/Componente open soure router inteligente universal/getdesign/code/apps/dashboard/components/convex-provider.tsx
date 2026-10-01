"use client";

import { ConvexProviderWithAuth, ConvexReactClient } from "convex/react";
import { useAccessToken, useAuth } from "@workos-inc/authkit-nextjs/components";
import { useCallback, useMemo } from "react";

function useConvexWorkOsAuth() {
  const { user, loading } = useAuth();
  const { getAccessToken, refresh } = useAccessToken();
  const fetchAccessToken = useCallback(
    async ({ forceRefreshToken }: { forceRefreshToken: boolean }) => {
      if (!user) return null;
      try {
        return (await (forceRefreshToken ? refresh() : getAccessToken())) ?? null;
      } catch {
        return null;
      }
    },
    [user, getAccessToken, refresh],
  );
  return { isLoading: loading, isAuthenticated: !!user, fetchAccessToken };
}

export function DashboardConvexProvider({
  children,
}: {
  children: React.ReactNode;
}) {
  const convex = useMemo(() => {
    const url = process.env.NEXT_PUBLIC_CONVEX_URL;
    if (!url) {
      throw new Error("Missing NEXT_PUBLIC_CONVEX_URL.");
    }
    return new ConvexReactClient(url);
  }, []);

  return (
    <ConvexProviderWithAuth client={convex} useAuth={useConvexWorkOsAuth}>
      {children}
    </ConvexProviderWithAuth>
  );
}
