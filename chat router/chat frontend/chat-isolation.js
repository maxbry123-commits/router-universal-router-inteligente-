import { api } from "./api.js";

const STORAGE_KEY = "riu_chat_isolation_v1";
const CHATS_KEY = "riu_chats_v1";
const DEFAULT_STATE = Object.freeze({
  draft: "",
  provider: "auto",
  model: "",
  agent: "",
  mode: "balanced",
});

const MODES = {
  fast: "⚡ rápido",
  balanced: "⚖ equilibrado",
  think: "🧠 pensar",
};

const FICHA_ROUTE = Object.freeze({
  "groq-qwen-3-8": { provider: "groq", model: "qwen/qwen3.8-27b" },
  "nv-kimi-k3": { provider: "nvidia", model: "moonshotai/kimi-k3" },
  "nv-nemotron-super": { provider: "nvidia", model: "nvidia/nemotron-3-super-120b-a12b" },
  "nv-nemotron-lightning": { provider: "nvidia", model: "nvidia/nemotron-3.5-lightning-30b-a3b" },
  "nv-muse-glimmer": { provider: "nvidia", model: "meta/muse-glimmer-30b" },
});

function loadState() {
  try {
    const value = JSON.parse(sessionStorage.getItem(STORAGE_KEY) || "{}");
    return value && typeof value === "object" && !Array.isArray(value) ? value : {};
  } catch (_) {
    return {};
  }
}

function saveState(value) {
  try { sessionStorage.setItem(STORAGE_KEY, JSON.stringify(value)); } catch (_) {}
}

function sessionFromButton(button) {
  const title = String(button?.title || "");
  const marker = "sesión ";
  const at = title.indexOf(marker);
  return at >= 0 ? title.slice(at + marker.length).trim() : "";
}

function chatButtons(root) {
  return [...root.querySelectorAll("#chat-tabs button")].filter((button) => sessionFromButton(button));
}

function activeSession(root) {
  const button = chatButtons(root).find((item) => item.classList.contains("on"));
  return sessionFromButton(button);
}

function activeChatIndex(root) {
  return chatButtons(root).findIndex((item) => item.classList.contains("on"));
}

function forceHistorySection(root) {
  const idx = activeChatIndex(root);
  if (idx < 0) return;
  const histories = [...root.querySelectorAll("#histories > .chat-history")];
  histories.forEach((history, i) => {
    const active = i === idx;
    history.hidden = !active;
    history.setAttribute("aria-hidden", active ? "false" : "true");
    history.style.display = active ? "flex" : "none";
  });
  const session = activeSession(root);
  const activeHistory = histories[idx];
  if (activeHistory && session) activeHistory.dataset.sessionId = session;
}

function modeFromUI(root) {
  const text = String(root.querySelector("#modo")?.textContent || "").toLowerCase();
  if (text.includes("rápido")) return "fast";
  if (text.includes("pensar")) return "think";
  return "balanced";
}

function selectHas(select, value) {
  return !!select && [...select.options].some((option) => option.value === value);
}

function snapshot(root) {
  return {
    draft: root.querySelector("#message")?.value || "",
    provider: root.querySelector("#provider")?.value || "auto",
    model: root.querySelector("#model")?.value || "",
    agent: root.querySelector("#agent")?.value || "",
    mode: modeFromUI(root),
  };
}

function persistActive(root) {
  const session = activeSession(root);
  if (!session) return;
  const all = loadState();
  all[session] = snapshot(root);
  saveState(all);
}

function setMode(root, mode) {
  const wanted = MODES[mode] || MODES.balanced;
  const current = String(root.querySelector("#modo")?.textContent || "").toLowerCase();
  if (current.includes(wanted.replace(/^.. /, "").toLowerCase())) return;
  const button = [...root.querySelectorAll("#sh-modo-lista button")]
    .find((item) => String(item.textContent || "").toLowerCase().includes(wanted.replace(/^.. /, "").toLowerCase()));
  if (button) button.click();
}

function restoreModelWhenReady(root, wanted) {
  const select = root.querySelector("#model");
  if (!select || !wanted) return;
  if (selectHas(select, wanted)) { select.value = wanted; return; }
  const observer = new MutationObserver(() => {
    if (selectHas(select, wanted)) {
      select.value = wanted;
      observer.disconnect();
    }
  });
  observer.observe(select, { childList: true, subtree: true });
  setTimeout(() => observer.disconnect(), 2500);
}

function restoreActive(root) {
  forceHistorySection(root);
  const session = activeSession(root);
  if (!session) return;
  const all = loadState();
  const state = { ...DEFAULT_STATE, ...(all[session] || {}) };

  const message = root.querySelector("#message");
  const provider = root.querySelector("#provider");
  const model = root.querySelector("#model");
  const agent = root.querySelector("#agent");

  if (message) message.value = state.draft;
  if (agent && selectHas(agent, state.agent)) agent.value = state.agent;

  if (provider) {
    const nextProvider = selectHas(provider, state.provider) ? state.provider : "auto";
    if (provider.value !== nextProvider) {
      provider.value = nextProvider;
      provider.dispatchEvent(new Event("change", { bubbles: true }));
    }
  }

  if (model) {
    if (selectHas(model, state.model)) model.value = state.model;
    else restoreModelWhenReady(root, state.model);
  }
  setMode(root, state.mode);

  if (!all[session]) {
    all[session] = state;
    saveState(all);
  }
  root.dataset.riuActiveSession = session;
}

function fichaForSession(session) {
  try {
    const rows = JSON.parse(sessionStorage.getItem(CHATS_KEY) || "[]");
    const row = Array.isArray(rows) ? rows.find((item) => item && item.sesion === session) : null;
    return String(row?.ficha || "");
  } catch (_) {
    return "";
  }
}

function shouldFallback(error) {
  return /(MODELO_NO_RESPONDE|EXCEPCION|TIEMPO_TOTAL_AGOTADO|CHAT_FAILED|TODAS_LAS_CLAVES_FALLARON|SIN_RESPUESTA|pipeline)/i
    .test(String(error?.message || error || ""));
}

function installHarnessFallback(root) {
  const original = window.RIU_HARNESS;
  if (typeof original !== "function" || original.__riuFallbackInstalled) return;

  const wrapped = async (options) => {
    try {
      return await original(options);
    } catch (error) {
      if (!shouldFallback(error)) throw error;

      const session = String(options?.sesion || activeSession(root) || "");
      const ficha = fichaForSession(session);
      const route = FICHA_ROUTE[ficha] || { provider: "auto", model: "" };
      const agent = root.querySelector("#agent")?.value || "";
      const body = {
        message: String(options?.message || ""),
        provider: route.provider,
        model: route.model,
        mode: agent ? "agent" : "direct",
        agent_id: agent || null,
        max_tokens: Number(options?.max_tokens || 1024),
      };
      const answer = await api("/chat/send", { method: "POST", body });
      return {
        reply: answer.reply || "",
        tools: [],
        conversation_id: answer.conversation_id || null,
        fallback: "chat_send",
        provider: answer.provider || route.provider,
        model: answer.model || route.model,
      };
    }
  };
  wrapped.__riuFallbackInstalled = true;
  window.RIU_HARNESS = wrapped;
}

export function installChatIsolation(root = document) {
  const tabs = root.querySelector("#chat-tabs");
  const message = root.querySelector("#message");
  if (!tabs || !message) return false;

  // Guarda el estado del chat actual ANTES de que panel-chat cambie la pestaña.
  tabs.addEventListener("click", (event) => {
    if (!event.target.closest("button")) return;
    persistActive(root);
    setTimeout(() => restoreActive(root), 0);
  }, true);

  message.addEventListener("input", () => persistActive(root));
  ["#provider", "#model", "#agent"].forEach((selector) => {
    root.querySelector(selector)?.addEventListener("change", () => persistActive(root));
  });
  root.querySelector("#sh-modo-lista")?.addEventListener("click", () => {
    setTimeout(() => persistActive(root), 0);
  });

  // El renderer rehace los botones de pestañas; sincroniza también la sección
  // visible para que un chat nunca comparta el historial DOM de otro.
  const observer = new MutationObserver(() => restoreActive(root));
  observer.observe(tabs, { childList: true });

  restoreActive(root);
  installHarnessFallback(root);
  return true;
}

export const __test = {
  sessionFromButton,
  activeSession,
  activeChatIndex,
  modeFromUI,
  snapshot,
  fichaForSession,
  shouldFallback,
};
