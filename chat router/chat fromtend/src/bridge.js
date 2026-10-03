export class ActionError extends Error {
  constructor(code, detail = "") {
    super(detail ? `${code}: ${detail}` : code);
    this.name = "ActionError";
    this.code = code;
  }
}

export async function executeAction(actionId, payload = {}, host = globalThis) {
  if (!actionId) throw new ActionError("ACTION_UNCONFIGURED");
  host.dispatchEvent?.(new CustomEvent("yaiwes:ui-action", { detail: { actionId, payload } }));
  const execute = host.YAIWES_PLUGIN_BRIDGE?.execute;
  if (typeof execute !== "function") throw new ActionError("BRIDGE_MISSING");
  try {
    const result = await execute.call(host.YAIWES_PLUGIN_BRIDGE, actionId, payload);
    if (!result || typeof result !== "object" || result.ok !== true || result.error) {
      throw new ActionError("ACTION_FAILED", String(result?.error || "sin confirmación del backend"));
    }
    return result;
  } catch (error) {
    if (error instanceof ActionError) throw error;
    throw new ActionError("ACTION_FAILED", error?.message || String(error));
  }
}
