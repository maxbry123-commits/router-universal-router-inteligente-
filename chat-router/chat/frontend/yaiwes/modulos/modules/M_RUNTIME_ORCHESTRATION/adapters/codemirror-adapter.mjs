// T2-R5A1 — minimum CodeMirror adapter for RUN-07/RUN-08.
// Owner: ➡️ Astra plan fábrica UI YAIWES
// Policy: frontend-only, no backend writes, no raw secret handling.

const REQUIRED_RUNTIME_KEYS = ["EditorState", "EditorView"];

function assertRuntime(runtime) {
  if (!runtime || typeof runtime !== "object") {
    throw new TypeError("CODEMIRROR_RUNTIME_REQUIRED");
  }
  for (const key of REQUIRED_RUNTIME_KEYS) {
    if (!runtime[key]) throw new Error(`CODEMIRROR_RUNTIME_MISSING:${key}`);
  }
  if (typeof runtime.EditorState.create !== "function") {
    throw new Error("CODEMIRROR_RUNTIME_INVALID:EditorState.create");
  }
  if (typeof runtime.EditorView !== "function") {
    throw new Error("CODEMIRROR_RUNTIME_INVALID:EditorView");
  }
}

function normalizeExtensions(runtime, extensions, onChange) {
  const result = Array.isArray(extensions) ? [...extensions] : [];
  if (runtime.basicSetup) result.unshift(runtime.basicSetup);

  if (typeof onChange === "function") {
    const listenerFactory = runtime.EditorView.updateListener?.of;
    if (typeof listenerFactory !== "function") {
      throw new Error("CODEMIRROR_RUNTIME_MISSING:EditorView.updateListener.of");
    }
    result.push(
      listenerFactory((update) => {
        if (update?.docChanged !== true) return;
        const value = update.state?.doc?.toString?.();
        if (typeof value !== "string") {
          throw new Error("CODEMIRROR_UPDATE_DOC_INVALID");
        }
        onChange(value);
      }),
    );
  }
  return result;
}

export function createCodeMirrorAdapter(runtime) {
  assertRuntime(runtime);

  return Object.freeze({
    mount({ parent, doc = "", extensions = [], onChange } = {}) {
      if (!parent) throw new Error("CODEMIRROR_PARENT_REQUIRED");
      if (typeof doc !== "string") throw new TypeError("CODEMIRROR_DOC_MUST_BE_STRING");

      const state = runtime.EditorState.create({
        doc,
        extensions: normalizeExtensions(runtime, extensions, onChange),
      });
      const view = new runtime.EditorView({ state, parent });

      let destroyed = false;
      const ensureAlive = () => {
        if (destroyed) throw new Error("CODEMIRROR_ADAPTER_DESTROYED");
      };

      return Object.freeze({
        getValue() {
          ensureAlive();
          const value = view.state?.doc?.toString?.();
          if (typeof value !== "string") throw new Error("CODEMIRROR_VIEW_DOC_INVALID");
          return value;
        },
        setValue(nextValue) {
          ensureAlive();
          if (typeof nextValue !== "string") throw new TypeError("CODEMIRROR_DOC_MUST_BE_STRING");
          const currentLength = view.state?.doc?.length;
          if (!Number.isInteger(currentLength) || currentLength < 0) {
            throw new Error("CODEMIRROR_VIEW_DOC_LENGTH_INVALID");
          }
          if (typeof view.dispatch !== "function") throw new Error("CODEMIRROR_VIEW_DISPATCH_MISSING");
          view.dispatch({ changes: { from: 0, to: currentLength, insert: nextValue } });
        },
        destroy() {
          if (destroyed) return;
          if (typeof view.destroy !== "function") throw new Error("CODEMIRROR_VIEW_DESTROY_MISSING");
          view.destroy();
          destroyed = true;
        },
      });
    },
  });
}
