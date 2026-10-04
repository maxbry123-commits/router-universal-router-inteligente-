import test from "node:test";
import assert from "node:assert/strict";
import { toggleRecording } from "../src/actions/record-voice.js";

test("discarding a chat while microphone permission is pending stops its tracks", async () => {
  let grantPermission;
  let stopped = 0;
  let recorderCreated = false;
  const originalNavigator = Object.getOwnPropertyDescriptor(globalThis, "navigator");
  const originalWindow = globalThis.window;
  const originalMediaRecorder = globalThis.MediaRecorder;
  try {
    Object.defineProperty(globalThis, "navigator", { configurable: true, value: {
      mediaDevices: { getUserMedia: () => new Promise(resolve => { grantPermission = resolve; }) },
    } });
    globalThis.window = { YAIWES_PLUGIN_BRIDGE: { execute() {} } };
    globalThis.MediaRecorder = class { constructor() { recorderCreated = true; } };
    const context = {
      config: { voiceActionId: "voice.send" }, recorder: null, sessionVersion: 0,
      notice() { assert.fail("A cancelled recording must not show a status"); },
    };
    const recording = toggleRecording(context, {});
    context.sessionVersion++;
    grantPermission({ getTracks: () => [{ stop() { stopped++; } }] });
    await recording;
    assert.equal(stopped, 1);
    assert.equal(recorderCreated, false);
  } finally {
    if (originalNavigator) Object.defineProperty(globalThis, "navigator", originalNavigator);
    else delete globalThis.navigator;
    globalThis.window = originalWindow;
    globalThis.MediaRecorder = originalMediaRecorder;
  }
});
