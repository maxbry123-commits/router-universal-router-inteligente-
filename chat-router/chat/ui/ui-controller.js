import { renderSelector, MODEL_GROUPS } from './model-selector.js';

let activeEndpoint = MODEL_GROUPS.yaiwes_local.endpoint || "";
let activeModel = MODEL_GROUPS.yaiwes_local.models[0].id;

// Inicializar el selector en el contenedor del chat
document.addEventListener("DOMContentLoaded", () => {
  renderSelector("model-selector-container", (endpoint, modelId, groupKey) => {
    activeEndpoint = endpoint;
    activeModel = modelId;
    console.log(`Modelo cambiado a: ${modelId} (${groupKey}) en ${endpoint}`);
    
    // Despachar evento global para que el chat o los paneles se enteren
    window.dispatchEvent(new CustomEvent("model:changed", {
      detail: { endpoint, modelId, groupKey }
    }));
  });

  // El grupo local define el endpoint por modelo: se toma de la primera opcion real.
  const sel = document.getElementById("model-select");
  if (sel && sel.selectedOptions.length) {
    activeEndpoint = sel.selectedOptions[0].dataset.endpoint || activeEndpoint;
    activeModel = (sel.selectedOptions[0].value || "").split(":").pop() || activeModel;
  }
});

// Función para que el chat sepa a dónde enviar las peticiones
export function getActiveEndpoint() {
  return activeEndpoint;
}

export function getActiveModel() {
  return activeModel;
}
