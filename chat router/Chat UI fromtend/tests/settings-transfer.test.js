import test from "node:test";
import assert from "node:assert/strict";
import { DEFAULT_CONFIG, normalizeConfig } from "../src/config.js";
import { exportSettings, importSettings, parseSettings } from "../src/actions/settings-transfer.js";

test("settings export uses only normalized configuration and round-trips Gris plus commands", async () => {
  let body, filename, revoked;
  const host = {
    URL: { createObjectURL(blob) { body = blob; return "blob:config"; }, revokeObjectURL(url) { revoked = url; } },
    document: { body: { append() {} }, createElement() { return { click() {}, remove() {}, set download(name) { filename = name; } }; } },
    setTimeout(callback) { callback(); },
  };
  const config = normalizeConfig({ theme: "gris", title: "Y", sendActionId: "chat.send", messages: ["secret"] });
  exportSettings(config, host);
  assert.equal(filename, "chat-yaiwes-configuracion.json");
  assert.equal(revoked, "blob:config");
  const text = await body.text();
  assert.ok(!text.includes("secret"));
  assert.deepEqual(parseSettings(text), config);
  assert.deepEqual(await importSettings({ size: text.length, text: async () => text }), config);
});

test("settings import rejects malformed, unrelated and oversized files without changing defaults", async () => {
  for (const text of ["{", "{}", "null", '{"format":"yaiwes-chat-settings","version":99,"config":{}}']) {
    assert.throws(() => parseSettings(text), /INVALID_CONFIG_FILE/);
  }
  await assert.rejects(importSettings({ size: 1024 * 1024 + 1, text() { throw new Error("read"); } }), /INVALID_CONFIG_FILE/);
  assert.equal(normalizeConfig(DEFAULT_CONFIG).theme, "gris");
});
