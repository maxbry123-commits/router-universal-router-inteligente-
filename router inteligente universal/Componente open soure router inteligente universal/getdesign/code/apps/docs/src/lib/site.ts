export const DOCS_ORIGIN = "https://docs.getdesign.app";
export const MARKETING_ORIGIN = "https://www.getdesign.app";
export const DASHBOARD_ORIGIN = "https://dashboard.getdesign.app";
export const API_ORIGIN = "https://api.getdesign.app";
export const GITHUB_ORIGIN = "https://github.com/MohtashamMurshid/getdesign";
// Reuse the existing branded PNG served by the marketing site.
export const SOCIAL_IMAGE = `${MARKETING_ORIGIN}/opengraph-image`;
export const SOCIAL_IMAGE_ALT = "getdesign · the design system for any URL";

/** NODE_ENV is production for Vercel preview builds as well. */
export function isProductionDeployment(env = process.env): boolean {
  return (env.VERCEL_TARGET_ENV ?? env.VERCEL_ENV) === "production";
}
