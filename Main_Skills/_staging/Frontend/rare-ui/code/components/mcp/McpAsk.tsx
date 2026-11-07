import McpCode from "@/components/mcp/McpCode";
import { MCP_ASK, MCP_PROMPT, MCP_PROMPT_DIRECT } from "@/lib/mcp";

const LABEL = "text-xs font-medium text-foreground/40";

export default function McpAsk() {
  return (
    <div className="flex flex-col gap-4">
      <div className="flex flex-col gap-2">
        <span className={LABEL}>Works</span>
        <McpCode value={MCP_PROMPT} />
        <McpCode value={MCP_ASK} />
      </div>

      <div className="flex flex-col gap-2">
        <span className={LABEL}>Won&apos;t find it</span>
        <div className="flex items-center gap-3 rounded-lg border border-dashed border-foreground/10 px-3 py-2.5">
          <code className="font-mono text-xs text-foreground/40 line-through decoration-foreground/30">
            {MCP_PROMPT_DIRECT}
          </code>
          <span className="ml-auto text-xs text-foreground/40">
            searches the default shadcn registry
          </span>
        </div>
      </div>
    </div>
  );
}
