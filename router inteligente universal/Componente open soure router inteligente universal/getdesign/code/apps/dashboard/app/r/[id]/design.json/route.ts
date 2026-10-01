import { loadPublicRun, PUBLIC_RUN_HEADERS, publicRequestOrigin } from "@/lib/public-runs";

export const dynamic = "force-dynamic";

export async function GET(request: Request, { params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  const run = await loadPublicRun(id, publicRequestOrigin(request));
  if (!run) return Response.json({ error: "Run not found." }, { status: 404, headers: PUBLIC_RUN_HEADERS });
  return Response.json(run, { headers: PUBLIC_RUN_HEADERS });
}
