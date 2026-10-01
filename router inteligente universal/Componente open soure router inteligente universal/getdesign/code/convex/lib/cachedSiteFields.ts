import { v } from "convex/values";

export const cachedSiteSummaryFields = {
  slug: v.string(), title: v.string(), url: v.string(), capturedAt: v.string(),
  images: v.array(v.object({ url: v.string(), alt: v.string(), width: v.number(), height: v.number() })),
  summary: v.string(), colors: v.array(v.string()), mode: v.literal("visual"), tiles: v.number(),
};
export const cachedSiteFields = { ...cachedSiteSummaryFields, markdown: v.string() };
