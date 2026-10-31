import test from "node:test";
import assert from "node:assert/strict";

// api() corta los fetch a los 15 s salvo los de chat largo: el envio SWE por /web/v1/chat/completions (modelos locales HF) debe tener el mismo tope largo que /v1/chat/completions
const datos = new Map();
globalThis.window = globalThis;
globalThis.localStorage = { getItem: (k) => datos.get(k) ?? null, setItem: (k, v) => datos.set(k, String(v)) };
globalThis.sessionStorage = { getItem: () => "k" };
globalThis.addEventListener = () => {}; globalThis.removeEventListener = () => {}; globalThis.dispatchEvent = () => true;
globalThis.document = { addEventListener() {}, visibilityState: "visible" };
globalThis.location = { hostname: "x.hf.space", origin: "https://x.hf.space", search: "" };
globalThis.CustomEvent = class { constructor(t, o) { this.type = t; this.detail = o && o.detail; } };
window.RIU_CONFIG = { proxyDestino: "https://comand-center-1-riu-router.hf.space", liveUrl: "" };
globalThis.fetch = async () => ({ ok: true, status: 200, headers: { get: () => "application/json" }, json: async () => ({}) });
const { api } = await import("../api.js");

test("los POST de chat SWE (/v1 y /web/v1) esperan la respuesta completa (450 s); una ruta normal, 15 s", async () => {
  const esperas = [];
  const st = globalThis.setTimeout;
  globalThis.setTimeout = (fn, ms, ...a) => { esperas.push(ms); return st(fn, ms, ...a); };
  try {
    for (const ruta of ["/v1/chat/completions", "/web/v1/chat/completions", "/health"]) {
      esperas.length = 0;
      await api(ruta, { method: "POST", body: {} });
      assert.ok(esperas.includes(ruta === "/health" ? 15000 : 450000), ruta + " -> " + JSON.stringify(esperas));
    }
  } finally { globalThis.setTimeout = st; }
});
