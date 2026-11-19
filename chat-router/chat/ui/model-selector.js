// model-selector.js — FIX MINIMAX 2E + 2F:
//  · falta el grupo del ROUTER PRINCIPAL (el proxy con la cadena Local->NVIDIA->Groq)
//  · los ids de NVIDIA/Groq que habia estaban MUERTOS (410/404) -> el chat fallaba
//  · no habia forma de hablar con los agentes (openclaw/hermes/chat_a/chat_b)
//  · MINIMAX 2F: los agentes se leen del REGISTRO VIVO (GET /v1/agents), se
//    anaden ruflo y rowboat (las dos raices reales del workspace) y cada agente
//    aparece con su interruptor ON/OFF: un agente OFF no se puede elegir.
// Las fuentes de verdad son: external/core/space_inventory.py (Spaces) y
// router_llm_hf/AGENTS_REGISTRY.json (agentes). Aqui no hay secretos.

export const MODEL_GROUPS = {
  router: {
    label: "ROUTER (proxy principal)",
    endpoint: "https://comand-center-1-space-grupo-1-router-mvp-1.hf.space/v1",
    models: [
      { id: "auto", label: "Router · Auto (recomendado)", endpoint: "https://comand-center-1-space-grupo-1-router-mvp-1.hf.space/v1" }
    ]
  },
  yaiwes_local: {
    label: "YAIWES HF (Grupo 2 · motores locales)",
    models: [
      { id: "Qwen/Qwen2.5-Coder-0.5B-Instruct-GGUF", label: "Qwen 2.5 Coder 0.5B", endpoint: "https://comand-center-1-space-grupo-2-router-llm-hf-1.hf.space/v1" },
      { id: "LiquidAI/LFM2.5-350M-GGUF", label: "LFM 2.5 350M", endpoint: "https://comand-center-1-space-grupo-2-router-llm-hf-2.hf.space/v1" },
      { id: "unsloth/Qwen3.5-0.8B-GGUF", label: "Qwen 3.5 0.8B", endpoint: "https://comand-center-1-space-grupo-2-router-llm-hf-3.hf.space/v1" }
    ]
  },
  nvidia: {
    label: "NVIDIA (Fallback Externo)",
    endpoint: "https://comand-center-1-space-grupo-1-router-mvp-1.hf.space/v1/nvidia",
    models: [
      { id: "minimaxai/minimax-m3.1-flash", label: "Minimax M3.1 Flash" },
      { id: "nvidia/nemotron-3.5-lightning-30b-a3b", label: "Nemotron 3.5 Lightning 30B" },
      { id: "nvidia/nemotron-3.5-bolt-e4b", label: "Nemotron 3.5 Bolt 4B" }
    ]
  },
  groq: {
    label: "Groq (Fallback Externo)",
    endpoint: "https://comand-center-1-space-grupo-1-router-mvp-1.hf.space/v1/groq",
    models: [
      { id: "llama-3.1-8b-instant", label: "Llama 3.1 8B Instant" },
      { id: "llama-3.3-70b-versatile", label: "Llama 3.3 70B" },
      { id: "openai/gpt-oss-20b", label: "GPT OSS 20B" },
      { id: "openai/gpt-oss-120b", label: "GPT OSS 120B" }
    ]
  },
  swe_code_free: {
    label: "Grupo 2 · LLM local (gratis)",
    endpoint: "https://comand-center-1-space-grupo-1-router-mvp-1.hf.space/v1/swe-free",
    models: [{ id: "swe-code-free", label: "Agente Auto" }]
  },
  swe_code: {
    label: "Grupo 2 · LLM local",
    endpoint: "https://comand-center-1-space-grupo-1-router-mvp-1.hf.space/v1/swe",
    models: [{ id: "swe-code-standard", label: "Agente Standard" }]
  },
  team_qwe: {
    label: "Team QWE",
    endpoint: "https://comand-center-1-space-grupo-1-router-mvp-1.hf.space/v1/team-qwe",
    models: [{ id: "team-qwe-orchestrator", label: "Orquestador Múltiple" }]
  }
};

// Reserva (solo si el registro vivo no responde): los 6 agentes declarados.
export const AGENTS_FALLBACK = [
  { name: "openclaw", enabled: true,  type: "mirror",   chat_path: "/v1/agents/openclaw", role: "Agente autonomo" },
  { name: "hermes",   enabled: true,  type: "mirror",   chat_path: "/v1/agents/hermes",   role: "Comunicacion" },
  { name: "chat_a",  enabled: true,  type: "internal", chat_path: "/v1/agents/chat_a",  role: "Arquitecto" },
  { name: "chat_b",  enabled: true,  type: "internal", chat_path: "/v1/agents/chat_b",  role: "Implementador" },
  { name: "ruflo",    enabled: false, type: "workspace", chat_path: "/v1/agents/ruflo",   role: "Raiz claude-flow" },
  { name: "rowboat",  enabled: false, type: "workspace", chat_path: "/v1/agents/rowboat", role: "Raiz rowboat" }
];

// Ultimo registro vivo cargado (lo consume la ventana AGENTES).
export let AGENT_REGISTRY = { agents: [], roots: {}, ok: false };

export async function loadAgents(apiBase = "") {
  // Lee el registro vivo de agentes. Sin red -> lista de reserva (nunca inventada).
  const url = (apiBase || "") + "/v1/agents";
  try {
    const res = await fetch(url, { method: "GET", headers: { "x-api-key": window.__YAWES_KEY__ || "" } });
    if (!res.ok) throw new Error("HTTP " + res.status);
    const data = await res.json();
    const agents = Object.entries(data.agents || {}).map(([name, cfg]) => ({
      name,
      enabled: !!cfg.enabled,
      type: cfg.type,
      role: cfg.role,
      chat_path: cfg.chat_path,
      root: cfg.root,
      tools: cfg.tools || [],
      history_count: cfg.history_count || 0,
      memory_keys: cfg.memory_keys || [],
      implemented: !!cfg.implemented
    }));
    if (!agents.length) throw new Error("registro vacio");
    AGENT_REGISTRY = { agents, roots: data.roots || {}, ok: true, version: data.version };
    return AGENT_REGISTRY;
  } catch (e) {
    AGENT_REGISTRY = { agents: AGENTS_FALLBACK.slice(), roots: {}, ok: false, error: String(e && e.message || e) };
    return AGENT_REGISTRY;
  }
}

export function renderSelector(containerId, onSelect, agents) {
  const container = document.getElementById(containerId);
  if (!container) return;
  const select = document.createElement("select");
  select.className = "model-selector";
  select.id = "model-select";

  for (const [key, group] of Object.entries(MODEL_GROUPS)) {
    const optgroup = document.createElement("optgroup");
    optgroup.label = group.label;
    for (const model of group.models) {
      const option = document.createElement("option");
      // Para modelos locales, guardamos el endpoint específico en el value
      option.value = `${key}:${model.id}`;
      option.dataset.endpoint = model.endpoint || group.endpoint;
      option.dataset.agent = model.endpoint && model.endpoint.includes("/v1/agents/") ? model.endpoint.split("/v1/agents/")[1] : "";
      option.textContent = model.label;
      optgroup.appendChild(option);
    }
    select.appendChild(optgroup);
  }

  // Grupo AGENTES: se construye con el registro vivo (nada hardcodeado).
  const list = (agents && agents.length) ? agents : AGENTS_FALLBACK;
  const optgroup = document.createElement("optgroup");
  optgroup.label = "AGENTES (registro central · ON/OFF)";
  for (const agent of list) {
    const option = document.createElement("option");
    option.value = `agentes:${agent.name}`;
    option.dataset.endpoint = agent.chat_path || ("/v1/agents/" + agent.name);
    option.dataset.agent = agent.name;
    option.dataset.enabled = agent.enabled ? "1" : "0";
    option.textContent = `${agent.enabled ? "" : "⏻ "}${agent.name} · ${agent.role || agent.type || ""}`;
    if (!agent.enabled) option.disabled = true;
    optgroup.appendChild(option);
  }
  select.appendChild(optgroup);

  select.addEventListener("change", (e) => {
    const selected = e.target.selectedOptions[0];
    const [groupKey, modelId] = e.target.value.split(":");
    onSelect(selected.dataset.endpoint, modelId, groupKey, selected.dataset.agent || "");
  });

  container.innerHTML = "";
  container.appendChild(select);
}

// API Global para compatibilidad
window.buildSelector = renderSelector;
window.getSelectedModel = () => {
  const sel = document.getElementById("model-select");
  if (!sel || !sel.selectedOptions.length) return null;
  return sel.selectedOptions[0].dataset.endpoint || null;
};
