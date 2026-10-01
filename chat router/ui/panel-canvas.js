import { media, node } from "./api.js";

export async function mount(root, { api, tell }) {
  let currentUrl;
  try {
    const files = (await api("/chat/org/files")).data.files;
    const list = root.querySelector("#canvas-files");
    for (const file of files) {
      const button = node("button", `${file.name} · ${file.mime}`, "secondary");
      button.addEventListener("click", async () => {
        try {
          const preview = root.querySelector("#preview");
          if (currentUrl) URL.revokeObjectURL(currentUrl);
          currentUrl = undefined;
          if (/^(image\/(png|jpeg|gif|webp)|video\/(mp4|webm))$/.test(file.mime)) {
            currentUrl = URL.createObjectURL(await media(file.id));
            const element = document.createElement(file.mime.startsWith("image/") ? "img" : "video");
            element.src = currentUrl;
            element.alt = file.name;
            if (element.tagName === "VIDEO") element.controls = true;
            preview.replaceChildren(element);
          } else {
            const detail = await api(`/chat/documents/${encodeURIComponent(file.id)}`);
            preview.textContent = detail.preview || "Sin vista previa de este formato";
          }
        } catch (error) { tell(error.message); }
      });
      list.append(button);
    }
    if (!files.length) list.append(node("p", "Sin adjuntos", "muted"));
  } catch (error) { tell(error.message); }
  return () => { if (currentUrl) URL.revokeObjectURL(currentUrl); };
}
