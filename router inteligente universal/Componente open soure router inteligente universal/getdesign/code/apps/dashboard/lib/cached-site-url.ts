/** Match the exact public page, ignoring only its fragment and root slash. */
export function findCachedSite<T extends { slug: string; url: string }>(
  input: string,
  sites: readonly T[],
): T | undefined {
  try {
    const normalized = new URL(/^https?:\/\//i.test(input.trim()) ? input.trim() : `https://${input.trim()}`);
    normalized.hash = "";
    return sites.find(site => new URL(site.url).href === normalized.href);
  } catch {
    return undefined;
  }
}
