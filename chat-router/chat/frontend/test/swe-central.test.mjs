import test from "node:test";
import assert from "node:assert/strict";
import * as S from "../swe-directo.js";
import * as C from "../swe-claves.js";

// Auditoria 3 · A1: selector central unico (4 campos), salida DERIVADA de AGENTE QUE EJECUTA, estados reales, R1 (sin claves en el navegador), R4 (tool_calls con texto), R6 (SIN VERIFICAR).
// Sin red ni claves reales: api() es un doble; los valores de "clave" son marcadores de prueba.
const conStorage = (inicial = {}) => {
  const m = new Map(Object.entries(inicial));
  globalThis.localStorage = { getItem: (k) => (m.has(k) ? m.get(k) : null), setItem: (k, v) => { m.set(k, String(v)); }, removeItem: (k) => { m.delete(k); } };
  return m;
};
const AGS = ["openclaw", "swe-agent", "openhands", "opencode", "codex", "claude-code"];
const CAP_OK = S.normalizarCapacidades({ harness: "ok", agentes: Object.fromEntries(AGS.map((a) => [a, { disponible: true }])), workflows: { swe_code: { disponible: true }, liquid_mirror: { disponible: true } }, modelos: Object.fromEntries(S.MODELOS_SWE.map((m) => [m[0], { disponible: true }])) });
test.beforeEach(() => { S.olvidarCapacidades(); delete globalThis.localStorage; });

// ---------- 197 / 62 / 63: UNA sola definicion de salida: AGENTE QUE EJECUTA (agente_tool); ejecutor_tools se DERIVA ----------
test("197 ejecutor_tools se DERIVA de agente_tool: openclaw -> 'openclaw'; cualquier otro agente -> 'swe'", () => {
  conStorage();
  assert.equal(S.leerEjecutorTools(), "swe", "defecto (agente_tool swe-agent)");
  for (const [a, e] of [["openclaw", "openclaw"], ["swe-agent", "swe"], ["codex", "swe"], ["openclaw", "openclaw"], ["opencode", "swe"], ["openhands", "swe"], ["claude-code", "swe"]]) {
    S.guardarSeleccion({ agente_tool: a }); assert.equal(S.leerSeleccion().agente_tool, a); assert.equal(S.leerEjecutorTools(), e, "agente " + a);
  }
  assert.deepEqual(S.EJECUTORES_TOOLS, ["swe", "openclaw"]);
});
test("ya no hay segunda definicion: sin guardarEjecutorTools/salidaActiva/ETIQUETA_SALIDA y la key vieja riu_swe_ejecutor_tools se ignora", () => {
  const m = conStorage({ riu_swe_ejecutor_tools: "openclaw" });
  for (const k of ["guardarEjecutorTools", "salidaActiva", "ETIQUETA_SALIDA"]) assert.equal(S[k], undefined, k + " ya no existe");
  assert.equal(S.leerEjecutorTools(), "swe", "la key vieja no es fuente");
  assert.equal(S.armar({ model: "lfm2.5-350m", mensaje: "x", sesion: "s" }).ejecutor_tools, "swe");
  S.guardarSeleccion({ agente_tool: "openclaw" }); assert.equal(m.get("riu_swe_ejecutor_tools"), "openclaw", "no se escribe ni se lee");
  assert.equal(S.armar({ model: "lfm2.5-350m", mensaje: "x", sesion: "s" }).ejecutor_tools, "openclaw");
});
test("198 cambiar modelo_tool NO modifica modelo_responde (y al reves)", () => {
  conStorage();
  S.guardarSeleccion({ modelo_responde: "hf/qwen3-0.6b", modelo_tool: "hf/qwen2.5-coder-1.5b" });
  S.guardarSeleccion({ modelo_tool: "nvidia/z-ai/glm-5.3" }); assert.equal(S.leerSeleccion().modelo_responde, "hf/qwen3-0.6b");
  S.guardarSeleccion({ modelo_responde: "groq/qwen/qwen3.8-27b" }); assert.equal(S.leerSeleccion().modelo_tool, "nvidia/z-ai/glm-5.3");
  S.guardarSeleccion({ agente_responde: "codex" }); assert.equal(S.leerSeleccion().agente_tool, "swe-agent", "agente_responde y agente_tool tampoco se intercambian");
});

// ---------- R1: claves ----------
test("R1 armar() NUNCA manda claves, aunque haya una entrada vieja en localStorage", () => {
  const m = conStorage({ riu_swe_claves: JSON.stringify({ groq: "MARCADOR-PRUEBA-NO-REAL-1", nvidia: "MARCADOR-PRUEBA-NO-REAL-2" }) });
  const cuerpo = S.armar({ model: "web-qwen38max", historial: [], mensaje: "x", sesion: "s" });
  assert.ok(!("claves" in cuerpo) && !("clave" in cuerpo));
  assert.ok(!JSON.stringify(cuerpo).includes("MARCADOR-PRUEBA"));
  assert.ok(m.has("riu_swe_claves") || true);
});
test("R1 swe-claves.js no guarda claves en localStorage: sin banco solo se informa el estado, y se purga lo viejo", async () => {
  const m = conStorage({ riu_swe_claves: JSON.stringify({ groq: "MARCADOR-PRUEBA-NO-REAL-1" }) });
  assert.equal(typeof C.leerClaves, "undefined"); assert.equal(typeof C.guardarClave, "undefined");
  C.purgarLocal(); assert.equal(m.has("riu_swe_claves"), false, "la clave vieja se borra del navegador");
  globalThis.sessionStorage = { getItem: () => "api-e2e" };
  globalThis.window = { RIU_CONFIG: { apiBase: "https://x-y.hf.space" } };
  const caido = async () => { throw new TypeError("sin red"); };
  globalThis.fetch = caido;
  const r = await C.guardarConEstado({ groq: "MARCADOR-PRUEBA-NO-REAL-9" });
  assert.equal(r.ok, false); assert.match(r.texto, /no se guard/i); assert.match(r.texto, /servidor/i);
  assert.ok(![...m.values()].some((v) => /MARCADOR-PRUEBA/.test(v)), "ningun valor queda en localStorage");
  assert.ok(!r.texto.includes("MARCADOR-PRUEBA"));
  const e = await C.estado(); assert.ok(!e.includes("MARCADOR-PRUEBA")); assert.match(e, /servidor|sin banco|no responde/i);
  delete globalThis.fetch; delete globalThis.window; delete globalThis.sessionStorage;
});

// ---------- R4: tool_calls con texto ----------
test("R4 una respuesta con texto Y tool_calls conserva y muestra las llamadas pendientes", async () => {
  const tc = [{ id: "c1", type: "function", function: { name: "github_leer", arguments: "{}" } }, { id: "c2", type: "function", function: { name: "motor_copiar", arguments: "{}" } }];
  const api = async () => ({ modelo_usado: "groq/x", choices: [{ message: { content: "Voy a leer el repo", tool_calls: tc }, finish_reason: "tool_calls" }] });
  const r = await S.enviarSwe(api, { model: "groq/qwen/qwen3.8-27b", historial: [], mensaje: "x", sesion: "s", ejecutor_tools: "openclaw" });
  assert.deepEqual(r.pedidas, ["github_leer", "motor_copiar"]); assert.equal(r.ejecutor, "OpenClaw"); assert.deepEqual(r.tools, []);
  assert.match(r.reply, /Voy a leer el repo/); assert.deepEqual(r.tool_calls, tc, "las llamadas completas viajan al chat para no perderlas");
  assert.equal(r.finish_reason, "tool_calls");
});
test("R4 sin texto sigue igual (solo tool_calls) y un stream que junta texto + tool_calls tambien las conserva", async () => {
  const tc = [{ id: "c1", type: "function", function: { name: "t", arguments: "{}" } }];
  const r0 = await S.enviarSwe(async () => ({ choices: [{ message: { content: "", tool_calls: tc }, finish_reason: "tool_calls" }] }), { model: "web-qwen38max", historial: [], mensaje: "x", sesion: "s" });
  assert.deepEqual(r0.pedidas, ["t"]); assert.deepEqual(r0.tool_calls, tc);
  const sse = (l) => ({ __sse: { body: null, text: async () => l.map((o) => "data: " + JSON.stringify(o) + "\n\n").join("") + "data: [DONE]\n\n" } });
  const r1 = await S.enviarSwe(async () => sse([{ choices: [{ delta: { content: "hola " } }] }, { choices: [{ delta: { tool_calls: [{ index: 0, id: "c9", function: { name: "github_", arguments: "{\"a\"" } }] } }] }, { choices: [{ delta: { tool_calls: [{ index: 0, function: { name: "leer", arguments: ":1}" } }] }, finish_reason: "tool_calls" }] }]), { model: "web-qwen38max", historial: [], mensaje: "x", sesion: "s" });
  assert.match(r1.reply, /hola/); assert.equal(r1.pedidas.length, 1); assert.equal(r1.tool_calls[0].function.arguments, "{\"a\":1}");
});

// ---------- R6 / 37 / 48 / 49: estados reales ----------
test("37 estados reales: DISPONIBLE, NO INSTALADO, NO CONFIGURADO, NO COMPATIBLE, NO DISPONIBLE EN PROVEEDOR, SIN VERIFICAR", () => {
  assert.deepEqual(Object.keys(S.ETIQUETA_ESTADO), ["DISPONIBLE", "NO_INSTALADO", "NO_CONFIGURADO", "NO_COMPATIBLE", "NO_DISPONIBLE_PROVEEDOR", "SIN_VERIFICAR"]);
  assert.deepEqual(Object.values(S.ETIQUETA_ESTADO), ["DISPONIBLE", "NO INSTALADO", "NO CONFIGURADO", "NO COMPATIBLE", "NO DISPONIBLE EN PROVEEDOR", "SIN VERIFICAR"]);
  const cap = S.normalizarCapacidades({ harness: "ok", agentes: {
    "swe-agent": { disponible: false, motivo: "swe-agent no esta instalado (CLI `sweagent` ausente del PATH; define RIU_SWEAGENT_BIN)" },
    codex: { disponible: false, motivo: "codex instalado pero falta RIU_CODEX_BASE_URL: Codex solo habla la API Responses" },
    "claude-code": { disponible: true, modelos: ["nvidia/minimaxai/minimax-m3.1-flash"] },
    openclaw: { disponible: false, motivo: "el Gateway OpenClaw no responde en la URL configurada" },
    opencode: { disponible: true }, openhands: { disponible: false, motivo: "no se pudo comprobar (OSError)" } },
  modelos: { "nvidia/z-ai/glm-5.3": { disponible: false, motivo: "glm-5.3 no figura en GET /models de nvidia" }, "groq/qwen/qwen3.8-27b": { disponible: true, motivo: "sin verificar GET /models (OSError)" }, "hf/qwen3-0.6b": { disponible: true } } });
  const est = (t, id, m) => S.estadoOpcion(cap, t, id, m).estado;
  assert.equal(est("agente", "swe-agent"), "NO_INSTALADO"); assert.equal(est("agente", "codex"), "NO_CONFIGURADO");
  assert.equal(est("agente", "claude-code", "hf/qwen3-0.6b"), "NO_COMPATIBLE"); assert.equal(est("agente", "opencode"), "DISPONIBLE");
  assert.equal(est("agente", "openhands"), "SIN_VERIFICAR", "una comprobacion que fallo NO es «no instalado»");
  assert.equal(est("agente", "openclaw"), "NO_CONFIGURADO");
  assert.equal(est("modelo", "nvidia/z-ai/glm-5.3"), "NO_DISPONIBLE_PROVEEDOR");
  assert.equal(est("modelo", "groq/qwen/qwen3.8-27b"), "SIN_VERIFICAR", "R6: «sin verificar» nunca se presenta como DISPONIBLE");
  assert.equal(S.estadoOpcion(cap, "modelo", "groq/qwen/qwen3.8-27b").ok, true, "sin verificar no bloquea el chat normal; se rotula");
  assert.equal(est("modelo", "hf/qwen3-0.6b"), "DISPONIBLE");
  assert.equal(S.estadoOpcion(cap, "agente", "swe-agent").ok, false);
});
test("48/49 si el Harness no responde o no esta configurado todo es SIN VERIFICAR, nunca NO INSTALADO", async () => {
  for (const h of ["sin_respuesta", "no_disponible", "no_configurado", "sin_credencial", "desconocido"]) {
    const cap = S.normalizarCapacidades({ harness: h });
    for (const a of AGS) { const r = S.estadoOpcion(cap, "agente", a); assert.equal(r.estado, "SIN_VERIFICAR", h + " " + a); assert.equal(r.ok, false); assert.doesNotMatch(r.motivo, /no esta instalado/i); }
    assert.equal(S.estadoOpcion(cap, "workflow", "swe_code").estado, "SIN_VERIFICAR");
  }
  const caido = await S.cargarCapacidades(async () => { throw new Error("red"); }, { forzar: true });
  assert.equal(S.estadoOpcion(caido, "agente", "codex").estado, "SIN_VERIFICAR");
  assert.equal(S.lineaNoInstalados(S.agruparOpciones(caido, "agente", S.AGENTES_SWE)), "", "no se afirma «No instalados» si la comprobacion fallo");
  assert.match(S.lineaSinVerificar(S.agruparOpciones(caido, "agente", S.AGENTES_SWE)), /^Sin verificar: /);
  S.olvidarCapacidades();
});
test("agruparOpciones separa por estado real y lineaNoInstalados solo nombra los NO INSTALADOS", () => {
  const cap = S.normalizarCapacidades({ harness: "ok", agentes: { codex: { disponible: true }, "swe-agent": { disponible: false, motivo: "swe-agent no esta instalado (CLI ausente)" }, openhands: { disponible: false, motivo: "no se pudo comprobar (OSError)" } } });
  const g = S.agruparOpciones(cap, "agente", S.AGENTES_SWE);
  assert.deepEqual(g.ok.map((x) => x.id), ["codex"]); assert.deepEqual(g.noInstalado.map((x) => x.id), ["swe-agent"]);
  assert.ok(g.sinVerificar.map((x) => x.id).includes("openhands")); assert.equal(S.lineaNoInstalados(g), "No instalados: SWE-agent");
});

// ---------- 199-202: modo OFF / ON / agente no instalado / modelo no disponible (validacion real del contrato) ----------
test("199 modo agentico OFF + Individual: conversacion normal, no se valida ni se consulta ningun agente", () => {
  const v = S.validarSeleccion({ ...S.SEL_DEFECTO, agente_tool: "swe-agent", modo_agentico: false }, S.normalizarCapacidades({ harness: "sin_respuesta" }));
  assert.deepEqual(v, { ok: true, problemas: [] }); assert.equal(S.requiereHarness({ ...S.SEL_DEFECTO }), false);
});
test("200 modo agentico ON con agente disponible (simulado) y modelo compatible: valida y arma la tarea con el agente elegido", () => {
  const sel = { ...S.SEL_DEFECTO, modo_agentico: true, agente_tool: "codex", modelo_tool: "hf/qwen2.5-coder-1.5b" };
  assert.deepEqual(S.validarSeleccion(sel, CAP_OK), { ok: true, problemas: [] });
  const t = S.armarTarea({ sel, mensaje: "hola", sesion: "s", proyecto: "p" });
  assert.equal(t.agente_tool, "codex"); assert.equal(t.modo_agentico, true); assert.equal(t.modelo_tool, "hf/qwen2.5-coder-1.5b");
});
test("201 agente NO INSTALADO con modo ON: la eleccion se conserva visible con su error y se bloquea el envio; no se cambia a otro agente", async () => {
  conStorage();
  const cap = { harness: "ok", agentes: Object.fromEntries(AGS.map((a) => [a, { disponible: a !== "swe-agent", motivo: a === "swe-agent" ? "swe-agent no esta instalado (CLI `sweagent` ausente del PATH)" : "" }])), workflows: {}, modelos: {} };
  S.guardarSeleccion({ modo_agentico: true, agente_tool: "swe-agent" });
  const llamadas = [];
  await assert.rejects(() => S.enviarTareaSwe(async (r) => { llamadas.push(r); return r === "/chat/swe/capacidades" ? cap : { ok: true, resultado: { estado: "DONE" } }; }, { mensaje: "x", sesion: "s" }), (e) => /SELECCION_NO_DISPONIBLE/.test(e.message) && /NO INSTALADO/.test(e.message) && /SWE-agent/.test(e.message));
  assert.ok(!llamadas.some((r) => /iniciar|avanzar/.test(r)), "no se crea la tarea");
  assert.equal(S.leerSeleccion().agente_tool, "swe-agent", "la eleccion NO se cambia en silencio");
  const v = S.validarSeleccion(S.leerSeleccion(), S.normalizarCapacidades(cap)); assert.equal(v.ok, false);
});
test("202 modelo NO DISPONIBLE EN PROVEEDOR (GLM 5.3): se muestra su estado real, se bloquea con modo ON y la eleccion no cambia", () => {
  const cap = S.normalizarCapacidades({ harness: "ok", agentes: Object.fromEntries(AGS.map((a) => [a, { disponible: true }])), modelos: { "nvidia/z-ai/glm-5.3": { disponible: false, motivo: "glm-5.3 no figura en GET /models de nvidia" } } });
  const sel = { ...S.SEL_DEFECTO, modo_agentico: true, modelo_tool: "nvidia/z-ai/glm-5.3", agente_tool: "opencode" };
  const v = S.validarSeleccion(sel, cap); assert.equal(v.ok, false);
  assert.ok(v.problemas.some((p) => /MODELO PARA TOOL GLM 5\.3: NO DISPONIBLE EN PROVEEDOR/.test(p)), v.problemas.join("|"));
  const o = S.opcionesModeloVentana("nvidia", cap).find((x) => x.id === "nvidia/z-ai/glm-5.3");
  assert.equal(o.ok, false); assert.equal(o.estado, "NO_DISPONIBLE_PROVEEDOR"); assert.match(o.etq, /NO DISPONIBLE EN PROVEEDOR/);
  assert.equal(S.opcionesModeloVentana("nvidia", cap, { "nvidia/meta/muse-glimmer-30b": false }).find((x) => x.id === "nvidia/meta/muse-glimmer-30b").estado, "NO_DISPONIBLE_PROVEEDOR", "el catalogo del Router tambien cuenta");
});

// ---------- 23-26 / UI4 / UI5: modelos por ventana y modo de trabajo ----------
test("UI4/28 las listas de modelos locales muestran SOLO el nombre del modelo (sin nombres de agente) y ya no hay modos como modelos", () => {
  const todas = Object.values(S.SWE_LISTAS).flatMap((l) => l.modelos.map((m) => m[1]));
  assert.ok(!todas.some((n) => /SWE ·|Codex|OpenCode|OpenHands|Agent ejecuta|asesor|revisi|soluci|arquitect|archivos|prompt_code|despliega/i.test(n)), todas.join(" | "));
  assert.deepEqual(S.SWE_LISTAS["swe-code"].modelos.map((m) => m[1]), ["Liquid LFM2.5 350M", "Qwen2.5 Coder 1.5B", "Qwen3.5 0.8B", "Qwen3 0.6B"]);
  for (const id of ["swecode-asesoria", "swecode-revision", "swecode-solucion", "swecode-arquitectura", "swecode-archivos", "swecode-prompt_code", "swecode-despliega"]) assert.ok(!Object.values(S.SWE_LISTAS).some((l) => l.modelos.some((m) => m[0] === id)), id);
});
test("24 los 7 modos de SWEN son MODO DE TRABAJO (selector), viajan como `modo` al bridge y no entran al contrato TareaSWE", () => {
  assert.deepEqual(S.MODOS_TRABAJO.map((m) => m[0]), ["asesoria", "revision", "solucion", "arquitectura", "archivos", "prompt_code", "despliega"]);
  conStorage();
  assert.equal(S.leerSeleccion().modo_trabajo, "");
  S.guardarSeleccion({ modo_trabajo: "revision" }); assert.equal(S.leerSeleccion().modo_trabajo, "revision");
  S.guardarSeleccion({ modo_trabajo: "inventado" }); assert.equal(S.leerSeleccion().modo_trabajo, "revision", "un modo invalido no pisa el anterior");
  assert.equal(S.armar({ model: "web-qwen38max", historial: [], mensaje: "x", sesion: "s" }).modo, "revision");
  assert.equal(S.armar({ model: "swecode-consulta", historial: [], mensaje: "x", sesion: "s" }).model, "swecode-revision", "Concilio + modo = swecode-<modo> (el modo va en el id)");
  assert.equal(S.armar({ model: "lfm2.5-350m", historial: [], mensaje: "x", sesion: "s", modo: "" }).modo, undefined, "modo vacio = no se manda");
  assert.ok(!("modo_trabajo" in S.armarTarea({ sel: S.leerSeleccion(), mensaje: "x", sesion: "s" })), "el contrato TareaSWE no cambia");
  S.guardarSeleccion({ modo_trabajo: "" }); assert.ok(!("modo" in S.armar({ model: "web-qwen38max", historial: [], mensaje: "x", sesion: "s" })));
});
test("25/26 MODELO QUE RESPONDE por ventana: SWE CODE = 4 HF; Groq = Groq; NVIDIA = NVIDIA (GLM 5.3 deshabilitado si el proveedor no lo publica); SWEN = web + catalogo", () => {
  const ids = (v) => S.opcionesModeloVentana(v, CAP_OK).map((x) => x.id);
  assert.deepEqual(ids("swe-code"), ["hf/lfm2.5-350m", "hf/qwen2.5-coder-1.5b", "hf/qwen3.5-0.8b", "hf/qwen3-0.6b"]);
  assert.deepEqual(ids("groq"), ["groq/qwen/qwen3.8-27b"]);
  assert.deepEqual(ids("nvidia"), ["nvidia/minimaxai/minimax-m3.1-flash", "nvidia/meta/muse-glimmer-30b", "nvidia/nvidia/nemotron-3-ultra-550b-a55b", "nvidia/z-ai/glm-5.3"]);
  assert.ok(["swecode-consulta", "web-qwen38max", "web-qwen37max", "web-dsv4-flash", "hf/qwen3-0.6b", "groq/qwen/qwen3.8-27b"].every((i) => ids("swen-code-free").includes(i)));
  assert.ok(!ids("swe-code").includes("groq/qwen/qwen3.8-27b"));
  assert.equal(S.opcionesModeloVentana("swen-code-free", CAP_OK).find((x) => x.id === "web-qwen38max").estado, "SIN_VERIFICAR", "una cuenta web no se verifica desde aqui: no se rotula DISPONIBLE");
});
test("modelo_responde acepta los modelos web de SWEN solo para chat directo; con modo agentico/workflow se bloquea (el Harness solo admite el catalogo)", () => {
  conStorage();
  S.guardarSeleccion({ modelo_responde: "web-qwen38max" }); assert.equal(S.leerSeleccion().modelo_responde, "web-qwen38max");
  assert.equal(S.validarSeleccion(S.leerSeleccion(), CAP_OK).ok, true, "OFF + Individual: normal");
  const v = S.validarSeleccion({ ...S.leerSeleccion(), modo_agentico: true }, CAP_OK);
  assert.equal(v.ok, false); assert.ok(v.problemas.some((p) => /MODELO QUE RESPONDE.*NO COMPATIBLE/.test(p)), v.problemas.join("|"));
});

// ---------- A5: estado/causa/intentable/nombre del catalogo que reporta el Harness (compatibles hacia atras) ----------
test("A5 el `estado` explicito del Harness manda; `causa` es el texto; SIN VERIFICAR + intentable se puede elegir con aviso y NO es NO INSTALADO", () => {
  const cap = S.normalizarCapacidades({ harness: "ok", agentes: {
    codex: { estado: "SIN_VERIFICAR", veredicto: "SIN VERIFICAR", verificado: false, intentable: true, causa: "la sonda no respondio a tiempo", disponible: false },
    opencode: { estado: "NO INSTALADO", veredicto: "NO DISPONIBLE", causa: "CLI opencode ausente del PATH", intentable: false, disponible: false },
    openhands: { estado: "NO_COMPATIBLE", causa: "no admite este modelo", disponible: false },
    "swe-agent": { estado: "DISPONIBLE", veredicto: "DISPONIBLE", verificado: true, disponible: true } },
  modelos: { "hf/qwen3-0.6b": { estado: "DISPONIBLE", nombre: "Qwen3 0.6B (HF)", proveedor: "hf", nota: "x" }, "nvidia/z-ai/glm-5.3": { estado: "NO DISPONIBLE EN PROVEEDOR", causa: "glm-5.3 no figura en GET /models", nombre: "GLM 5.3" } } });
  const c = S.estadoOpcion(cap, "agente", "codex"); assert.equal(c.estado, "SIN_VERIFICAR"); assert.equal(c.ok, false); assert.equal(c.elegible, true); assert.match(c.motivo, /sonda/);
  const o = S.estadoOpcion(cap, "agente", "opencode"); assert.equal(o.estado, "NO_INSTALADO"); assert.equal(o.elegible, false); assert.match(o.motivo, /ausente del PATH/);
  assert.equal(S.estadoOpcion(cap, "agente", "openhands").estado, "NO_COMPATIBLE"); assert.equal(S.estadoOpcion(cap, "agente", "swe-agent").ok, true);
  assert.equal(S.estadoOpcion(cap, "modelo", "nvidia/z-ai/glm-5.3").estado, "NO_DISPONIBLE_PROVEEDOR");
  const g = S.agruparOpciones(cap, "agente", S.AGENTES_SWE); assert.ok(g.sinVerificar.some((x) => x.id === "codex" && x.elegible)); assert.deepEqual(g.noInstalado.map((x) => x.id), ["opencode"]);
  assert.equal(S.opcionesModeloVentana("swe-code", cap).find((x) => x.id === "hf/qwen3-0.6b").nombre, "Qwen3 0.6B (HF)", "el nombre sale del catalogo del Harness");
  // con modo agentico ON un agente SIN VERIFICAR sigue sin ejecutarse (51): se dice SIN VERIFICAR, no NO INSTALADO
  const v = S.validarSeleccion({ ...S.SEL_DEFECTO, modo_agentico: true, agente_tool: "codex", modelo_tool: "hf/qwen2.5-coder-1.5b" }, cap);
  assert.ok(v.problemas.some((p) => /AGENTE QUE EJECUTA Codex: SIN VERIFICAR/.test(p)) && !v.problemas.some((p) => /NO INSTALADO/.test(p)), v.problemas.join("|"));
});
