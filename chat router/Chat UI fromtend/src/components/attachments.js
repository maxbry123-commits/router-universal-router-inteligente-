import { button, el } from "../dom.js";
import { t } from "../i18n.js";
import { dispatchLocalAction } from "../bridge.js";

export function attachments(context) {
  const input = el("input", { type: "file", multiple: "", "aria-label": t(context, "fileInput"), class: "visually-hidden" });
  const list = el("div", { class: "attachments" });
  let uploadActionId = context.config.attachActionId;
  const redraw = () => {
    list.replaceChildren(...context.attachments.map((attachment, i) =>
      button(`${attachment.file.name} · ${t(context, attachment.id ? "fileUploaded" : "fileLocal")} ×`, () => {
        context.attachments.splice(i, 1);
        redraw();
      }, "chip")));
  };
  input.addEventListener("change", async () => {
    const actionId = uploadActionId;
    for (const file of input.files) {
      dispatchLocalAction("chat.attach.select", { name: file.name, size: file.size, type: file.type });
      const attachment = { file, id: null };
      context.attachments.push(attachment);
      redraw();
      try {
        const result = await context.execute(actionId, { file, name: file.name, size: file.size, type: file.type });
        if (!result.attachmentId) throw new Error("INVALID_ATTACHMENT_RESPONSE");
        attachment.id = result.attachmentId;
        if (context.attachments.includes(attachment)) context.notice(t(context, "uploadConfirmed", { name: file.name }));
      } catch (error) { if (context.attachments.includes(attachment)) context.notice(t(context, "uploadLocal", { name: file.name, error: error.message }), true); }
      redraw();
    }
    input.value = "";
  });
  redraw();
  return { input, list, pickFiles(actionId = context.config.attachActionId) { uploadActionId = actionId; input.click(); } };
}
