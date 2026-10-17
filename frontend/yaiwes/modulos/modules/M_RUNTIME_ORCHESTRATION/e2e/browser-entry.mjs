import { basicSetup } from "codemirror";
import { EditorState } from "@codemirror/state";
import { EditorView } from "@codemirror/view";
import { createCodeMirrorAdapter } from "../adapters/codemirror-adapter.mjs";
import { createRuntimeOrchestrationContract } from "../runtime-orchestration-contract.mjs";

const events = [];
const messages = [];
const failures = [];

const actionBus = Object.freeze({
  publish(event) {
    events.push(event);
  },
});

window.addEventListener("message", (event) => {
  if (event.origin !== window.location.origin) {
    failures.push(`UNEXPECTED_MESSAGE_ORIGIN:${event.origin}`);
    return;
  }
  messages.push(event.data);
});

const codeMirrorAdapter = createCodeMirrorAdapter({ EditorState, EditorView, basicSetup });
const contract = createRuntimeOrchestrationContract({
  codeMirrorAdapter,
  actionBus,
  postMessageTarget: window,
  postMessageOrigin: window.location.origin,
});

const editorHost = document.querySelector("#run07-editor");
const inspectorOutput = document.querySelector("#run08-output");
const statusOutput = document.querySelector("#e2e-status");

const editor = contract.mountRun07Editor({
  parent: editorHost,
  doc: "node: initial\n",
});

window.__YAIWES_E2E__ = Object.freeze({
  setEditorValue(value) {
    editor.setValue(value);
    return editor.getValue();
  },
  updateInspector(snapshot) {
    const event = contract.updateRun08Inspector(snapshot);
    inspectorOutput.textContent = JSON.stringify(event.payload.snapshot);
    return event;
  },
  assertSecretDenied() {
    try {
      contract.updateRun08Inspector({ nodeId: "n-secret", input: { apiKey: "DENY" } });
      return false;
    } catch (error) {
      return String(error?.message || error).startsWith("RAW_SECRET_FIELD_DENIED:");
    }
  },
  getState() {
    return {
      editorValue: editor.getValue(),
      events: structuredClone(events),
      messages: structuredClone(messages),
      failures: [...failures],
    };
  },
  destroy() {
    editor.destroy();
  },
});

statusOutput.textContent = "READY";
statusOutput.dataset.ready = "true";
