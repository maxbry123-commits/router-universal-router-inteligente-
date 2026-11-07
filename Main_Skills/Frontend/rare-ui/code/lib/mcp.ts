import type { LogoName } from "@/components/logos";

export const MCP_REGISTRY_URL =
  "https://raw.githubusercontent.com/swamimalode07/rare-ui/main/public/r/{name}.json";

export const MCP_COMPONENTS_JSON = `{
  "registries": {
    "@rare-ui": "${MCP_REGISTRY_URL}"
  }
}`;

export const MCP_CODEX = `[mcp_servers.shadcn]
command = "npx"
args = ["shadcn@latest", "mcp"]`;

export type McpClient = {
  id: string;
  label: string;
  logo: LogoName;
  color?: string;
  hint: string;
  command?: string;
  config?: string;
};

export const MCP_CLIENTS: McpClient[] = [
  {
    id: "claude",
    logo: "claude",
    color: "#D97757",
    label: "Claude Code",
    hint: "Run this in your project, then restart Claude Code. `/mcp` should list shadcn as connected.",
    command: "npx shadcn@latest mcp init --client claude",
  },
  {
    id: "cursor",
    logo: "cursor",
    label: "Cursor",
    hint: "Run this in your project, then enable shadcn in Cursor's MCP settings.",
    command: "npx shadcn@latest mcp init --client cursor",
  },
  {
    id: "vscode",
    logo: "vscode",
    color: "#007ACC",
    label: "VS Code",
    hint: "Run this in your project, then open `.vscode/mcp.json` and click Start next to shadcn.",
    command: "npx shadcn@latest mcp init --client vscode",
  },
  {
    id: "codex",
    logo: "openai",
    label: "Codex",
    hint: "Codex can't write its own config. Add this to `~/.codex/config.toml`, then restart Codex.",
    config: MCP_CODEX,
  },
];

export const MCP_PROMPT_DIRECT = "add fluid-orb";

export const MCP_PROMPT = "add @rare-ui/fluid-orb";

export const MCP_ASK = "Add the fluid orb from Rare UI";

export const MCP_CLI =
  "npx shadcn@latest add swamimalode07/rare-ui/fluid-orb";
