// Selector de modelos del chat. 3 locales + NVIDIA (4) + Groq (6 Qwen3.8).
const MODELS = {
  local: [
    { id: "qwen2.5-coder-0.5b", label: "Qwen 2.5 Coder 0.5B", group: "HF Local" },
    { id: "lfm2.5-350m", label: "LFM 2.5 350M", group: "HF Local" },
    { id: "qwen3.5-0.8b", label: "Qwen 3.5 0.8B", group: "HF Local" }
  ],
  nvidia: [
    { id: "minimax-m3.1-flash", label: "Minimax M3.1 Flash", group: "NVIDIA" },
    { id: "granite-meta", label: "Granite Meta", group: "NVIDIA" },
    { id: "nemotron-super", label: "Nemotron Super", group: "NVIDIA" },
    { id: "nemotron-ultra", label: "Nemotron Ultra", group: "NVIDIA" }
  ],
  groq: [
    { id: "qwen3.8-32b", label: "Qwen 3.8 32B", group: "Groq" }
  ]
};

function buildSelector(containerId) {
  const container = document.getElementById(containerId);
  if (!container) return;
  const groups = [
    { name: "HF Local (Grupo 2)", models: MODELS.local },
    { name: "NVIDIA (4 APIs)", models: MODELS.nvidia },
    { name: "Groq (6 APIs)", models: MODELS.groq }
  ];
  let html = '<select id="model-select">';
  for (const g of groups) {
    html += `<optgroup label="${g.name}">`;
    for (const m of g.models) html += `<option value="${m.id}">${m.label}</option>`;
    html += `</optgroup>`;
  }
  html += '</select>';
  container.innerHTML = html;
}

function getSelectedModel() {
  const sel = document.getElementById("model-select");
  return sel ? sel.value : "qwen2.5-coder-0.5b";
}

window.buildSelector = buildSelector;
window.getSelectedModel = getSelectedModel;
