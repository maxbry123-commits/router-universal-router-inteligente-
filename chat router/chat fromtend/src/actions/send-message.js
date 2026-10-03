import { t } from "../i18n.js";

export async function sendMessage(context, textarea, send) {
  const original = textarea.value;
  const message = original.trim();
  if ((!message && !context.attachments.length) || send.disabled) return;
  if (!context.selection.modelId) { context.notice(t(context, "modelRequired"), true); return; }
  if (/deepseek|(^|\/)auto(\/|$)/i.test(context.selection.modelId)) { context.notice("MODEL_PROVIDER_REQUIRED_OR_FORBIDDEN", true); return; }
  send.disabled = true;
  const sessionVersion = context.sessionVersion || 0;
  context.notice(t(context, "backendSending"), false, true);
  try {
    const response = await context.execute(context.config.sendActionId, {
      message, modelId: context.selection.modelId, modeId: context.selection.modeId,
      selectors: { ...context.selection.selectors }, toggles: { ...context.selection.toggles },
      attachments: context.attachments.map(attachment => ({ name: attachment.file.name, file: attachment.file, attachmentId: attachment.id })),
    });
    if ((context.sessionVersion || 0) !== sessionVersion) return;
    if (typeof response.reply !== "string" || !response.reply.trim()) throw new Error("INVALID_CHAT_RESPONSE");
    context.messages.push({ role: "user", text: message || context.attachments.map(attachment => attachment.file.name).join(", ") });
    context.messages.push({ role: "assistant", text: response.reply });
    context.attachments = [];
    context.draft = textarea.value === original ? "" : textarea.value;
    context.notice(t(context, "backendReceived"));
    context.refresh();
  } catch (error) {
    if ((context.sessionVersion || 0) !== sessionVersion) return;
    context.draft = textarea.value;
    context.notice(error.message, true);
  } finally { send.disabled = false; }
}
