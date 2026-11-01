// A4 (auditoria 3) con server.js REAL: propietario por clave de acceso (128-130, 211), streaming real con tarea_id + checkpoint incremental (R5, 137-138),
// finish_reason=stop != tarea terminada (140), plan (141), texto + tool_calls sin perder llamadas en JSON y SSE (R4). Proveedores falsos (node:http); claves FALSAS.
import test, { before, after } from "node:test";
import assert from "node:assert/strict";
import fs from "node:fs";
import http from "node:http";
import os from "node:os";
import path from "node:path";
import { prepararApp, arrancar, limpiar, registrarMock } from "./helpers/bridge_app.mjs";
import './helpers/acceso.mjs';

const CONT = "Continúa exactamente donde terminó, sin repetir";
const USUARIO2 = "clave-de-acceso-usuario-dos", KGROQ = "gsk_FAKEKEYNOREAL1234567890";
const ev = (o) => `data: ${typeof o === "string" ? o : JSON.stringify(o)}\n\n`;
const delta = (content) => ({ choices: [{ index: 0, delta: { content }, finish_reason: null }] });
const finr = (r) => ({ choices: [{ index: 0, delta: {}, finish_reason: r }] });
const ok = (content, finish_reason = "stop", extra = {}) => ({ status: 200, json: { choices: [{ finish_reason, message: { role: "assistant", content, ...extra } }] } });
const tc = (id, name = "escribir") => ({ id, type: "function", function: { name, arguments: "{}" } });
const pausa = (ms) => new Promise((r) => setTimeout(r, ms));
const disco = (n) => fs.mkdtempSync(path.join(os.tmpdir(), `a4s-${n}-`));
const arch = (dir, id) => path.join(dir, "checkpoints", `${id}.json`);

const proveedor = (handler) => new Promise((listo) => {
  const chat = []; let n = 0;
  const s = http.createServer((req, res) => {
    let d = ""; req.on("data", (c) => d += c); req.on("end", () => {
      const v = { url: req.url, auth: req.headers.authorization, body: d ? JSON.parse(d) : null };
      if (v.url.endsWith("/models")) { res.writeHead(200, { "content-type": "application/json" }); return res.end(JSON.stringify({ data: [{ id: "qwen/qwen3.8-27b" }] })); }
      chat.push(v); n++;
      const r = handler({ ...v, n, res });
      if (r === undefined) return;
      res.writeHead(r.status, { "content-type": "application/json" }); res.end(JSON.stringify(r.json ?? {}));
    });
  }).listen(0, "127.0.0.1", () => { registrarMock(s); listo({ chat, url: `http://127.0.0.1:${s.address().port}` }); });
});
const post = async (srv, ruta, body, headers = {}) => {
  const r = await fetch(srv.base + ruta, { method: "POST", headers: { "content-type": "application/json", ...headers }, ...(body ? { body: JSON.stringify(body) } : {}) });
  return { status: r.status, headers: r.headers, json: await r.json().catch(() => null) };
};
const get = async (srv, ruta, headers = {}) => { const r = await fetch(srv.base + ruta, { headers }); return { status: r.status, json: await r.json().catch(() => null) }; };
const chat = (srv, body, headers) => post(srv, "/v1/chat/completions", { model: "qwen2.5-coder-1.5b", messages: [{ role: "user", content: "escribe A" }], ...body }, headers);
// SSE: bloques conforme llegan; alPrimerContenido se espera antes de seguir leyendo
async function leerSse(srv, body, { alPrimerContenido, headers = {} } = {}) {
  const r = await fetch(srv.base + "/v1/chat/completions", { method: "POST", headers: { "content-type": "application/json", ...headers }, body: JSON.stringify({ messages: [{ role: "user", content: "hola mundo" }], stream: true, ...body }) });
  const dec = new TextDecoder(); let buf = "", avisado = false; const datos = [];
  for await (const c of r.body) {
    buf += dec.decode(c, { stream: true });
    let i; while ((i = buf.indexOf("\n\n")) >= 0) {
      const b = buf.slice(0, i).trim(); buf = buf.slice(i + 2); if (!b.startsWith("data: ")) continue;
      datos.push(b.slice(6));
      if (!avisado && alPrimerContenido && b !== "data: [DONE]" && JSON.parse(b.slice(6)).choices?.[0]?.delta?.content) { avisado = true; await alPrimerContenido(); }
    }
  }
  const chunks = datos.filter((d) => d !== "[DONE]").map((d) => JSON.parse(d));
  return { status: r.status, headers: r.headers, datos, chunks, texto: chunks.map((c) => c.choices?.[0]?.delta?.content || "").join("") };
}

before(() => { prepararApp(); });
after(() => { limpiar(); });

test("128: el id de la tarea viaja en x-tarea-id y en tarea.id; reenviado, la tarea es la misma (estable) y no repite al modelo", async () => {
  const s1 = await proveedor(({ n }) => ok("RESP-" + n)), dir = disco("a");
  const B = await arrancar("a4-id", { BRIDGE_STATE_DIR: dir, SWECODE_URL_S1: s1.url });
  const a = await chat(B, { tarea_id: "estable-1" });
  assert.equal(a.headers.get("x-tarea-id"), "estable-1"); assert.equal(a.json.tarea.id, "estable-1");
  const b = await chat(B, { tarea_id: "estable-1" });
  assert.equal(b.json.tarea.id, "estable-1"); assert.equal(b.json.tarea.desde_checkpoint, true); assert.equal(s1.chat.length, 1);
});

test("129-130/211: dos usuarios (claves de acceso distintas): el 2º no recupera ni reanuda la tarea del 1º conociendo su tarea_id (403), tampoco por /secciones ni en el listado; el id derivado difiere", async () => {
  const s1 = await proveedor(({ n }) => ok("RESP-" + n)), dir = disco("b");
  const B = await arrancar("a4-own", { BRIDGE_STATE_DIR: dir, SWECODE_URL_S1: s1.url, RIU_API_KEY: USUARIO2 });
  const U2 = { "x-api-key": USUARIO2 };
  const a = await chat(B, { tarea_id: "mia-1", proyecto: "proy", workflow: "swe", conv_id: "sesion-1" });
  assert.equal(a.status, 200);
  const ck = JSON.parse(fs.readFileSync(arch(dir, "mia-1"), "utf8"));
  assert.match(ck.vinculo.propietario, /^p-[0-9a-f]{24}$/); assert.deepEqual({ ...ck.vinculo, propietario: "x" }, { propietario: "x", proyecto: "proy", sesion: "sesion-1", workflow: "swe", operacion: null });
  assert.ok(!fs.readFileSync(arch(dir, "mia-1"), "utf8").includes("clave-de-acceso-del-chat"), "el checkpoint guarda el hash, nunca la clave");
  const ajena = await chat(B, { tarea_id: "mia-1" }, U2);
  assert.equal(ajena.status, 403); assert.equal(ajena.json.error.code, "TAREA_AJENA"); assert.equal(s1.chat.length, 1, "no se llama al modelo");
  const ret = await post(B, "/v1/secciones/mia-1/retomar", null, U2);
  assert.equal(ret.status, 403); assert.equal(ret.json.error.code, "TAREA_AJENA");
  assert.equal((await get(B, "/v1/secciones")).json.secciones.some((s) => s.conv_id === "mia-1"), true);
  assert.equal((await get(B, "/v1/secciones", U2)).json.secciones.some((s) => s.conv_id === "mia-1"), false, "el listado no revela tareas ajenas");
  assert.equal((await chat(B, { tarea_id: "mia-1", proyecto: "otro" })).status, 409, "mismo dueño, otro proyecto: otro contexto");
  const d1 = await chat(B, { conv_id: "c-compartido" }), d2 = await chat(B, { conv_id: "c-compartido" }, U2);
  assert.notEqual(d1.json.tarea.id, d2.json.tarea.id, "mismo conv_id y mensajes, distinto usuario => distinta tarea");
  assert.equal(d2.status, 200);
});

test("140: stop no cierra la tarea (RESPUESTA_COMPLETA); tarea_completa:true / x-tarea-completa:1 la cierra (DONE)", async () => {
  const s1 = await proveedor(({ n }) => ok("OK" + n)), dir = disco("c");
  const B = await arrancar("a4-140", { BRIDGE_STATE_DIR: dir, SWECODE_URL_S1: s1.url });
  const a = await chat(B, { tarea_id: "t140" });
  assert.equal(a.json.tarea.estado, "RESPUESTA_COMPLETA"); assert.equal(a.json.choices[0].finish_reason, "stop"); assert.equal(JSON.parse(fs.readFileSync(arch(dir, "t140"), "utf8")).completo, false);
  const b = await chat(B, { tarea_id: "t140", tarea_completa: true });
  assert.equal(b.json.tarea.estado, "DONE"); assert.equal(s1.chat.length, 1);
  const c = await chat(B, { tarea_id: "t141" }, { "x-tarea-completa": "1" }); assert.equal(c.json.tarea.estado, "DONE");
});

test("141: exigir_confirmacion + tools => sin objetivo y operaciones_previstas 409 PLAN_REQUERIDO (el modelo no se llama); fuera del plan 409 OPERACION_NO_PREVISTA; dentro, ESPERANDO tools", async () => {
  const s1 = await proveedor(() => ok("", "tool_calls", { content: null, tool_calls: [tc("c1", "escribir")] })), dir = disco("d");
  const B = await arrancar("a4-plan", { BRIDGE_STATE_DIR: dir, SWECODE_URL_S1: s1.url });
  const tools = [{ type: "function", function: { name: "escribir", parameters: {} } }];
  const sin = await chat(B, { tarea_id: "p1", tools, exigir_confirmacion: true });
  assert.equal(sin.status, 409); assert.equal(sin.json.error.code, "PLAN_REQUERIDO"); assert.equal(s1.chat.length, 0);
  const fuera = await chat(B, { tarea_id: "p2", tools, exigir_confirmacion: true, objetivo: "borrar", operaciones_previstas: ["leer"] });
  assert.equal(fuera.status, 409); assert.equal(fuera.json.error.code, "OPERACION_NO_PREVISTA");
  const bien = await chat(B, { tarea_id: "p3", tools, exigir_confirmacion: true, objetivo: "crear A", operaciones_previstas: ["escribir"] });
  assert.equal(bien.status, 200); assert.equal(bien.json.tarea.fase, "ESPERANDO_TOOLS"); assert.equal(bien.json.choices[0].message.tool_calls[0].id, "c1");
  assert.equal(JSON.parse(fs.readFileSync(arch(dir, "p3"), "utf8")).plan.objetivo, "crear A");
  const libre = await chat(B, { tarea_id: "p4", tools }); assert.equal(libre.status, 409, "la confirmacion esta activa POR DEFECTO con tools (efectos); se apaga con BRIDGE_EXIGIR_CONFIRMACION=0 (ver sin_variables.test.mjs)"); assert.equal(libre.json.error.code, "PLAN_REQUERIDO");
  const sinTools = await chat(B, { tarea_id: "p5" }); assert.equal(sinTools.status, 200, "el chat sin tools no pide confirmacion");
});

test("R5 + 137-138: stream:true con tarea_id entrega el primer fragmento MIENTRAS el proveedor sigue, vuelca el texto al checkpoint antes de terminar y termina sin duplicar", async () => {
  let soltar; const espera = new Promise((r) => { soltar = r; });
  const g = await proveedor(({ res }) => { res.writeHead(200, { "content-type": "text/event-stream" }); res.write(ev(delta("Hola "))); res.write(ev(delta("mundo "))); espera.then(() => { res.write(ev(delta("feliz."))); res.write(ev(finr("stop"))); res.end(ev("[DONE]")); }); });
  const dir = disco("e");
  const B = await arrancar("a4-r5", { BRIDGE_STATE_DIR: dir, TEST_GROQ_URL: g.url, GROQ_API_KEY: KGROQ, BRIDGE_CHECKPOINT_FLUSH_CHARS: "4", BRIDGE_CHECKPOINT_FLUSH_MS: "0", BRIDGE_SSE_KEEPALIVE_MS: "60000" });
  let enDiscoAntes = null;
  const r = await leerSse(B, { model: "groq/qwen/qwen3.8-27b", tarea_id: "r5-1" }, { alPrimerContenido: async () => {
    for (let i = 0; i < 40 && !(fs.existsSync(arch(dir, "r5-1")) && JSON.parse(fs.readFileSync(arch(dir, "r5-1"), "utf8")).stream?.texto?.includes("mundo")); i++) await pausa(50);
    enDiscoAntes = JSON.parse(fs.readFileSync(arch(dir, "r5-1"), "utf8")); soltar();
  } });
  assert.equal(r.status, 200); assert.equal(r.texto, "Hola mundo feliz."); assert.equal(r.datos.at(-1), "[DONE]");
  assert.ok(enDiscoAntes.stream.texto.startsWith("Hola "), "el texto estaba en el checkpoint antes de que terminara la respuesta"); assert.equal(enDiscoAntes.fase, "RESPUESTA_PARCIAL");
  assert.equal(r.chunks.filter((c) => c.choices?.[0]?.finish_reason).length, 1); assert.equal(r.chunks.filter((c) => c.choices?.[0]?.delta?.role).length, 1);
  const ult = r.chunks.at(-1); assert.equal(ult.tarea.id, "r5-1"); assert.equal(ult.tarea.estado, "RESPUESTA_COMPLETA"); assert.equal(r.headers.get("x-tarea-id"), "r5-1");
  const fin = JSON.parse(fs.readFileSync(arch(dir, "r5-1"), "utf8")); assert.equal(fin.stream, undefined); assert.equal(fin.resultado.salida, "Hola mundo feliz."); assert.ok(!JSON.stringify(fin).includes("FAKEKEY"));
  // reintento del mismo tarea_id en streaming: se entrega lo guardado una sola vez y no se llama al proveedor
  const antes = g.chat.length, r2 = await leerSse(B, { model: "groq/qwen/qwen3.8-27b", tarea_id: "r5-1" });
  assert.equal(r2.texto, "Hola mundo feliz."); assert.equal(g.chat.length, antes);
});

test("R5 + 188: el proveedor se cae a mitad de un stream con tarea_id: el cliente conserva lo recibido + error; el reintento (stream) recibe el texto una sola vez y el proveedor CONTINUA desde el checkpoint", async () => {
  const g = await proveedor(({ res, n }) => {
    res.writeHead(200, { "content-type": "text/event-stream" });
    if (n === 1) { res.write(ev(delta("Primera parte. "))); setTimeout(() => res.destroy(), 80); return; }
    res.write(ev(delta("Segunda parte."))); res.write(ev(finr("stop"))); res.end(ev("[DONE]"));
  });
  const dir = disco("f");
  const B = await arrancar("a4-caida", { BRIDGE_STATE_DIR: dir, TEST_GROQ_URL: g.url, GROQ_API_KEY: KGROQ, BRIDGE_CHECKPOINT_FLUSH_CHARS: "4", BRIDGE_SSE_KEEPALIVE_MS: "60000" });
  const r1 = await leerSse(B, { model: "groq/qwen/qwen3.8-27b", tarea_id: "caida-1" });
  assert.equal(r1.texto, "Primera parte. "); assert.ok(r1.chunks.some((c) => c.error), "chunk de error"); assert.equal(r1.datos.at(-1), "[DONE]");
  const ck = JSON.parse(fs.readFileSync(arch(B.state, "caida-1"), "utf8")); assert.equal(ck.parcial, "Primera parte. "); assert.equal(ck.estado, "ERROR");
  const r2 = await leerSse(B, { model: "groq/qwen/qwen3.8-27b", tarea_id: "caida-1" });
  assert.equal(r2.texto, "Primera parte. Segunda parte.", "completo, una sola vez");
  assert.deepEqual(g.chat.at(-1).body.messages.slice(-2), [{ role: "assistant", content: "Primera parte. " }, { role: "user", content: CONT }]);
  assert.equal(g.chat.length, 2, "no se repite la parte ya generada");
});

test("R4: texto + tool_calls viajan JUNTOS en JSON y en SSE, tambien con tarea_id, y finish_reason es tool_calls aunque el proveedor diga stop; la tarea queda ESPERANDO_TOOLS y el listado cuenta las pendientes", async () => {
  const s1 = await proveedor(() => ok("voy a escribir el archivo", "stop", { tool_calls: [tc("call_a"), tc("call_b", "leer")] })), dir = disco("g");
  const B = await arrancar("a4-r4", { BRIDGE_STATE_DIR: dir, SWECODE_URL_S1: s1.url });
  const j = await chat(B, {});
  assert.equal(j.json.choices[0].finish_reason, "tool_calls"); assert.equal(j.json.choices[0].message.content, "voy a escribir el archivo"); assert.deepEqual(j.json.choices[0].message.tool_calls.map((t) => t.id), ["call_a", "call_b"]);
  const s = await leerSse(B, { model: "qwen2.5-coder-1.5b" });
  assert.equal(s.texto, "voy a escribir el archivo"); const tcs = s.chunks.flatMap((c) => c.choices?.[0]?.delta?.tool_calls || []); assert.deepEqual(tcs.map((t) => t.id), ["call_a", "call_b"]);
  assert.equal(s.chunks.at(-1).choices[0].finish_reason, "tool_calls");
  const t = await chat(B, { tarea_id: "r4-t" });
  assert.equal(t.json.choices[0].finish_reason, "tool_calls"); assert.equal(t.json.choices[0].message.content, "voy a escribir el archivo"); assert.equal(t.json.choices[0].message.tool_calls.length, 2);
  assert.equal(t.json.tarea.estado, "WAIT_TOOLS"); assert.equal(t.json.tarea.fase, "ESPERANDO_TOOLS");
  const ts = await leerSse(B, { model: "qwen2.5-coder-1.5b", tarea_id: "r4-t", messages: [{ role: "user", content: "escribe A" }] });  // el cliente perdio la respuesta: reintenta y las llamadas siguen ahi (mismos ids)
  assert.equal(ts.texto, "voy a escribir el archivo"); assert.deepEqual(ts.chunks.flatMap((c) => c.choices?.[0]?.delta?.tool_calls || []).map((x) => x.id), ["call_a", "call_b"]); assert.equal(ts.chunks.at(-1).choices[0].finish_reason, "tool_calls");
  assert.equal(s1.chat.length, 3, "el reintento de la tarea no vuelve a llamar al modelo");
  const sec = (await get(B, "/v1/secciones")).json.secciones.find((x) => x.conv_id === "r4-t");
  assert.equal(sec.herramientas_pendientes, 2); assert.equal(sec.fase, "ESPERANDO_TOOLS");
});
