// model-selector.js
export const MODEL_GROUPS = {
  yaiwes_local: {
    label: "YAIWES HF (Grupo 2)",
    endpoint: "https://comand-center-1-swe-code-s1.hf.space/v1",
    models: [
      { id: "Qwen/Qwen2.5-Coder-0.5B-Instruct-GGUF", label: "Qwen 2.5 Coder 0.5B" },
      { id: "LiquidAI/LFM2.5-350M-GGUF", label: "LFM 2.5 350M" },
      { id: "unsloth/Qwen3.5-0.8B-GGUF", label: "Qwen 3.5 0.8B" }
    ]
  },
  nvidia: {
    label: "NVIDIA (Fallback Externo)",
    endpoint: "https://comand-center-1-local-llm-router.hf.space/v1/nvidia",
    models: [
      { id: "minimaxai/minimax-m3.1-flash", label: "Minimax M3.1 Flash" },
      { id: "meta/llama-3.3-70b-instruct", label: "Granite Meta" },
      { id: "nvidia/llama-3.1-nemotron-70b-instruct", label: "Nemotron Super" },
      { id: "nvidia/llama-3.1-nemotron-ultra-253b-v1", label: "Nemotron Ultra" }
    ]
  },
  groq: {
    label: "Groq (Fallback Externo)",
    endpoint: "https://comand-center-1-local-llm-router.hf.space/v1/groq",
    models: [
      { id: "qwen/qwen3-32b", label: "Qwen 3.8" } // 6 APIs rotativas
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
  },
  openclaw: {
    label: "OpenClaw Agent",
    endpoint: "wss://comand-center-1-riu-router.hf.space/openclaw",
    models: [{ id: "openclaw", label: "OpenClaw WS" }]
  },
  hermes: {
    label: "Hermes Agent",
    endpoint: "wss://comand-center-1-riu-router.hf.space/hermes",
    models: [{ id: "hermes", label: "Hermes WS" }]
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
      option.value = `${key}:${model.id}`;
      option.textContent = model.label;
      optgroup.appendChild(option);
    }
    select.appendChild(optgroup);
  }

  select.addEventListener("change", (e) => {
    const [groupKey, modelId] = e.target.value.split(":");
    onSelect(MODEL_GROUPS[groupKey].endpoint, modelId, groupKey);
  });

  container.innerHTML = "";
  container.appendChild(select);
}

export function getEndpointFor(groupKey) {
  return MODEL_GROUPS[groupKey]?.endpoint || MODEL_GROUPS.yaiwes_local.endpoint;
}
