export async function toggleRecording(context, buttonNode) {
  if (context.recorder?.state === "recording") { context.recorder.stop(); return; }
  if (!context.config.voiceActionId) { context.notice("ACTION_UNCONFIGURED", true); return; }
  if (!window.YAIWES_PLUGIN_BRIDGE?.execute) { context.notice("BRIDGE_MISSING", true); return; }
  if (!navigator.mediaDevices?.getUserMedia || typeof MediaRecorder === "undefined") {
    context.notice("VOICE_UNAVAILABLE: el navegador no permite grabar.", true);
    return;
  }
  try {
    const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
    const recorder = new MediaRecorder(stream);
    const chunks = [];
    context.recorder = recorder;
    recorder.addEventListener("dataavailable", event => { if (event.data.size) chunks.push(event.data); });
    recorder.addEventListener("stop", async () => {
      stream.getTracks().forEach(track => track.stop());
      buttonNode.textContent = context.config.labels.voice;
      try {
        await context.execute(context.config.voiceActionId, { audio: new Blob(chunks, { type: recorder.mimeType }), mimeType: recorder.mimeType });
        context.notice("Audio confirmado por el backend.");
      } catch (error) { context.notice(error.message, true); }
      context.recorder = null;
    });
    recorder.start();
    buttonNode.textContent = `Detener ${context.config.labels.voice}`;
    context.notice("Grabando audio localmente…");
  } catch (error) { context.notice(`VOICE_UNAVAILABLE: ${error.message}`, true); }
}
