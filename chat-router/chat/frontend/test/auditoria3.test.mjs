import test from "node:test";
import assert from "node:assert/strict";

// Auditoria 3 / hallazgos 8: selectores fijos por workflow, Qwen3 0.6B, tools pedidas, mensaje de seleccion no disponible, claves multiples. Sin red.
const datos = new Map();
globalThis.window = globalThis;
globalThis.localStorage = { getItem: (k) => datos.get(k) ?? null, setItem: (k, v) => datos.set(k, String(v)), removeItem: (k) => datos.delete(k) };
const S = await import("../swe-directo.js");
test.beforeEach(() => datos.clear());

// ---- 8) controles que no influyen en el workflow elegido ----
test("camposFijos: swe_code y liquid_mirror fijan modelo_responde, agente_responde y modelo_tool; individual no fija nada", () => {
  assert.deepEqual([...S.camposFijos("swe_code")].sort(), ["agente_responde", "modelo_responde", "modelo_tool"]);
  assert.deepEqual([...S.camposFijos("liquid_mirror")].sort(), ["agente_responde", "modelo_responde", "modelo_tool"]);
  assert.deepEqual([...S.camposFijos("individual")], []);
  assert.deepEqual([...S.camposFijos("raro")], []);
});

// ---- E) Qwen3 0.6B ----
test("Qwen3 0.6B (HF) esta en la lista de SWE CODE y se envia como qwen3-0.6b", () => {
  const e = S.SWE_LISTAS["swe-code"].modelos.find((m) => m[0] === "hf-qwen3-06b");
  assert.deepEqual(e, ["hf-qwen3-06b", "Qwen3 0.6B (HF)", "Qwen3-0.6B"]);
  assert.ok(S.esSwe("hf-qwen3-06b"));
  assert.equal(S.armar({ model: "hf-qwen3-06b", mensaje: "x", sesion: "s" }).model, "qwen3-0.6b");
  assert.equal(S.rutaSwe("hf-qwen3-06b"), "/web/v1/chat/completions");
  assert.equal(S.idCatalogo("hf-qwen3-06b"), "hf/qwen3-0.6b");
});

test("entradaParaCatalogo: el desplegable «Responde» y la lista de la hoja eligen el mismo modelo", () => {
  assert.equal(S.entradaParaCatalogo("swe-code", "hf/qwen3-0.6b", "hf-qwen25-coder-15b"), "hf-qwen3-06b");
  assert.equal(S.entradaParaCatalogo("swe-code", "hf/lfm2.5-350m", "swe-agent-lfm25"), "swe-agent-lfm25", "si la seleccion ya equivale, se conserva");
  assert.equal(S.entradaParaCatalogo("swe-code", "hf/lfm2.5-350m", "hf-qwen3-06b"), "hf-liquid-lfm25");
  assert.equal(S.entradaParaCatalogo("swen-code-free", "nvidia/z-ai/glm-5.3", "web-qwen38max"), "nvidia/z-ai/glm-5.3");
  assert.equal(S.entradaParaCatalogo("swen-code-free", "hf/qwen3-0.6b", "web-qwen38max"), null, "sin entrada equivalente no se inventa");
  assert.equal(S.entradaParaCatalogo("nada", "hf/qwen3-0.6b", "x"), null);
});

// ---- C) tools pedidas ----
test("tool_calls con Salida OpenClaw/SWE-agent: no son «usadas»; tools queda vacio y se listan como pedidas", async () => {
  const tc = [{ id: "c1", type: "function", function: { name: "github_leer", arguments: "{}" } }];
  const api = async () => ({ modelo_usado: "groq/x", choices: [{ message: { content: "", tool_calls: tc }, finish_reason: "tool_calls" }] });
  for (const [ej, quien] of [["openclaw", "OpenClaw"], ["swe", "SWE-agent"]]) {
    const r = await S.enviarSwe(api, { model: "groq/qwen/qwen3.8-27b", historial: [], mensaje: "x", sesion: "s", ejecutor_tools: ej });
    assert.deepEqual(r.tools, []); assert.deepEqual(r.pedidas, ["github_leer"]); assert.equal(r.ejecutor, quien);
    assert.equal(r.finish_reason, "tool_calls"); assert.match(r.reply, /github_leer/);
  }
});

// ---- D) seleccion no disponible: mensaje legible ----
test("SELECCION_NO_DISPONIBLE: sin parentesis anidados y termina con la salida para chatear", async () => {
  S.guardarSeleccion({ modo_agentico: true }); S.olvidarCapacidades();
  const api = async () => ({ harness: "ok", agentes: {}, workflows: {} });
  await assert.rejects(() => S.enviarTareaSwe(api, { mensaje: "x", sesion: "s" }), (e) => {
    assert.match(e.message, /^GAP: SELECCION_NO_DISPONIBLE · /);
    assert.match(e.message, /SWE-agent.*NO DISPONIBLE/);
    assert.ok(!/\([^)]*\(/.test(e.message), "sin parentesis anidados: " + e.message);
    assert.ok(e.message.endsWith("Para chatear: abre SWE CODE/SWEN → Agentes → Modo agéntico OFF y Workflow Individual"), e.message);
    return true;
  });
});

// ---- F) claves: varias por proveedor ----
const C = await import("../swe-claves.js");
test("varias claves por proveedor: se separan por coma, punto y coma, espacio o salto de linea; tope 20; sin duplicados", () => {
  assert.deepEqual(C.separarClaves("a1234567, b1234567;c1234567\nd1234567  e1234567"), ["a1234567", "b1234567", "c1234567", "d1234567", "e1234567"]);
  assert.deepEqual(C.separarClaves(["a1234567 b1234567", " ", "a1234567", 3]), ["a1234567", "b1234567"]);
  const muchas = Array.from({ length: 30 }, (_, i) => "clave-numero-" + i).join(",");
  assert.equal(C.separarClaves(muchas).length, 20);
  assert.deepEqual(C.separarClaves(""), []); assert.deepEqual(C.separarClaves(null), []);
  C.guardarClave("groq", "g1234567, g7654321");
  assert.deepEqual(C.leerClaves(), { groq: ["g1234567", "g7654321"] });
  C.guardarClave("nvidia", " solo-una-clave ");
  assert.deepEqual(C.leerClaves().nvidia, "solo-una-clave");
});

function banco(respuestas) {
  globalThis.window = { RIU_CONFIG: { apiBase: "https://t.hf.space" } };
  globalThis.sessionStorage = { getItem: () => "k" };
  const llamadas = [];
  globalThis.fetch = async (url, op) => { llamadas.push({ metodo: op.method, body: op.body ? JSON.parse(op.body) : undefined }); const r = respuestas.shift() || { status: 200, json: { groq: 0, nvidia: 0 } }; if (r.red) throw new TypeError("x"); return { ok: r.status < 300, status: r.status, json: async () => r.json || {} }; };
  return llamadas;
}
test("guardar manda arrays al banco y cuenta bien; el respaldo local dice cuantas", async () => {
  let ll = banco([{ status: 200, json: { groq: 3, nvidia: 0 } }]);
  assert.equal(await C.guardar({ groq: "g1234567 g2234567,g3234567" }), "Groq: 3 guardadas");
  assert.deepEqual(ll[0].body.groq, ["g1234567", "g2234567", "g3234567"]);
  ll = banco([{ red: true }]);
  assert.match(await C.guardar({ groq: "g1234567 g2234567" }), /Groq: 2 guardadas solo en este navegador/);
  assert.deepEqual(C.leerClaves().groq, ["g1234567", "g2234567"]);
});
test("el 400 explica la regla", async () => {
  banco([{ status: 400, json: { error: { code: "CLAVE_INVALIDA" } } }]);
  assert.match(await C.guardar({ groq: "corta" }), /8.300 caracteres, sin espacios/);
});
test("guardarConEstado: ok solo si se guardo (banco o respaldo); un 401/400 no es exito (los inputs no se vacian)", async () => {
  banco([{ status: 200, json: { groq: 1, nvidia: 0 } }]); assert.equal((await C.guardarConEstado({ groq: "g1234567" })).ok, true);
  banco([{ red: true }]); assert.equal((await C.guardarConEstado({ groq: "g1234567" })).ok, true);
  banco([{ status: 401 }]); assert.equal((await C.guardarConEstado({ groq: "g1234567" })).ok, false);
  banco([{ status: 400 }]); assert.equal((await C.guardarConEstado({ groq: "g1234567" })).ok, false);
  assert.equal((await C.guardarConEstado({ groq: "  " })).ok, false);
});
