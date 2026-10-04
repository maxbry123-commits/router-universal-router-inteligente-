import { dispatchLocalAction } from "../bridge.js";

export function closeChat(context, host = globalThis) {
  context.sessionVersion = (context.sessionVersion || 0) + 1;
  context.messages = [];
  context.attachments = [];
  context.draft = "";
  context.selection.modelId = "";
  context.recorder?.state === "recording" && context.recorder.stop();
  host.YAIWES_PLUGIN_BRIDGE?.resetSession?.();
  dispatchLocalAction("chat.close", {}, host);
  context.refresh();
}

export function exportChat(context, host = globalThis) {
  const json = JSON.stringify({ modelId: context.selection.modelId, modeId: context.selection.modeId, messages: context.messages }, null, 2);
  const url = host.URL.createObjectURL(new Blob([json], { type: "application/json" }));
  const link = host.document.createElement("a");
  link.href = url;
  link.download = "chat-yaiwes.json";
  host.document.body.append(link);
  link.click();
  link.remove();
  host.setTimeout(() => host.URL.revokeObjectURL(url), 1000);
  dispatchLocalAction("chat.export", { count: context.messages.length }, host);
}
