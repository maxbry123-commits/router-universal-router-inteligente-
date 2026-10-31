// Integracion de server.js REAL: SSE con streaming real desde Groq/NVIDIA (fragmentos reenviados al instante como chat.completion.chunk),
// sin duplicar respuesta en el failover, tool_calls reconstruidos, rutas no-stream intactas, /health con metricas y disponibilidad (GET /models).
// Proveedores falsos con node:http, claves FALSAS. Nunca red real.
import test, { before, after } from "node:test";
import assert from "node:assert/strict";
import fs from "node:fs";
import http from "node:http";
import path from "node:path";
import { prepararApp, arrancar, limpiar, registrarMock, TMP } from "./helpers/bridge_app.mjs";
import './helpers/acceso.mjs';

const CONT = "Continúa exactamente donde terminó, sin repetir";
const ev = (o) => `data: ${typeof o === "string" ? o : JSON.stringify(o)}\n\n`;
const delta = (content) => ({ choices: [{ index: 0, delta: { content }, finish_reason: null }] });
const fin = (r) => ({ choices: [{ index: 0, delta: {}, finish_reason: r }] });

// handler({ body, n, url, req, res }) controla la respuesta; /models por defecto devuelve la lista de `modelos`
const proveedor = (handler, modelos = []) => new Promise((listo) => {
  const chat = [], vistos = []; let n = 0;
  const s = http.createServer((req, res) => {
    let d = ""; req.on("data", (c) => d += c); req.on("end", () => {
      const v = { url: req.url, auth: req.headers.authorization, body: d ? JSON.parse(d) : null };
      vistos.push(v);
      if (v.url.endsWith("/models")) { res.writeHead(200, { "content-type": "application/json" }); return res.end(JSON.stringify({ data: modelos.map((id) => ({ id })) })); }
      chat.push(v); n++;
      handler({ ...v, n, req, res });
    });
  }).listen(0, "127.0.0.1", () => { registrarMock(s); listo({ chat, vistos, url: `http://127.0.0.1:${s.address().port}` }); });
});
const sseHead = (res) => res.writeHead(200, { "content-type": "text/event-stream", "cache-control": "no-cache" });
const jsonRes = (res, o, status = 200) => { res.writeHead(status, { "content-type": "application/json" }); res.end(JSON.stringify(o)); };
const textoJson = (t) => ({ choices: [{ finish_reason: "stop", message: { role: "assistant", content: t } }] });

let groq, nvidia, S, g, nv, puerta;
let soltar = () => {};
const comportamiento = { groq: null, nvidia: null };  // el test fija que hace cada proveedor falso

before(async () => {
  prepararApp();
  fs.writeFileSync(path.join(TMP, "app", "preload.mjs"), `const r = await import('./src/respaldo.js');\nif (process.env.TEST_GROQ_URL) r.BASES.groq = process.env.TEST_GROQ_URL;\nif (process.env.TEST_NVIDIA_URL) r.BASES.nvidia = process.env.TEST_NVIDIA_URL;\n`);
  g = await proveedor((x) => comportamiento.groq(x), ["qwen/qwen3.8-27b", "otro"]);
  nv = await proveedor((x) => comportamiento.nvidia(x), ["minimaxai/minimax-m3.1-flash", "meta/muse-glimmer-30b"]);
  S = await arrancar("stream", { TEST_GROQ_URL: g.url, TEST_NVIDIA_URL: nv.url, GROQ_API_KEY: "gsk-FAKE-STREAM-1", GROQ_API_KEY_2: "gsk-FAKE-STREAM-2", NVIDIA_API_KEY: "nv-FAKE-STREAM-1", BRIDGE_RESPALDO_MS: "4000", BRIDGE_DEADLINE_MS: "8000", BRIDGE_SSE_KEEPALIVE_MS: "60000" });
});
after(() => limpiar());
test.beforeEach(() => { g.chat.length = 0; nv.chat.length = 0; comportamiento.groq = ({ res }) => jsonRes(res, textoJson("de-groq")); comportamiento.nvidia = ({ res }) => jsonRes(res, textoJson("de-nvidia")); });

// lee el SSE por bloques conforme llegan: [{t (ms desde el inicio), bloque}]
async function leerSse(body, { alPrimerContenido, senal } = {}) {
  const r = await fetch(S.base + "/v1/chat/completions", { method: "POST", headers: { "content-type": "application/json" }, body: JSON.stringify({ messages: [{ role: "user", content: "hola mundo" }], stream: true, ...body }), signal: senal });
  const dec = new TextDecoder(), t0 = Date.now(), bloques = []; let buf = "", avisado = false;
  for await (const c of r.body) {
    buf += dec.decode(c, { stream: true });
    let i; while ((i = buf.indexOf("\n\n")) >= 0) {
      const b = buf.slice(0, i).trim(); buf = buf.slice(i + 2); if (!b) continue;
      bloques.push({ t: Date.now() - t0, b });
      if (!avisado && alPrimerContenido && b.startsWith("data: ") && b !== "data: [DONE]" && JSON.parse(b.slice(6)).choices?.[0]?.delta?.content) { avisado = true; await alPrimerContenido(); }
    }
  }
  const datos = bloques.filter((x) => x.b.startsWith("data: ")).map((x) => x.b.slice(6));
  return { status: r.status, headers: r.headers, bloques, datos, chunks: datos.filter((d) => d !== "[DONE]").map((d) => JSON.parse(d)) };
}
const contenido = (chunks) => chunks.map((c) => c.choices?.[0]?.delta?.content || "").join("");

test("ST1. groq/<id> con stream:true: el primer fragmento llega al cliente MIENTRAS el proveedor aun no termina (streaming real, no chunks tras la espera)", async () => {
  let abrir; const hasta = new Promise((r) => { abrir = r; });
  comportamiento.groq = ({ res }) => { sseHead(res); res.write(ev(delta("Hola "))); hasta.then(() => { res.write(ev(delta("mundo"))); res.write(ev({ ...fin("stop"), usage: { completion_tokens: 7 } })); res.end(ev("[DONE]")); }); };
  const r = await leerSse({ model: "groq/qwen/qwen3.8-27b" }, { alPrimerContenido: async () => { assert.equal(g.chat.length, 1); await new Promise((x) => setTimeout(x, 150)); abrir(); } });
  assert.equal(r.status, 200); assert.match(r.headers.get("content-type"), /text\/event-stream/);
  assert.equal(r.datos.at(-1), "[DONE]");
  assert.equal(r.chunks[0].choices[0].delta.role, "assistant");
  assert.ok(r.chunks.every((c) => c.object === "chat.completion.chunk" && c.id === r.chunks[0].id));
  assert.equal(contenido(r.chunks), "Hola mundo");
  const primero = r.bloques.find((x) => x.b.includes("Hola ")), ultimo = r.bloques.at(-1);
  assert.ok(ultimo.t - primero.t >= 100, `el primer fragmento llego ${ultimo.t - primero.t} ms antes del final`);
  const ult = r.chunks.at(-1);
  assert.equal(ult.choices[0].finish_reason, "stop"); assert.equal(r.chunks.filter((c) => c.choices?.[0]?.finish_reason).length, 1);
  assert.equal(ult.modelo_usado, "groq/qwen/qwen3.8-27b"); assert.equal(ult.via_respaldo, "groq");
  assert.equal(ult.metricas.stream, true); assert.equal(typeof ult.metricas.ttft_ms, "number");
  assert.equal(r.headers.get("x-modelo-usado"), "groq/qwen/qwen3.8-27b"); assert.equal(r.headers.get("x-via-respaldo"), "groq");
  assert.equal(g.chat[0].body.stream, true); assert.equal(g.chat[0].body.model, "qwen/qwen3.8-27b"); assert.equal(g.chat[0].body.reasoning_format, "hidden");
});

test("ST2. tool_calls en streaming: texto al instante, tool_calls completos (con index) en un chunk, finish_reason tool_calls; el bridge no ejecuta nada", async () => {
  const tc = (index, extra) => ({ choices: [{ delta: { tool_calls: [{ index, ...extra }] }, finish_reason: null }] });
  comportamiento.nvidia = ({ res }) => { sseHead(res); for (const e of [delta("Leo. "), tc(0, { id: "call_1", type: "function", function: { name: "github_leer", arguments: "" } }), tc(0, { function: { arguments: "{\"ruta\":" } }), tc(0, { function: { arguments: "\"a.js\"}" } }), fin("tool_calls")]) res.write(ev(e)); res.end(ev("[DONE]")); };
  const tools = [{ type: "function", function: { name: "github_leer", parameters: { type: "object" } } }];
  const r = await leerSse({ model: "nvidia/minimaxai/minimax-m3.1-flash", tools, tool_choice: "auto" });
  assert.equal(contenido(r.chunks), "Leo. ");
  const conT = r.chunks.filter((c) => c.choices?.[0]?.delta?.tool_calls);
  assert.equal(conT.length, 1);
  assert.deepEqual(conT[0].choices[0].delta.tool_calls, [{ index: 0, id: "call_1", type: "function", function: { name: "github_leer", arguments: "{\"ruta\":\"a.js\"}" } }]);
  assert.equal(r.chunks.at(-1).choices[0].finish_reason, "tool_calls"); assert.equal(r.datos.at(-1), "[DONE]");
  assert.equal(nv.chat[0].body.model, "minimaxai/minimax-m3.1-flash"); assert.deepEqual(nv.chat[0].body.tools, tools); assert.equal(nv.chat[0].body.max_tokens, 4096);
});

test("ST3. failover tras emitir texto: lo emitido NO se repite; el siguiente proveedor continua con [assistant parcial, 'Continua...'] y el cliente recibe todo una sola vez", async () => {
  comportamiento.groq = ({ res }) => { if (g.chat.length > 1) return jsonRes(res, {}, 503); sseHead(res); res.write(ev(delta("Parte uno. "))); setTimeout(() => res.destroy(), 30); };
  comportamiento.nvidia = ({ res }) => { sseHead(res); res.write(ev(delta("Parte dos."))); res.write(ev(fin("stop"))); res.end(ev("[DONE]")); };
  const r = await leerSse({ model: "groq/qwen/qwen3.8-27b" });
  assert.equal(contenido(r.chunks), "Parte uno. Parte dos.");
  assert.equal(r.chunks.at(-1).choices[0].finish_reason, "stop"); assert.equal(r.datos.at(-1), "[DONE]");
  assert.equal(r.chunks.at(-1).via_respaldo, "nvidia"); assert.equal(r.chunks.at(-1).modelo_usado, "nvidia/minimaxai/minimax-m3.1-flash");
  assert.deepEqual(nv.chat[0].body.messages.slice(-2), [{ role: "assistant", content: "Parte uno. " }, { role: "user", content: CONT }]);
  assert.equal(r.chunks.filter((c) => c.choices?.[0]?.delta?.role).length, 1, "un solo chunk de rol");
  assert.equal(r.chunks.filter((c) => c.choices?.[0]?.finish_reason).length, 1);
});

test("ST4. todo cae tras texto parcial: el cliente conserva lo recibido y obtiene un chunk de error + [DONE] (sin claves)", async () => {
  comportamiento.groq = ({ res }) => { if (g.chat.length > 1) return jsonRes(res, {}, 503); sseHead(res); res.write(ev(delta("Solo esto. "))); setTimeout(() => res.destroy(), 30); };
  comportamiento.nvidia = ({ res }) => jsonRes(res, {}, 503);
  const r = await leerSse({ model: "groq/qwen/qwen3.8-27b" });
  assert.equal(r.status, 200); assert.equal(contenido(r.chunks), "Solo esto. ");
  const err = r.chunks.find((c) => c.error);
  assert.ok(err); assert.equal(err.error.code, "RESPALDO_AGOTADO"); assert.equal(r.datos.at(-1), "[DONE]");
  assert.ok(!JSON.stringify(r.datos).includes("FAKE-STREAM"));
});

test("ST5. sin stream: la misma peticion devuelve JSON de siempre, sin stream hacia el proveedor", async () => {
  const j = await fetch(S.base + "/v1/chat/completions", { method: "POST", headers: { "content-type": "application/json" }, body: JSON.stringify({ model: "groq/qwen/qwen3.8-27b", messages: [{ role: "user", content: "hola" }] }) });
  assert.match(j.headers.get("content-type"), /application\/json/);
  const o = await j.json();
  assert.equal(o.choices[0].message.content, "de-groq"); assert.equal(o.object, "chat.completion"); assert.equal(o.via_respaldo, "groq");
  assert.ok(!("stream" in g.chat[0].body)); assert.equal(g.chat[0].body.reasoning_effort, "medium");
  assert.equal(o.metricas.stream, false);
});

test("ST6. el cliente se desconecta a mitad: el bridge cancela la conexion con el proveedor y no prueba otras claves", async () => {
  let cerrada; const alCerrar = new Promise((r) => { cerrada = r; });
  comportamiento.groq = ({ res, req }) => { sseHead(res); res.write(ev(delta("empiezo "))); req.on("close", cerrada); res.on("close", cerrada); };
  const ac = new AbortController();
  await leerSse({ model: "groq/qwen/qwen3.8-27b" }, { senal: ac.signal, alPrimerContenido: async () => ac.abort() }).catch(() => {});
  await Promise.race([alCerrar, new Promise((_, no) => setTimeout(() => no(new Error("el proveedor no vio el cierre")), 3000))]);
  await new Promise((r) => setTimeout(r, 200));
  assert.equal(g.chat.length, 1, "no se reintento con otra clave ni proveedor");
  assert.equal(nv.chat.length, 0);
});

test("ST7. /health trae metricas (TTFT, tokens/s) por modelo sin valores de claves; GET /v1/modelos/disponibilidad marca NO DISPONIBLE los ids ausentes del GET /models", async () => {
  comportamiento.groq = ({ res }) => { sseHead(res); res.write(ev(delta("a"))); res.write(ev(fin("stop"))); res.end(ev("[DONE]")); };
  await leerSse({ model: "groq/qwen/qwen3.8-27b" });
  const h = await (await fetch(S.base + "/health")).json();
  assert.ok(h.metricas["groq/qwen/qwen3.8-27b"].llamadas >= 1); assert.ok(!JSON.stringify(h).includes("FAKE-STREAM"));
  const d = await (await fetch(S.base + "/v1/modelos/disponibilidad")).json();
  const por = Object.fromEntries(d.modelos.map((m) => [m.id, m.estado]));
  assert.equal(por["groq/qwen/qwen3.8-27b"], "DISPONIBLE"); assert.equal(por["nvidia/minimaxai/minimax-m3.1-flash"], "DISPONIBLE"); assert.equal(por["nvidia/meta/muse-glimmer-30b"], "DISPONIBLE");
  assert.equal(por["nvidia/nvidia/nemotron-3-ultra-550b-a55b"], "NO DISPONIBLE"); assert.equal(por["nvidia/z-ai/glm-5.3"], "NO DISPONIBLE");
  assert.ok(!JSON.stringify(d).includes("FAKE-STREAM"));
  assert.ok(!d.modelos.some((m) => /llama/i.test(m.id)));
});

test("ST8. swecode-asesoria usa Groq con el id Qwen 3.8 (no Llama) como via primaria", async () => {
  const r = await fetch(S.base + "/v1/chat/completions", { method: "POST", headers: { "content-type": "application/json" }, body: JSON.stringify({ model: "swecode-asesoria", proyecto: "demo-stream", messages: [{ role: "user", content: "planear" }] }) });
  const o = await r.json();
  assert.equal(r.status, 200); assert.equal(o.via_primaria, "groq");
  assert.equal(g.chat[0].body.model, "qwen/qwen3.8-27b");
});
