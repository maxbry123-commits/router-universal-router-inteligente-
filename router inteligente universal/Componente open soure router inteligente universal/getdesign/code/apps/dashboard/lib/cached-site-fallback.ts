/** Only undeployed local/preview backends may use the committed seed bundle. */
export function canUseBundledCatalog(
  env: { VERCEL_ENV?: string; NODE_ENV?: string },
  error?: unknown,
) {
  const nonProduction = env.VERCEL_ENV === "preview" ||
    (env.VERCEL_ENV !== "production" && env.NODE_ENV !== "production");
  if (!nonProduction) return false;
  return !error || (error instanceof Error && /Could not find public function.*cachedSites:(list|get)/.test(error.message));
}
