import { el, button } from "../dom.js";

export function renderCanvas(context) {
  const state = el("p", { class: "panel-state pending", role: "status", "aria-live": "polite", text: "Pendiente de consulta al Router" });
  const items = el("div", { class: "panel-results" });
  const preview = el("div", { class: "canvas-preview", "aria-live": "polite" });
  let revision = 0;
  let mediaUrl;
  const root = el("section", { class: "workspace-panel", "aria-label": "Canvas" },
    el("header", { class: "workspace-heading" }, el("h2", { text: "Canvas" }), el("p", { class: "sub", text: "Vista previa de adjuntos confirmados por el Router." })),
    button("Actualizar adjuntos", load), state, items, preview);

  function clearPreview() {
    if (mediaUrl) URL.revokeObjectURL(mediaUrl);
    mediaUrl = undefined;
    preview.replaceChildren();
  }
  root.release = clearPreview;
  async function load() {
    const current = ++revision;
    state.className = "panel-state pending progress";
    state.textContent = "Consultando adjuntos…";
    clearPreview();
    items.replaceChildren();
    try {
      const result = await context.execute("chat.documents");
      if (current !== revision || !root.isConnected) return;
      if (!Array.isArray(result.documents)) throw new Error("INVALID_DOCUMENTS_RESPONSE");
      state.className = "panel-state";
      state.textContent = `${result.documents.length} adjunto(s) confirmados`;
      if (!result.documents.length) items.append(el("p", { class: "muted", text: "Sin adjuntos." }));
      for (const doc of result.documents) {
        if (typeof doc?.id !== "string") continue;
        items.append(button(String(doc.name || doc.id), () => show(doc), "workspace-item"));
      }
    } catch (error) {
      if (current !== revision || !root.isConnected) return;
      state.className = "panel-state error";
      state.textContent = `No se pudieron cargar adjuntos: ${error.message}`;
    }
  }
  async function show(doc) {
    const current = ++revision;
    clearPreview();
    state.className = "panel-state pending progress";
    state.textContent = "Solicitando vista previa…";
    try {
      const details = await context.execute("chat.document", { id: doc.id });
      if (current !== revision || !root.isConnected) return;
      if (typeof details.preview === "string") {
        preview.append(el("h3", { text: String(details.document.name || doc.id) }),
          el("pre", { text: details.preview }));
      } else {
        const result = await context.execute("chat.media", { id: doc.id });
        if (current !== revision || !root.isConnected) return;
        if (!(result.media instanceof Blob)) throw new Error("INVALID_MEDIA_RESPONSE");
        mediaUrl = URL.createObjectURL(result.media);
        const tag = result.media.type.startsWith("video/") ? "video" : "img";
        preview.append(el(tag, tag === "video"
          ? { src: mediaUrl, controls: "controls", "aria-label": String(doc.name || doc.id) }
          : { src: mediaUrl, alt: String(doc.name || doc.id) }));
      }
      state.className = "panel-state";
      state.textContent = "Vista previa cargada desde el Router";
    } catch (error) {
      if (current !== revision || !root.isConnected) return;
      state.className = "panel-state error";
      state.textContent = `Vista previa no disponible: ${error.message}`;
    }
  }
  queueMicrotask(load);
  return root;
}
