// model-selector.js — FIX MINIMAX 2E:
//  · falta el grupo del ROUTER PRINCIPAL (el proxy con la cadena Local->NVIDIA->Groq)
//  · los ids de NVIDIA/Groq que habia estaban MUERTOS (410/404) -> el chat fallaba
//  · no habia forma de hablar con los agentes (openclaw/hermes/chat_a/chat_b)
// Las fuentes de verdad son: external/core/space_inventory.py (Spaces) y
// router_llm_hf/AGENTS_REGISTRY.json (agentes). Aqui no hay secretos.

export const MODEL_GROUPS = {
  router: {
    label: "ROUTER (proxy principal)",
    endpoint: "https://comand-center-1-local-llm-router.hf.space/v1",
    models: [
      { id: "minimaxai/minimax-m3.1-flash", label: "Router · Minimax M3.1 Flash", endpoint: "https://comand-center-1-local-llm-router.hf.space/v1" }
    ]
  },
  yaiwes_local: {
    label: "YAIWES HF (Grupo 2 · motores locales)",
    models: [
      { id: "Qwen/Qwen2.5-Coder-0.5B-Instruct-GGUF", label: "Qwen 2.5 Coder 0.5B", endpoint: "https://comand-center-1-swe-code-s1.hf.space/v1" },
      { id: "LiquidAI/LFM2.5-350M-GGUF", label: "LFM 2.5 350M", endpoint: "https://comand-center-1-swe-code-s2.hf.space/v1" },
      { id: "unsloth/Qwen3.5-0.8B-GGUF", label: "Qwen 3.5 0.8B", endpoint: "https://comand-center-1-swe-code-s3.hf.space/v1" }
    ]
  },
  nvidia: {
    label: "NVIDIA (Fallback Externo)",
    endpoint: "https://comand-center-1-local-llm-router.hf.space/v1/nvidia",
    models: [
      { id: "minimaxai/minimax-m3.1-flash", label: "Minimax M3.1 Flash" },
      { id: "nvidia/nemotron-3.5-lightning-30b-a3b", label: "Nemotron 3.5 Lightning 30B" },
      { id: "nvidia/nemotron-3.5-bolt-e4b", label: "Nemotron 3.5 Bolt 4B" }
    ]
  },
  groq: {
    label: "Groq (Fallback Externo)",
    endpoint: "https://comand-center-1-local-llm-router.hf.space/v1/groq",
    models: [
      { id: "llama-3.1-8b-instant", label: "Llama 3.1 8B Instant" },
      { id: "llama-3.3-70b-versatile", label: "Llama 3.3 70B" },
      { id: "openai/gpt-oss-20b", label: "GPT OSS 20B" },
      { id: "openai/gpt-oss-120b", label: "GPT OSS 120B" }
    ]
  },
  // Agentes del registro central: se hablan por /v1/agents/<nombre> (espejo).
  // El motor es el mismo que el del chat, asi que el espejo es determinista.
  agentes: {
    label: "AGENTES (espejo del registro central)",
    models: [
      { id: "minimaxai/minimax-m3.1-flash", label: "OpenClaw · agente autonomo", endpoint: "/v1/agents/openclaw" },
      { id: "minimaxai/minimax-m3.1-flash", label: "Hermes · comunicacion", endpoint: "/v1/agents/hermes" },
      { id: "minimaxai/minimax-m3.1-flash", label: "ChatA · arquitecto", endpoint: "/v1/agents/chat_a" },
      { id: "minimaxai/minimax-m3.1-flash", label: "ChatB · implementador", endpoint: "/v1/agents/chat_b" }
    ]
  },
  swe_code_free: {
    label: "SWE CODE Free",
    endpoint: "https://comand-center-1-local-llm-router.hf.space/v1/swe-free",
    models: [{ id: "swe-code-free", label: "Agente Auto" }]
  },
  swe_code: {
    label: "SWE CODE",
    endpoint: "https://comand-center-1-local-llm-router.hf.space/v1/swe",
    models: [{ id: "swe-code-standard", label: "Agente Standard" }]
  },
  team_qwe: {
    label: "Team QWE",
    endpoint: "https://comand-center-1-local-llm-router.hf.space/v1/team-qwe",
    models: [{ id: "team-qwe-orchestrator", label: "Orquestador Múltiple" }]
  }
};

export function renderSelector(containerId, onSelect) {
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
