const STORAGE_KEY = "riu_chat_isolation_v1";
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

function activeSession(root) {
  const button = [...root.querySelectorAll("#chat-tabs button")]
    .find((item) => item.classList.contains("on") && sessionFromButton(item));
  return sessionFromButton(button);
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

  // El renderer rehace los botones de pestañas; este observer solo restaura
  // controles de la sesión activa. No guarda historial: eso pertenece al Punto 2.
  const observer = new MutationObserver(() => restoreActive(root));
  observer.observe(tabs, { childList: true });

  restoreActive(root);
  return true;
}

export const __test = { sessionFromButton, activeSession, modeFromUI, snapshot };
