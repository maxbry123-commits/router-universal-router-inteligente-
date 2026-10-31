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

// ---- F1: lo que muestra el desplegable «Responde» es lo que se envia, aunque la lista de la hoja no tenga ese modelo ----
test("F1 modeloParaLista: modelo del catalogo que la lista no trae -> id del bridge (hf/x -> x; groq/ y nvidia/ tal cual) con su etiqueta", () => {
  assert.deepEqual(S.modeloParaLista("swe-code", "groq/qwen/qwen3.8-27b", "hf-liquid-lfm25"), { model_id: "groq/qwen/qwen3.8-27b", label: "Qwen 3.8 Groq" });
  assert.deepEqual(S.modeloParaLista("swe-code", "nvidia/z-ai/glm-5.3", "hf-liquid-lfm25"), { model_id: "nvidia/z-ai/glm-5.3", label: "GLM 5.3" });
  assert.deepEqual(S.modeloParaLista("swen-code-free", "hf/qwen3-0.6b", "swecode-consulta"), { model_id: "qwen3-0.6b", label: "Qwen3 0.6B" });
  assert.deepEqual(S.modeloParaLista("swen-code-free", "hf/lfm2.5-350m", "swecode-consulta"), { model_id: "lfm2.5-350m", label: "Liquid LFM2.5 350M" });
});

test("F1 modeloParaLista: si la lista lo trae usa su entrada (y conserva la actual si ya equivale); un id fuera del catalogo da null", () => {
  assert.deepEqual(S.modeloParaLista("swe-code", "hf/qwen2.5-coder-1.5b", "hf-liquid-lfm25"), { model_id: "swe-codex-qwen25-15b", label: "SWE · Codex escribe" });
  assert.deepEqual(S.modeloParaLista("swe-code", "hf/qwen2.5-coder-1.5b", "hf-qwen25-coder-15b"), { model_id: "hf-qwen25-coder-15b", label: "Qwen Code (HF)" });
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
  assert.deepEqual(S.modeloGuardado("swen-code-free", "qwen3-0.6b"), { model_id: "qwen3-0.6b", label: "Qwen3 0.6B" });
  assert.deepEqual(S.modeloGuardado("swe-code", "swe-agent-lfm25"), { model_id: "swe-agent-lfm25", label: "SWE · Agent ejecuta" });
  assert.deepEqual(S.modeloGuardado("swe-code", "no-existe"), { model_id: "hf-liquid-lfm25", label: "Liquid AI (HF)" });
  assert.deepEqual(S.modeloGuardado("swe-code", undefined), { model_id: "hf-liquid-lfm25", label: "Liquid AI (HF)" });
});

// ---- F4: las entradas «SWE · X» son etiquetas de modelo + agente ----
test("F4 seleccionDeEntrada: Codex escribe fija modelo y agente (responde y ejecuta) cuando el agente esta conectado; rotulo corto del agente", () => {
  const c = cap({ codex: { disponible: true }, opencode: { disponible: true }, "swe-agent": { disponible: true }, openhands: { disponible: true } });
  const casos = [["swe-codex-qwen25-15b", "codex", "Codex", "hf/qwen2.5-coder-1.5b"], ["swe-opencode-qwen35-08b", "opencode", "OpenCode", "hf/qwen3.5-0.8b"],
    ["swe-agent-lfm25", "swe-agent", "SWE-agent", "hf/lfm2.5-350m"], ["swe-openhands-lfm25", "openhands", "OpenHands", "hf/lfm2.5-350m"]];
  for (const [mid, ag, rot, cat] of casos) {
    const r = S.seleccionDeEntrada(mid, c);
    assert.deepEqual(r.fila, { agente: ag, rotulo: rot, soloModelo: false, motivo: "" }, mid);
    assert.deepEqual(r.parcial, { modelo_responde: cat, agente_responde: ag, agente_tool: ag }, mid);
  }
});

test("F4 seleccionDeEntrada: agente no disponible (o incompatible con el modelo) -> «solo modelo»: envia solo el modelo y no toca los agentes", () => {
  const vacio = S.seleccionDeEntrada("swe-codex-qwen25-15b", S.normalizarCapacidades(null));
  assert.equal(vacio.fila.soloModelo, true); assert.equal(vacio.fila.rotulo, "solo modelo"); assert.equal(vacio.fila.agente, "codex");
  assert.deepEqual(vacio.parcial, { modelo_responde: "hf/qwen2.5-coder-1.5b" });
  const inc = S.seleccionDeEntrada("swe-codex-qwen25-15b", cap({ codex: { disponible: true, modelos: ["hf/qwen3-0.6b"] } }));
  assert.equal(inc.fila.soloModelo, true); assert.match(inc.fila.motivo, /incompatible/); assert.deepEqual(inc.parcial, { modelo_responde: "hf/qwen2.5-coder-1.5b" });
});

test("F4 seleccionDeEntrada: las entradas que no son de agente (Liquid, Qwen Code, web-*) no llevan fila de agente y solo fijan el modelo", () => {
  const c = cap({ codex: { disponible: true } });
  assert.equal(S.seleccionDeEntrada("hf-liquid-lfm25", c).fila, null);
  assert.deepEqual(S.seleccionDeEntrada("hf-liquid-lfm25", c).parcial, { modelo_responde: "hf/lfm2.5-350m" });
  assert.deepEqual(S.seleccionDeEntrada("hf-qwen25-coder-15b", c).parcial, { modelo_responde: "hf/qwen2.5-coder-1.5b" });
  assert.deepEqual(S.seleccionDeEntrada("web-qwen38max", c), { fila: null, parcial: {} });
});

test("F4 aplicada sobre la seleccion: elegir «SWE · Codex escribe» deja agente_tool=codex y agente_responde=codex; sin el agente, solo el modelo", () => {
  conStorage();
  S.guardarSeleccion(S.seleccionDeEntrada("swe-codex-qwen25-15b", cap({ codex: { disponible: true } })).parcial);
  const s = S.leerSeleccion(); assert.equal(s.agente_tool, "codex"); assert.equal(s.agente_responde, "codex"); assert.equal(s.modelo_responde, "hf/qwen2.5-coder-1.5b");
  conStorage();
  S.guardarSeleccion(S.seleccionDeEntrada("swe-opencode-qwen35-08b", S.normalizarCapacidades(null)).parcial);
  const t = S.leerSeleccion(); assert.equal(t.agente_tool, S.SEL_DEFECTO.agente_tool); assert.equal(t.agente_responde, S.SEL_DEFECTO.agente_responde); assert.equal(t.modelo_responde, "hf/qwen3.5-0.8b");
});

// ---- F8: hoja NVIDIA «NVIDIA · modelos» y config.js solo con el respaldo ----
test("F8 la hoja NVIDIA se titula «NVIDIA · modelos» y config.js ya no trae Nemotron 3 Super; la ficha de respaldo se rotula", async () => {
  const fs = await import("node:fs"), url = await import("node:url"), path = await import("node:path");
  const dir = path.dirname(url.fileURLToPath(import.meta.url)), leer = (f) => fs.readFileSync(path.join(dir, "..", f), "utf8");
  assert.match(leer("panel-chat.html"), /<div id="sh-ficha"[^>]*>.*?<strong>NVIDIA · modelos<\/strong>/);
  assert.ok(!/Glimmer \/ Nemotron 3 Super/.test(leer("panel-chat.html")));
  const cfg = leer("config.js"); assert.ok(!/nv-nemotron-super/.test(cfg)); assert.match(cfg, /nv-muse-glimmer'[^}]*\(respaldo\)/);
});
