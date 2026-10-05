import { api, media, node } from "../api.js";
import { tell } from "./base.js";

const supported = /^(image\/(png|jpeg|gif|webp)|video\/(mp4|webm))$/;

export async function mount(root, { api, tell }) {
  let files = [];
  let currentUrl;
  let selected;
  let previewRequest = 0;
  let disposed = false;
  const status = root.querySelector("#media-status");
  const preview = root.querySelector("#media-preview");
  const actions = root.querySelector("#media-actions");
  const clearPreview = () => {
    previewRequest++;
    if (currentUrl) URL.revokeObjectURL(currentUrl);
    currentUrl = undefined;
    actions.replaceChildren();
    preview.textContent = "Selecciona un archivo registrado.";
  };
  const render = () => {
    const query = root.querySelector("#media-search").value.toLocaleLowerCase();
    const type = root.querySelector("#media-type").value;
    const list = root.querySelector("#media-files");
    list.replaceChildren();
    const matching = files.filter(file => {
      const mime = file.mime || "";
      return (file.name || "").toLocaleLowerCase().includes(query) &&
        (!type || (type === "other" ? !mime.startsWith("image/") && !mime.startsWith("video/") : mime.startsWith(type)));
    });
    for (const file of matching) {
      const button = node("button", `${file.name} · ${file.mime || "tipo desconocido"} · ${file.size} bytes`, "secondary");
      button.type = "button";
      button.setAttribute("aria-pressed", String(selected === file.id));
      button.addEventListener("click", async () => {
        selected = file.id;
        render();
        clearPreview();
        const request = previewRequest;
        preview.textContent = "Cargando vista previa…";
        try {
          if (supported.test(file.mime || "")) {
            const blob = await media(file.id);
            if (disposed || request !== previewRequest) return;
            currentUrl = URL.createObjectURL(blob);
            const element = document.createElement(file.mime.startsWith("image/") ? "img" : "video");
            element.src = currentUrl;
            if (element.tagName === "IMG") element.alt = file.name;
            else element.controls = true;
            preview.replaceChildren(element);
            const link = node("a", "Descargar archivo");
            link.href = currentUrl;
            link.download = file.name;
            actions.replaceChildren(link);
          } else {
            const result = await api(`/chat/documents/${encodeURIComponent(file.id)}`);
            if (disposed || request !== previewRequest) return;
            preview.textContent = result.preview || "Sin vista previa de este formato.";
          }
        } catch (error) {
          if (request === previewRequest && !disposed) {
            preview.textContent = "Vista previa no disponible.";
            tell(error.message);
          }
        }
      });
      list.append(button);
    }
    if (!matching.length) list.append(node("p", "No hay archivos para este filtro.", "muted"));
  };
  const reload = async () => {
    status.textContent = "Consultando archivos del Router…";
    try {
      let filesFound;
      try {
        const response = await api("/chat/org/files");
        filesFound = response.data.files;
      } catch (error) {
        if (!["Not Found", "HTTP 404"].includes(error.message)) throw error;
        const response = await api("/chat/documents");
        filesFound = response.documents;
      }
      if (disposed) return;
      files = filesFound || [];
      status.textContent = `${files.length} archivos registrados en Router`;
      render();
      return true;
    } catch (error) {
      if (disposed) return;
      files = [];
      status.textContent = "No se pudo consultar el Router.";
      render();
      tell(error.message);
      return false;
    }
  };
  root.querySelector("#media-search").addEventListener("input", render);
  root.querySelector("#media-type").addEventListener("change", render);
  root.querySelector("#media-reload").addEventListener("click", reload);
  root.querySelector("#media-upload").addEventListener("submit", async event => {
    event.preventDefault();
    const file = root.querySelector("#media-input").files[0];
    if (!file || file.size > 10 * 1024 * 1024) { tell("Selecciona un archivo de hasta 10 MB."); return; }
    const submit = root.querySelector("#media-upload button");
    submit.disabled = true;
    status.textContent = "Subiendo al Router…";
    try {
      const bytes = new Uint8Array(await file.arrayBuffer());
      const parts = [];
      for (let i = 0; i < bytes.length; i += 8192) parts.push(String.fromCharCode(...bytes.subarray(i, i + 8192)));
      const result = await api("/chat/documents", { method: "POST", body: {
        name: file.name, mime: file.type || "application/octet-stream", data_b64: btoa(parts.join(""))
      } });
      if (disposed) return;
      root.querySelector("#media-upload").reset();
      const listed = await reload();
      if (!disposed) status.textContent = `Guardado en Router: ${result.document.id}. ${listed ? "Lista actualizada." : "Lista no disponible."} Sin sincronización HF confirmada.`;
    } catch (error) {
      if (!disposed) { status.textContent = "Subida no confirmada."; tell(error.message); }
    } finally { submit.disabled = false; }
  });
  await reload();
  return () => { disposed = true; clearPreview(); };
}

void mount(document, { api, tell }).catch(error => tell(error.message));
