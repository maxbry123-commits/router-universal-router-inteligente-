import { renderSelector, MODEL_GROUPS } from './model-selector.js';

// FIX MINIMAX 2E: el valor por defecto era el primer motor local (s1) y no el
// ROUTER principal (el proxy con la cadena Local->NVIDIA->Groq). Ahora el
// chat arranca en el router y ademas se guarda el agente elegido (espejo).
let activeEndpoint = (MODEL_GROUPS.router && MODEL_GROUPS.router.endpoint) || "";
let activeModel = MODEL_GROUPS.router.models[0].id;
let activeAgent = "";

// Inicializar el selector en el contenedor del chat
document.addEventListener("DOMContentLoaded", () => {
  renderSelector("model-selector-container", (endpoint, modelId, groupKey, agent) => {
    activeEndpoint = endpoint;
    activeModel = modelId;
    activeAgent = agent || "";
    console.log(`Modelo cambiado a: ${modelId} (${groupKey}) en ${endpoint}${activeAgent ? ' · agente ' + activeAgent : ''}`);

    // Despachar evento global para que el chat o los paneles se enteren
    window.dispatchEvent(new CustomEvent("model:changed", {
      detail: { endpoint, modelId, groupKey, agent: activeAgent }
    }));
  });

  // El grupo local define el endpoint por modelo: se toma de la primera opcion real.
  const sel = document.getElementById("model-select");
  if (sel && sel.selectedOptions.length) {
    activeEndpoint = sel.selectedOptions[0].dataset.endpoint || activeEndpoint;
    activeModel = (sel.selectedOptions[0].value || "").split(":").pop() || activeModel;
    activeAgent = sel.selectedOptions[0].dataset.agent || "";
  }
});

// Función para que el chat sepa a dónde enviar las peticiones
export function getActiveEndpoint() {
  return activeEndpoint;
}

export function getActiveModel() {
  return activeModel;
}

export function getActiveAgent() {
  return activeAgent;
}
