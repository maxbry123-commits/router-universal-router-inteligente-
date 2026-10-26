import assert from "node:assert/strict";
import test from "node:test";
import { createCodeMirrorAdapter } from "../adapters/codemirror-adapter.mjs";

class FakeDoc {
  constructor(value) { this.value = value; }
  get length() { return this.value.length; }
  toString() { return this.value; }
}

class FakeEditorView {
  static updateListener = { of: (listener) => ({ listener }) };
  constructor({ state, parent }) {
    this.state = { ...state, doc: new FakeDoc(state.doc) };
    this.parent = parent;
    this.destroyed = false;
    this.listeners = (state.extensions || []).filter((item) => item?.listener).map((item) => item.listener);
  }
  dispatch({ changes }) {
    const before = this.state.doc.toString();
    assert.equal(changes.from, 0);
    assert.equal(changes.to, before.length);
    this.state.doc = new FakeDoc(changes.insert);
    const update = { docChanged: true, state: this.state };
    for (const listener of this.listeners) listener(update);
  }
  destroy() { this.destroyed = true; }
}

const runtime = {
  basicSetup: { name: "basicSetup" },
  EditorState: {
    create({ doc, extensions }) { return { doc, extensions }; },
  },
  EditorView: FakeEditorView,
};

test("fails closed when CodeMirror runtime is absent", () => {
  assert.throws(() => createCodeMirrorAdapter(), /CODEMIRROR_RUNTIME_REQUIRED/);
});

test("mount/get/set/change/destroy stays frontend-local", () => {
  const changes = [];
  const adapter = createCodeMirrorAdapter(runtime);
  const session = adapter.mount({ parent: {}, doc: "node: A", onChange: (value) => changes.push(value) });

  assert.equal(session.getValue(), "node: A");
  session.setValue("node: B");
  assert.equal(session.getValue(), "node: B");
  assert.deepEqual(changes, ["node: B"]);

  session.destroy();
  session.destroy();
  assert.throws(() => session.getValue(), /CODEMIRROR_ADAPTER_DESTROYED/);
});

test("rejects non-string documents", () => {
  const adapter = createCodeMirrorAdapter(runtime);
  assert.throws(() => adapter.mount({ parent: {}, doc: { secret: "never" } }), /CODEMIRROR_DOC_MUST_BE_STRING/);
});
