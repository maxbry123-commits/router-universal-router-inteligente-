// A4 (auditoria 3): checkpoints grandes con manifiesto + SHA256 (134-135), propietario/vinculo (128-130), almacenamiento incremental en streaming (137-138, R5),
// finish_reason=stop != tarea terminada (140), plan confirmado (141), recuperacion sin repetir (188, 208-211). Servidores falsos (node:http); claves FALSAS.
import test from "node:test";
import assert from "node:assert/strict";
import http from "node:http";
import fs from "node:fs";
import os from "node:os";
import path from "node:path";
import { retomarLocal, retomarPorId, verificarVinculo } from "../src/retomar_local.js";
import { guardarCheckpoint, leerCheckpoint, empaquetar, desempaquetar } from "../src/checkpoint_hf.js";
import { listarCheckpoints } from "../src/bloques.js";
import { BASES, limpiarEstado, limpiarClaves } from "../src/respaldo.js";

const CONT = "Continúa exactamente donde terminó, sin repetir";
const KH = "acceso-falso-harness-123", KGROQ = "gsk_FAKEKEYNOREAL1234567890";
const MODELO = "qwen2.5-coder-1.5b", GROQ = "groq/qwen/qwen3.8-27b";
const msgs = [{ role: "user", content: "escribe la funcion A" }];
const ok = (content, finish_reason = "stop", extra = {}) => ({ status: 200, json: { choices: [{ finish_reason, message: { role: "assistant", content, ...extra } }] } });
const tc = (id, name = "escribir", args = "{}") => ({ id, type: "function", function: { name, arguments: args } });
const tmp = () => fs.mkdtempSync(path.join(os.tmpdir(), "a4-"));
const rapido = { continuaciones: 0, esperar: async () => {} };
const env = (dir, extra = {}) => ({ BRIDGE_STATE_DIR: dir, ...extra });
const ex = (e, mas = {}) => ({ env: e, opts: rapido, ...mas });
const archivo = (dir, id) => path.join(dir, "checkpoints", `${id}.json`);
const leerArch = (dir, id) => JSON.parse(fs.readFileSync(archivo(dir, id), "utf8"));
const ev = (o) => `data: ${typeof o === "string" ? o : JSON.stringify(o)}\n\n`;
const delta = (content) => ({ choices: [{ index: 0, delta: { content }, finish_reason: null }] });
const finr = (r) => ({ choices: [{ index: 0, delta: {}, finish_reason: r }] });
const pausa = (ms) => new Promise((r) => setTimeout(r, ms));

const fake = (handler) => new Promise((listo) => {
  const chat = []; let n = 0;
  const s = http.createServer((req, res) => {
    let d = ""; req.on("data", (c) => d += c); req.on("end", () => {
      const v = { url: req.url, body: d ? JSON.parse(d) : null };
      if (v.url.endsWith("/models")) { res.writeHead(200, { "content-type": "application/json" }); return res.end(JSON.stringify({ data: [{ id: "qwen/qwen3.8-27b" }] })); }
      if (v.url.endsWith("/chat/completions")) { chat.push(v); n++; }
      const r = handler({ ...v, n, res });
      if (r === undefined) return;  // el handler escribe en res (SSE)
      res.writeHead(r.status, { "content-type": "application/json" }); res.end(JSON.stringify(r.json ?? {}));
    });
  }).listen(0, "127.0.0.1", () => listo({ chat, url: `http://127.0.0.1:${s.address().port}`, cerrar: () => { s.closeAllConnections?.(); s.close(); } }));
});
const harness = () => new Promise((listo) => {
  const almacen = new Map(), nombres = [];
  const s = http.createServer((req, res) => {
    let d = ""; req.on("data", (c) => d += c); req.on("end", () => {
      const b = JSON.parse(d); const json = (o) => { res.writeHead(200, { "content-type": "application/json" }); res.end(JSON.stringify(o)); };
      if (req.headers["x-api-key"] !== KH) return json({ status: "error", error: "clave de acceso invalida" });
      nombres.push(b.args.nombre);
      if (b.tool === "guardar") { almacen.set(b.args.nombre, b.args.valor); return json({ status: "ok", result: { nombre: b.args.nombre } }); }
      return almacen.has(b.args.nombre) ? json({ status: "ok", result: { nombre: b.args.nombre, valor: almacen.get(b.args.nombre) } }) : json({ status: "error", error: "no encontrado" });
    });
  }).listen(0, "127.0.0.1", () => listo({ almacen, nombres, url: `http://127.0.0.1:${s.address().port}`, cerrar: () => { s.closeAllConnections?.(); s.close(); } }));
});
const base0 = { groq: BASES.groq, nvidia: BASES.nvidia };
test.beforeEach(() => { limpiarEstado(); limpiarClaves(); });
test.afterEach(() => Object.assign(BASES, base0));

// ------------------------------------------------------------------ 134-135: fragmentos + manifiesto + version + SHA256
test("134-135: un checkpoint grande se fragmenta (manifiesto con version y SHA256 por fragmento y total) y se lee de vuelta identico", async () => {
  const dir = tmp(), e = env(dir, { RIU_CHECKPOINT_FRAGMENTO: "200" });
  const grande = { tipo: "retomar_local", estado: "CONTINUAR", tarea_id: "g1", parcial: "ñ😀".repeat(300), lista: Array.from({ length: 30 }, (_, i) => ({ i })) };
  const r = await guardarCheckpoint("g1", grande, { env: e });
  assert.equal(r.local, true); assert.ok(r.partes >= 3, "varios fragmentos");
  const m = leerArch(dir, "g1");
  assert.equal(m.fragmentado, true); assert.equal(m.integridad.version, 2); assert.equal(m.integridad.algoritmo, "sha256"); assert.match(m.integridad.sha256, /^[0-9a-f]{64}$/);
  assert.equal(m.integridad.partes.length, r.partes); assert.ok(m.integridad.partes.every((p) => /^[0-9a-f]{64}$/.test(p.sha256) && fs.existsSync(path.join(dir, "checkpoints", p.nombre))));
  assert.equal(m.parcial, undefined, "el manifiesto no lleva el cuerpo"); assert.equal(m.estado, "CONTINUAR"); assert.equal(m.tipo, "retomar_local");
  assert.ok(!fs.readdirSync(path.join(dir, "checkpoints")).some((f) => f.endsWith(".tmp")));
  const ck = await leerCheckpoint("g1", { env: e });
  assert.equal(ck.parcial, grande.parcial); assert.deepEqual(ck.lista, grande.lista); assert.equal(ck.integridad, undefined);
});

test("135: un checkpoint pequeno sigue en un solo archivo, con version y SHA256 que se verifican", async () => {
  const dir = tmp(), e = env(dir);
  await guardarCheckpoint("p1", { estado: "X", n: 1 }, { env: e });
  assert.deepEqual(fs.readdirSync(path.join(dir, "checkpoints")), ["p1.json"]);
  const d = leerArch(dir, "p1"); assert.equal(d.integridad.version, 2); assert.equal(d.integridad.partes, 0);
  assert.equal((await leerCheckpoint("p1", { env: e })).n, 1);
});

test("135: integridad al leer — contenido alterado, fragmento alterado o ausente, version desconocida => CORRUPTO y no se usa (sin copia buena lanza CHECKPOINT_CORRUPTO)", async () => {
  const dir = tmp(), e = env(dir, { RIU_CHECKPOINT_FRAGMENTO: "100" });
  await guardarCheckpoint("c1", { estado: "OK", texto: "x".repeat(400) }, { env: e });
  const m = leerArch(dir, "c1"), f0 = path.join(dir, "checkpoints", m.integridad.partes[0].nombre), original = fs.readFileSync(f0, "utf8");
  fs.writeFileSync(f0, original.replace(/x/, "y"));  // un caracter cambiado
  await assert.rejects(leerCheckpoint("c1", { env: e }), { code: "CHECKPOINT_CORRUPTO" });
  fs.rmSync(f0); await assert.rejects(leerCheckpoint("c1", { env: e }), { code: "CHECKPOINT_CORRUPTO" }, "fragmento ausente");
  fs.writeFileSync(f0, original); assert.equal((await leerCheckpoint("c1", { env: e })).texto.length, 400, "restaurado vuelve a leerse");
  await guardarCheckpoint("c2", { estado: "OK" }, { env: env(dir) });
  const d = leerArch(dir, "c2"); fs.writeFileSync(archivo(dir, "c2"), JSON.stringify({ ...d, estado: "ALTERADO" }));
  await assert.rejects(leerCheckpoint("c2", { env: e }), { code: "CHECKPOINT_CORRUPTO" }, "cuerpo alterado");
  fs.writeFileSync(archivo(dir, "c2"), JSON.stringify({ ...d, integridad: { ...d.integridad, version: 99 } }));
  await assert.rejects(leerCheckpoint("c2", { env: e }), { code: "CHECKPOINT_CORRUPTO" }, "version desconocida");
  fs.writeFileSync(archivo(dir, "c3"), JSON.stringify({ estado: "previo", ts: "2020-01-01" }));  // formato previo sin integridad: se acepta
  assert.equal((await leerCheckpoint("c3", { env: e })).estado, "previo");
});

test("134-135 + 209: con Harness los fragmentos y el manifiesto van al Harness; tras perder el disco se reconstruye y verifica; una copia local corrupta cae a la buena del Harness", async () => {
  const h = await harness(), dir = tmp();
  try {
    const e = env(dir, { RIU_CHECKPOINT_FRAGMENTO: "150", RIU_DEEPSEEK_HARNESS_URL: h.url, RIU_API_KEY: KH });
    const cuerpo = { tipo: "retomar_local", estado: "CONTINUAR", origen: "openclaw", parcial: "z".repeat(700) };
    const r = await guardarCheckpoint("h1", cuerpo, { env: e });
    assert.equal(r.harness, true);
    const claves = [...h.almacen.keys()];
    assert.ok(claves.includes("tareas/swe/openclaw/h1/checkpoint.json")); assert.ok(claves.filter((k) => k.endsWith(".frag")).length >= 4);
    assert.ok(claves.every((k) => k.length <= 128 && !/\.(py|js|sh)$/.test(k)), "nombres validos para el almacen HF");
    fs.rmSync(path.join(dir, "checkpoints"), { recursive: true });  // reinicio: disco perdido
    assert.equal((await leerCheckpoint("h1", { env: e })).parcial, cuerpo.parcial);
    await guardarCheckpoint("h1", cuerpo, { env: e });  // vuelve a haber copia local
    const m = leerArch(dir, "h1"); fs.writeFileSync(path.join(dir, "checkpoints", m.integridad.partes[1].nombre), "basura");
    assert.equal((await leerCheckpoint("h1", { env: e })).parcial, cuerpo.parcial, "local corrupto: se usa la copia verificada del Harness");
    // fragmento alterado en el Harness Y local corrupto => ninguna copia buena
    const k = [...h.almacen.keys()].filter((x) => x.endsWith(".002.frag")).pop(); h.almacen.set(k, "alterado");  // el fragmento 2 de la version vigente
    await assert.rejects(leerCheckpoint("h1", { env: e }), { code: "CHECKPOINT_CORRUPTO" });
  } finally { h.cerrar(); }
});

test("134: al guardar una version nueva se borran los fragmentos de la anterior y un corte entre fragmentos y manifiesto deja legible la version previa", async () => {
  const dir = tmp(), e = env(dir, { RIU_CHECKPOINT_FRAGMENTO: "100" });
  await guardarCheckpoint("v", { estado: "A", t: "a".repeat(350) }, { env: e });
  const f1 = leerArch(dir, "v").integridad.partes.map((p) => p.nombre);
  // corte simulado: fragmentos de una version nueva escritos pero el manifiesto no
  const nuevo = empaquetar({ estado: "B", t: "b".repeat(350), ts: "t" }, 100, "v");
  for (const p of nuevo.partes) fs.writeFileSync(path.join(dir, "checkpoints", p.nombre), p.texto);
  assert.equal((await leerCheckpoint("v", { env: e })).estado, "A", "sigue la version previa, entera");
  await guardarCheckpoint("v", { estado: "C", t: "c".repeat(350) }, { env: e });
  assert.ok(f1.every((n) => !fs.existsSync(path.join(dir, "checkpoints", n))), "fragmentos viejos borrados");
  assert.equal((await leerCheckpoint("v", { env: e })).estado, "C");
});

test("135: desempaquetar rechaza documentos invalidos", async () => {
  assert.deepEqual(await desempaquetar(null, async () => null), { corrupto: "DOCUMENTO_INVALIDO" });
  const { doc } = empaquetar({ a: 1 }, 1000, "z"); doc.integridad.sha256 = "0".repeat(64);
  assert.equal((await desempaquetar(doc, async () => null)).corrupto, "SHA256_NO_COINCIDE");
});

// ------------------------------------------------------------------ 128-130 + 211: propietario y aislamiento
test("128-130: la tarea queda vinculada a propietario/proyecto/sesion/workflow/operacion (sin claves); otro propietario o ninguno => TAREA_AJENA y no se llama al modelo", async () => {
  const s1 = await fake(({ n }) => ok("R" + n)), dir = tmp(); const e = ex(env(dir, { SWECODE_URL_S1: s1.url }));
  try {
    const A = { propietario: "p-aaaa", proyecto: "proy1", sesion: "ses1", workflow: "swe", operacion: "chat" };
    const a = await retomarLocal("tk", MODELO, msgs, { ...e, ...A });
    assert.equal(a.salida, "R1");
    const v = leerArch(dir, "tk").vinculo;
    assert.deepEqual(v, A); assert.ok(!JSON.stringify(leerArch(dir, "tk")).includes("FAKEKEY"));
    await assert.rejects(retomarLocal("tk", MODELO, msgs, { ...e, propietario: "p-bbbb" }), { code: "TAREA_AJENA" });
    await assert.rejects(retomarLocal("tk", MODELO, msgs, { ...e }), { code: "TAREA_AJENA" }, "sin propietario tampoco");
    await assert.rejects(retomarPorId("tk", { ...e, propietario: "p-bbbb" }), { code: "TAREA_AJENA" });
    await assert.rejects(retomarLocal("tk", MODELO, msgs, { ...e, ...A, proyecto: "otro" }), { code: "TAREA_OTRO_CONTEXTO" });
    await assert.rejects(retomarLocal("tk", MODELO, msgs, { ...e, ...A, workflow: "otro" }), { code: "TAREA_OTRO_CONTEXTO" });
    assert.equal(s1.chat.length, 1, "ningun intento ajeno llega al modelo");
    const otra = await retomarLocal("tk", MODELO, msgs, { ...e, ...A });  // el dueño si
    assert.equal(otra.desde_checkpoint, true); assert.equal(otra.salida, "R1");
    assert.equal((await retomarPorId("tk", { ...e, propietario: "p-aaaa" })).salida, "R1");
    assert.equal((await retomarPorId("tk", { ...e, interno: true })).salida, "R1", "la puesta en marcha del bridge retoma en nombre del dueño");
  } finally { s1.cerrar(); }
});

test("130/211: la tarea ajena no se recupera tampoco desde el Harness (otro disco), y un checkpoint previo sin dueño lo adopta el primer propietario", async () => {
  const s1 = await fake(({ n }) => ok("R" + n)), h = await harness(), d1 = tmp(), d2 = tmp();
  try {
    const hv = { RIU_DEEPSEEK_HARNESS_URL: h.url, RIU_API_KEY: KH };
    await retomarLocal("rem", MODELO, msgs, ex(env(d1, { SWECODE_URL_S1: s1.url, ...hv }), { propietario: "p-uno" }));
    await assert.rejects(retomarLocal("rem", MODELO, msgs, ex(env(d2, { SWECODE_URL_S1: s1.url, ...hv }), { propietario: "p-dos" })), { code: "TAREA_AJENA" });
    assert.equal(s1.chat.length, 1);
    const st = { vinculo: undefined }; verificarVinculo(st, { propietario: "p-x" }); assert.equal(st.vinculo.propietario, "p-x");
  } finally { s1.cerrar(); h.cerrar(); }
});

test("211: dos tareas del mismo usuario no se mezclan (herramientas, texto, checkpoint) y listarCheckpoints solo lista las propias", async () => {
  const s1 = await fake(({ body }) => ok("RESP:" + body.messages[0].content)), dir = tmp(); const e = ex(env(dir, { SWECODE_URL_S1: s1.url }));
  try {
    const a = await retomarLocal("ta", MODELO, [{ role: "user", content: "AAA" }], { ...e, propietario: "p-1" });
    const b = await retomarLocal("tb", MODELO, [{ role: "user", content: "BBB" }], { ...e, propietario: "p-1" });
    const c = await retomarLocal("tc", MODELO, [{ role: "user", content: "CCC" }], { ...e, propietario: "p-2" });
    assert.deepEqual([a.salida, b.salida, c.salida], ["RESP:AAA", "RESP:BBB", "RESP:CCC"]);
    const previo = process.env.BRIDGE_STATE_DIR; process.env.BRIDGE_STATE_DIR = dir;
    try {
      assert.deepEqual(listarCheckpoints("p-1").map((x) => x.conv_id).sort(), ["ta", "tb"]);
      assert.deepEqual(listarCheckpoints("p-2").map((x) => x.conv_id), ["tc"]);
      assert.deepEqual(listarCheckpoints(null).map((x) => x.conv_id), [], "sin identidad no se ve ninguna tarea con dueño");
    } finally { if (previo === undefined) delete process.env.BRIDGE_STATE_DIR; else process.env.BRIDGE_STATE_DIR = previo; }
    await assert.rejects(retomarLocal("ta", MODELO, [{ role: "user", content: "BBB" }], { ...e, propietario: "p-1" }), { code: "CHECKPOINT_OTRA_TAREA" });
  } finally { s1.cerrar(); }
});

// ------------------------------------------------------------------ 140-141: finish_reason=stop y plan confirmado
test("140: finish_reason=stop deja la tarea en RESPUESTA_COMPLETA (no DONE); repetir devuelve lo guardado sin llamar al modelo; DONE solo al confirmar", async () => {
  const s1 = await fake(({ n }) => ok("LISTO" + n)), dir = tmp(); const e = ex(env(dir, { SWECODE_URL_S1: s1.url }));
  try {
    const a = await retomarLocal("t140", MODELO, msgs, e);
    assert.equal(a.estado, "RESPUESTA_COMPLETA"); assert.equal(a.fase, "RESPUESTA_COMPLETA"); assert.equal(leerArch(dir, "t140").completo, false);
    assert.deepEqual(await retomarPorId("t140", e).then((r) => r.estado), "RESPUESTA_COMPLETA", "no es yaCompleto");
    const b = await retomarLocal("t140", MODELO, msgs, e);
    assert.equal(b.salida, "LISTO1"); assert.equal(b.desde_checkpoint, true); assert.equal(s1.chat.length, 1);
    const c = await retomarLocal("t140", MODELO, msgs, { ...e, confirmarCompleta: true });
    assert.equal(c.estado, "DONE"); assert.equal(leerArch(dir, "t140").completo, true); assert.equal(s1.chat.length, 1);
    assert.deepEqual(await retomarPorId("t140", e), { yaCompleto: true });
  } finally { s1.cerrar(); }
});

test("141: con tools y exigirPlan hace falta objetivo + operaciones previstas; un tool_call fuera del plan se rechaza antes de entregarse/ejecutarse", async () => {
  const s1 = await fake(() => ok("", "tool_calls", { content: null, tool_calls: [tc("c1", "borrar_todo")] })), dir = tmp();
  const tools = [{ type: "function", function: { name: "escribir" } }], e = ex(env(dir, { SWECODE_URL_S1: s1.url }), { tools, exigirPlan: true });
  try {
    await assert.rejects(retomarLocal("pl1", MODELO, msgs, e), { code: "PLAN_REQUERIDO" });
    assert.equal(s1.chat.length, 0, "sin plan no se llama al modelo");
    const ejecutadas = [];
    await assert.rejects(retomarLocal("pl2", MODELO, msgs, { ...e, plan: { objetivo: "crear A", operaciones: ["escribir"] }, ejecutarHerramienta: async (t) => { ejecutadas.push(t.id); return 1; } }), { code: "OPERACION_NO_PREVISTA" });
    assert.deepEqual(ejecutadas, []); assert.equal(leerArch(dir, "pl2").plan.objetivo, "crear A");
    const s2 = await fake(() => ok("", "tool_calls", { content: null, tool_calls: [tc("c9", "escribir")] }));
    try {
      const r = await retomarLocal("pl3", MODELO, msgs, { ...e, env: env(dir, { SWECODE_URL_S1: s2.url }), plan: { objetivo: "crear A", operaciones: ["escribir"] } });
      assert.equal(r.estado, "WAIT_TOOLS"); assert.equal(r.fase, "ESPERANDO_TOOLS"); assert.equal(r.tool_calls[0].id, "c9");
    } finally { s2.cerrar(); }
    const sin = await retomarLocal("pl4", MODELO, msgs, ex(env(dir, { SWECODE_URL_S1: s1.url }), {}));  // sin tools y sin exigir: nada cambia
    assert.equal(sin.estado, "WAIT_TOOLS");
  } finally { s1.cerrar(); }
});

// ------------------------------------------------------------------ 137-138 + R5: almacenamiento incremental durante el streaming
test("137-138/R5: durante el streaming el texto confirmado se vuelca al checkpoint ANTES de terminar; la caida deja el parcial y el reintento continua sin repetirlo ni duplicar al cliente", async () => {
  const dir = tmp(); let fase = 1; let soltar;
  const bloqueo = new Promise((r) => { soltar = r; });
  const g = await fake(({ res, body }) => {
    res.writeHead(200, { "content-type": "text/event-stream" });
    if (fase === 1) { res.write(ev(delta("Uno dos tres "))); res.write(ev(delta("cuatro cinco "))); bloqueo.then(() => res.destroy()); return; }
    res.write(ev(delta("seis siete."))); res.write(ev(finr("stop"))); res.end(ev("[DONE]"));
  });
  BASES.groq = g.url;
  const e = ex(env(dir, { GROQ_API_KEY: KGROQ }), { propietario: "p-1", flushChars: 5, flushMs: 0 });
  try {
    const c1 = { texto: "" }, recibido1 = [];
    const p1 = retomarLocal("st1", GROQ, msgs, { ...e, sinRespaldo: true, onDelta: (t) => recibido1.push(t), flujo: c1 });
    p1.catch(() => {});
    for (let i = 0; i < 60 && !(fs.existsSync(archivo(dir, "st1")) && leerArch(dir, "st1").stream?.texto?.includes("cuatro")); i++) await pausa(50);
    const ck = leerArch(dir, "st1");  // la respuesta aun NO termino y ya esta en disco
    assert.equal(ck.fase, "RESPUESTA_PARCIAL"); assert.ok(ck.stream.texto.startsWith("Uno dos tres")); assert.equal(recibido1.join(""), "Uno dos tres cuatro cinco ");
    soltar(); await assert.rejects(p1);  // caida del proveedor a mitad
    const roto = leerArch(dir, "st1"); assert.equal(roto.parcial, "Uno dos tres cuatro cinco "); assert.equal(roto.stream, undefined); assert.equal(roto.estado, "ERROR");
    // reintento (cliente nuevo, nada recibido todavia): recibe lo guardado UNA vez y luego la continuacion
    fase = 2; const c2 = { texto: "" }, recibido2 = [];
    const r = await retomarLocal("st1", GROQ, msgs, { ...e, sinRespaldo: true, onDelta: (t) => recibido2.push(t), flujo: c2 });
    assert.equal(r.salida, "Uno dos tres cuatro cinco seis siete."); assert.equal(recibido2.join(""), r.salida, "el cliente recibe todo exactamente una vez");
    assert.deepEqual(g.chat.at(-1).body.messages.slice(-2), [{ role: "assistant", content: "Uno dos tres cuatro cinco " }, { role: "user", content: CONT }]);
    assert.equal(r.estado, "RESPUESTA_COMPLETA");
  } finally { g.cerrar(); }
});

test("137-138 + 208-209: caida del PROCESO a mitad del streaming (queda solo st.stream en el checkpoint): el reinicio con otro disco lo recupera desde el Harness y continua", async () => {
  const h = await harness(), d1 = tmp(), d2 = tmp(); let tope = false;
  const g = await fake(({ res, body }) => {
    res.writeHead(200, { "content-type": "text/event-stream" });
    if (!tope) { tope = true; res.write(ev(delta("AAAA BBBB "))); res.write(ev(delta("CCCC "))); return; }  // se queda colgado: lo mata el timeout/la caida
    res.write(ev(delta("DDDD."))); res.write(ev(finr("stop"))); res.end(ev("[DONE]"));
  });
  BASES.groq = g.url;
  const hv = { GROQ_API_KEY: KGROQ, RIU_DEEPSEEK_HARNESS_URL: h.url, RIU_API_KEY: KH };
  try {
    // primera ejecucion: se corta por inactividad (timeout) con texto ya volcado
    await assert.rejects(retomarLocal("crash", GROQ, msgs, { env: env(d1, hv), opts: { ...rapido, timeoutMs: 400, timeoutsModelo: { "qwen/qwen3.8-27b": 400 } }, sinRespaldo: true, onDelta: () => {}, flujo: { texto: "" }, flushChars: 4, flushMs: 0, propietario: "p-1" }));
    // simulamos la muerte del proceso ANTES de consolidar: dejamos solo el volcado incremental en el Harness
    const k = "tareas/swe/bridge/crash/checkpoint.json", doc = JSON.parse(h.almacen.get(k));
    const sinConsolidar = { ...doc }; delete sinConsolidar.integridad; sinConsolidar.parcial = ""; sinConsolidar.secciones = []; sinConsolidar.stream = { vuelta: 1, usado: GROQ, texto: "AAAA BBBB CCCC " }; sinConsolidar.estado = "CONTINUAR";
    await guardarCheckpoint("crash", sinConsolidar, { env: env(d2, hv) });
    limpiarEstado();  // la clave enfriada por el timeout no cuenta en el proceso nuevo
    const rec = [], r = await retomarLocal("crash", GROQ, msgs, { env: env(d2, hv), opts: rapido, sinRespaldo: true, propietario: "p-1", onDelta: (t) => rec.push(t), flujo: { texto: "" } });
    assert.equal(r.salida, "AAAA BBBB CCCC DDDD."); assert.equal(rec.join(""), r.salida, "el cliente nuevo recibe lo recuperado y la continuacion, una vez"); assert.equal(r.reanudado, true);
    assert.deepEqual(g.chat.at(-1).body.messages.slice(-2), [{ role: "assistant", content: "AAAA BBBB CCCC " }, { role: "user", content: CONT }]);
    assert.ok(r.secciones >= 1);
  } finally { g.cerrar(); h.cerrar(); }
});

// ------------------------------------------------------------------ 188, 208-210: recuperacion sin repetir
test("188/210: una operacion completada no se repite tras reiniciar (otro disco, solo el Harness); una iniciada sin confirmar pasa a RECONCILIAR y se verifica antes de reintentar", async () => {
  const h = await harness(), d1 = tmp(), d2 = tmp(), d3 = tmp();
  const s1 = await fake(({ n }) => n === 1 ? ok("", "tool_calls", { content: null, tool_calls: [tc("t1"), tc("t2", "desplegar")] }) : ok("HECHO"));
  const hv = { SWECODE_URL_S1: s1.url, RIU_DEEPSEEK_HARNESS_URL: h.url, RIU_API_KEY: KH }, vistas = [];
  try {
    // t1 se ejecuta y se confirma; t2 muere a mitad (caida entre "iniciada" y "confirmada")
    await assert.rejects(retomarLocal("op", MODELO, msgs, ex(env(d1, hv), { propietario: "p-1", ejecutarHerramienta: async (t) => { vistas.push(t.id); if (t.id === "t2") throw new Error("caida del proceso"); return { ok: t.id }; } })));
    assert.deepEqual(vistas, ["t1", "t2"]);
    // reinicio sin poder verificar: NO se reintenta a ciegas
    await assert.rejects(retomarLocal("op", MODELO, msgs, ex(env(d2, hv), { propietario: "p-1", ejecutarHerramienta: async (t) => { vistas.push("REPETIDA:" + t.id); } })), { code: "VERIFICAR_HERRAMIENTAS_PENDIENTES" });
    assert.equal((await leerCheckpoint("op", { env: env(d2, hv) })).fase, "RECONCILIAR");
    // con verificacion: t2 si se hizo -> no se repite; t1 (confirmada) tampoco
    const r = await retomarLocal("op", MODELO, msgs, ex(env(d3, hv), { propietario: "p-1", ejecutarHerramienta: async (t) => { vistas.push("REPETIDA:" + t.id); }, verificarHerramienta: async (t) => ({ hecha: t.id === "t2", resultado: { ya: true } }) }));
    assert.equal(r.salida, "HECHO"); assert.ok(!vistas.some((v) => String(v).startsWith("REPETIDA:t1")), "t1 no se repite");
    assert.ok(!vistas.includes("REPETIDA:t2"), "t2 verificada como hecha: no se repite");
  } finally { s1.cerrar(); h.cerrar(); }
});

test("208: timeout del modelo entre checkpoints: la seccion guardada se conserva, el error es tipado y el reintento continua desde ella", async () => {
  let colgar = false;
  const s1 = await fake(({ body, n }) => { if (n === 1) return ok("PARTE1 ", "length"); if (colgar) return undefined; return body.messages.at(-1).content === CONT ? ok("PARTE2") : ok("?"); });
  const dir = tmp(); colgar = true;
  try {
    await assert.rejects(retomarLocal("to", MODELO, msgs, { env: env(dir, { SWECODE_URL_S1: s1.url }), opts: { ...rapido, timeoutMs: 300 }, sinRespaldo: true }), (e) => !!e.code);
    const ck = leerArch(dir, "to"); assert.equal(ck.parcial, "PARTE1 "); assert.equal(ck.secciones.length, 1);
    colgar = false; s1.chat.length = 0;
    const r = await retomarLocal("to", MODELO, msgs, ex(env(dir, { SWECODE_URL_S1: s1.url })));
    assert.equal(r.salida, "PARTE1 PARTE2"); assert.equal(s1.chat.length, 1, "la seccion 1 no se repite");
  } finally { s1.cerrar(); }
});
