---
source_url: https://openbot.run/providers/local-models
fetched: 2026-10-25
tool: firecrawl_scrape (markdown)
---

# Ollama and LM Studio Agent App: Run Local Models in OpenBot

(Published 2026-10-03, author Norbert Bodziony.) Run a coding agent on a model from Ollama or LM Studio, in OpenBot on macOS, Windows or Linux. The model and your files stay on your computer.

## How to set it up

1. **Download OpenBot.** For macOS 13 or later on Apple silicon or Intel, Windows 10 or later on x64, or x64 or arm64 Linux.
2. **Connect Ollama and LM Studio.** Start Ollama or LM Studio. OpenBot looks at their usual addresses, 127.0.0.1:11434 and 127.0.0.1:1234, and shows the server under Found on this computer, in onboarding and in Settings. Press Add, and OpenCode runs your agents on its models.
3. **Give your agent a job.** Create an agent on Ollama and LM Studio, choose its model, and give it a task. OpenBot makes a workspace folder for it. When the work grows, add agents on other providers to the same channel.

## What OpenBot adds

- **Model requests stay on your computer.** With a local model, the requests go to a server on your computer, not to a provider. Any other OpenAI-compatible server works too.
- **Local and hosted models in one team.** Give the simple jobs to a local model, and the hard ones to Claude Code or Codex, in the same channel.
- **A team, not one chat.** Each agent has its own job and workspace. A lead agent gives parts of a task to other agents in a shared channel, and you step in when a decision needs you.
- **Your agents on your phone.** The OpenBot apps for iPhone and Android connect to the computer that runs your agents, over an encrypted connection, with no VPN. Remote access needs an OpenBot account.
- **Change the provider, keep the work.** Move an agent to a different provider and it keeps its role, workspace and conversation. Agents on different providers work in the same channel. When a plan reaches its limit, an agent can move to a backup model.
- **Your data on your computer.** Workspaces, chats and files stay on the computer that runs OpenBot. The provider you choose gets the requests you send.
- **Use your AI plans.** OpenBot is free for noncommercial use. Your agents use the plans you already pay for.

## Official apps

| App | Runs on | What it is |
| --- | --- | --- |
| Ollama | macOS 14+, Windows 10 22H2+, Linux | A model server with a chat app on macOS and Windows. Its OpenAI-compatible API supports tools. |
| LM Studio | macOS 14+ on Apple silicon, Windows x64 and Arm, Linux x64 and arm64 | A desktop app to download and chat with models, with a local server. Free at home and at work. |

Apps from Ollama and LM Studio, as checked on Oct 3, 2026 (per the source page).

## Every plan an agent can use

Choose a provider for each agent, and change it later: the agent keeps its role, workspace and conversation.

- Your own model: any OpenAI-compatible server, also one on your computer.
- ChatGPT: your ChatGPT plan, through Codex.
- Claude: your Claude plan, through Claude Code.
- Gemini: your Google AI Pro or Ultra plan.
- Grok: your Grok account or an xAI API key.
- Cursor: your Cursor plan, or a Cursor API key.
- OpenCode: free models, or an OpenCode Go key.
- Cline: your Cline account, or a Cline API key.
- Muse Code: your Meta account, or a Meta API key.
- Pi: included with OpenBot. Sign in to a provider with /login in Pi.
- Inception: Mercury models, with an Inception API key.
- Custom agent: any ACP agent, such as Goose, Qwen Code or GitHub Copilot.

## Comparisons

- [Best AI Agent Apps in 2026: 13 Apps Compared](https://openbot.run/compare/best-ai-agent-apps)

## Questions

**Can I use Ollama or LM Studio with a coding agent?** Yes. In OpenBot, OpenCode runs the agent on the OpenAI-compatible server of Ollama or LM Studio. Choose a model that supports tool calls: smaller models and models not trained for tools can send tool calls in the wrong format.

**How much context does a local model need?** More than the default. Ollama says that agents and coding tools need at least 64,000 tokens of context, and its default can be 4,000 tokens on a smaller graphics card. Set it higher in Ollama before you start.

**Does a local model need an account?** No. Ollama and LM Studio need no account for local models.

**Can I use a model server on another computer?** Yes. Add the address of any OpenAI-compatible server in OpenBot's settings, with a key if the server needs one.

## Sources (as listed by the page, checked Oct 3, 2026)

- [Ollama: download](https://ollama.com/download)
- [Ollama: macOS](https://docs.ollama.com/macos)
- [Ollama: Windows](https://docs.ollama.com/windows)
- [Ollama: OpenAI compatibility](https://docs.ollama.com/api/openai-compatibility)
- [Ollama: context length](https://docs.ollama.com/context-length)
- [Ollama: the new app](https://ollama.com/blog/new-app)
- [LM Studio: system requirements](https://lmstudio.ai/docs/app/system-requirements)
- [LM Studio: OpenAI compatibility](https://lmstudio.ai/docs/developer/openai-compat)
- [LM Studio: tool use](https://lmstudio.ai/docs/developer/openai-compat/tools)
- [LM Studio: free for work](https://lmstudio.ai/blog/free-for-work)

Other provider pages linked: muse-code, pi, inception, custom-agents, claude-code, codex, gemini, grok, cursor, opencode, cline (under https://openbot.run/providers/).
