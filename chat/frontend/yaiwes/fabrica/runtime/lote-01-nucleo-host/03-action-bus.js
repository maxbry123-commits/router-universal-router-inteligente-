/* 03-action-bus.js
 * 1 función: registrar y disparar actions por id (RibbonX onAction).
 * Fail-closed: action no registrada => no ejecuta.
 * Cablear: import { ActionBus, actions } from "./03-action-bus.js";
 */

export class ActionBus {
  constructor() {
    this._handlers = new Map();
    this._log = [];
  }

  register(actionId, handler) {
    if (typeof actionId !== "string" || !actionId.trim()) {
      throw new Error("ActionBus.register: actionId vacío");
    }
    if (typeof handler !== "function") {
      throw new Error("ActionBus.register: handler no es función");
    }
    this._handlers.set(actionId, handler);
    return () => this._handlers.delete(actionId);
  }

  has(actionId) {
    return this._handlers.has(actionId);
  }

  list() {
    return Array.from(this._handlers.keys());
  }

  async dispatch(actionId, payload) {
    const handler = this._handlers.get(actionId);
    const record = {
      at: Date.now(),
      actionId,
      ok: false,
      reason: null
    };
    if (!handler) {
      record.reason = "action_missing";
      this._log.push(record);
      return { ok: false, reason: "action_missing", actionId };
    }
    try {
      const result = await handler(payload || {}, actionId);
      record.ok = true;
      this._log.push(record);
      return { ok: true, actionId, result };
    } catch (err) {
      record.reason = "handler_throw";
      record.message = String(err && err.message ? err.message : err);
      this._log.push(record);
      return { ok: false, reason: "handler_throw", actionId, error: record.message };
    }
  }

  last(n) {
    const count = typeof n === "number" ? n : 20;
    return this._log.slice(-count);
  }
}

export const actions = new ActionBus();
