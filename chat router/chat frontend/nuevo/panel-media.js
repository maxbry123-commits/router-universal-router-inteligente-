import { api, media, node } from "../api.js";
import { tell } from "./base.js";

const supported = /^(image\/(png|jpeg|gif|webp)|video\/(mp4|webm))$/;
const PIN_KEY = "yaiwes-media-pins";
let pinned = new Set();
try {
  const savedPins = JSON.parse(localStorage.getItem(PIN_KEY) || "[]");
  if (Array.isArray(savedPins)) pinned = new Set(savedPins.filter(id => typeof id === "string"));
} catch {}
const savePins = () => {
  try { localStorage.setItem(PIN_KEY, JSON.stringify([...pinned])); } catch {}
};

export async function mount(root, { api, tell }) {
  let files = [];
  let currentUrl;
  let localUrl;
  let selected;
  let previewRequest = 0;
  let disposed = false;
  const status = root.querySelector("#media-status");
  const preview = root.querySelector("#media-preview");
  const actions = root.querySelector("#media-actions");
  const localPreview = root.querySelector("#media-local-preview");
  const localStatus = root.querySelector("#media-local-status");
  const clearLocalPreview = () => {
    localPreview.replaceChildren();
    if (localUrl) URL.revokeObjectURL(localUrl);
    localUrl = undefined;
    localPreview.textContent = "Aún no hay archivo seleccionado.";
    localStatus.textContent = "Selecciona un archivo para verlo antes de subirlo.";
  };
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
    const onlyPinned = root.querySelector("#media-pinned").checked;
    const list = root.querySelector("#media-files");
    list.replaceChildren();
    const matching = files.filter(file => {
      const mime = file.mime || "";
      return (!onlyPinned || pinned.has(file.id)) &&
        (file.name || "").toLocaleLowerCase().includes(query) &&
        (!type || (type === "other" ? !mime.startsWith("image/") && !mime.startsWith("video/") : mime.startsWith(type)));
    }).sort((a, b) => Number(pinned.has(b.id)) - Number(pinned.has(a.id)));
    for (const file of matching) {
      const marker = pinned.has(file.id) ? "★ " : "";
      const button = node("button", `${marker}${file.name} · ${file.mime || "tipo desconocido"} · ${file.size} bytes`, "secondary");
      button.type = "button";
      button.setAttribute("aria-pressed", String(selected === file.id));
      button.addEventListener("click", async () => {
        selected = file.id;
        render();
        clearPreview();
        const pinButton = node("button", pinned.has(file.id) ? "Desanclar local" : "Anclar local", "secondary");
        pinButton.type = "button";
        pinButton.addEventListener("click", () => {
          if (pinned.has(file.id)) pinned.delete(file.id); else pinned.add(file.id);
          savePins();
          pinButton.textContent = pinned.has(file.id) ? "Desanclar local" : "Anclar local";
          render();
        });
        actions.append(pinButton);
        const remove = node("button", "Eliminar registro", "secondary");
        remove.type = "button";
        let armed = false;
        remove.addEventListener("click", async () => {
          if (!armed) { armed = true; remove.textContent = "Confirmar eliminación"; return; }
          remove.disabled = true;
          try {
            await api(`/chat/documents/${encodeURIComponent(file.id)}`, { method: "DELETE" });
            if (disposed) return;
            selected = undefined;
            clearPreview();
            status.textContent = `Registro ${file.id} eliminado en el Router.`;
            await reload();
          } catch (error) {
            if (!disposed) { armed = false; remove.disabled = false; remove.textContent = "Eliminar registro"; tell(error.message); }
          }
        });
        actions.append(remove);
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
            actions.prepend(link);
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
    root.querySelector("#media-count").textContent =
      matching.length === files.length ? `${files.length} archivos.` : `${matching.length} de ${files.length} archivos coinciden con el filtro.`;
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
  root.querySelector("#media-pinned").addEventListener("change", render);
  root.querySelector("#media-reload").addEventListener("click", reload);
  root.querySelector("#media-input").addEventListener("change", event => {
    clearLocalPreview();
    const file = event.target.files[0];
    if (!file) return;
    if (file.size > 10 * 1024 * 1024) {
      localStatus.textContent = `${file.name} · ${file.type || "tipo desconocido"} · ${file.size} bytes · supera los 10 MB permitidos.`;
      return;
    }
    localStatus.textContent = `${file.name} · ${file.type || "tipo desconocido"} · ${file.size} bytes · Vista previa local; aún no guardado en el Router.`;
    if (!supported.test(file.type)) {
      localPreview.textContent = "Este formato no tiene vista previa local.";
      return;
    }
    localUrl = URL.createObjectURL(file);
    const element = document.createElement(file.type.startsWith("image/") ? "img" : "video");
    element.src = localUrl;
    if (element.tagName === "IMG") element.alt = file.name;
    else element.controls = true;
    localPreview.replaceChildren(element);
  });
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
      clearLocalPreview();
      const listed = await reload();
      if (!disposed) status.textContent = `Guardado en Router: ${result.document.id}. ${listed ? "Lista actualizada." : "Lista no disponible."} Sin sincronización HF confirmada.`;
    } catch (error) {
      if (!disposed) { status.textContent = "Subida no confirmada."; tell(error.message); }
    } finally { submit.disabled = false; }
  });
  await reload();
  return () => { disposed = true; clearPreview(); clearLocalPreview(); };
}

void mount(document, { api, tell }).catch(error => tell(error.message));
