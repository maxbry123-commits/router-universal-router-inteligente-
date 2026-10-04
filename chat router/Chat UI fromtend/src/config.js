export const STORAGE_KEY = "yaiwes.chat.frontend.v1";
export const CONTROL_LABELS = Object.freeze({
  configure: "Configurar", back: "Volver al chat", save: "Guardar configuración", close: "Nuevo chat", export: "Exportar chat",
  models: "Elegir modelo", modes: "Razonamiento", functions: "+ 12 funciones",
  attach: "Adjuntar", voice: "Voz", watchdog: "Watchdog", send: "Enviar ↗",
  skills: "Habilidades", connectors: "Conectores", plugins: "Plugins del Router", fichas: "Fichas del Router", components: "Componentes UI", agents: "Agentes del Router", conversations: "Conversaciones",
  tools: "Herramientas", selectors: "Selectores", controls: "Controles", chatMenu: "Menú del chat", documents: "Subir documentos",
});

const slots = (count, prefix) => Array.from({ length: count }, (_, i) => ({
  id: `${prefix}-${i + 1}`,
  label: `${prefix === "mode" ? "Nivel" : prefix === "selector" ? "Selector" : prefix === "toggle" ? "Control" : "Función"} ${i + 1}`,
  description: "",
  actionId: "",
  ...(prefix === "selector" ? { options: [] } : {}),
}));

export const DEFAULT_CONFIG = Object.freeze({
  title: "Chat YAIWES",
  description: "Elige un modelo y configura las acciones para conectar tu backend.",
  theme: "gris",
  locale: "es",
  labels: CONTROL_LABELS,
  descriptions: {},
  models: [],
  modelsActionId: "chat.models",
  modelActionId: "",
  sendActionId: "chat.send",
  attachActionId: "chat.attach",
  documentsActionId: "chat.attach",
  voiceActionId: "",
  watchdogActionId: "",
  skillsActionId: "",
  connectorsActionId: "",
  modes: slots(8, "mode"),
  selectors: slots(5, "selector"),
  toggles: slots(8, "toggle"),
  actions: slots(12, "action"),
});

const asString = value => typeof value === "string" ? value.trim().slice(0, 200) : "";
const item = (value, fallback) => ({
  id: fallback.id,
  label: asString(value?.label) || fallback.label,
  description: asString(value?.description),
  actionId: asString(value?.actionId),
  ...(fallback.options ? { options: Array.isArray(value?.options)
    ? value.options.slice(0, 50).map((entry, index) => ({
        id: asString(entry?.id) || String(index + 1),
        label: asString(entry?.label) || `Opción ${index + 1}`,
        actionId: asString(entry?.actionId),
      })) : [] } : {}),
});

export function normalizeConfig(value = {}) {
  if (!value || typeof value !== "object") value = {};
  const result = {};
  for (const key of ["title", "description", "modelsActionId", "modelActionId", "sendActionId", "attachActionId", "documentsActionId", "voiceActionId", "watchdogActionId", "skillsActionId", "connectorsActionId"]) {
    result[key] = asString(value[key] ?? DEFAULT_CONFIG[key]);
  }
  result.theme = ["gris", "little", "matte", "blanco", "crystal", "orange", "blue"].includes(value.theme) ? value.theme : "gris";
  result.locale = ["es", "en", "fr", "pt"].includes(value.locale) ? value.locale : "es";
  result.labels = Object.fromEntries(Object.entries(CONTROL_LABELS).map(([key, label]) => [key, asString(value.labels?.[key]) || label]));
  result.descriptions = Object.fromEntries(Object.keys(CONTROL_LABELS).map(key => [key, asString(value.descriptions?.[key])]));
  result.models = Array.isArray(value.models) ? value.models.slice(0, 100).map((model, index) => ({
    id: asString(model?.id) || `model-${index + 1}`,
    label: asString(model?.label) || asString(model?.id) || `Modelo ${index + 1}`,
  })) : [];
  for (const key of ["modes", "selectors", "toggles", "actions"]) {
    result[key] = DEFAULT_CONFIG[key].map((fallback, i) => item(value[key]?.[i], fallback));
  }
  return result;
}

export function readConfig(storage) {
  try { return normalizeConfig(JSON.parse((storage ?? globalThis.localStorage).getItem(STORAGE_KEY) || "{}")); }
  catch { return normalizeConfig(); }
}

export function saveConfig(config, storage = globalThis.localStorage) {
  const normalized = normalizeConfig(config);
  storage.setItem(STORAGE_KEY, JSON.stringify(normalized));
  return normalized;
}
