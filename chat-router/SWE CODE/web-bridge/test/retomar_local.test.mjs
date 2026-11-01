// Pruebas de retomar_local.js: checkpoint universal para modelos locales HF, Groq y NVIDIA.
// Servidores falsos (node:http) para S1/S2/Groq y para el Harness DeepSeek; claves FALSAS.
import test from "node:test";
import assert from "node:assert/strict";
import http from "node:http";
import fs from "node:fs";
import os from "node:os";
import path from "node:path";
import { retomarLocal, retomarPorId, huellaDe, TIPO, MAX_VUELTAS } from "../src/retomar_local.js";
import { guardarCheckpoint, leerCheckpoint } from "../src/checkpoint_hf.js";
import { BASES, limpiarEstado, limpiarClaves } from "../src/respaldo.js";

const CONT = "Continúa exactamente donde terminó, sin repetir";
const KGROQ = "gsk_FAKEKEYNOREAL1234567890", KHARNESS = "acceso-falso-harness-123";
const MODELO = "qwen2.5-coder-1.5b";
const msgs = [{ role: "user", content: "escribe la funcion A" }];
const ok = (content, finish_reason = "stop", extra = {}) => ({ status: 200, json: { choices: [{ finish_reason, message: { role: "assistant", content, ...extra } }] } });
const tmp = () => fs.mkdtempSync(path.join(os.tmpdir(), "rl-"));
const rapido = { continuaciones: 0, esperar: async () => {} };

// servidor de modelo falso: handler({url, body, auth, n}) -> {status, json}; n = nº de peticion de chat
const fake = (handler) => new Promise((listo) => {
  const chat = []; let n = 0;
  const s = http.createServer((req, res) => {
    let d = ""; req.on("data", (c) => d += c); req.on("end", () => {
      const v = { url: req.url, auth: req.headers.authorization, body: d ? JSON.parse(d) : null };
      if (v.url.endsWith("/chat/completions")) { chat.push(v); n++; }
      const r = handler({ ...v, n }) || { status: 404, json: {} };
      res.writeHead(r.status, { "content-type": "application/json" }); res.end(JSON.stringify(r.json ?? {}));
    });
  }).listen(0, "127.0.0.1", () => listo({ chat, url: `http://127.0.0.1:${s.address().port}`, cerrar: () => { s.closeAllConnections?.(); s.close(); } }));
});

// Harness falso (guardar/leer reales)
const harness = () => new Promise((listo) => {
  const almacen = new Map(), crudos = [];
  const s = http.createServer((req, res) => {
    let d = ""; req.on("data", (c) => d += c); req.on("end", () => {
      crudos.push(d); const b = JSON.parse(d); const json = (o) => { res.writeHead(200, { "content-type": "application/json" }); res.end(JSON.stringify(o)); };
      if (req.headers["x-api-key"] !== KHARNESS) return json({ status: "error", error: "clave de acceso invalida" });
      if (b.tool === "guardar") { almacen.set(b.args.nombre, b.args.valor); return json({ status: "ok", result: { nombre: b.args.nombre } }); }
      return almacen.has(b.args.nombre) ? json({ status: "ok", result: { nombre: b.args.nombre, valor: almacen.get(b.args.nombre) } }) : json({ status: "error", error: "no encontrado" });
    });
  }).listen(0, "127.0.0.1", () => listo({ almacen, crudos, url: `http://127.0.0.1:${s.address().port}`, cerrar: () => { s.closeAllConnections?.(); s.close(); } }));
});

const env = (dir, extra = {}) => ({ BRIDGE_STATE_DIR: dir, ...extra });
const extra = (e, mas = {}) => ({ env: e, opts: rapido, ...mas });
const archivo = (dir, id) => path.join(dir, "checkpoints", `${id}.json`);
const leerArch = (dir, id) => JSON.parse(fs.readFileSync(archivo(dir, id), "utf8"));
const base0 = { groq: BASES.groq, nvidia: BASES.nvidia };

test.beforeEach(() => { limpiarEstado(); limpiarClaves(); });
test.afterEach(() => Object.assign(BASES, base0));

test("una tarea simple: responde, guarda el checkpoint (RESPUESTA_COMPLETA hasta confirmar -> DONE) y no lleva claves", async () => {
  const s1 = await fake(() => ok("LISTO")); const dir = tmp();
  try {
    const r = await retomarLocal("t-simple", MODELO, msgs, extra(env(dir, { SWECODE_URL_S1: s1.url }), { confirmarCompleta: true }));
    assert.equal(r.salida, "LISTO"); assert.equal(r.finish_reason, "stop"); assert.equal(r.via, "hf-local"); assert.equal(r.usado, MODELO);
    assert.equal(r.estado, "DONE"); assert.equal(r.desde_checkpoint, false);
    const ck = leerArch(dir, "t-simple");
    assert.equal(ck.tipo, TIPO); assert.equal(ck.estado, "DONE"); assert.equal(ck.completo, true); assert.equal(ck.modelo, MODELO);
    assert.equal(ck.huella, huellaDe(MODELO, msgs));
    assert.equal(ck.secciones.length, 1);
  } finally { s1.cerrar(); }
});

test("terminado: el segundo llamado devuelve lo guardado SIN llamar al modelo", async () => {
  const s1 = await fake(({ n }) => ok("RESPUESTA-" + n)); const dir = tmp();
  try {
    const e = extra(env(dir, { SWECODE_URL_S1: s1.url }), { confirmarCompleta: true });
    const a = await retomarLocal("t-fin", MODELO, msgs, e);
    const b = await retomarLocal("t-fin", MODELO, msgs, e);
    assert.equal(s1.chat.length, 1);
    assert.equal(b.salida, a.salida); assert.equal(b.desde_checkpoint, true); assert.equal(b.estado, "DONE");
  } finally { s1.cerrar(); }
});

test("reinicio simulado: el 2º llamado con el mismo tarea_id continua desde el checkpoint (Harness) y no repite la seccion", async () => {
  const h = await harness(); const dir1 = tmp(), dir2 = tmp();
  let fase = 1;  // fase 1: solo la 1ª peticion responde (length) y despues el modelo se cae; fase 2: el modelo vuelve
  const s1 = await fake(({ body, n }) => fase === 1 ? (n === 1 ? ok("AAA", "length") : { status: 500, json: {} }) : body.messages.at(-1).content === CONT ? ok("-BBB", "stop") : ok("AAA", "length"));
  try {
    const hv = { RIU_DEEPSEEK_HARNESS_URL: h.url, RIU_API_KEY: KHARNESS };
    // 1ª ejecucion: la seccion 1 sale, la 2 se cae el modelo y no hay respaldo -> error, pero el checkpoint de la seccion 1 ya esta guardado
    await assert.rejects(retomarLocal("t-reinicio", MODELO, msgs, extra(env(dir1, { SWECODE_URL_S1: s1.url, ...hv }))), { code: "RESPALDO_AGOTADO" });
    const ck1 = await leerCheckpoint("t-reinicio", { env: env(dir1, hv) });
    assert.equal(ck1.parcial, "AAA"); assert.equal(ck1.secciones.length, 1); assert.equal(ck1.estado, "ERROR");
    // reinicio: disco nuevo (dir2) -> solo el Harness conserva el checkpoint; el modelo vuelve
    fase = 2; s1.chat.length = 0;
    const r = await retomarLocal("t-reinicio", MODELO, msgs, extra(env(dir2, { SWECODE_URL_S1: s1.url, ...hv }), { confirmarCompleta: true }));
    assert.equal(r.salida, "AAA-BBB"); assert.equal(r.estado, "DONE"); assert.equal(r.reanudado, true);
    assert.equal(s1.chat.length, 1, "una sola peticion: la seccion 1 no se repite");
    assert.deepEqual(s1.chat[0].body.messages, [...msgs, { role: "assistant", content: "AAA" }, { role: "user", content: CONT }]);
    assert.equal(JSON.parse([...h.almacen.values()][0]).estado, "DONE");
  } finally { s1.cerrar(); h.cerrar(); }
});

test("caida de S1: pasa a S2 (via hf-local) y el checkpoint lo anota", async () => {
  const s1 = await fake(() => ({ status: 500, json: {} })), s2 = await fake(() => ok("DE-S2")); const dir = tmp();
  try {
    const r = await retomarLocal("t-s2", MODELO, msgs, extra(env(dir, { SWECODE_URL_S1: s1.url, SWECODE_URL_S2: s2.url })));
    assert.equal(r.salida, "DE-S2"); assert.equal(r.via, "hf-local"); assert.equal(s1.chat.length, 1); assert.equal(s2.chat.length, 1);
  } finally { s1.cerrar(); s2.cerrar(); }
});

test("respuesta truncada (length): continua solo mientras sea length, concatena y se detiene en stop", async () => {
  const s1 = await fake(({ n }) => n < 4 ? ok("p" + n, "length") : ok("FIN", "stop")); const dir = tmp();
  try {
    const r = await retomarLocal("t-len", MODELO, msgs, extra(env(dir, { SWECODE_URL_S1: s1.url })));
    assert.equal(r.salida, "p1p2p3FIN"); assert.equal(s1.chat.length, 4); assert.equal(r.finish_reason, "stop"); assert.equal(r.secciones, 4);
    assert.deepEqual(s1.chat[2].body.messages.slice(-2), [{ role: "assistant", content: "p1p2" }, { role: "user", content: CONT }]);
    assert.deepEqual(s1.chat[0].body.messages, msgs);
  } finally { s1.cerrar(); }
  // un stop NO continua
  const s2 = await fake(() => ok("completo", "stop"));
  try { await retomarLocal("t-stop", MODELO, msgs, extra(env(tmp(), { SWECODE_URL_S1: s2.url }))); assert.equal(s2.chat.length, 1); } finally { s2.cerrar(); }
});

test("tope de 12 vueltas; al agotarlo devuelve lo parcial (length) y el siguiente llamado sigue desde ahi", async () => {
  assert.equal(MAX_VUELTAS, 12);
  const s1 = await fake(() => ok("x", "length")); const dir = tmp();
  try {
    const e = extra(env(dir, { SWECODE_URL_S1: s1.url }));
    const r = await retomarLocal("t-tope", MODELO, msgs, e);
    assert.equal(s1.chat.length, 12); assert.equal(r.finish_reason, "length"); assert.equal(r.salida, "x".repeat(12)); assert.equal(r.estado, "CONTINUAR");
    const r2 = await retomarLocal("t-tope", MODELO, msgs, e);
    assert.equal(s1.chat.length, 24); assert.equal(r2.salida, "x".repeat(24));
  } finally { s1.cerrar(); }
});

test("cambio de API: el local se cae a mitad de tarea y sigue por Groq con el texto ya generado; contexto separado por modelo; sin claves", async () => {
  const s1 = await fake(({ n }) => n === 1 ? ok("AAA", "length") : { status: 500, json: {} });
  const groq = await fake(({ url }) => url.endsWith("/models") ? { status: 200, json: { data: [] } } : ok("-DESDE-GROQ", "stop"));
  const dir = tmp(); BASES.groq = groq.url;
  try {
    const e = extra(env(dir, { SWECODE_URL_S1: s1.url, GROQ_API_KEY: KGROQ }));
    const r = await retomarLocal("t-api", MODELO, msgs, e);
    assert.equal(r.salida, "AAA-DESDE-GROQ"); assert.equal(r.via, "groq");
    assert.deepEqual(groq.chat[0].body.messages, [...msgs, { role: "assistant", content: "AAA" }, { role: "user", content: CONT }]);
    assert.equal(groq.chat[0].auth, "Bearer " + KGROQ);
    const ck = leerArch(dir, "t-api");
    assert.deepEqual(ck.secciones.map((s) => s.via), ["hf-local", "groq"]);
    assert.deepEqual(Object.keys(ck.contextos).sort(), [MODELO, groq.chat[0].body.model.startsWith("groq/") ? groq.chat[0].body.model : "groq/" + groq.chat[0].body.model].sort());
    assert.ok(!fs.readFileSync(archivo(dir, "t-api"), "utf8").includes(KGROQ), "sin claves en el checkpoint");
  } finally { s1.cerrar(); groq.cerrar(); }
});

test("modelo groq/qwen/qwen3.8-27b va directo por Groq con la clave; si falla, respaldo", async () => {
  const groq = await fake(() => ok("DIRECTO")); const dir = tmp(); BASES.groq = groq.url;
  try {
    const r = await retomarLocal("t-groq", "groq/qwen/qwen3.8-27b", msgs, extra(env(dir, { GROQ_API_KEY: KGROQ })));
    assert.equal(r.salida, "DIRECTO"); assert.equal(r.via, "groq"); assert.equal(r.usado, "groq/qwen/qwen3.8-27b"); assert.equal(groq.chat[0].body.model, "qwen/qwen3.8-27b");
  } finally { groq.cerrar(); }
});

test("checkpoint de OTRA tarea con el mismo id se rechaza (CHECKPOINT_OTRA_TAREA) y no se toca ni se llama al modelo", async () => {
  const s1 = await fake(() => ok("X")); const dir = tmp();
  try {
    const e = extra(env(dir, { SWECODE_URL_S1: s1.url }));
    await retomarLocal("t-otra", MODELO, msgs, e);
    const antes = fs.readFileSync(archivo(dir, "t-otra"), "utf8"); s1.chat.length = 0;
    await assert.rejects(retomarLocal("t-otra", MODELO, [{ role: "user", content: "OTRA COSA" }], e), { code: "CHECKPOINT_OTRA_TAREA" });
    await assert.rejects(retomarLocal("t-otra", "qwen3-0.6b", msgs, e), { code: "CHECKPOINT_OTRA_TAREA" });
    assert.equal(s1.chat.length, 0); assert.equal(fs.readFileSync(archivo(dir, "t-otra"), "utf8"), antes);
    // un archivo que no es de este sistema (p. ej. una seccion web con el mismo nombre) tambien cuenta como otra tarea
    fs.writeFileSync(archivo(dir, "web1"), JSON.stringify({ modo: "solucion", modelo: "qwen38max", texto: "t", total: 2, enviados: 1 }));
    await assert.rejects(retomarLocal("web1", MODELO, msgs, e), { code: "CHECKPOINT_OTRA_TAREA" });
  } finally { s1.cerrar(); }
});

test("ids y modelos invalidos", async () => {
  await assert.rejects(retomarLocal("../x", MODELO, msgs, extra(env(tmp()))), { code: "TAREA_ID_INVALIDO" });
  await assert.rejects(retomarLocal("ok", "web-qwen38max", msgs, extra(env(tmp()))), { code: "MODELO_NO_SOPORTADO" });
});

// ---------- herramientas ----------
const tc = (id, name = "escribir", args = '{"x":1}') => ({ id, type: "function", function: { name, arguments: args } });

test("no ejecuta herramientas si el Harness configurado no confirma checkpoint remoto", async () => {
  const modelo = await fake(() => ok("", "tool_calls", { content: null, tool_calls: [
    { id: "x1", type: "function", function: { name: "escribir", arguments: '{}' } }
  ] }));
  const dir = tmp(), llamadas = [];
  try {
    const e = extra(env(dir, { SWECODE_URL_S1: modelo.url,
      RIU_DEEPSEEK_HARNESS_URL: "http://127.0.0.1:9", RIU_API_KEY: KHARNESS }), {
      sinRespaldo: true, ejecutarHerramienta: async (t) => { llamadas.push(t.id); return "MAL"; },
      tools: [{ type: "function", function: { name: "escribir" } }], timeoutCheckpointMs: 200,
    });
    await assert.rejects(retomarLocal("t-sin-remoto", MODELO, msgs, e), { code: "CHECKPOINT_REMOTO_REQUERIDO" });
    assert.deepEqual(llamadas, []);
    const st = await leerCheckpoint("t-sin-remoto", { env: e.env });
    assert.equal(st.lote.herramientas[0].estado, "iniciada");
  } finally { modelo.cerrar(); }
});

test("tool_calls con ejecutor: cada herramienta se ejecuta UNA sola vez, su resultado se guarda y el 2º llamado no la repite", async () => {
  const s1 = await fake(({ n }) => n === 1 ? ok("", "tool_calls", { content: null, tool_calls: [tc("c1"), tc("c2", "leer", "{}")] }) : ok("HECHO"));
  const dir = tmp(); const vistas = [];
  const ejecutarHerramienta = async (t) => { vistas.push(t.id); return { ok: t.id }; };
  try {
    const e = extra(env(dir, { SWECODE_URL_S1: s1.url }), { ejecutarHerramienta, confirmarCompleta: true, tools: [{ type: "function", function: { name: "escribir" } }] });
    const r = await retomarLocal("t-tool", MODELO, msgs, e);
    assert.deepEqual(vistas, ["c1", "c2"]); assert.equal(r.salida, "HECHO"); assert.equal(r.estado, "DONE");
    const m2 = s1.chat[1].body.messages;
    assert.equal(m2.at(-3).role, "assistant"); assert.deepEqual(m2.at(-3).tool_calls.map((t) => t.id), ["c1", "c2"]);
    assert.deepEqual(m2.slice(-2).map((m) => [m.role, m.tool_call_id, m.content]), [["tool", "c1", '{"ok":"c1"}'], ["tool", "c2", '{"ok":"c2"}']]);
    assert.deepEqual(s1.chat[0].body.tools, [{ type: "function", function: { name: "escribir" } }]);
    await retomarLocal("t-tool", MODELO, msgs, e);
    assert.deepEqual(vistas, ["c1", "c2"], "no se repiten");
    const ck = leerArch(dir, "t-tool");
    assert.deepEqual(Object.keys(ck.herramientas).sort(), ["c1", "c2"]); assert.deepEqual(ck.herramientas.c1.resultado, { ok: "c1" });
  } finally { s1.cerrar(); }
});

const sembrar = async (dir, id, estado, hv = {}) => guardarCheckpoint(id, { tipo: TIPO, version: 1, tarea_id: id, huella: huellaDe(MODELO, msgs), modelo: MODELO, mensajes: msgs, completo: false, conversacion: [], parcial: "", secciones: [{ n: 1 }], contextos: {}, herramientas: {}, ...estado }, { env: env(dir, hv) });
const lote = (...ts) => ({ assistant: { role: "assistant", content: null, tool_calls: ts.map((x) => tc(x)) }, herramientas: ts.map((x) => ({ id: x, nombre: "escribir", argumentos: '{"x":1}', estado: "pendiente" })) });

test("WAIT_TOOLS tras un corte: la herramienta ya hecha NO se repite, solo se ejecuta la pendiente", async () => {
  const s1 = await fake(() => ok("FIN")); const dir = tmp(); const vistas = [];
  try {
    const l = lote("a1", "a2"); l.herramientas[0].estado = "hecha";
    await sembrar(dir, "t-wait", { estado: "WAIT_TOOLS", lote: l, herramientas: { a1: { resultado: "R1", ts: "2026-01-01T00:00:00.000Z" } } });
    const r = await retomarLocal("t-wait", MODELO, msgs, extra(env(dir, { SWECODE_URL_S1: s1.url }), { ejecutarHerramienta: async (t) => { vistas.push(t.id); return "R-" + t.id; } }));
    assert.deepEqual(vistas, ["a2"]); assert.equal(r.salida, "FIN");
    const m = s1.chat[0].body.messages.filter((x) => x.role === "tool");
    assert.deepEqual(m.map((x) => [x.tool_call_id, x.content]), [["a1", '"R1"'], ["a2", '"R-a2"']]);
  } finally { s1.cerrar(); }
});

test("herramienta sin confirmar (iniciada y sin resultado): VERIFICAR_HERRAMIENTAS_PENDIENTES; con verificador se reutiliza o se reintenta", async () => {
  const s1 = await fake(() => ok("FIN")); const dir = tmp(); const vistas = [];
  const ejecutarHerramienta = async (t) => { vistas.push(t.id); return "R-" + t.id; };
  try {
    const l = lote("z1"); l.herramientas[0].estado = "iniciada";
    await sembrar(dir, "t-ver", { estado: "WAIT_TOOLS", lote: l });
    const e = extra(env(dir, { SWECODE_URL_S1: s1.url }), { ejecutarHerramienta });
    await assert.rejects(retomarLocal("t-ver", MODELO, msgs, e), (err) => err.code === "VERIFICAR_HERRAMIENTAS_PENDIENTES" && /z1/.test(err.message));
    assert.deepEqual(vistas, []); assert.equal(s1.chat.length, 0);
    assert.equal(leerArch(dir, "t-ver").estado, "WAIT_TOOLS", "el checkpoint sigue igual");
    // el verificador dice que SI se hizo -> se usa su resultado y NO se vuelve a ejecutar
    const r = await retomarLocal("t-ver", MODELO, msgs, { ...e, verificarHerramienta: async () => ({ hecha: true, resultado: "YA-HECHA" }) });
    assert.deepEqual(vistas, []); assert.equal(r.salida, "FIN");
    assert.ok(s1.chat[0].body.messages.some((m) => m.role === "tool" && m.content === '"YA-HECHA"'));
    // el verificador dice que NO se hizo -> se reintenta una vez
    await sembrar(dir, "t-ver2", { estado: "WAIT_TOOLS", lote: l });
    await retomarLocal("t-ver2", MODELO, msgs, { ...e, verificarHerramienta: async () => ({ hecha: false }) });
    assert.deepEqual(vistas, ["z1"]);
  } finally { s1.cerrar(); }
});

test("tool_calls sin ejecutor (el Harness las corre): se devuelven con ids estables y el reintento NO vuelve a llamar al modelo", async () => {
  const s1 = await fake(() => ok("", "tool_calls", { content: null, tool_calls: [tc("w1")] })); const dir = tmp();
  try {
    const e = extra(env(dir, { SWECODE_URL_S1: s1.url }));
    const a = await retomarLocal("t-harn", MODELO, msgs, e);
    assert.equal(a.finish_reason, "tool_calls"); assert.equal(a.estado, "WAIT_TOOLS"); assert.deepEqual(a.tool_calls.map((t) => t.id), ["w1"]);
    const b = await retomarLocal("t-harn", MODELO, msgs, e);
    assert.equal(s1.chat.length, 1); assert.deepEqual(b.tool_calls, a.tool_calls); assert.equal(b.desde_checkpoint, true);
  } finally { s1.cerrar(); }
});

test("ids de herramienta repetidos entre modelos se hacen unicos (un id ya usado no se toma por hecho)", async () => {
  const s1 = await fake(({ n }) => n <= 2 ? ok("", "tool_calls", { content: null, tool_calls: [tc("call_1", "f", JSON.stringify({ n }))] }) : ok("FIN")); const dir = tmp(); const vistas = [];
  try {
    await retomarLocal("t-uniq", MODELO, msgs, extra(env(dir, { SWECODE_URL_S1: s1.url }), { ejecutarHerramienta: async (t) => { vistas.push(t.argumentos); return "r"; } }));
    assert.deepEqual(vistas, ['{"n":1}', '{"n":2}'], "las dos llamadas distintas con el mismo id se ejecutan");
    assert.equal(new Set(Object.keys(leerArch(dir, "t-uniq").herramientas)).size, 2);
  } finally { s1.cerrar(); }
});

// ---------- sin claves / concurrencia / retomar por id ----------
test("sin claves: ni el checkpoint local ni lo enviado al Harness llevan claves (aunque el modelo o el usuario las repitan)", async () => {
  const h = await harness(); const dir = tmp(); BASES.groq = "http://127.0.0.1:9";
  const s1 = await fake(() => ok(`tu clave es ${KGROQ} y Authorization: Bearer ${KGROQ}`));
  try {
    const mensajes = [{ role: "user", content: `usa mi clave ${KGROQ}`, authorization: "Bearer " + KGROQ }];
    const e = extra(env(dir, { SWECODE_URL_S1: s1.url, GROQ_API_KEY: KGROQ, RIU_DEEPSEEK_HARNESS_URL: h.url, RIU_API_KEY: KHARNESS }));
    await retomarLocal("t-claves", MODELO, mensajes, e);
    const textos = [fs.readFileSync(archivo(dir, "t-claves"), "utf8"), ...h.crudos];
    for (const t of textos) for (const mal of ["FAKEKEYNOREAL", KHARNESS]) assert.ok(!t.includes(mal), mal);
    await retomarLocal("t-claves", MODELO, mensajes, e);  // la huella sigue siendo estable aunque el mensaje lleve una clave
  } finally { s1.cerrar(); h.cerrar(); }
});

test("el error final no filtra claves", async () => {
  BASES.groq = "http://127.0.0.1:9"; BASES.nvidia = "http://127.0.0.1:9";
  await assert.rejects(retomarLocal("t-err", MODELO, msgs, extra(env(tmp(), { GROQ_API_KEY: KGROQ }))), (e) => e.code === "RESPALDO_AGOTADO" && !e.message.includes("FAKEKEYNOREAL"));
});

test("dos llamados simultaneos con el mismo tarea_id: el modelo se llama una sola vez", async () => {
  const s1 = await fake(() => ok("UNA-VEZ")); const dir = tmp();
  try {
    const e = extra(env(dir, { SWECODE_URL_S1: s1.url }));
    const [a, b] = await Promise.all([retomarLocal("t-conc", MODELO, msgs, e), retomarLocal("t-conc", MODELO, msgs, e)]);
    assert.equal(s1.chat.length, 1); assert.equal(a.salida, "UNA-VEZ"); assert.equal(b.salida, "UNA-VEZ");
  } finally { s1.cerrar(); }
});

test("retomarPorId: retoma con el modelo y mensajes guardados; null si no es de este sistema; yaCompleto si DONE", async () => {
  const s1 = await fake(({ body }) => body.messages.at(-1).content === CONT ? ok("-FIN") : ok("INI", "length")); const dir = tmp();
  try {
    const e = extra(env(dir, { SWECODE_URL_S1: s1.url }), { hasta: Date.now() - 1 });  // fuera de plazo: solo hace la 1ª seccion
    const p = await retomarLocal("t-id", MODELO, msgs, e);
    assert.equal(p.estado, "CONTINUAR"); assert.equal(p.salida, "INI");
    const r = await retomarPorId("t-id", extra(env(dir, { SWECODE_URL_S1: s1.url }), { confirmarCompleta: true }));
    assert.equal(r.salida, "INI-FIN"); assert.equal(r.estado, "DONE");
    assert.deepEqual(await retomarPorId("t-id", extra(env(dir, { SWECODE_URL_S1: s1.url }))), { yaCompleto: true });
    assert.equal(await retomarPorId("no-hay", extra(env(dir))), null);
    fs.writeFileSync(archivo(dir, "web2"), JSON.stringify({ modo: "x", modelo: "qwen38max", texto: "t" }));
    assert.equal(await retomarPorId("web2", extra(env(dir))), null);
  } finally { s1.cerrar(); }
});
