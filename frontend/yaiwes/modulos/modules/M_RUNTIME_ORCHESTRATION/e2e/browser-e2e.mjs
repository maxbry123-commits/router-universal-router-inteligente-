import assert from "node:assert/strict";
import { chromium } from "playwright";

const url = process.env.E2E_URL || "http://127.0.0.1:4173/index.html";
const browser = await chromium.launch({ headless: true });
try {
  const page = await browser.newPage();
  await page.goto(url, { waitUntil: "networkidle" });
  await page.waitForFunction(() => document.querySelector("#e2e-status")?.dataset.ready === "true");

  const initial = await page.evaluate(() => window.__YAIWES_E2E__.getState());
  assert.equal(initial.editorValue, "node: initial\n");
  assert.deepEqual(initial.failures, []);

  const nextValue = "node: alpha\nstatus: running\n";
  const editorValue = await page.evaluate((value) => window.__YAIWES_E2E__.setEditorValue(value), nextValue);
  assert.equal(editorValue, nextValue);

  const inspectorEvent = await page.evaluate(() =>
    window.__YAIWES_E2E__.updateInspector({
      nodeId: "node-alpha",
      status: "running",
      input: { task: "compile" },
      output: { progress: 1 },
      error: null,
    }),
  );
  assert.equal(inspectorEvent.type, "RUN08_INSPECTOR_UPDATED");
  assert.equal(inspectorEvent.payload.windowId, "RUN-08");

  const secretDenied = await page.evaluate(() => window.__YAIWES_E2E__.assertSecretDenied());
  assert.equal(secretDenied, true);

  await page.waitForFunction(() => window.__YAIWES_E2E__.getState().messages.length >= 2);
  const state = await page.evaluate(() => window.__YAIWES_E2E__.getState());

  assert.deepEqual(state.failures, []);
  assert.ok(state.events.some((event) => event.type === "RUN07_DOCUMENT_CHANGED"));
  assert.ok(state.events.some((event) => event.type === "RUN08_INSPECTOR_UPDATED"));
  assert.ok(state.messages.some((event) => event.type === "RUN07_DOCUMENT_CHANGED"));
  assert.ok(state.messages.some((event) => event.type === "RUN08_INSPECTOR_UPDATED"));

  const leaked = JSON.stringify(state).match(/apiKey|token|secret|password|credential|private[_-]?key/i);
  assert.equal(leaked, null, "No secret-bearing field names may cross the event/message boundary");

  console.log(JSON.stringify({
    status: "PASS",
    url,
    assertions: {
      real_browser: true,
      run07_editor_event: true,
      run08_inspector_event: true,
      same_origin_postmessage: true,
      secret_field_fail_closed: true,
      backend_write_surface_used: false,
    },
    counts: { events: state.events.length, messages: state.messages.length, failures: state.failures.length },
  }, null, 2));
} finally {
  await browser.close();
}
