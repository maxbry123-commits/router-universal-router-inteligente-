const MAX_UPLOAD_BYTES = 10 * 1024 * 1024;
const MEDIA_TYPES = new Set(["image/png", "image/jpeg", "image/gif", "image/webp", "video/mp4", "video/webm"]);

function documentId(payload) {
  const id = payload.id;
  if (typeof id !== "string" || !/^[a-zA-Z0-9_-]{1,128}$/.test(id)) throw new Error("DOCUMENT_ID_INVALID");
  return encodeURIComponent(id);
}

function fichaId(payload) {
  const id = payload.id;
  if (typeof id !== "string" || !/^[a-zA-Z0-9_.-]{1,128}$/.test(id) || id === "." || id === "..") {
    throw new Error("FICHA_ID_INVALID");
  }
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
      if (actionId === "chat.plugins") {
        const data = await request("/plugins");
        if (!Array.isArray(data.plugins)) throw new Error("INVALID_PLUGINS_RESPONSE");
        return { ok: true, items: data.plugins.map(plugin => ({
          id: String(plugin.id || ""), label: String(plugin.id || ""),
          description: String(plugin.status || "UNKNOWN"),
        })).filter(plugin => plugin.id && !/deepseek/i.test(plugin.id)) };
      }
      if (actionId === "chat.fichas") {
        const data = await request("/chat/fichas");
        if (!Array.isArray(data.fichas)) throw new Error("INVALID_FICHAS_RESPONSE");
        const fichas = data.fichas.filter(ficha =>
          typeof ficha?.id === "string" && ficha.id &&
          !/(^|[.\/_-])(?:ficha[.\/_-]?)?0(?:$|[.\/_-])/i.test(ficha.id) &&
          !/deepseek/i.test(ficha.id));
        return { ok: true, items: fichas.map(ficha => ({
          id: ficha.id, label: ficha.id, description: String(ficha.status || "UNKNOWN"),
        })) };
      }
      if (actionId === "chat.ficha") {
        const id = fichaId(payload);
        const data = await request(`/chat/fichas/${id}`);
        if (data.ficha?.id !== payload.id) throw new Error("INVALID_FICHA_RESPONSE");
        return { ok: true, ficha: data.ficha };
      }
      if (actionId === "chat.agents") {
        const data = await request("/chat/agents");
        if (!Array.isArray(data.agents)) throw new Error("INVALID_AGENTS_RESPONSE");
        return { ok: true, items: data.agents.map(agent => ({
          id: String(agent.id || agent.agent_id || ""),
          label: String(agent.label || agent.name || agent.id || agent.agent_id || ""),
          description: String(agent.status || agent.model || "UNKNOWN"),
        })).filter(agent => agent.id && !/deepseek/i.test(agent.id)) };
      }
      if (actionId === "chat.conversations") {
        const data = await request("/chat/conversations");
        const items = Array.isArray(data.conversations) ? data.conversations : [];
        if (!Array.isArray(data.conversations)) throw new Error("INVALID_CONVERSATIONS_RESPONSE");
        return { ok: true, items: items.map(item => ({
          id: String(item.id || ""),
          label: String(item.title || item.id || ""),
          description: String(item.updated_at || item.status || "UNKNOWN"),
        })).filter(item => item.id) };
      }
      if (actionId === "chat.usage") {
        const data = await request("/chat/usage");
        if (!data || typeof data !== "object") throw new Error("INVALID_USAGE_RESPONSE");
        return { ok: true, usage: data };
      }
      if (actionId === "chat.storage") {
        const data = await request("/chat/storage");
        if (!data || typeof data !== "object") throw new Error("INVALID_STORAGE_RESPONSE");
        return { ok: true, storage: data };
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
