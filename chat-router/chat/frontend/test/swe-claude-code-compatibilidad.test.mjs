import test from "node:test";
import assert from "node:assert/strict";
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import * as SWE from "../swe-directo.js";

// Contrato de los seis agentes y la visibilidad de Claude Code.
// La sonda real del Harness es la autoridad; la UI NUNCA inventa instalaciones.
const raiz = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const selector = fs.readFileSync(path.join(raiz, "swe-selectores.js"), "utf8");
const ficheros = (p) => fs.readFileSync(path.resolve(raiz, p), "utf8");

const CAP = SWE.normalizarCapacidades({
  harness: "ok",
  agentes: {
    "claude-code": { disponible: true, estado: "DISPONIBLE", modelos: ["nvidia/minimaxai/minimax-m3.1-flash"] },
    "swe-agent": { disponible: false, estado: "NO INSTALADO", motivo: "CLI sweagent ausente" },
    codex: { disponible: true, estado: "DISPONIBLE" },
  },
  workflows: { individual: { disponible: true } },
  modelos: {
    "hf/qwen2.5-coder-1.5b": { disponible: true, estado: "DISPONIBLE" },
    "nvidia/minimaxai/minimax-m3.1-flash": { disponible: true, estado: "DISPONIBLE" },
  }
});
const HFM = "hf/qwen2.5-coder-1.5b", NVM = "nvidia/minimaxai/minimax-m3.1-flash";

test("Claude Code esta disponible aun si el usuario tenia otro modelo TOOL", () => {
  assert.equal(SWE.estadoOpcion(CAP, "agente", "claude-code").estado, "DISPONIBLE");
  assert.equal(SWE.estadoOpcion(CAP, "agente", "claude-code", HFM).estado, "NO_COMPATIBLE");
  const lista = SWE.agruparOpciones(CAP, "agente", SWE.AGENTES_SWE);
  assert.ok(lista.ok.some(x => x.id === "claude-code"));
  assert.ok(lista.noInstalado.some(x => x.id === "swe-agent"));
});

test("al seleccionar Claude Code cambia solo modelo TOOL; responde sigue HF", () => {
  assert.equal(SWE.modeloToolCompatible(CAP, "claude-code", HFM), NVM);
  assert.equal(SWE.modeloToolCompatible(CAP, "codex", HFM), HFM);
  const seleccion = { ...SWE.SEL_DEFECTO, modo_agentico: true,
    agente_tool: "claude-code", modelo_responde: HFM,
    modelo_tool: SWE.modeloToolCompatible(CAP, "claude-code", HFM) };
  assert.equal(seleccion.modelo_responde, HFM);
  assert.deepEqual(SWE.validarSeleccion(seleccion, CAP), { ok: true, problemas: [] });
  const tarea = SWE.armarTarea({ sel: seleccion, mensaje: "prueba", sesion: "test" });
  assert.equal(tarea.agente_tool, "claude-code");
  assert.equal(tarea.modelo_tool, NVM);
  assert.equal(tarea.modelo_responde, HFM);
});

test("modelo no anunciado o agente no instalado nunca se convierte en disponible", () => {
  assert.equal(SWE.modeloToolCompatible(CAP, "swe-agent", HFM), HFM);
  const plan = { ...SWE.SEL_DEFECTO, agente_tool: "swe-agent",
    modo_agentico: true, modelo_tool: HFM };
  assert.ok(SWE.validarSeleccion(plan, CAP).problemas.some(p => /NO INSTALADO/.test(p)));
});

test("interfaz conserva seis agentes, no filtra Claude por compatibilidad anticipada", () => {
  assert.ok(selector.includes("modeloToolCompatible(CAP, actual.agente_tool, actual.modelo_tool)"));
  assert.ok(selector.includes('const modelo = k === "agente_responde" ? sel.modelo_responde : undefined'));
  assert.ok(selector.includes('estadoOpcion(CAP, tipo, valor, k === "agente_responde" ? sel.modelo_responde : undefined)'));
  assert.ok(selector.includes('const spB = e.target.closest && e.target.closest("[data-swe-systemprompt], #btn-system-prompt-on")'));
  assert.deepEqual(SWE.AGENTES_SWE.map(a => a[0]), ["openclaw", "swe-agent", "openhands", "opencode", "codex", "claude-code"]);
  assert.ok(ficheros("panel-chat.html").includes("btn-system-prompt-on"));
});
