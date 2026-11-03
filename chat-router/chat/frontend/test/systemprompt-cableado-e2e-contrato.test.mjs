// Regresion sin credenciales ni red: contrato real del boton System Prompt
// y trazabilidad estandar de los 6 agentes + todos los selectores.
// Ejecutar: node --test chat-router/chat/frontend/test/systemprompt-cableado-e2e-contrato.test.mjs
import test from "node:test";
import assert from "node:assert/strict";
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const raiz = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..", "..", "..", "..");
const leer = p => fs.readFileSync(path.join(raiz, p), "utf8");
const front = "chat-router/chat/frontend/";
const backend = "chat-router/chat/backend/";

function crearBoton(api) {
  const fuente = leer(front + "swe-systemprompt.js")
    .replace(/^import \{ api \} from "\.\/api\.js";\s*$/m, "")
    .replace(/\bexport (?=const |async function |function )/g, "");
  return new Function("api", fuente + "\nreturn { cargarSystemPromptOn, alternarSystemPromptOn, systemPromptOnCache };")(api);
}

test("System Prompt: ON/OFF se confirma en el Router via bridge, sin inventar estado", async () => {
  let on = false;
  const llamadas = [];
  const boton = crearBoton(async (ruta, req) => {
    llamadas.push({ ruta, metodo: req.method });
    if (req.method === "POST") on = req.body.on;
    return { ok: true, on };
  });
  assert.equal(await boton.cargarSystemPromptOn(), false);
  assert.equal(await boton.alternarSystemPromptOn(), true);
  assert.equal(await boton.alternarSystemPromptOn(), false);
  assert.deepEqual(llamadas.map(x => x.ruta), Array(3).fill("/web/v1/system-prompt-on"));
  assert.deepEqual(llamadas.map(x => x.metodo), ["GET", "POST", "POST"]);
});

test("System Prompt: HTTP 503 no se trata como ON ni permite activar sin recibo", async () => {
  let peticiones = 0;
  const boton = crearBoton(async () => { peticiones++; throw new Error("HTTP 503"); });
  assert.equal(await boton.cargarSystemPromptOn(), null);
  await assert.rejects(boton.alternarSystemPromptOn(), /HTTP 503/);
  assert.equal(boton.systemPromptOnCache(), null);
  assert.equal(peticiones, 2);
});

test("System Prompt: respuesta contradictoria a POST no cambia el indicador", async () => {
  const boton = crearBoton(async (_, req) => ({ ok: true, on: false }));
  assert.equal(await boton.cargarSystemPromptOn(), false);
  await assert.rejects(boton.alternarSystemPromptOn(), /CAMBIO_NO_CONFIRMADO/);
  assert.equal(boton.systemPromptOnCache(), false);
});

test("Los 6 agentes existen en catalogo, dispatcher y selector central; el boton llega al chat", () => {
  const catalogo = leer("chat-router/agentes/adaptadores/modelos.py");
  const dispatcher = leer("chat-router/agentes/adaptadores/dispatcher.py");
  const selector = leer(front + "swe-directo.js");
  const html = leer(front + "panel-chat.html");
  const central = leer(front + "swe-selectores.js");
  const agentes = ["openclaw", "swe-agent", "openhands", "opencode", "codex", "claude-code"];
  for (const agente of agentes) {
    assert.ok(catalogo.includes('"' + agente + '"'), agente + " en catalogo");
    assert.ok(dispatcher.includes('"' + agente + '":'), agente + " en dispatcher");
    assert.ok(selector.includes('["' + agente + '",'), agente + " en selectores");
  }
  assert.ok(html.includes('id="btn-system-prompt-on"'));
  assert.ok(central.includes("#btn-system-prompt-on"));
  assert.ok(central.includes("SIN VERIFICAR"));
});

test("Harness aplica el prompt a agentes, LLM y Liquid; bridge consulta Router", () => {
  const harness = leer(backend + "deepseek_harness/server.py");
  const bridge = leer("chat-router/SWE CODE/web-bridge/src/server.js");
  const mvp = leer(backend + "mvp/app.py");
  const control = leer(backend + "mvp/control.py");
  for (const contract of ["ejecutar_agente=_ejecutar_agente_con_prompt",
                          "llm=_llm_swe_con_prompt",
                          "servidor_llm=_servidor_llm_swe_con_prompt"])
    assert.ok(harness.includes(contract), contract);
  assert.ok(harness.includes('ACCIONES_CONTROL = ("tools_lock", "agent_access_lock")'));
  assert.ok(mvp.includes('app.mount("/plugins/deepseek_harness", harness_app)'));
  assert.ok(control.includes('self.d["prompt_on"] = on'));
  assert.ok(bridge.includes("await sincronizarPromptParaInferencia()"));
  assert.ok(bridge.includes("await consultarPromptRouter()"));
});

test("Todos los selectores conservados, sin cambiar modelo que responde", () => {
  const selectors = leer(front + "chat-selectores.js");
  for (const id of ["nvidia-groq-team", "groq", "swe-code", "swen-code-free", "team-qwen", "team-5-mvp"])
    assert.ok(selectors.includes('id: "' + id + '"'), id);
  const rutas = leer(front + "swe-directo.js");
  assert.ok(rutas.includes('"/plugins/deepseek_harness/modelos/v1/chat/completions"'));
  assert.ok(rutas.includes("modelo_responde:"));
  assert.ok(rutas.includes("agente_tool:"));
});
