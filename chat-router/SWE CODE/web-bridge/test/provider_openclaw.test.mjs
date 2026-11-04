// provider-openclaw.json (SWE CODE free): catalogo del proveedor "swecode" para OpenClaw. Los 5 modelos API entran al array existente,
// los dos Llama salen, y todo lo demas (modelos previos, mcp, ejecutor_tools, puerto 7870) se conserva.
import test from "node:test";
import assert from "node:assert/strict";
import fs from "node:fs";
import { fileURLToPath } from "node:url";
import { MODELOS_API, idsRespaldo } from "../src/respaldo.js";
import { prepararApp, arrancar, limpiar } from "./helpers/bridge_app.mjs";
import "./helpers/acceso.mjs";

const RUTA = fileURLToPath(new URL("../../../SWE CODE free/provider-openclaw.json", import.meta.url));
const cfg = JSON.parse(fs.readFileSync(RUTA, "utf8"));
const porId = Object.fromEntries(cfg.modelos.map((m) => [m.id, m.nombre]));

test("los 5 modelos API estan en el array modelos con su nombre", () => {
  assert.deepEqual(
    ["groq/qwen/qwen3.8-27b", "nvidia/minimaxai/minimax-m3.1-flash", "nvidia/meta/muse-glimmer-30b", "nvidia/nvidia/nemotron-3-ultra-550b-a55b", "nvidia/z-ai/glm-5.3"].map((id) => porId[id]),
    ["Groq · Qwen 3.8 27B", "NVIDIA · MiniMax M3.1 Flash", "NVIDIA · Muse Glimmer 30B", "NVIDIA · Nemotron 3 Ultra", "NVIDIA · GLM 5.3"]);
  for (const m of MODELOS_API.filter((m) => /^(groq|nvidia)\//.test(m.id))) assert.ok(porId[m.id], `falta ${m.id} (MODELOS_API)`);
});

test("los dos Llama ya no estan; no hay ids duplicados; Muse Glimmer una sola vez", () => {
  assert.ok(!cfg.modelos.some((m) => /llama/i.test(m.id) || /llama/i.test(m.nombre)));
  const ids = cfg.modelos.map((m) => m.id);
  assert.equal(new Set(ids).size, ids.length);
  assert.equal(ids.filter((i) => /muse-glimmer/.test(i)).length, 1);
});

test("alcance SOLO Groq+NVIDIA: modos SWE + ids groq/nvidia de idsRespaldo(); sin web Qwen/DeepSeek, concilio ni locales Liquid/Qwen", () => {
  for (const id of ["swecode-revision", "swecode-solucion", "swecode-arquitectura", "swecode-archivos", "swecode-prompt_code", "swecode-despliega", "swecode-asesoria"]) assert.ok(porId[id], `falta ${id}`);
  for (const id of idsRespaldo().filter((i) => /^(groq|nvidia)\//.test(i))) assert.ok(porId[id], `falta ${id} de idsRespaldo()`);
  for (const id of ["web-qwen38max", "web-qwen37max", "web-dsv4-flash", "swecode-consulta", "lfm2.5-350m", "qwen3-0.6b"]) assert.ok(!porId[id], `sobra ${id}`);
});

test("estructura intacta: provider swecode, openai-compatible, puerto 7870, mcp y ejecutor_tools", () => {
  assert.equal(cfg.provider, "swecode"); assert.equal(cfg.nombre, "SWE CODE / SWEN CODE free"); assert.equal(cfg.tipo, "openai-compatible");
  assert.equal(cfg.base_url, "http://localhost:7870/v1");
  assert.equal(cfg.mcp.nombre, "yaiwes-router"); assert.equal(cfg.mcp.valor_desde_env, "RIU_API_KEY");
  assert.deepEqual(cfg.ejecutor_tools.valores, ["swe", "openclaw"]); assert.equal(cfg.ejecutor_tools.defecto, "swe");
  assert.ok(cfg.gramatica && cfg.via);
});

test("el archivo no contiene claves", () => {
  assert.ok(!/(gsk_|nvapi-|sk-)[A-Za-z0-9_-]{10,}/.test(fs.readFileSync(RUTA, "utf8")));
});

// ---------- cableado de modelos con OpenClaw: el provider y el bridge hablan de los mismos ids ----------
test("provider: baseUrl, api_key por variable de entorno y los 5 modelos API + 4 locales HF con ids exactos", () => {
  assert.equal(cfg.base_url, "http://localhost:7870/v1"); assert.equal(cfg.api_key, "${RIU_API_KEY}"); assert.ok(!cfg.api_key.includes("BRIDGE_TOKEN"), "BRIDGE_TOKEN es opcional: el provider usa la clave de acceso por Bearer");
  assert.deepEqual(MODELOS_API.map((m) => m.id).filter((id) => /^(groq|nvidia)\//.test(id)), ["groq/qwen/qwen3.8-27b", "nvidia/minimaxai/minimax-m3.1-flash", "nvidia/meta/muse-glimmer-30b", "nvidia/nvidia/nemotron-3-ultra-550b-a55b", "nvidia/z-ai/glm-5.3", "nvidia/z-ai/glm-5.3-flash"]);
  assert.deepEqual(idsRespaldo().slice(MODELOS_API.length), ["lfm2.5-350m", "qwen2.5-coder-1.5b", "qwen3.5-0.8b", "qwen3-0.6b"]);
  for (const id of idsRespaldo()) assert.ok(porId[id], id);
});

test("GET /v1/models del bridge REAL devuelve exactamente los mismos ids que provider-openclaw.json (ni uno mas ni uno menos)", async () => {
  prepararApp();
  const S = await arrancar("MODELOS", { BRIDGE_TOKEN: "token-prueba-modelos" });
  try {
    const r = await fetch(S.base + "/v1/models", { headers: { authorization: "Bearer token-prueba-modelos" } });
    assert.equal(r.status, 200);
    const ids = (await r.json()).data.map((m) => m.id);
    assert.deepEqual([...ids].sort(), cfg.modelos.map((m) => m.id).sort());
  } finally { limpiar(); }
});
