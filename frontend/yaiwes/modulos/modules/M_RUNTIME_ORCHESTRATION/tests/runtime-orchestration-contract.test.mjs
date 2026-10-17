import assert from "node:assert/strict";
import test from "node:test";
import {
  createRuntimeOrchestrationContract,
  RUNTIME_ORCHESTRATION_WINDOWS,
} from "../runtime-orchestration-contract.mjs";

const TEST_ORIGIN = "https://comand-center-1-yaiwes-ui-factory.static.hf.space";

function fixture() {
  const busEvents = [];
  const postMessages = [];
  let value = "";
  let onChange;
  let destroyed = false;
  const codeMirrorAdapter = {
    mount(options) {
      value = options.doc;
      onChange = options.onChange;
      return {
        getValue: () => value,
        setValue(next) { value = next; onChange(next); },
        destroy() { destroyed = true; },
      };
    },
  };
  const actionBus = { publish(event) { busEvents.push(event); } };
  const postMessageTarget = { postMessage(event, targetOrigin) { postMessages.push({ event, targetOrigin }); } };
  return {
    codeMirrorAdapter,
    actionBus,
    postMessageTarget,
    postMessageOrigin: TEST_ORIGIN,
    busEvents,
    postMessages,
    destroyed: () => destroyed,
  };
}

test("fails closed without required frontend dependencies", () => {
  assert.throws(() => createRuntimeOrchestrationContract(), /CODEMIRROR_ADAPTER_REQUIRED/);
  assert.throws(
    () => createRuntimeOrchestrationContract({ codeMirrorAdapter: { mount() {} } }),
    /ACTION_BUS_REQUIRED/,
  );
});

test("fails closed when postMessage origin is absent, wildcard, or invalid", () => {
  const f = fixture();
  const base = {
    codeMirrorAdapter: f.codeMirrorAdapter,
    actionBus: f.actionBus,
    postMessageTarget: f.postMessageTarget,
  };
  assert.throws(() => createRuntimeOrchestrationContract(base), /POSTMESSAGE_ORIGIN_REQUIRED/);
  assert.throws(
    () => createRuntimeOrchestrationContract({ ...base, postMessageOrigin: "*" }),
    /POSTMESSAGE_WILDCARD_ORIGIN_DENIED/,
  );
  assert.throws(
    () => createRuntimeOrchestrationContract({ ...base, postMessageOrigin: "javascript:alert(1)" }),
    /POSTMESSAGE_ORIGIN_INVALID/,
  );
});

test("RUN-07 editor routes changes only through ActionBus/postMessage contract", () => {
  const f = fixture();
  const contract = createRuntimeOrchestrationContract(f);
  assert.deepEqual(contract.windows, { editor: "RUN-07", inspector: "RUN-08" });
  assert.equal(RUNTIME_ORCHESTRATION_WINDOWS.editor, "RUN-07");

  const editor = contract.mountRun07Editor({ parent: {}, doc: "node: A" });
  assert.equal(editor.windowId, "RUN-07");
  assert.equal(editor.getValue(), "node: A");
  editor.setValue("node: B");
  assert.equal(editor.getValue(), "node: B");
  assert.equal(f.busEvents.length, 1);
  assert.equal(f.busEvents[0].type, "RUN07_DOCUMENT_CHANGED");
  assert.deepEqual(f.busEvents[0].payload, { windowId: "RUN-07", value: "node: B" });
  assert.equal(f.postMessages.length, 1);
  assert.equal(f.postMessages[0].targetOrigin, TEST_ORIGIN);
  editor.destroy();
  assert.equal(f.destroyed(), true);
  assert.equal("backend" in contract, false);
});

test("RUN-08 inspector publishes an immutable safe snapshot", () => {
  const f = fixture();
  const contract = createRuntimeOrchestrationContract(f);
  const event = contract.updateRun08Inspector({
    nodeId: "node-7",
    status: "READY",
    input: { text: "hello" },
    output: { ok: true },
  });
  assert.equal(event.type, "RUN08_INSPECTOR_UPDATED");
  assert.equal(event.payload.windowId, "RUN-08");
  assert.equal(event.payload.snapshot.nodeId, "node-7");
  assert.equal(Object.isFrozen(event.payload.snapshot), true);
  assert.equal(f.busEvents.length, 1);
  assert.equal(f.postMessages.length, 1);
  assert.equal(f.postMessages[0].targetOrigin, TEST_ORIGIN);
});

test("RUN-08 rejects undeclared and secret-bearing fields", () => {
  const f = fixture();
  const contract = createRuntimeOrchestrationContract(f);
  assert.throws(() => contract.updateRun08Inspector({ nodeId: "n", arbitrary: true }), /RUN08_FIELD_DENIED:arbitrary/);
  assert.throws(
    () => contract.updateRun08Inspector({ nodeId: "n", input: { api_key: "do-not-accept" } }),
    /RAW_SECRET_FIELD_DENIED/,
  );
  assert.equal(f.busEvents.length, 0);
  assert.equal(f.postMessages.length, 0);
});
