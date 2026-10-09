import { controlLabel, t } from "../i18n.js";

export async function toggleRecording(context, buttonNode) {
  if (context.recorder?.state === "recording") { context.recorder.stop(); return; }
  if (!context.config.voiceActionId) { context.notice("ACTION_UNCONFIGURED", true); return; }
  if (!window.YAIWES_PLUGIN_BRIDGE?.execute) { context.notice("BRIDGE_MISSING", true); return; }
  if (!navigator.mediaDevices?.getUserMedia || typeof MediaRecorder === "undefined") {
    context.notice(t(context, "voiceUnavailable"), true);
    return;
  }
  const sessionVersion = context.sessionVersion || 0;
  let stream;
  try {
    stream = await navigator.mediaDevices.getUserMedia({ audio: true });
    if ((context.sessionVersion || 0) !== sessionVersion) {
      stream.getTracks().forEach(track => track.stop());
      return;
    }
    const recorder = new MediaRecorder(stream);
    const chunks = [];
    context.recorder = recorder;
    recorder.addEventListener("dataavailable", event => { if (event.data.size) chunks.push(event.data); });
    recorder.addEventListener("stop", async () => {
      stream.getTracks().forEach(track => track.stop());
      buttonNode.setAttribute("aria-label", controlLabel(context, "voice"));
      buttonNode.setAttribute("title", controlLabel(context, "voice"));
      buttonNode.setAttribute("aria-pressed", "false");
      if ((context.sessionVersion || 0) !== sessionVersion) {
        if (context.recorder === recorder) context.recorder = null;
        return;
      }
      try {
        await context.execute(context.config.voiceActionId, { audio: new Blob(chunks, { type: recorder.mimeType }), mimeType: recorder.mimeType });
        if ((context.sessionVersion || 0) === sessionVersion) context.notice(t(context, "audioConfirmed"));
      } catch (error) {
        if ((context.sessionVersion || 0) === sessionVersion) context.notice(error.message, true);
      }
      if (context.recorder === recorder) context.recorder = null;
    });
    recorder.start();
    buttonNode.setAttribute("aria-label", t(context, "stopRecording", { name: controlLabel(context, "voice") }));
    buttonNode.setAttribute("title", t(context, "stopRecording", { name: controlLabel(context, "voice") }));
    buttonNode.setAttribute("aria-pressed", "true");
    context.notice(t(context, "recording"));
  } catch (error) {
    stream?.getTracks().forEach(track => track.stop());
    context.notice(`VOICE_UNAVAILABLE: ${error.message}`, true);
  }
}
