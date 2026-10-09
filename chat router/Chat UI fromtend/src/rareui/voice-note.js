import { el, button } from "../dom.js";
// 22 voice-note: nota de voz con grabación real; si el navegador no graba, error explícito.
export function voiceNote({ onRecorded } = {}) {
  const status = el("span", { class: "muted" });
  let recorder;
  const b = button("●", async () => {
    if (recorder?.state === "recording") { recorder.stop(); return; }
    if (!navigator.mediaDevices?.getUserMedia || typeof MediaRecorder !== "function") {
      status.textContent = "VOICE_UNAVAILABLE"; status.className = "error"; return;
    }
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const chunks = [];
      recorder = new MediaRecorder(stream);
      recorder.ondataavailable = e => chunks.push(e.data);
      recorder.onstop = () => {
        stream.getTracks().forEach(track => track.stop());
        b.setAttribute("aria-pressed", "false");
        onRecorded?.(new Blob(chunks, { type: recorder.mimeType || "audio/webm" }));
      };
      recorder.start();
      b.setAttribute("aria-pressed", "true");
      status.textContent = "●";
    } catch (error) { status.textContent = error.message || "VOICE_DENIED"; status.className = "error"; }
  }, "icon-btn rui-voice");
  return el("span", { class: "rui-voice-wrap" }, b, status);
}
