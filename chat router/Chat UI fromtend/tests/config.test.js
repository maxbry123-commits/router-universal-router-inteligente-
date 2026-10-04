import test from "node:test";
import assert from "node:assert/strict";
import { DEFAULT_CONFIG, normalizeConfig, readConfig, saveConfig } from "../src/config.js";

test("maintains exact slot counts and stable ids after editing", () => {
  const config = normalizeConfig({ modes: [{ id: "unsafe", label: "Profundo", actionId: "mode.deep" }], selectors: [{ options: [{ id: "file", label: "Archivo", actionId: "file.pick" }] }] });
  assert.equal(config.modes.length, 8);
  assert.equal(config.selectors.length, 5);
  assert.equal(config.toggles.length, 8);
  assert.equal(config.actions.length, 12);
  assert.equal(config.modes[0].id, "mode-1");
  assert.equal(config.modes[0].actionId, "mode.deep");
  assert.deepEqual(config.selectors[0].options[0], { id: "file", label: "Archivo", actionId: "file.pick" });
  assert.equal(DEFAULT_CONFIG.models.length, 0);
  assert.equal(config.theme, "gris");
  assert.equal(normalizeConfig({ theme: "little" }).theme, "little");
});

test("configuration persists without serializing File or runtime state", () => {
  const store = new Map();
  const storage = { getItem: key => store.get(key), setItem: (key, value) => store.set(key, value) };
  const saved = saveConfig({ title: "Mi chat", models: [{ id: "my-model", label: "Mi modelo" }], toggles: [{ label: "Activar", actionId: "control.on" }], messages: ["private"] }, storage);
  assert.deepEqual(readConfig(storage), saved);
  assert.ok(![...store.values()][0].includes("private"));
  assert.deepEqual(readConfig({ getItem: () => "not json" }), normalizeConfig());
  assert.deepEqual(readConfig({ getItem: () => { throw new Error("Storage blocked"); } }), normalizeConfig());
  assert.deepEqual(normalizeConfig(null), normalizeConfig());
});
