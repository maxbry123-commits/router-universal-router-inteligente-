import { DEFAULT_WALL_STATE } from "./data.js";

export function loadWallState(storage = globalThis.localStorage) {
  const state = JSON.parse(JSON.stringify(DEFAULT_WALL_STATE));
  try {
    const raw = storage?.getItem("yaiwes-wall");
    if (raw) {
      const parsed = JSON.parse(raw);
      if ((parsed.v || 0) >= (state.v || 0)) Object.assign(state, parsed);
    }
  } catch { /* estado local ilegible: se usa el estado por defecto */ }
  return state;
}

export function persistWall(state, storage = globalThis.localStorage) {
  try { storage?.setItem("yaiwes-wall", JSON.stringify(state)); } catch { /* sin storage */ }
}

export function exportWallVersion(state, doc = globalThis.document) {
  state.v = (state.v || 2) + 1;
  persistWall(state);
  const blob = new Blob([JSON.stringify(state, null, 2)], { type: "application/json" });
  const a = doc.createElement("a");
  a.href = URL.createObjectURL(blob);
  a.download = "yaiwes-wall-v" + state.v + ".json";
  a.click();
  setTimeout(() => URL.revokeObjectURL(a.href), 1000);
  return state.v;
}
