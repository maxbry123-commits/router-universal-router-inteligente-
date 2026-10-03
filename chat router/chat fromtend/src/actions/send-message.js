export async function sendMessage(context, textarea, send) {
  const original = textarea.value;
  const message = original.trim();
  if ((!message && !context.attachments.length) || send.disabled) return;
  if (!context.selection.modelId) { context.notice("Selecciona un modelo antes de enviar.", true); return; }
  send.disabled = true;
  context.notice("Enviando al backend…");
  try {
    const response = await context.execute(context.config.sendActionId, {
      message, modelId: context.selection.modelId, modeId: context.selection.modeId,
      selectors: { ...context.selection.selectors }, toggles: { ...context.selection.toggles },
      attachments: context.attachments.map(attachment => ({ name: attachment.file.name, file: attachment.file, attachmentId: attachment.id })),
    });
    if (typeof response.reply !== "string") throw new Error("INVALID_CHAT_RESPONSE: falta reply del backend");
    context.messages.push({ role: "user", text: message || context.attachments.map(attachment => attachment.file.name).join(", ") });
    context.messages.push({ role: "assistant", text: response.reply });
    context.attachments = [];
    context.draft = textarea.value === original ? "" : textarea.value;
    context.notice("Respuesta recibida del backend.");
    context.refresh();
  } catch (error) {
    context.draft = textarea.value;
    context.notice(error.message, true);
  } finally { send.disabled = false; }
}
