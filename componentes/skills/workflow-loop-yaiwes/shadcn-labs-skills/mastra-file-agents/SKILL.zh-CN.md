---
name: mastra-file-agents
description: >-
  将使用 new Agent 构建并在 Mastra agents 映射中注册的 Mastra agent 迁移到 src/mastra/agents 下的一 agent 一目录布局。
  当用户要求基于文件的 agent、agentConfig、按目录划分的 agent 布局，或拆分 src/mastra/index.ts 或 agents.ts 时使用。
  需要 @mastra/core 1.48 或更高版本。
compatibility: 使用 @mastra/core 1.48.0 或更高版本的 Mastra 项目。文件发现依赖 mastra dev 或 mastra build。
---

> English: [SKILL.md](SKILL.md)

# 将 Mastra agent 迁移到基于文件的目录

把使用 `new Agent({...})` 构建并在 `new Mastra({ agents: {...} })` 映射中注册的 agent，转换为 `src/mastra/agents/<name>/` 下的一 agent 一目录。同目录下的兄弟文件取代旧的构造器选项。

保持 agent 的行为不变。把每个选项移到拥有它的文件，保持相同的模型、指令、工具、记忆、技能与子 agent，不要发明 agent 原本没有的配置。

## 先检查发现机制与冲突

### 确认发现路径

Mastra 打包器在 `mastra dev` 和 `mastra build` 期间发现基于文件的 agent。当应用直接导入 `mastra` 实例时——比如作为库、自定义服务器或测试——它不会发现它们。迁移前先确认应用的运行方式。对被直接导入的 agent 保持代码注册并说明原因。

### 消除代码冲突

当同一个 agent 同时存在于基于文件的目录中时，代码注册优先。Mastra 会记录一条警告并忽略该目录。在第 5 步把该 agent 从 `Mastra({ agents })` 映射中移除之前，迁移不会生效。

## 工作流程

一次处理一个 agent。复制这份清单并跟踪进度：

```
Migration progress for <agent>:
- [ ] Confirmed the app runs through mastra dev or mastra build
- [ ] Created src/mastra/agents/<name>/
- [ ] config.ts uses agentConfig and keeps the model plus remaining config
- [ ] Static instructions moved to instructions.md, or dynamic instructions stayed in config.ts
- [ ] Each tools/*.ts file has one default export and uses the tool key as its name
- [ ] Moved memory, workspace, skills, and subagents when present
- [ ] Removed the agent from the Mastra({ agents }) map
- [ ] Deleted dead imports and the old agent file when nothing else uses it
- [ ] Verified with mastra dev
```

### 第 1 步：找到基于代码的 agent

定位每一个 `new Agent({...})` 及其注册方式。注册通常位于 `src/mastra/index.ts` 中的 `new Mastra({ agents: { ... } })` 之内，但 agent 也可能定义在 `src/mastra/agents/*.ts` 文件或一个大型 `agents.ts` 文件中再被导入。完整阅读每个 agent 的 `Agent` 配置，让每个选项都有去处。记录 `agents` 映射中使用的键。该键控制 `mastra.getAgent('weather')`、Studio 与客户端 SDK 中的注册与查找，它还会成为目录名。

### 第 2 步：创建目录并拆分配置

对于注册为 `agents: { weather: weatherAgent }` 的 agent，创建 `src/mastra/agents/weather/`。

目录以映射键命名，而不是 `id`。目录名会成为 agent 的注册/查找键，因此使用映射键可以保住每一个既有的 `getAgent(...)` 调用与客户端引用。当映射键与 `id` 不同时这一点很重要：对 `agents: { browserAgent }` 搭配 `new Agent({ id: 'browser-agent' })`，目录名应为 `browserAgent`。在 `config.ts` 中显式设置 `id` 与 `name`，以保留原有的 `'browser-agent'` 和 `'Browser Agent'` 值。如果映射键与 `id` 本来就一致，两个值都默认取目录名，可以省略。

#### config.ts

把内联指令与工具之外的一切移入 `config.ts`。使用 `agentConfig()` 让这个 partial 是类型化的，其余由兄弟文件补齐：

```typescript
import { agentConfig } from '@mastra/core/agent'

export default agentConfig({
  model: 'openai/gpt-5.5',
  // instructions come from instructions.md
  // tools come from tools/*.ts
})
```

`model` 是必填的。缺失 model 会让构建失败并指名目录。

#### instructions.md

如果原来的 `instructions` 是一个字符串、静态字符串数组或消息数组，把文本移入 `instructions.md`，并从 config.ts 中省略 `instructions`。`instructions.md` 优先于静态 `instructions` 字符串，两个都留是冗余的。

如果原来的 `instructions` 是一个读取运行时上下文的函数，它不能放进 `instructions.md`。把它保留在 `config.ts` 中，因为动态函数指令优先于 `instructions.md`。见 `references/mapping.md`。

### 第 3 步：拆分工具

每个工具在 `tools/` 下有自己的文件，为 `createTool()` 调用提供默认导出。文件名即工具键，因此使用原 `tools` 映射中的键或工具自身的 `id`。如果原来是 `tools: { get_weather: getWeatherTool }`，文件必须是 `tools/get_weather.ts`。

```typescript
import { createTool } from '@mastra/core/tools'
import { z } from 'zod'

export default createTool({
  id: 'get_weather',
  description: 'Get the current weather for a city',
  inputSchema: z.object({ city: z.string() }),
  execute: async ({ context }) => ({ city: context.city, tempC: 21 }),
})
```

来自 `tools/*.ts` 的工具与任何 `config.tools` 合并。键冲突时 `config.tools` 优先且 Mastra 记录警告，所以不要把一个工具同时列在两处。如果 `config.tools` 是函数，Mastra 忽略发现的工具文件。那种情况下把工具留在 config.ts 并说明。`*.test.ts` 与 `*.spec.ts` 等测试文件会被发现机制忽略。

并非每个工具都是 `createTool()`。`openai.tools.webSearch({})` 等提供商原生工具及其他预构建工具对象不符合 `createTool()` 的形状。要么把它们内联保留在 `config.tools` 中，要么从 `tools/<key>.ts` 文件默认导出该工具对象。两种形式 Mastra 都能发现。拿不准时，把提供商工具保留在 `config.tools` 是最简单忠实的做法。把 `tools/*.ts` 文件留给项目自己的 `createTool()` 定义。

如果一个工具被多个 agent 共享，不要强行塞进某一个 agent 的 `tools/`。把共享工具放在公共模块中从 `config.tools` 引用，或有意识地复制一份。把你的选择告知用户。

### 第 4 步：处理其余配置

记忆、工作区、技能与子 agent 各有自己的文件/目录与优先级规则。当你迁移的 agent 用到了其中任何一个，阅读 [references/mapping.md](references/mapping.md) 获取精确映射，包括动态配置、子 agent 描述与种子文件。迁移期间不要丢弃它们。丢失一个 agent 的记忆或子 agent 会静默改变行为。

### 第 5 步：移除代码注册

这一步完成迁移。从 `Mastra({ agents: {...} })` 映射中删除该 agent 的条目，然后移除现在已无用的导入与定义。如果旧的 `new Agent(...)` 位于自己的文件中且没有其他地方导入它，删除该文件。

当应用直接导入某个 agent、动态注册它或在别处共享该实例时，把它保留在代码注册中。代码与基于文件的 agent 可以共存。

### 第 6 步：验证

通过 CLI 运行应用，让打包器发现新目录：

```bash
npx mastra dev
```

在无法启动开发服务器时，`npx mastra build` 是一个好的非交互检查。它运行同样的发现机制，并在缺失模型、缺失子 agent 描述或目录无法解析时失败。如果你的环境没有安装依赖，如实说明并把验证标注为仅结构性检查，而不是声称它跑得起来。

确认每个迁移后的 agent 仍以原有注册键出现并能响应。检查没有出现 "code agent overrides file-based" 或 "config.X wins" 警告。那些警告意味着残留冲突或冗余配置条目。在宣告完成之前修掉警告。

## 映射速查表

| `new Agent({...})` 选项 | 基于文件的位置 |
| --- | --- |
| agents 映射键 | 目录名；保留注册与查找键 |
| `id` / `name` | 默认取目录名；与文件夹不一致时在 `config.ts` 中设置 |
| `model` | `config.ts` 中必填 |
| 静态 `instructions` | `instructions.md` |
| 指令函数 | 保留在 `config.ts` |
| `description` | `config.ts`；子 agent 必填 |
| `tools: { key: createTool(...) }` | `tools/<key>.ts` 作为默认导出 |
| 提供商或预构建工具 | 保留在 `config.tools`，或从 `tools/<key>.ts` 默认导出 |
| `skills` | `skills/`；见 references/mapping.md |
| `memory` | `memory.ts`；见 references/mapping.md |
| `workspace` | `workspace.ts` + `workspace/` 种子文件 |
| 委派的 `agents` | `subagents/<childId>/` |
| 其余一切 | `config.ts` 经由 `agentConfig()` |
