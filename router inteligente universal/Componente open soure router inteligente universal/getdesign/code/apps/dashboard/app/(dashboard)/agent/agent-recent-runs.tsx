import { getConvexClient } from "@/lib/convex-server";
import {
  type ListedDesignRun,
} from "@/lib/design-run-preview";
import { api } from "@convex/_generated/api";

import { AgentRecentRuns } from "./agent-command";

const RECENT_RUN_LIMIT = 3;

export async function AgentRecentRunsLoader({
  userId,
  accessToken,
}: {
  userId: string;
  accessToken: string;
}) {
  const recent = (await getConvexClient(accessToken).query(
    api.designRuns.listRecent,
    {
      userId,
      limit: RECENT_RUN_LIMIT,
    },
  )) as ListedDesignRun[];

  return (
    <AgentRecentRuns
      runs={recent.slice(0, RECENT_RUN_LIMIT).map((run) => ({
        id: String(run._id),
        domain: run.domain,
        status: run.status,
      }))}
    />
  );
}
