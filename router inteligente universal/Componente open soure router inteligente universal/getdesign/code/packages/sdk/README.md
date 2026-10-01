# @getdesign/sdk

> Generate production-ready `design.md` specs from live websites.

`@getdesign/sdk` captures a rendered landing page, analyzes visual style and CSS
tokens, and returns a structured design system plus ready-to-save markdown. It
runs on your own machine or server with request-scoped Daytona and OpenAI
credentials, so your keys stay under your control.

## Install

```bash
bun add @getdesign/sdk
```

Runtime note: the SDK currently targets Bun/server environments with enough time
for browser capture and LLM generation. It is not a browser or edge-runtime
client.

## Preview

```ts
import { getDesign } from "@getdesign/sdk";

const system = await getDesign("https://cursor.com", {
  credentials: {
    daytonaApiKey: process.env.DAYTONA_API_KEY,
    openaiApiKey: process.env.OPENAI_API_KEY,
  },
});
console.log(system.markdown);
```

## Streaming

```ts
import { streamDesign } from "@getdesign/sdk";

for await (const event of streamDesign("https://linear.app", {
  credentials: {
    daytonaApiKey: process.env.DAYTONA_API_KEY,
    openaiApiKey: process.env.OPENAI_API_KEY,
  },
})) {
  if (event.type === "progress") console.log(event.event);
  if (event.type === "result") console.log(event.result.markdown);
}
```

MIT © getdesign

## Save the document and its images

Visual results include actual hero and full-page captures in `images`. Each entry contains `path`, `alt`, `mimeType`, `imageBase64`, `width`, and `height`. Markdown references those relative paths. Save both the document and its files:

```ts
import { mkdir, writeFile } from "node:fs/promises";
import { dirname, join } from "node:path";

const output = "./design-output";
await mkdir(output, { recursive: true });
for (const image of system.images) {
  const path = join(output, image.path);
  await mkdir(dirname(path), { recursive: true });
  await writeFile(path, Buffer.from(image.imageBase64, "base64"));
}
await writeFile(join(output, "design.md"), system.markdown);
```

`streamDesign` includes the same files in its final `result`; progress events remain small and contain no image bytes. Normal runs fail if capture is unavailable, including when no Daytona key is configured. Only an explicit `visualRequirement: "text_only_fallback"` skips images and returns `mode: "text_only"` with an empty `images` array.
