import test from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { execFileSync } from "node:child_process";
import { fileURLToPath } from "node:url";
import { runInNewContext } from "node:vm";
import { createSameOriginChatBridge } from "../src/plugins/same-origin-chat.js";
import { renderFiles } from "../src/panels/files.js";
import { renderTracking } from "../src/panels/tracking.js";
import { renderCanvas } from "../src/panels/canvas.js";
import { RUN_VIEWS } from "../src/panels/run-views.js";
import { WALL_VIEWS } from "../src/panels/wall-views.js";
import { fixture, settle } from "./dom-fixture.js";

test("second-phase bridge reads only verified document and provenance paths", async () => {
  const calls = [];
  const bridge = createSameOriginChatBridge(async (path, options) => {
    calls.push({ path, options });
    if (path === "/chat/documents") return { ok: true, json: async () => ({ documents: [{ id: "aabbcc", name: "Real" }] }) };
    if (path === "/chat/documents/aabbcc") return { ok: true, json: async () => ({ document: { id: "aabbcc" }, preview: "Texto real" }) };
    if (path === "/chat/graph") return { ok: true, json: async () => ({ nodes: [], edges: [] }) };
    if (path === "/chat/media/aabbcc") return { ok: true, blob: async () => new Blob(["image"], { type: "image/png" }) };
    throw new Error(`UNEXPECTED_PATH:${path}`);
  });
  assert.equal((await bridge.execute("chat.documents")).documents[0].name, "Real");
  assert.equal((await bridge.execute("chat.document", { id: "aabbcc" })).preview, "Texto real");
  assert.deepEqual((await bridge.execute("chat.graph")).edges, []);
  assert.equal((await bridge.execute("chat.media", { id: "aabbcc" })).media.type, "image/png");
  assert.equal(calls.every(call => call.options.credentials === "same-origin" && call.options.cache === "no-store"), true);
  for (const id of ["../admin", "", "x?mode=bad"]) {
    await assert.rejects(bridge.execute("chat.document", { id }), /DOCUMENT_ID_INVALID/);
    await assert.rejects(bridge.execute("chat.media", { id }), /DOCUMENT_ID_INVALID/);
  }
  await assert.rejects(bridge.execute("run.ledger", { id: "test" }), /ACTION_UNCONFIGURED/);
  assert.equal(calls.length, 4);
});

test("unavailable media cannot be rendered as a successful preview", async () => {
  const bridge = createSameOriginChatBridge(async () => ({
    ok: false, status: 401, blob: async () => new Blob(["not an image"], { type: "text/html" }),
  }));
  await assert.rejects(bridge.execute("chat.media", { id: "aabbcc" }), /BACKEND_HTTP_401/);
  const malformed = createSameOriginChatBridge(async () => ({
    ok: true, blob: async () => new Blob(["svg"], { type: "image/svg+xml" }),
  }));
  await assert.rejects(malformed.execute("chat.media", { id: "aabbcc" }), /MEDIA_TYPE_OR_SIZE_INVALID/);
});

test("files and canvas expose backend failures, never sample documents", async () => {
  const { document, context } = fixture({}, async () => { throw new Error("BACKEND_HTTP_401"); });
  const files = renderFiles(context);
  const canvas = renderCanvas(context);
  document.body.append(files, canvas);
  await settle();
  assert.match(files.querySelector(".panel-state").textContent, /BACKEND_HTTP_401/);
  assert.match(canvas.querySelector(".panel-state").textContent, /BACKEND_HTTP_401/);
  assert.equal(files.querySelectorAll(".workspace-row").length, 0);
  assert.equal(canvas.querySelectorAll(".workspace-item").length, 0);
});

test("files are searchable only after an actual backend read", async () => {
  const { document, window, context } = fixture({}, async actionId => {
    assert.equal(actionId, "chat.documents");
    return { ok: true, documents: [{ id: "aabbcc", name: "Real.txt", size: 4, mime: "text/plain" }] };
  });
  const files = renderFiles(context);
  document.body.append(files);
  await settle();
  assert.equal(files.querySelectorAll(".workspace-row").length, 1);
  const input = files.querySelector('input[type="search"]');
  input.value = "not found";
  input.dispatchEvent(new window.Event("input"));
  assert.equal(files.querySelectorAll(".workspace-row").length, 0);
});

test("Run/Wall inventory remains exact and unavailable DAG ledger never claims success", async () => {
  const { document, context } = fixture({}, async actionId => {
    if (actionId === "chat.graph") return { ok: true, nodes: [], edges: [] };
    throw new Error("ACTION_UNCONFIGURED");
  });
  assert.equal(RUN_VIEWS.length, 8);
  assert.equal(WALL_VIEWS.length, 16);
  const tracking = renderTracking(context);
  document.body.append(tracking);
  await settle();
  assert.match(tracking.querySelector(".panel-state").textContent, /Procedencia leída/);
  tracking.querySelector('input[aria-label="ID de ejecución"]').value = "run-123";
  [...tracking.querySelectorAll("button")].find(item => item.textContent === "Consultar ledger").click();
  await settle();
  assert.match(tracking.querySelector(".panel-state").textContent, /ACTION_UNCONFIGURED/);
  assert.equal(tracking.querySelectorAll(".workspace-section").length, 2);
});

test("standalone four-panel review bundles source without external imports", () => {
  execFileSync(process.execPath, [fileURLToPath(new URL("../scripts/build-shell-review.mjs", import.meta.url))]);
  const html = readFileSync(new URL("../paneles Yaiwes fromtend.revisar.html", import.meta.url), "utf8");
  assert.equal([...html.matchAll(/<style>/g)].length, 8);
  assert.equal([...html.matchAll(/<script>/g)].length, 1);
  assert.doesNotMatch(html, /<script[^>]*src=|<link[^>]*stylesheet|type="module"/);
  const { document, window } = fixture({}, undefined, html);
  const host = { document, window, location: { protocol: "file:" }, structuredClone, CustomEvent, console, setTimeout, clearTimeout, queueMicrotask };
  Object.defineProperty(host, "localStorage", { get() { throw new Error("STORAGE_BLOCKED"); } });
  runInNewContext(document.querySelector("script").textContent, host, { timeout: 1000 });
  assert.equal(document.querySelectorAll(".workspace-nav button").length, 6);
  assert.equal(document.querySelectorAll(".chat-panel button").length, 8);
  document.querySelector('[data-panel="files"]').click();
  assert.ok(document.querySelector('[aria-label="Archivos"]'));
  document.querySelector('[data-panel="run"]').click();
  assert.ok(document.querySelector(".run-app"), "Run panel must mount the ported YAIWES Run shell");
  document.querySelector('[data-panel="wall"]').click();
  assert.ok(document.querySelector(".wall"), "Crazy Wall panel must mount the ported wall shell");
});
