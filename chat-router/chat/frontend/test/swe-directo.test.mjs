import test from "node:test";
import assert from "node:assert/strict";
import { esSwe, armar, enviarSwe } from "../swe-directo.js";

test("reconoce los ids SWE del selector y deja pasar a los demas modelos por el Router", () => {
  for (const m of ["web-qwen38max", "swecode-asesoria", "hf-liquid-lfm25", "swe-agent-lfm25", "lfm2.5-350m", "groq/qwen/qwen3.8-27b", "nvidia/z-ai/glm-5.3"]) assert.ok(esSwe(m), m);
  for (const m of ["qwen3.8-max", "glm-5.3", "deepseek-v4-pro", "", null]) assert.ok(!esSwe(m), String(m));
});

test("arma el POST OpenAI con el historial, la sesion y el proyecto; los alias hf-* se traducen al id real", () => {
  const b = armar({ model: "hf-liquid-lfm25", historial: [{ role: "user", content: "a" }, { role: "assistant", content: "b" }], mensaje: "c", sesion: "s1", proyecto: "P" });
  assert.equal(b.model, "lfm2.5-350m"); assert.equal(b.conv_id, "s1"); assert.equal(b.proyecto, "P");
  assert.deepEqual(b.messages.map((m) => m.content), ["a", "b", "c"]);
});

test("enviarSwe usa /v1/chat/completions y devuelve la forma que pinta el chat", async () => {
  let visto;
  const api = async (ruta, op) => { visto = { ruta, op }; return { modelo_usado: "web-qwen38max", via_respaldo: "groq", choices: [{ message: { content: "listo" }, finish_reason: "stop" }] }; };
  const r = await enviarSwe(api, { model: "web-qwen38max", historial: [], mensaje: "hola", sesion: "s" });
  assert.equal(visto.ruta, "/v1/chat/completions"); assert.equal(visto.op.method, "POST");
  assert.equal(r.reply, "listo"); assert.equal(r.finish_reason, "stop"); assert.match(r.nota, /groq/);
});

test("si la respuesta no trae texto lanza el error con su codigo (no se pinta como respuesta del modelo)", async () => {
  await assert.rejects(() => enviarSwe(async () => ({ error: { code: "RESPALDO_AGOTADO", message: "nada responde" } }), { model: "web-qwen38max", historial: [], mensaje: "x", sesion: "s" }), /GAP: RESPALDO_AGOTADO/);
});

import { SWE_LISTAS, esSelectorSwe } from "../swe-directo.js";

test("hay dos selectores propios, SWE CODE y SWEN CODE free, cada uno con sus modelos y todos pasan por esSwe", () => {
  assert.deepEqual(Object.keys(SWE_LISTAS).sort(), ["swe-code", "swen-code-free"]);
  assert.ok(esSelectorSwe("swe-code") && esSelectorSwe("swen-code-free") && !esSelectorSwe("groq") && !esSelectorSwe("constructor"));
  for (const [id, l] of Object.entries(SWE_LISTAS)) {
    assert.ok(l.modelos.length >= 4, id);
    for (const [mid] of l.modelos) assert.ok(esSwe(mid), mid + " debe enrutarse por el bridge");
  }
  assert.ok(!SWE_LISTAS["swen-code-free"].modelos.some(([m]) => /^swecode-(asesoria|revision|solucion)/.test(m)), "los modos son MODO DE TRABAJO, no modelos");
  assert.ok(SWE_LISTAS["swe-code"].modelos.some(([m]) => m === "hf-liquid-lfm25"));
});

test("esSwe no se deja engañar por propiedades heredadas y un GAP del bridge es un error, no una respuesta", async () => {
  assert.ok(!esSwe("constructor") && !esSwe("__proto__") && !esSwe("toString"));
  await assert.rejects(() => enviarSwe(async () => ({ error: { code: "RESPALDO_AGOTADO", message: "nada responde" } }), { model: "web-qwen38max", historial: [], mensaje: "x", sesion: "s" }), /RESPALDO_AGOTADO/);
});

test("el historial que viaja al modelo SWE se acota (no se manda todo el chat a un modelo de 350M)", () => {
  const h = Array.from({ length: 50 }, (_, i) => ({ role: i % 2 ? "assistant" : "user", content: "m" + i }));
  const b = armar({ model: "lfm2.5-350m", historial: h, mensaje: "ultimo", sesion: "s" });
  assert.ok(b.messages.length <= 21); assert.equal(b.messages.at(-1).content, "ultimo");
});

test("R1 armar NO incluye claves (ni de localStorage); nunca van en el texto de error ni en la nota", async () => {
  const m = new Map([["riu_swe_claves", JSON.stringify({ groq: "MARCADOR-PRUEBA-1" })]]);
  globalThis.localStorage = { getItem: (k) => (m.has(k) ? m.get(k) : null), setItem: (k, v) => { m.set(k, String(v)); }, removeItem: (k) => { m.delete(k); } };
  const base = { model: "web-qwen38max", historial: [], mensaje: "x", sesion: "s" };
  assert.ok(!("claves" in armar(base)));
  const r1 = await enviarSwe(async (_r, op) => { assert.ok(!("claves" in op.body)); return { choices: [{ message: { content: "ok" } }] }; }, base);
  assert.ok(!JSON.stringify(r1).includes("MARCADOR-PRUEBA"));
  await assert.rejects(() => enviarSwe(async () => ({ error: { code: "X", message: "rechazo" } }), base), (e) => !/MARCADOR-PRUEBA/.test(e.message));
  delete globalThis.localStorage;
});

test("SWEN CODE free incluye los 5 modelos de Groq y NVIDIA autorizados y ya no trae los dos Llama", () => {
  const ids = SWE_LISTAS["swen-code-free"].modelos.map(([m]) => m);
  for (const m of ["groq/qwen/qwen3.8-27b", "nvidia/minimaxai/minimax-m3.1-flash", "nvidia/meta/muse-glimmer-30b", "nvidia/nvidia/nemotron-3-ultra-550b-a55b", "nvidia/z-ai/glm-5.3"]) assert.equal(ids.filter((x) => x === m).length, 1, m + " exactamente una vez");
  assert.ok(!ids.some((m) => /llama/i.test(m)), "sin Llama en el selector");
  const todo = JSON.stringify(SWE_LISTAS);
  assert.ok(!/llama/i.test(todo), "ninguna etiqueta/descripcion menciona Llama");
  const fila = SWE_LISTAS["swen-code-free"].modelos.find(([m]) => m === "nvidia/meta/muse-glimmer-30b");
  assert.deepEqual(fila.slice(1), ["Muse Glimmer 30B", "API NVIDIA"]);
});

import { rutaSwe } from "../swe-directo.js";

test("los modelos locales y groq/nvidia viajan por /web/v1 (el proxy del Space manda /web/* al bridge); web-* y swecode-* siguen por /v1", async () => {
  // el proxy del Space solo reenvia /v1/* al bridge si el modelo empieza por web-/swecode-: un id local por /v1 cae en el Router (400 MODEL_NOT_IN_CERTIFIED_REGISTRY)
  for (const m of ["hf-liquid-lfm25", "swe-codex-qwen25-15b", "swe-opencode-qwen35-08b", "swe-agent-lfm25", "swe-openhands-lfm25", "hf-qwen25-coder-15b", "lfm2.5-350m", "qwen2.5-coder-1.5b", "qwen3.5-0.8b", "qwen3-0.6b", "groq/qwen/qwen3.8-27b", "nvidia/minimaxai/minimax-m3.1-flash", "nvidia/meta/muse-glimmer-30b", "nvidia/nvidia/nemotron-3-ultra-550b-a55b", "nvidia/z-ai/glm-5.3"])
    assert.equal(rutaSwe(m), "/web/v1/chat/completions", m);
  for (const m of ["web-qwen38max", "web-dsv4-flash", "swecode-consulta", "swecode-asesoria"]) assert.equal(rutaSwe(m), "/v1/chat/completions", m);
  for (const [id, real] of [["hf-liquid-lfm25", "lfm2.5-350m"], ["swe-codex-qwen25-15b", "qwen2.5-coder-1.5b"], ["swe-opencode-qwen35-08b", "qwen3.5-0.8b"], ["swe-agent-lfm25", "lfm2.5-350m"], ["swe-openhands-lfm25", "lfm2.5-350m"], ["hf-qwen25-coder-15b", "qwen2.5-coder-1.5b"]]) {
    let visto;
    const r = await enviarSwe(async (ruta, op) => { visto = { ruta, op }; return { modelo_usado: real, choices: [{ message: { content: "hola" }, finish_reason: "stop" }] }; }, { model: id, historial: [], mensaje: "x", sesion: "s" });
    assert.equal(visto.ruta, "/web/v1/chat/completions", id); assert.equal(visto.op.body.model, real, id); assert.equal(r.reply, "hola");
  }
});

import { EJECUTORES_TOOLS, leerEjecutorTools, leerSeleccion, guardarSeleccion } from "../swe-directo.js";

const conStorage = (inicial = {}) => {
  const m = new Map(Object.entries(inicial));
  globalThis.localStorage = { getItem: (k) => (m.has(k) ? m.get(k) : null), setItem: (k, v) => { m.set(k, String(v)); }, removeItem: (k) => { m.delete(k); } };
  return m;
};

test("ejecutor_tools: dos valores de contrato (swe|openclaw), defecto 'swe', DERIVADO de agente_tool (sin key propia)", () => {
  assert.deepEqual(EJECUTORES_TOOLS, ["swe", "openclaw"]);
  delete globalThis.localStorage;
  assert.equal(leerEjecutorTools(), "swe", "sin localStorage -> swe");
  const m = conStorage();
  assert.equal(leerEjecutorTools(), "swe");
  guardarSeleccion({ agente_tool: "openclaw" }); assert.equal(leerSeleccion().agente_tool, "openclaw");
  assert.equal(leerEjecutorTools(), "openclaw"); assert.equal(m.has("riu_swe_ejecutor_tools"), false, "no hay key propia de salida");
  guardarSeleccion({ agente_tool: "otro" }); assert.equal(leerEjecutorTools(), "openclaw", "agente invalido no pisa el anterior");
  guardarSeleccion({ agente_tool: "codex" }); assert.equal(leerEjecutorTools(), "swe");
  m.set("riu_swe_ejecutor_tools", "openclaw"); assert.equal(leerEjecutorTools(), "swe", "la key vieja se ignora");
  m.set("riu_swe_seleccion", "{corrupto"); assert.equal(leerEjecutorTools(), "swe");
  delete globalThis.localStorage;
});

test("armar envia ejecutor_tools en cada peticion (derivado del agente que ejecuta; o el explicito)", () => {
  const base = { model: "web-qwen38max", historial: [], mensaje: "x", sesion: "s" };
  delete globalThis.localStorage;
  assert.equal(armar(base).ejecutor_tools, "swe");
  conStorage({ riu_swe_seleccion: JSON.stringify({ agente_tool: "openclaw" }) });
  assert.equal(armar(base).ejecutor_tools, "openclaw");
  assert.equal(armar({ ...base, ejecutor_tools: "swe" }).ejecutor_tools, "swe");
  assert.equal(armar({ ...base, ejecutor_tools: "x" }).ejecutor_tools, "swe");
  delete globalThis.localStorage;
});

test("enviarSwe con tool_calls (passthrough a OpenClaw) no es un GAP: devuelve los nombres de las tools y la nota", async () => {
  delete globalThis.localStorage;
  const tc = [{ id: "c1", type: "function", function: { name: "github_leer", arguments: "{}" } }];
  const api = async (_r, op) => { assert.equal(op.body.ejecutor_tools, "openclaw"); return { modelo_usado: "groq/x", choices: [{ message: { content: "", tool_calls: tc }, finish_reason: "tool_calls" }] }; };
  const r = await enviarSwe(api, { model: "groq/qwen/qwen3.8-27b", historial: [], mensaje: "x", sesion: "s", ejecutor_tools: "openclaw" });
  assert.deepEqual(r.tools, []); assert.deepEqual(r.pedidas, ["github_leer"]); assert.equal(r.finish_reason, "tool_calls"); assert.match(r.nota, /OpenClaw/);  // pedidas, no usadas
  assert.match(r.reply, /github_leer/);
});

test("X-Ray modelos locales: el id hf/ del selector se traduce a modelo real del bridge y NO al router MVP", async () => {
  for (const m of ["lfm2.5-350m", "qwen2.5-coder-1.5b", "qwen3.5-0.8b", "qwen3-0.6b"]) {
    assert.ok(esSwe("hf/" + m));
    let visto;
    const out = await enviarSwe(async (ruta, opts) => {
      visto = { ruta, body: opts.body };
      return { modelo_usado: m, choices: [{ message: { content: "OK" }, finish_reason: "stop" }] };
    }, { model: "hf/" + m, mensaje: "hola", sesion: "prueba", historial: [] });
    assert.equal(visto.ruta, "/web/v1/chat/completions");
    assert.equal(visto.body.model, m);
    assert.equal(out.reply, "OK");
  }
  assert.equal(esSwe("hf/modelo-inventado"), false);
});

test("X-Ray selector: la ausencia del Harness NO bloquea modelos de chat directo del bridge", async () => {
  const { opcionesModeloVentana } = await import("../swe-directo.js");
  const cap = { harness: "sin_respuesta", agentes: {}, modelos: {}, workflows: {} };
  for (const [ventana, modelo] of [["swe-code", "hf/qwen3-0.6b"], ["groq", "groq/qwen/qwen3.8-27b"], ["nvidia", "nvidia/z-ai/glm-5.3"]]) {
    const op = opcionesModeloVentana(ventana, cap, {}).find(x => x.id === modelo);
    assert.ok(op, modelo);
    assert.equal(op.estado, "SIN_VERIFICAR");
    assert.ok(op.elegible, "seleccionable sin declarar falsamente DISPONIBLE");
  }
});
