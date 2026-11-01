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

const NO = (a) => ({ disponible: false, motivo: a + " no esta instalado (CLI ausente del PATH)" });
test("agruparOpciones: disponibles arriba y los no instalados agrupados al final, en el orden del catalogo", () => {
  const g = S.agruparOpciones(cap({ "swe-agent": { disponible: true }, codex: { disponible: true }, openclaw: NO("openclaw"), openhands: NO("openhands"), opencode: NO("opencode"), "claude-code": NO("claude-code") }), "agente", S.AGENTES_SWE);
  assert.deepEqual(g.ok.map((x) => x.id), ["swe-agent", "codex"]);
  assert.deepEqual(g.noInstalado.map((x) => x.id), ["openclaw", "openhands", "opencode", "claude-code"]);
  assert.deepEqual(g.incompatible, []); assert.deepEqual(g.sinVerificar, []);
});

test("agruparOpciones: si el Harness no reporta nada es SIN VERIFICAR (no «no instalado»), salvo Individual; incompatible con el modelo va aparte", () => {
  const vacio = S.agruparOpciones(S.normalizarCapacidades(null), "agente", S.AGENTES_SWE);
  assert.equal(vacio.ok.length, 0); assert.equal(vacio.noInstalado.length, 0); assert.equal(vacio.sinVerificar.length, 6);
  const wf = S.agruparOpciones(S.normalizarCapacidades(null), "workflow", S.WORKFLOWS_SWE);
  assert.deepEqual(wf.ok.map((x) => x.id), ["individual"]); assert.deepEqual(wf.sinVerificar.map((x) => x.id), ["swe_code", "liquid_mirror"]);
  const inc = S.agruparOpciones(cap({ codex: { disponible: true, modelos: ["hf/qwen3-0.6b"] } }), "agente", [["codex", "Codex"]], "hf/lfm2.5-350m");
  assert.deepEqual(inc.incompatible.map((x) => x.id), ["codex"]); assert.equal(inc.noInstalado.length, 0);
});

test("lineaNoInstalados: una sola linea «No instalados: X, Y, Z» (vacia si no falta ninguno)", () => {
  const g = S.agruparOpciones(cap({ "swe-agent": { disponible: true }, openclaw: NO("openclaw"), openhands: NO("openhands"), opencode: NO("opencode"), codex: NO("codex"), "claude-code": NO("claude-code") }), "agente", S.AGENTES_SWE);
  assert.equal(S.lineaNoInstalados(g), "No instalados: OpenClaw, OpenHands, OpenCode, Codex, Claude Code");
  const todos = S.agruparOpciones(cap(Object.fromEntries(S.AGENTES_SWE.map((a) => [a[0], { disponible: true }]))), "agente", S.AGENTES_SWE);
  assert.equal(S.lineaNoInstalados(todos), "");
});

test("el contrato no cambia: la seleccion y el ejecutor siguen persistiendo como antes", () => {
  conStorage();
  S.guardarSeleccion({ agente_tool: "codex", workflow: "swe_code", modo_agentico: true });
  assert.deepEqual(S.leerSeleccion(), { ...S.SEL_DEFECTO, agente_tool: "codex", workflow: "swe_code", modo_agentico: true });
  S.guardarEjecutorTools("openclaw");
  assert.equal(S.leerSeleccion().agente_tool, "codex", "la salida NO cambia agente_tool"); assert.equal(S.leerEjecutorTools(), "openclaw");
});

// ---- F1: lo que muestra el desplegable «Responde» es lo que se envia, aunque la lista de la hoja no tenga ese modelo ----
test("F1 modeloParaLista: modelo del catalogo que la lista no trae -> id del bridge (hf/x -> x; groq/ y nvidia/ tal cual) con su etiqueta", () => {
  assert.deepEqual(S.modeloParaLista("swe-code", "groq/qwen/qwen3.8-27b", "hf-liquid-lfm25"), { model_id: "groq/qwen/qwen3.8-27b", label: "Qwen 3.8 Groq" });
  assert.deepEqual(S.modeloParaLista("swe-code", "nvidia/z-ai/glm-5.3", "hf-liquid-lfm25"), { model_id: "nvidia/z-ai/glm-5.3", label: "GLM 5.3" });
  assert.deepEqual(S.modeloParaLista("swen-code-free", "hf/qwen3-0.6b", "swecode-consulta"), { model_id: "hf-qwen3-06b", label: "Qwen3 0.6B" });
  assert.deepEqual(S.modeloParaLista("swen-code-free", "hf/lfm2.5-350m", "swecode-consulta"), { model_id: "hf-liquid-lfm25", label: "Liquid LFM2.5 350M" });
  assert.deepEqual(S.modeloParaLista("swe-code", "nvidia/z-ai/glm-5.3", "hf-liquid-lfm25"), { model_id: "nvidia/z-ai/glm-5.3", label: "GLM 5.3" });
});

test("F1 modeloParaLista: si la lista lo trae usa su entrada (y conserva la actual si ya equivale); un id fuera del catalogo da null", () => {
  assert.deepEqual(S.modeloParaLista("swe-code", "hf/qwen2.5-coder-1.5b", "hf-liquid-lfm25"), { model_id: "hf-qwen25-coder-15b", label: "Qwen2.5 Coder 1.5B" });
  assert.deepEqual(S.modeloParaLista("swe-code", "hf/qwen2.5-coder-1.5b", "hf-qwen25-coder-15b"), { model_id: "hf-qwen25-coder-15b", label: "Qwen2.5 Coder 1.5B" });
  assert.equal(S.modeloParaLista("swe-code", "hf/llama", "hf-liquid-lfm25"), null);
  assert.equal(S.modeloParaLista("inventada", "hf/qwen3-0.6b", ""), null);
});

test("F1 lo enviado es lo mostrado: el id elegido llega a armar() y a rutaSwe() (SWE CODE+Groq y SWEN+hf/qwen3-0.6b)", () => {
  const g = S.modeloParaLista("swe-code", "groq/qwen/qwen3.8-27b", "hf-liquid-lfm25");
  assert.equal(S.armar({ model: g.model_id, mensaje: "x", sesion: "s", ejecutor_tools: "swe" }).model, "groq/qwen/qwen3.8-27b");
  assert.equal(S.rutaSwe(g.model_id), "/web/v1/chat/completions"); assert.ok(S.esSwe(g.model_id));
  const q = S.modeloParaLista("swen-code-free", "hf/qwen3-0.6b", "swecode-consulta");
  assert.equal(S.armar({ model: q.model_id, mensaje: "x", sesion: "s", ejecutor_tools: "swe" }).model, "qwen3-0.6b"); assert.ok(S.esSwe(q.model_id));
});

test("F1 modeloGuardado: lo guardado fuera de la lista (id del bridge) se restaura tal cual; lo desconocido vuelve a la primera entrada", () => {
  assert.deepEqual(S.modeloGuardado("swe-code", "groq/qwen/qwen3.8-27b"), { model_id: "groq/qwen/qwen3.8-27b", label: "Qwen 3.8 Groq" });
  assert.deepEqual(S.modeloGuardado("swen-code-free", "qwen3-0.6b"), { model_id: "hf-qwen3-06b", label: "Qwen3 0.6B" });
  assert.deepEqual(S.modeloGuardado("swe-code", "swe-agent-lfm25"), { model_id: "hf-liquid-lfm25", label: "Liquid LFM2.5 350M" }, "un id viejo «SWE · Agent ejecuta» se traduce a su MODELO");
  assert.deepEqual(S.modeloGuardado("swe-code", "no-existe"), { model_id: "hf-liquid-lfm25", label: "Liquid LFM2.5 350M" });
  assert.deepEqual(S.modeloGuardado("swe-code", undefined), { model_id: "hf-liquid-lfm25", label: "Liquid LFM2.5 350M" });
});

// ---- F8: hoja NVIDIA «NVIDIA · modelos» y config.js solo con el respaldo ----
test("F8 la hoja NVIDIA se titula «NVIDIA · modelos» y config.js ya no trae Nemotron 3 Super; la ficha de respaldo se rotula", async () => {
  const fs = await import("node:fs"), url = await import("node:url"), path = await import("node:path");
  const dir = path.dirname(url.fileURLToPath(import.meta.url)), leer = (f) => fs.readFileSync(path.join(dir, "..", f), "utf8");
  assert.match(leer("panel-chat.html"), /<div id="sh-ficha"[^>]*>.*?<strong>NVIDIA · modelos<\/strong>/);
  assert.ok(!/Glimmer \/ Nemotron 3 Super/.test(leer("panel-chat.html")));
  const cfg = leer("config.js"); assert.ok(!/nv-nemotron-super/.test(cfg)); assert.match(cfg, /nv-muse-glimmer'[^}]*\(respaldo\)/);
});
