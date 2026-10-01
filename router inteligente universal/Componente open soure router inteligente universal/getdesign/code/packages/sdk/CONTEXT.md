# sdk — domain glossary

Terms and naming for the TypeScript SDK workspace (`packages/sdk`). Expand as the domain stabilizes.

## Terms

- **Execution SDK** — The v1 public TypeScript interface for getdesign. It runs the agent pipeline in-process on the caller's machine or server.
- **Design request** — A URL plus optional site name, visual fallback mode, measurement options, and request-scoped BYOK credentials.
- **Design result** — The final `design.md` markdown plus structured `DesignDoc`, extracted tokens, visual description metadata, tile count, and run mode.
- **Design stream event** — Public SSE event from `/v1/design/stream`. Progress events omit screenshot image data and credentials. Final results include captured image files, which are required in visual mode.
- **Fetch adapter** — Optional concrete `fetch` implementation passed to the SDK for tests and non-standard runtimes.

- **Design image** — A captured WebP file with a relative path, base64 bytes, MIME type and dimensions. Visual results include hero and full-page files; explicitly selected text-only results include no files.
