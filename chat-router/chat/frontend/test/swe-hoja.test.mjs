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

test("el contrato no cambia: la seleccion persiste como antes y el ejecutor de tools se deriva de agente_tool", () => {
  conStorage();
  S.guardarSeleccion({ agente_tool: "codex", workflow: "swe_code", modo_agentico: true });
  assert.deepEqual(S.leerSeleccion(), { ...S.SEL_DEFECTO, agente_tool: "codex", workflow: "swe_code", modo_agentico: true });
  assert.equal(S.leerEjecutorTools(), "swe");
  S.guardarSeleccion({ agente_tool: "openclaw" });
  assert.equal(S.leerSeleccion().workflow, "swe_code", "cambiar el agente no toca el workflow"); assert.equal(S.leerEjecutorTools(), "openclaw");
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

// ---- F3: los 6 agentes SIEMPRE aparecen en AMBOS selectores; si el Harness los reporta disponibles son elegibles y activos; si no, el rotulo dice por que ----
const SEIS = ["openclaw", "swe-agent", "openhands", "opencode", "codex", "claude-code"];
const reporta = (f) => S.normalizarCapacidades({ harness: "ok", agentes: Object.fromEntries(SEIS.map((a) => [a, f(a)])), workflows: { individual: { disponible: true } }, modelos: {} });
const DISP = { disponible: true, estado: "DISPONIBLE", veredicto: "DISPONIBLE", verificado: true, intentable: true };  // forma real de agentes/adaptadores/disponibilidad.py

test("F3 el Harness reporta los 6 agentes DISPONIBLES: los 6 salen activos (sin rotulo de estado) y se pueden elegir como RESPONDE y como EJECUTA", () => {
  conStorage();
  const cap6 = reporta(() => DISP);
  const g = S.agruparOpciones(cap6, "agente", S.AGENTES_SWE, "hf/qwen2.5-coder-1.5b");
  assert.deepEqual(g.ok.map((x) => x.id), SEIS); assert.equal(g.noInstalado.length + g.sinVerificar.length + g.incompatible.length + g.otros.length, 0);
  for (const a of SEIS) {
    const st = S.estadoOpcion(cap6, "agente", a, "hf/qwen2.5-coder-1.5b");
    assert.deepEqual([st.ok, st.estado, st.elegible], [true, "DISPONIBLE", true], a);
    S.guardarSeleccion({ agente_responde: a, agente_tool: a, modo_agentico: true });  // ambos selectores aceptan cada agente
    assert.equal(S.leerSeleccion().agente_responde, a); assert.equal(S.leerSeleccion().agente_tool, a);
    assert.equal(S.validarSeleccion(S.leerSeleccion(), cap6).ok, true, "modo agentico ON con " + a + " disponible no se bloquea");
  }
  assert.equal(S.lineaNoInstalados(g), ""); assert.equal(S.lineaOtros(g), "");
});

test("F3 capacidades REALES del runtime local (3 disponibles, 3 sin configurar): los 6 salen listados; los disponibles activos, los otros deshabilitados con su causa real", () => {
  const cfg = (motivo, causa) => ({ disponible: false, motivo, estado: "NO CONFIGURADO", veredicto: "NO DISPONIBLE", verificado: true, intentable: false, ...(causa ? { causa } : {}) });
  const real = S.normalizarCapacidades({ harness: "ok", workflows: { individual: DISP }, modelos: {}, agentes: {
    openclaw: cfg("openclaw sin configurar: falta OPENCLAW_GATEWAY_TOKEN en el entorno del Harness", "falta_token_gateway"), "swe-agent": DISP, openhands: DISP, opencode: DISP,
    codex: cfg("codex instalado pero falta RIU_CODEX_BASE_URL: Codex solo habla la API Responses y necesita un endpoint /responses"), "claude-code": cfg("claude-code instalado pero sin configurar: faltan RIU_CLAUDE_PASARELA_URL y/o RIU_CLAUDE_PASARELA_MODELO", "falta_pasarela") } });
  const g = S.agruparOpciones(real, "agente", S.AGENTES_SWE);
  assert.deepEqual(g.ok.map((x) => x.id), ["swe-agent", "openhands", "opencode"]);
  assert.deepEqual(g.otros.map((x) => x.id), ["openclaw", "codex", "claude-code"]);
  assert.equal(g.ok.length + g.otros.length, 6, "ninguno desaparece de la lista");
  assert.ok(g.ok.every((x) => x.elegible)); assert.ok(g.otros.every((x) => !x.elegible && x.estado === "NO_CONFIGURADO" && /falta|sin configurar/i.test(x.motivo)), JSON.stringify(g.otros));
  assert.match(S.lineaOtros(g), /^No configurados \/ no disponibles: OpenClaw \(no configurado\), Codex \(no configurado\), Claude Code \(no configurado\)$/);
});

test("F3 NO INSTALADO: la lista de los 6 sigue completa y el rotulo explica la causa en claro (nunca el codigo crudo binario_ausente)", () => {
  const sin = reporta(() => ({ disponible: false, estado: "NO INSTALADO", veredicto: "NO DISPONIBLE", verificado: true, intentable: false, causa: "binario_ausente" }));  // el Harness solo dio el codigo
  const g = S.agruparOpciones(sin, "agente", S.AGENTES_SWE);
  assert.deepEqual(g.noInstalado.map((x) => x.id), SEIS); assert.equal(g.ok.length, 0);
  assert.equal(S.lineaNoInstalados(g), "No instalados: OpenClaw, SWE-agent, OpenHands, OpenCode, Codex, Claude Code");
  for (const x of g.noInstalado) { assert.doesNotMatch(x.motivo, /binario_ausente/); assert.match(x.motivo, /no está instalado|no esta instalado/i); assert.equal(x.elegible, false); }
  const conMotivo = reporta(() => ({ disponible: false, estado: "NO INSTALADO", causa: "binario_ausente", motivo: "swe-agent no esta instalado (CLI `sweagent` ausente del PATH; define RIU_SWEAGENT_BIN)" }));
  assert.match(S.estadoOpcion(conMotivo, "agente", "swe-agent").motivo, /sweagent.*PATH/, "si el Harness manda el motivo concreto, manda el motivo");
});

test("Android: los modelos utilizan opciones planas, no optgroup nativo que cubre toda la pantalla", async () => {
  const { readFileSync } = await import("node:fs");
  const source = readFileSync(new URL("../swe-selectores.js", import.meta.url), "utf8");
  assert.doesNotMatch(source, /el\("optgroup"\)/);
  assert.match(source, /lista\.map\(x => op\(\{ \.\.\.x, etq:/);
});

test("selector chat YAIWES: solo un agente ejecutor real, no doble agente que responde sin motor", async () => {
  const { readFileSync } = await import("node:fs");
  const { fileURLToPath } = await import("node:url");
  const p = new URL("../swe-selectores.js", import.meta.url);
  const fuente = readFileSync(p, "utf8");
  const css = readFileSync(new URL("../shell.css", import.meta.url), "utf8");
  assert.match(fuente, /\["Responde", \[\["Modelo", "modelo_responde"\]\]\]/);
  assert.match(fuente, /\["Ejecuta", \[\["Agente", "agente_tool"\]/);
  assert.doesNotMatch(fuente, /\["Responde", "agente_responde"/);
  assert.match(css, /swe-rej-fila\[data-swe-fila="responde"\]/);
  assert.match(css, /max-height:min\(76dvh/);
  assert.equal(S.AGENTES_SWE.length, 6, "seis adaptadores, un solo selector agente");
  assert.equal(S.armarTarea({sel:S.SEL_DEFECTO,mensaje:"x",sesion:"s"}).agente_tool, "swe-agent");
});
