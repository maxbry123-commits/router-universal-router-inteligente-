const MAX_UPLOAD_BYTES = 10 * 1024 * 1024;
const MEDIA_TYPES = new Set(["image/png", "image/jpeg", "image/gif", "image/webp", "video/mp4", "video/webm"]);

function documentId(payload) {
  const id = payload.id;
  if (typeof id !== "string" || !/^[a-zA-Z0-9_-]{1,128}$/.test(id)) throw new Error("DOCUMENT_ID_INVALID");
  return encodeURIComponent(id);
}

function allowedModel(modelId) {
  if (typeof modelId !== "string" || /deepseek|(^|\/)auto(\/|$)/i.test(modelId)) return false;
  const slash = modelId.indexOf("/");
  return slash > 0 && slash < modelId.length - 1;
}

async function encodeFile(file) {
  const bytes = new Uint8Array(await file.arrayBuffer());
  const chunks = [];
  for (let offset = 0; offset < bytes.length; offset += 12288) {
    chunks.push(btoa(String.fromCharCode(...bytes.subarray(offset, offset + 12288))));
  }
  return chunks.join("");
}

export function createSameOriginChatBridge(fetchImpl) {
  let conversationId = null;
  let sessionVersion = 0;

  async function request(path, body) {
    const response = await fetchImpl(path, {
      method: body === undefined ? "GET" : "POST",
      credentials: "same-origin",
      cache: "no-store",
      ...(body === undefined ? {} : { headers: { "Content-Type": "application/json" }, body: JSON.stringify(body) }),
    });
    let data;
    try { data = await response.json(); }
    catch {
      if (!response.ok) throw new Error(`BACKEND_HTTP_${response.status}`);
      throw new Error(`BACKEND_INVALID_JSON:${response.status}`);
    }
    if (!response.ok) throw new Error(`BACKEND_HTTP_${response.status}: ${String(data.detail || data.error || "")}`);
    if (!data || typeof data !== "object") throw new Error("BACKEND_INVALID_RESPONSE");
    return data;
  }

  return {
    resetSession() { conversationId = null; sessionVersion++; },
    async execute(actionId, payload = {}) {
      if (actionId === "chat.documents") {
        const data = await request("/chat/documents");
        if (!Array.isArray(data.documents)) throw new Error("INVALID_DOCUMENTS_RESPONSE");
        return { ok: true, documents: data.documents };
      }
      if (actionId === "chat.document") {
        const data = await request(`/chat/documents/${documentId(payload)}`);
        if (!data.document || typeof data.document.id !== "string" || data.document.id !== payload.id) {
          throw new Error("INVALID_DOCUMENT_RESPONSE");
        }
        return { ok: true, document: data.document, preview: typeof data.preview === "string" ? data.preview : null };
      }
      if (actionId === "chat.media") {
        const response = await fetchImpl(`/chat/media/${documentId(payload)}`, { credentials: "same-origin", cache: "no-store" });
        if (!response.ok) throw new Error(`BACKEND_HTTP_${response.status}`);
        const blob = await response.blob();
        if (!MEDIA_TYPES.has(blob.type) || !blob.size || blob.size > MAX_UPLOAD_BYTES) throw new Error("MEDIA_TYPE_OR_SIZE_INVALID");
        return { ok: true, media: blob };
      }
      if (actionId === "chat.graph") {
        const data = await request("/chat/graph");
        if (!Array.isArray(data.nodes) || !Array.isArray(data.edges)) throw new Error("INVALID_GRAPH_RESPONSE");
        return { ok: true, nodes: data.nodes, edges: data.edges };
      }
      if (actionId === "chat.models") {
        const { providers } = await request("/chat/providers");
        if (!Array.isArray(providers)) throw new Error("INVALID_PROVIDERS_RESPONSE");
        const models = [];
        for (const provider of providers.filter(item => item.configured && item.id && !/^(auto|deepseek)$/i.test(item.id))) {
          const data = await request(`/chat/providers/${encodeURIComponent(provider.id)}/models`);
          if (!Array.isArray(data.models)) throw new Error("INVALID_MODELS_RESPONSE");
          for (const model of data.models) {
            if (model.selectable === false || !model.model_id || /deepseek/i.test(model.model_id)) continue;
            models.push({ id: `${provider.id}/${model.model_id}`, label: `${provider.label || provider.id} · ${model.label || model.model_id}` });
          }
        }
        return { ok: true, models };
      }
      if (actionId === "chat.attach") {
        const file = payload.file;
        if (!(file instanceof Blob) || !file.size || file.size > MAX_UPLOAD_BYTES) throw new Error("DOCUMENT_EMPTY_OR_TOO_LARGE");
        const data = await request("/chat/documents", {
          name: payload.name || file.name, mime: file.type || "application/octet-stream",
          data_b64: await encodeFile(file), conversation_id: conversationId,
        });
        if (typeof data.document?.id !== "string" || !data.document.id) throw new Error("INVALID_ATTACHMENT_RESPONSE");
        return { ok: true, attachmentId: data.document.id };
      }
      if (actionId === "chat.send") {
        if (!allowedModel(payload.modelId)) throw new Error("MODEL_PROVIDER_REQUIRED_OR_FORBIDDEN");
        if (payload.modeId !== "mode-1") throw new Error("MODE_NOT_SUPPORTED_BY_CHAT_API");
        if (!payload.message?.trim()) throw new Error("MESSAGE_REQUIRED_BY_CHAT_API");
        const attached = payload.attachments || [];
        if (attached.some(item => !item.attachmentId)) throw new Error("ATTACHMENT_NOT_UPLOADED");
        const separator = payload.modelId.indexOf("/");
        const provider = payload.modelId.slice(0, separator);
        const model = payload.modelId.slice(separator + 1);
        const version = sessionVersion;
        const data = await request("/chat/send", {
          message: payload.message, provider, model,
          mode: "direct", conversation_id: conversationId, doc_ids: attached.map(item => item.attachmentId),
        });
        if (sessionVersion !== version) throw new Error("CHAT_SESSION_CHANGED");
        if (typeof data.reply !== "string" || !data.reply.trim()) throw new Error("INVALID_CHAT_RESPONSE");
        if (data.provider !== provider || data.model !== model) throw new Error("BACKEND_MODEL_MISMATCH");
        conversationId = data.conversation_id || conversationId;
        return { ok: true, reply: data.reply, conversationId };
      }
      throw new Error(`ACTION_UNCONFIGURED: ${actionId}`);
    },
  };
}

export function installSameOriginChatBridge(host = globalThis) {
  if (host.YAIWES_PLUGIN_BRIDGE) return false;
  if (!/^https?:$/.test(host.location?.protocol || "") || typeof host.fetch !== "function") return false;
  host.YAIWES_PLUGIN_BRIDGE = createSameOriginChatBridge(host.fetch.bind(host));
  return true;
}
