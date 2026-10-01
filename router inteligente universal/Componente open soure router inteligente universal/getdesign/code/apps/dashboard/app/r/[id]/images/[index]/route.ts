import { api } from "@convex/_generated/api";
import { getConvexClient } from "@/lib/convex-server";
import { PUBLIC_RUN_HEADERS } from "@/lib/public-runs";

export const dynamic = "force-dynamic";

export async function GET(_request: Request, { params }: { params: Promise<{ id: string; index: string }> }) {
  const { id, index } = await params;
  if (!/^\d+$/.test(index) || !Number.isSafeInteger(Number(index))) {
    return new Response("Image not found.", { status: 404, headers: PUBLIC_RUN_HEADERS });
  }
  const image = await getConvexClient().action(api.publicRuns.image, { id, index: Number(index) });
  if (!image) return new Response("Image not found.", { status: 404, headers: PUBLIC_RUN_HEADERS });
  return new Response(image.bytes, { headers: { ...PUBLIC_RUN_HEADERS, "Content-Type": image.contentType } });
}
