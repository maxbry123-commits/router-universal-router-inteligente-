import test from "node:test";
import assert from "node:assert/strict";
import * as S from "../swe-directo.js";

// Selectores de agente/modelo/workflow de SWE CODE / SWEN CODE free y contrato TareaSWE (el mismo de agentes/adaptadores/contrato.py).
// Sin red: api() es un doble; ninguna clave real.
const conStorage = (inicial = {}) => {
  const m = new Map(Object.entries(inicial));
  globalThis.localStorage = { getItem: (k) => (m.has(k) ? m.get(k) : null), setItem: (k, v) => { m.set(k, String(v)); }, removeItem: (k) => { m.delete(k); } };
  return m;
};
const CAMPOS = ["task_id", "origen", "mensaje", "workflow", "modelo_responde", "modelo_lector", "modelo_tool", "modelo_revisor", "agente_responde", "agente_tool", "agente_verificador", "modo_agentico", "aprobacion", "sesion", "proyecto"];
const TODOS_OK = { harness: "ok", agentes: Object.fromEntries(["openclaw", "swe-agent", "openhands", "opencode", "codex", "claude-code"].map((a) => [a, { disponible: true }])), workflows: { swe_code: { disponible: true }, liquid_mirror: { disponible: true } }, modelos: {} };

test("catalogo: 9 modelos con el id exacto del catalogo unico (4 HF + Groq Qwen 3.8 + 4 NVIDIA), sin Llama", () => {
  assert.deepEqual(S.MODELOS_SWE.map((m) => m[0]), ["hf/lfm2.5-350m", "hf/qwen2.5-coder-1.5b", "hf/qwen3.5-0.8b", "hf/qwen3-0.6b", "groq/qwen/qwen3.8-27b", "nvidia/minimaxai/minimax-m3.1-flash", "nvidia/meta/muse-glimmer-30b", "nvidia/nvidia/nemotron-3-ultra-550b-a55b", "nvidia/z-ai/glm-5.3"]);
  assert.deepEqual(S.AGENTES_SWE.map((a) => a[0]), ["openclaw", "swe-agent", "openhands", "opencode", "codex", "claude-code"]);
  assert.deepEqual(S.WORKFLOWS_SWE.map((w) => w[0]), ["individual", "swe_code", "liquid_mirror"]);
  assert.deepEqual(S.WORKFLOWS_SWE.map((w) => w[1]), ["Individual", "SWE CODE cuatro pasos", "Liquid Mirror"]);
});

test("Liquid Mirror: dos participantes LIQUID 1 — LECTOR (S2) y LIQUID 2 — EJECUTOR (S3), ambos lfm2.5-350m, sin modelos web", () => {
  assert.deepEqual(S.LIQUID_MIRROR.map((p) => [p.etiqueta, p.servidor, p.modelo]), [["LIQUID 1 — LECTOR", "S2", "hf/lfm2.5-350m"], ["LIQUID 2 — EJECUTOR", "S3", "hf/lfm2.5-350m"]]);
  assert.ok(!JSON.stringify(S.LIQUID_MIRROR).includes("web-"));
});

test("seleccion: defectos, persistencia en localStorage y valores invalidos vuelven al defecto", () => {
  delete globalThis.localStorage;
  assert.deepEqual(S.leerSeleccion(), S.SEL_DEFECTO);
  assert.equal(S.SEL_DEFECTO.modo_agentico, false); assert.equal(S.SEL_DEFECTO.workflow, "individual");
  const m = conStorage();
  const g = S.guardarSeleccion({ workflow: "swe_code", modo_agentico: true, agente_tool: "codex", modelo_tool: "hf/qwen3.5-0.8b" });
  assert.equal(g.workflow, "swe_code"); assert.equal(g.modo_agentico, true);
  assert.equal(JSON.parse(m.get("riu_swe_seleccion")).agente_tool, "codex");
  assert.equal(S.leerSeleccion().modelo_tool, "hf/qwen3.5-0.8b");
  const mala = S.guardarSeleccion({ workflow: "otro", agente_responde: "gpt", modelo_responde: "hf/llama", modo_agentico: "si" });
  assert.equal(mala.workflow, "swe_code", "un valor invalido no pisa el anterior"); assert.equal(mala.agente_responde, S.SEL_DEFECTO.agente_responde);
  assert.equal(mala.modelo_responde, S.SEL_DEFECTO.modelo_responde); assert.equal(mala.modo_agentico, true);
  m.set("riu_swe_seleccion", "{corrupto"); assert.deepEqual(S.leerSeleccion(), S.SEL_DEFECTO);
  delete globalThis.localStorage;
});

test("el boton de salida (ejecutor_tools) es SWE-agent | OpenClaw y queda sincronizado con AGENTE QUE EJECUTA", () => {
  assert.deepEqual(S.EJECUTORES_TOOLS, ["swe", "openclaw"]);
  assert.deepEqual(S.ETIQUETA_SALIDA, { swe: "Salida: SWE-agent", openclaw: "Salida: OpenClaw" });
  conStorage();
  S.guardarEjecutorTools("openclaw"); assert.equal(S.leerSeleccion().agente_tool, "openclaw");
  S.guardarEjecutorTools("swe"); assert.equal(S.leerSeleccion().agente_tool, "swe-agent");
  S.guardarSeleccion({ agente_tool: "openclaw" }); assert.equal(S.leerEjecutorTools(), "openclaw");
  S.guardarSeleccion({ agente_tool: "codex" }); assert.equal(S.leerEjecutorTools(), "openclaw", "un tercer agente no cambia el boton");
  delete globalThis.localStorage;
});

test("requiereHarness: solo con workflow != individual o modo agentico ON", () => {
  assert.equal(S.requiereHarness({ ...S.SEL_DEFECTO }), false);
  assert.equal(S.requiereHarness({ ...S.SEL_DEFECTO, modo_agentico: true }), true);
  assert.equal(S.requiereHarness({ ...S.SEL_DEFECTO, workflow: "swe_code" }), true);
  assert.equal(S.requiereHarness({ ...S.SEL_DEFECTO, workflow: "liquid_mirror" }), true);
});

test("armarTarea: el contrato TareaSWE exacto (15 campos, origen yaiwes, ids hf/...), el agente no se convierte en modelo", () => {
  const sel = { modelo_responde: "hf/lfm2.5-350m", modelo_tool: "hf/qwen2.5-coder-1.5b", agente_responde: "openclaw", agente_tool: "swe-agent", modo_agentico: true, workflow: "swe_code" };
  const t = S.armarTarea({ sel, mensaje: "Revisar proyecto", sesion: "chat-001", proyecto: "yaiwes", task_id: "yaiwes-001" });
  assert.deepEqual(Object.keys(t).sort(), [...CAMPOS].sort());
  assert.deepEqual(t, { task_id: "yaiwes-001", origen: "yaiwes", workflow: "swe_code", mensaje: "Revisar proyecto", modelo_responde: "hf/lfm2.5-350m", modelo_lector: "hf/lfm2.5-350m", modelo_tool: "hf/qwen2.5-coder-1.5b", modelo_revisor: "hf/qwen3.5-0.8b", agente_responde: "openclaw", agente_tool: "swe-agent", agente_verificador: "openhands", modo_agentico: true, aprobacion: false, sesion: "chat-001", proyecto: "yaiwes" });
  assert.ok(S.MODELOS_SWE.some((m) => m[0] === t.modelo_responde) && !S.MODELOS_SWE.some((m) => m[0] === t.agente_responde));
});

test("armarTarea: la aprobacion SIEMPRE sale false del cliente, sin proyecto manda 'yaiwes', task_id valido y nuevo en cada tarea", () => {
  const t = S.armarTarea({ sel: { ...S.SEL_DEFECTO }, mensaje: "x", sesion: "s", aprobacion: true });
  assert.equal(t.aprobacion, false); assert.equal(t.proyecto, "yaiwes");
  const a = S.nuevoTaskId(), b = S.nuevoTaskId();
  assert.match(a, /^yaiwes-[A-Za-z0-9_-]{1,50}$/); assert.notEqual(a, b); assert.ok(a.length <= 64);
  assert.match(t.task_id, /^[A-Za-z0-9_-]{1,64}$/);
  const raro = S.armarTarea({ sel: { ...S.SEL_DEFECTO }, mensaje: "x", sesion: "chat 001/ñ" });
  assert.match(raro.sesion, /^[A-Za-z0-9_-]{1,64}$/, "la sesion se sanea como identificador");
});

test("armarTarea con Liquid Mirror: lector = Liquid 1 (S2) y tool = Liquid 2 (S3), ambos lfm2.5-350m, aunque el selector diga otra cosa", () => {
  const t = S.armarTarea({ sel: { ...S.SEL_DEFECTO, workflow: "liquid_mirror", modelo_tool: "nvidia/z-ai/glm-5.3", modelo_responde: "groq/qwen/qwen3.8-27b" }, mensaje: "Revisar y desplegar", sesion: "s" });
  assert.equal(t.modelo_lector, "hf/lfm2.5-350m"); assert.equal(t.modelo_tool, "hf/lfm2.5-350m"); assert.equal(t.workflow, "liquid_mirror");
  assert.equal(t.modelo_responde, "groq/qwen/qwen3.8-27b", "el modelo que responde no se toca");
});

test("capacidades: lo que el Harness no reporta es NO DISPONIBLE; un modelo solo se marca si lo reportan caido; incompatibilidad por modelo", () => {
  const vacio = S.normalizarCapacidades({});
  const ag = S.estadoOpcion(vacio, "agente", "codex");
  assert.equal(ag.ok, false); assert.match(ag.motivo, /adaptador/i);
  assert.equal(S.estadoOpcion(vacio, "workflow", "individual").ok, true);
  assert.equal(S.estadoOpcion(vacio, "workflow", "swe_code").ok, false);
  assert.equal(S.estadoOpcion(vacio, "modelo", "hf/lfm2.5-350m").ok, true);
  const cap = S.normalizarCapacidades({ agentes: { codex: { disponible: true, modelos: ["hf/qwen2.5-coder-1.5b"] }, openhands: { disponible: false, motivo: "SDK no instalado" } }, modelos: { "groq/qwen/qwen3.8-27b": { disponible: false, motivo: "no esta en GET /models" } } });
  assert.equal(S.estadoOpcion(cap, "agente", "codex", "hf/qwen2.5-coder-1.5b").ok, true);
  const inc = S.estadoOpcion(cap, "agente", "codex", "hf/qwen3-0.6b");
  assert.equal(inc.ok, false); assert.match(inc.motivo, /incompatible/i);
  assert.match(S.estadoOpcion(cap, "agente", "openhands").motivo, /SDK no instalado/);
  assert.equal(S.estadoOpcion(cap, "modelo", "groq/qwen/qwen3.8-27b").ok, false);
  assert.equal(S.estadoOpcion(S.normalizarCapacidades(null), "agente", "codex").ok, false);
  assert.equal(S.estadoOpcion(S.normalizarCapacidades({ agentes: { codex: { disponible: "true" } } }), "agente", "codex").ok, false, "solo true estricto");
});

test("validarSeleccion: sin modo agentico ni workflow no se valida nada; con ellos NO se envia lo que no esta conectado", () => {
  assert.equal(S.validarSeleccion({ ...S.SEL_DEFECTO }, S.normalizarCapacidades({})).ok, true);
  const v = S.validarSeleccion({ ...S.SEL_DEFECTO, modo_agentico: true }, S.normalizarCapacidades({}));
  assert.equal(v.ok, false); assert.ok(v.problemas.length >= 2); assert.ok(v.problemas.every((p) => /NO DISPONIBLE|incompatible/i.test(p)));
  assert.equal(S.validarSeleccion({ ...S.SEL_DEFECTO, modo_agentico: true }, S.normalizarCapacidades(TODOS_OK)).ok, true);
  const w = S.validarSeleccion({ ...S.SEL_DEFECTO, workflow: "liquid_mirror" }, S.normalizarCapacidades({ agentes: TODOS_OK.agentes }));
  assert.equal(w.ok, false); assert.ok(w.problemas.some((p) => /Liquid Mirror/.test(p)));
});

test.beforeEach(() => S.olvidarCapacidades());
const respuestaHarness = (resultado) => ({ ok: true, resultado });
const cuerpoDe = (op) => op.body;

test("enviarTareaSwe: iniciar y avanzar hasta DONE por /chat/swe/*; muestra evidencias reales y task_id; no manda campos ajenos", async () => {
  conStorage({ riu_swe_seleccion: JSON.stringify({ ...S.SEL_DEFECTO, workflow: "swe_code", modo_agentico: true }) });
  const visto = [];
  const api = async (ruta, op) => {
    visto.push({ ruta, op });
    if (ruta === "/chat/swe/capacidades") return TODOS_OK;
    if (ruta === "/chat/swe/iniciar") return respuestaHarness({ task_id: cuerpoDe(op).task_id, estado: "EJECUTANDO", paso_actual: "escribe" });
    if (ruta === "/chat/swe/avanzar") return respuestaHarness(visto.filter((x) => x.ruta === "/chat/swe/avanzar").length < 2 ? { task_id: cuerpoDe(op).task_id, estado: "VERIFICANDO", paso_actual: 3 } : { task_id: cuerpoDe(op).task_id, estado: "DONE", paso_actual: 4, resultado_tool: "Proyecto revisado", evidencia: ["git diff: 2 archivos"], pasos_terminados: [{ paso: "ejecuta", agente: "swe-agent", recibo: "r-1", herramientas: ["swe-agent"], resultado: "ok" }, { paso: "verifica", agente: "openhands", recibo: "r-2", herramientas: [], resultado: "verificado" }] });
    throw new Error("ruta inesperada " + ruta);
  };
  const r = await S.enviarTareaSwe(api, { mensaje: "Revisar proyecto", sesion: "chat-001", proyecto: "yaiwes" });
  const ini = visto.find((x) => x.ruta === "/chat/swe/iniciar");
  assert.equal(ini.op.method, "POST");
  assert.deepEqual(Object.keys(ini.op.body).sort(), [...CAMPOS].sort());
  assert.equal(ini.op.body.workflow, "swe_code"); assert.equal(ini.op.body.origen, "yaiwes");
  const av = visto.filter((x) => x.ruta === "/chat/swe/avanzar");
  assert.equal(av.length, 2); assert.equal(av[0].op.body.task_id, ini.op.body.task_id);
  assert.deepEqual(Object.keys(av[0].op.body).sort(), ["origen", "proyecto", "sesion", "task_id"]);
  assert.match(r.reply, /Proyecto revisado/); assert.match(r.reply, /git diff: 2 archivos/); assert.match(r.reply, /recibo ejecuta \(swe-agent\): r-1/); assert.match(r.reply, /recibo verifica \(openhands\): r-2/);
  assert.equal(r.estado, "DONE"); assert.equal(r.task_id, ini.op.body.task_id); assert.deepEqual(r.tools, ["swe-agent"]);
  assert.match(r.nota, /swe_code/); assert.match(r.nota, new RegExp(r.task_id));
  delete globalThis.localStorage;
});

test("enviarTareaSwe: con un agente NO DISPONIBLE no llama a iniciar y lo dice (sin cambiar a otro modelo ni agente)", async () => {
  conStorage({ riu_swe_seleccion: JSON.stringify({ ...S.SEL_DEFECTO, modo_agentico: true }) });
  const rutas = [];
  const api = async (ruta) => { rutas.push(ruta); if (ruta === "/chat/swe/capacidades") return { harness: "ok", agentes: { openclaw: { disponible: true }, "swe-agent": { disponible: false, motivo: "SWE-agent no instalado" } } }; throw new Error("no debia llamarse " + ruta); };
  await assert.rejects(() => S.enviarTareaSwe(api, { mensaje: "x", sesion: "s" }), /GAP: SELECCION_NO_DISPONIBLE.*SWE-agent.*NO DISPONIBLE/);
  assert.deepEqual(rutas, ["/chat/swe/capacidades"]);
  delete globalThis.localStorage;
});

test("enviarTareaSwe: si no se pueden leer las capacidades tampoco se presenta como funcional", async () => {
  conStorage({ riu_swe_seleccion: JSON.stringify({ ...S.SEL_DEFECTO, workflow: "liquid_mirror" }) });
  const api = async (ruta) => { if (ruta === "/chat/swe/capacidades") throw new Error("HTTP 503"); throw new Error("no debia llamarse " + ruta); };
  await assert.rejects(() => S.enviarTareaSwe(api, { mensaje: "x", sesion: "s" }), /GAP: SELECCION_NO_DISPONIBLE/);
  delete globalThis.localStorage;
});

test("enviarTareaSwe: REQUIERE_APROBACION se detiene (no avanza ni aprueba solo), dice que se aprueba y devuelve task_id y op_id", async () => {
  conStorage({ riu_swe_seleccion: JSON.stringify({ ...S.SEL_DEFECTO, workflow: "swe_code", modo_agentico: true }) });
  const rutas = [];
  const pendiente = { op_id: "0123456789abcdef", paso: "escribe", agente: "codex", modelo: "hf/qwen2.5-coder-1.5b", permisos: { escritura: true, ejecucion: false }, objetivo: "Voy a editar el repo" };
  const api = async (ruta, op) => { rutas.push(ruta); if (ruta === "/chat/swe/capacidades") return TODOS_OK; return respuestaHarness({ task_id: cuerpoDe(op).task_id, estado: "REQUIERE_APROBACION", paso_actual: 0, pendiente_aprobacion: pendiente }); };
  const r = await S.enviarTareaSwe(api, { mensaje: "Revisar y desplegar", sesion: "s" });
  assert.deepEqual(rutas, ["/chat/swe/capacidades", "/chat/swe/iniciar"]);
  assert.equal(r.estado, "REQUIERE_APROBACION"); assert.equal(r.requiere_aprobacion, true); assert.ok(r.task_id);
  assert.equal(r.pendiente.op_id, "0123456789abcdef");
  assert.match(r.reply, /aprobaci/i); assert.match(r.reply, /escribe/); assert.match(r.reply, /codex/); assert.match(r.reply, /escritura/); assert.match(r.reply, /Voy a editar el repo/);
  delete globalThis.localStorage;
});

test("enviarTareaSwe: RECONCILIAR (operacion iniciada sin confirmar) es un error visible; no se reintenta ni se da por hecha", async () => {
  conStorage({ riu_swe_seleccion: JSON.stringify({ ...S.SEL_DEFECTO, workflow: "swe_code", modo_agentico: true }) });
  const api = async (ruta, op) => (ruta === "/chat/swe/capacidades" ? TODOS_OK : respuestaHarness({ task_id: cuerpoDe(op).task_id, estado: "RECONCILIAR", pendiente_reconciliacion: { op_id: "aaaabbbbccccdddd", paso: "ejecuta", motivo: "OPERACION_SIN_CONFIRMAR" }, error: { codigo: "OPERACION_SIN_CONFIRMAR", mensaje: "quedo iniciada" } }));
  await assert.rejects(() => S.enviarTareaSwe(api, { mensaje: "x", sesion: "s" }), /GAP: RECONCILIAR.*aaaabbbbccccdddd.*OPERACION_SIN_CONFIRMAR/);
  delete globalThis.localStorage;
});

test("enviarTareaSwe: estado GAP o error del backend es un error visible, no una respuesta del modelo", async () => {
  conStorage({ riu_swe_seleccion: JSON.stringify({ ...S.SEL_DEFECTO, workflow: "swe_code" }) });
  const gap = async (ruta, op) => (ruta === "/chat/swe/capacidades" ? TODOS_OK : respuestaHarness({ task_id: cuerpoDe(op).task_id, estado: "GAP", error: { codigo: "AGENTE_NO_INSTALADO", mensaje: "Codex no esta instalado", paso: "escribe" } }));
  await assert.rejects(() => S.enviarTareaSwe(gap, { mensaje: "x", sesion: "s" }), /GAP: AGENTE_NO_INSTALADO.*Codex no esta instalado/);
  const caido = async (ruta) => { if (ruta === "/chat/swe/capacidades") return TODOS_OK; throw new Error("SWE_HARNESS_ERROR"); };
  await assert.rejects(() => S.enviarTareaSwe(caido, { mensaje: "x", sesion: "s" }), /GAP: SWE_HARNESS_ERROR/);
  delete globalThis.localStorage;
});

test("enviarTareaSwe: el avance esta acotado (no gira para siempre) y no pasa claves por el cuerpo", async () => {
  conStorage({ riu_swe_seleccion: JSON.stringify({ ...S.SEL_DEFECTO, workflow: "swe_code" }), riu_swe_claves: JSON.stringify({ groq: "gsk_SECRETA" }) });
  const cuerpos = [];
  const api = async (ruta, op) => { if (ruta === "/chat/swe/capacidades") return TODOS_OK; cuerpos.push(JSON.stringify(op.body)); return respuestaHarness({ task_id: op.body.task_id, estado: "EJECUTANDO" }); };
  await assert.rejects(() => S.enviarTareaSwe(api, { mensaje: "x", sesion: "s" }), /GAP: SWE_SIN_PROGRESO/);
  assert.ok(cuerpos.length <= S.MAX_AVANCES + 1);
  assert.ok(cuerpos.every((c) => !c.includes("gsk_SECRETA")));
  delete globalThis.localStorage;
});

test("aprobarTareaSwe / reanudarTareaSwe / estadoTareaSwe: operaciones por task_id; aprobar manda op_id y NO el campo aprobacion ni un operador", async () => {
  conStorage();
  const visto = [];
  const api = async (ruta, op) => { visto.push({ ruta, body: op.body }); return respuestaHarness({ task_id: op.body.task_id, estado: "CONTINUAR" }); };
  await S.aprobarTareaSwe(api, { task_id: "yaiwes-001", op_id: "op-1", sesion: "s", proyecto: "p" });
  await S.reanudarTareaSwe(api, { task_id: "yaiwes-001", sesion: "s", proyecto: "p" });
  const e = await S.estadoTareaSwe(api, { task_id: "yaiwes-001", sesion: "s", proyecto: "p" });
  assert.deepEqual(visto.map((v) => v.ruta), ["/chat/swe/aprobar", "/chat/swe/reanudar", "/chat/swe/estado"]);
  assert.ok(visto.every((v) => !("aprobacion" in v.body) && !("operador" in v.body) && v.body.origen === "yaiwes" && v.body.task_id === "yaiwes-001"));
  assert.equal(visto[0].body.op_id, "op-1"); assert.ok(!("op_id" in visto[1].body));
  assert.equal(e.estado, "CONTINUAR");
  await assert.rejects(() => S.estadoTareaSwe(api, { task_id: "../x", sesion: "s" }), /TASK_ID_INVALIDO/);
  await assert.rejects(() => S.aprobarTareaSwe(api, { task_id: "yaiwes-001", sesion: "s" }), /OP_ID_INVALIDO/);
  delete globalThis.localStorage;
});

test("idCatalogo: el modelo del selector clasico se traduce al id del catalogo (hf/...) o es null si no esta registrado", () => {
  assert.equal(S.idCatalogo("hf-liquid-lfm25"), "hf/lfm2.5-350m");
  assert.equal(S.idCatalogo("swe-codex-qwen25-15b"), "hf/qwen2.5-coder-1.5b");
  assert.equal(S.idCatalogo("qwen3-0.6b"), "hf/qwen3-0.6b");
  assert.equal(S.idCatalogo("nvidia/z-ai/glm-5.3"), "nvidia/z-ai/glm-5.3");
  assert.equal(S.idCatalogo("web-qwen38max"), null);
  assert.equal(S.idCatalogo("swecode-asesoria"), null);
});

test("aprobarYContinuarSwe: aprueba (el servidor identifica al operador) y sigue avanzando con el mismo task_id hasta DONE", async () => {
  conStorage({ riu_swe_seleccion: JSON.stringify({ ...S.SEL_DEFECTO, workflow: "swe_code", modo_agentico: true }) });
  const rutas = [];
  const api = async (ruta, op) => { rutas.push(ruta); return respuestaHarness(ruta === "/chat/swe/avanzar" ? { task_id: op.body.task_id, estado: "DONE", resultado_tool: "desplegado", evidencia: ["recibo:r2"] } : { task_id: op.body.task_id, estado: "CONTINUAR" }); };
  const r = await S.aprobarYContinuarSwe(api, { task_id: "yaiwes-009", op_id: "op-9", sesion: "s", proyecto: "p" });
  assert.deepEqual(rutas, ["/chat/swe/aprobar", "/chat/swe/avanzar"]);
  assert.equal(r.estado, "DONE"); assert.match(r.reply, /desplegado/); assert.match(r.nota, /yaiwes-009/);
  await assert.rejects(() => S.aprobarYContinuarSwe(api, { task_id: "mal id", op_id: "op-9", sesion: "s" }), /TASK_ID_INVALIDO/);
  delete globalThis.localStorage;
});

test("Liquid Mirror: la nota dice que S2 y S3 corren en secuencia (no se afirma paralelismo) y nombra los servidores reales de cada paso", async () => {
  conStorage({ riu_swe_seleccion: JSON.stringify({ ...S.SEL_DEFECTO, workflow: "liquid_mirror" }) });
  const api = async (ruta, op) => (ruta === "/chat/swe/capacidades" ? TODOS_OK : respuestaHarness({ task_id: cuerpoDe(op).task_id, estado: "DONE", ejecucion_s2_s3: "secuencial", resultado_tool: "", pasos_terminados: [{ paso: "liquid1", servidor: "S2", recibo: "s2-1", resultado: "lectura" }, { paso: "liquid2", servidor: "S3", recibo: "s3-1", resultado: "ejecucion lista" }] }));
  const r = await S.enviarTareaSwe(api, { mensaje: "x", sesion: "s" });
  assert.match(r.reply, /ejecucion lista/); assert.match(r.reply, /liquid1.*S2.*s2-1/); assert.match(r.reply, /liquid2.*S3.*s3-1/); assert.match(r.nota, /secuencial/);
  delete globalThis.localStorage;
});

test("enviarTareaSwe avisa de cada paso (alPaso) para pintar el progreso real en la burbuja: iniciar, cada avanzar, con estado y paso", async () => {
  conStorage({ riu_swe_seleccion: JSON.stringify({ ...S.SEL_DEFECTO, workflow: "swe_code" }) });
  let n = 0;
  const api = async (ruta, op) => { if (ruta === "/chat/swe/capacidades") return TODOS_OK; n++; return respuestaHarness({ task_id: op.body.task_id, estado: n < 3 ? "EJECUTANDO" : "DONE", paso_actual: n, plan: [{ paso: "escribe" }, { paso: "revisa" }, { paso: "ejecuta" }], resultado_tool: "ok" }); };
  const vistos = [];
  await S.enviarTareaSwe(api, { mensaje: "x", sesion: "s", alPaso: (t) => vistos.push(t) });
  assert.equal(vistos.length, 3); assert.ok(vistos.every((t) => /SWE/.test(t)));
  assert.match(vistos[0], /EJECUTANDO/); assert.match(vistos[2], /DONE/);
  delete globalThis.localStorage;
});
