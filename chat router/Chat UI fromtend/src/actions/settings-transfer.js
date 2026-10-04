import { normalizeConfig } from "../config.js";

const FORMAT = "yaiwes-chat-settings";

export function parseSettings(text) {
  let data;
  try { data = JSON.parse(text); }
  catch { throw new Error("INVALID_CONFIG_FILE"); }
  if (data?.format !== FORMAT || data.version !== 1 || !data.config ||
      typeof data.config !== "object" || Array.isArray(data.config) ||
      typeof data.config.title !== "string" || !Array.isArray(data.config.modes) ||
      !Array.isArray(data.config.selectors) || !Array.isArray(data.config.toggles) ||
      !Array.isArray(data.config.actions)) {
    throw new Error("INVALID_CONFIG_FILE");
  }
  return normalizeConfig(data.config);
}

export function exportSettings(config, host = globalThis) {
  const data = JSON.stringify({ format: FORMAT, version: 1, config: normalizeConfig(config) }, null, 2);
  const url = host.URL.createObjectURL(new Blob([data], { type: "application/json" }));
  try {
    const link = host.document.createElement("a");
    link.href = url;
    link.download = "chat-yaiwes-configuracion.json";
    host.document.body.append(link);
    link.click();
    link.remove();
  } finally {
    host.setTimeout(() => host.URL.revokeObjectURL(url), 1000);
  }
}

export async function importSettings(file) {
  if (!file || file.size > 1024 * 1024) throw new Error("INVALID_CONFIG_FILE");
  return parseSettings(await file.text());
}
