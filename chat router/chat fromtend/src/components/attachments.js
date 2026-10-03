import { button, el } from "../dom.js";

export function attachments(context) {
  const input = el("input", { type: "file", multiple: "", "aria-label": "Elegir archivos", class: "visually-hidden" });
  const list = el("div", { class: "attachments" });
  const redraw = () => {
    list.replaceChildren(...context.attachments.map((attachment, i) =>
      button(`${attachment.file.name} · ${attachment.id ? "subido" : "local"} ×`, () => {
        context.attachments.splice(i, 1);
        redraw();
      }, "chip")));
  };
  input.addEventListener("change", async () => {
    for (const file of input.files) {
      const attachment = { file, id: null };
      context.attachments.push(attachment);
      redraw();
      try {
        const result = await context.execute(context.config.attachActionId, { file, name: file.name, size: file.size, type: file.type });
        if (!result.attachmentId) throw new Error("INVALID_ATTACHMENT_RESPONSE");
        attachment.id = result.attachmentId;
        context.notice(`${file.name}: subida confirmada.`);
      } catch (error) { context.notice(`${file.name}: ${error.message}; sigue solo en esta pestaña.`, true); }
      redraw();
    }
    input.value = "";
  });
  redraw();
  return { input, list };
}
