"use client";

import { useState } from "react";
import CodeBlock from "@/components/ui/code-block";
import { LOGOS } from "@/components/logos";
import McpCode from "@/components/mcp/McpCode";
import McpText from "@/components/mcp/McpText";
import { MCP_CLIENTS } from "@/lib/mcp";
import { cn } from "@/lib/utils";

export default function McpClients() {
  const [active, setActive] = useState(MCP_CLIENTS[0].id);
  const current =
    MCP_CLIENTS.find((client) => client.id === active) ?? MCP_CLIENTS[0];

  return (
    <div className="flex flex-col gap-3">
      <div role="tablist" className="flex flex-wrap items-center gap-1">
        {MCP_CLIENTS.map((client) => {
          const selected = client.id === active;
          const Logo = LOGOS[client.logo];
          return (
            <button
              key={client.id}
              type="button"
              role="tab"
              aria-selected={selected}
              onClick={() => setActive(client.id)}
              data-active={selected}
              style={selected && client.color ? { color: client.color } : undefined}
              className={cn(
                "flex cursor-pointer items-center gap-1.5 rounded-md px-2 py-1 text-xs font-medium transition-colors",
                selected
                  ? "bg-muted text-foreground"
                  : "text-foreground/40 hover:text-foreground/70",
              )}
            >
              <Logo className="size-3.5" />
              {client.label}
            </button>
          );
        })}
      </div>

      <div role="tabpanel" className="flex flex-col gap-3">
        <McpText>{current.hint}</McpText>
        {current.command ? <McpCode value={current.command} /> : null}
        {current.config ? (
          <CodeBlock
            code={current.config}
            language="toml"
            showFrame={false}
            showLineNumbers={false}
            className="rounded-lg bg-muted p-3"
          />
        ) : null}
      </div>
    </div>
  );
}
