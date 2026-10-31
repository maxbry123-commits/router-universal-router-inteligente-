import test from "node:test";
import assert from "node:assert/strict";
import * as S from "../swe-directo.js";

// Hoja SWE CODE / SWEN CODE free compacta: agentes no instalados agrupados al final y secciones plegables persistidas. Sin red.
const conStorage = (inicial = {}) => {
  const m = new Map(Object.entries(inicial));
  globalThis.localStorage = { getItem: (k) => (m.has(k) ? m.get(k) : null), setItem: (k, v) => { m.set(k, String(v)); }, removeItem: (k) => { m.delete(k); } };
  return m;
};
const cap = (agentes) => S.normalizarCapacidades({ harness: "ok", agentes, workflows: { swe_code: { disponible: true } }, modelos: {} });

test("agruparOpciones: disponibles arriba y los no instalados agrupados al final, en el orden del catalogo", () => {
  const g = S.agruparOpciones(cap({ "swe-agent": { disponible: true }, codex: { disponible: true } }), "agente", S.AGENTES_SWE);
  assert.deepEqual(g.ok.map((x) => x.id), ["swe-agent", "codex"]);
  assert.deepEqual(g.noInstalado.map((x) => x.id), ["openclaw", "openhands", "opencode", "claude-code"]);
  assert.deepEqual(g.incompatible, []);
});

test("agruparOpciones: sin que el Harness reporte nada todo es no instalado salvo Individual; incompatible con el modelo va aparte", () => {
  const vacio = S.agruparOpciones(S.normalizarCapacidades(null), "agente", S.AGENTES_SWE);
  assert.equal(vacio.ok.length, 0); assert.equal(vacio.noInstalado.length, 6);
  const wf = S.agruparOpciones(S.normalizarCapacidades(null), "workflow", S.WORKFLOWS_SWE);
  assert.deepEqual(wf.ok.map((x) => x.id), ["individual"]); assert.deepEqual(wf.noInstalado.map((x) => x.id), ["swe_code", "liquid_mirror"]);
  const inc = S.agruparOpciones(cap({ codex: { disponible: true, modelos: ["hf/qwen3-0.6b"] } }), "agente", [["codex", "Codex"]], "hf/lfm2.5-350m");
  assert.deepEqual(inc.incompatible.map((x) => x.id), ["codex"]); assert.equal(inc.noInstalado.length, 0);
});

test("lineaNoInstalados: una sola linea «No instalados: X, Y, Z» (vacia si no falta ninguno)", () => {
  const g = S.agruparOpciones(cap({ "swe-agent": { disponible: true } }), "agente", S.AGENTES_SWE);
  assert.equal(S.lineaNoInstalados(g), "No instalados: OpenClaw, OpenHands, OpenCode, Codex, Claude Code");
  const todos = S.agruparOpciones(cap(Object.fromEntries(S.AGENTES_SWE.map((a) => [a[0], { disponible: true }]))), "agente", S.AGENTES_SWE);
  assert.equal(S.lineaNoInstalados(todos), "");
});

test("secciones plegables: defecto Modelo abierta, el resto cerrado; se persiste y un valor roto no la rompe", () => {
  conStorage();
  assert.deepEqual(S.leerSecciones(), { modelo: true, agentes: false, workflow: false });
  S.guardarSeccion("agentes", true); S.guardarSeccion("modelo", false);
  assert.deepEqual(S.leerSecciones(), { modelo: false, agentes: true, workflow: false });
  S.guardarSeccion("inventada", true);  // una seccion desconocida no entra
  assert.deepEqual(Object.keys(S.leerSecciones()).sort(), ["agentes", "modelo", "workflow"]);
  conStorage({ riu_swe_secciones: "{roto" });
  assert.deepEqual(S.leerSecciones(), { modelo: true, agentes: false, workflow: false });
  conStorage({ riu_swe_secciones: JSON.stringify({ modelo: "si", workflow: true }) });
  assert.deepEqual(S.leerSecciones(), { modelo: true, agentes: false, workflow: true });
});

test("el contrato no cambia: la seleccion y el ejecutor siguen persistiendo como antes", () => {
  conStorage();
  S.guardarSeleccion({ agente_tool: "codex", workflow: "swe_code", modo_agentico: true });
  assert.deepEqual(S.leerSeleccion(), { ...S.SEL_DEFECTO, agente_tool: "codex", workflow: "swe_code", modo_agentico: true });
  S.guardarEjecutorTools("openclaw");
  assert.equal(S.leerSeleccion().agente_tool, "openclaw"); assert.equal(S.leerEjecutorTools(), "openclaw");
});
