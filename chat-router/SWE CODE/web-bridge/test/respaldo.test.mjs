import test from "node:test";
import assert from "node:assert/strict";
import http from "node:http";
import { respaldo, BASES, esExterno, idsRespaldo, timeoutDe, TIMEOUT_DEFECTO_MS } from "../src/respaldo.js";

const servidor = (codigo, texto) => new Promise((ok) => {
  const vistos = [];
  const s = http.createServer((req, res) => {
    let d = ""; req.on("data", (c) => d += c); req.on("end", () => {
      vistos.push({ url: req.url, auth: req.headers.authorization, body: d ? JSON.parse(d) : null });
      res.writeHead(codigo, { "content-type": "application/json" }); res.end(JSON.stringify({ model: "m", choices: [{ message: { role: "assistant", content: texto } }] }));
    });
  }).listen(0, "127.0.0.1", () => ok({ s, vistos, url: `http://127.0.0.1:${s.address().port}` }));
});
const msgs = [{ role: "user", content: "hola" }];

test("si la web falla responde Groq primero, con su clave", async () => {
  const g = await servidor(200, "de groq"), n = await servidor(200, "de nvidia");
  Object.assign(BASES, { groq: g.url, nvidia: n.url });
  const r = await respaldo(msgs, { env: { GROQ_API_KEY: "gsk-1", NVIDIA_API_KEY: "nv-1" } });
  g.s.close(); n.s.close();
  assert.equal(r.salida, "de groq"); assert.equal(r.via, "groq"); assert.equal(n.vistos.length, 0);
  assert.equal(g.vistos[0].auth, "Bearer gsk-1");
});

test("si Groq no responde pasa a NVIDIA", async () => {
  const g = await servidor(500, ""), n = await servidor(200, "de nvidia");
  Object.assign(BASES, { groq: g.url, nvidia: n.url });
  const r = await respaldo(msgs, { env: { GROQ_API_KEY: "gsk-1", NVIDIA_API_KEY: "nv-1" } });
  g.s.close(); n.s.close();
  assert.equal(r.via, "nvidia");
});

test("si Groq y NVIDIA fallan (o no hay clave) cae a HF local S1..S3, saltando al siguiente slot", async () => {
  const l1 = await servidor(500, ""), l2 = await servidor(200, "de S2");
  Object.assign(BASES, { groq: "http://127.0.0.1:9", nvidia: "http://127.0.0.1:9" });
  const r = await respaldo(msgs, { env: { GROQ_API_KEY: "gsk-1", SWECODE_URL_S1: l1.url, SWECODE_URL_S2: l2.url } });
  l1.s.close(); l2.s.close();
  assert.equal(r.salida, "de S2"); assert.equal(r.via, "hf-local"); assert.equal(l2.vistos[0].body.model, "lfm2.5-350m");
});

test("sin nada configurado devuelve error claro", async () => {
  await assert.rejects(() => respaldo(msgs, { env: {} }), /RESPALDO_AGOTADO/);
});

test("ids groq/ y nvidia/ del selector son externos y se listan para OpenClaw", () => {
  assert.ok(esExterno("groq/qwen/qwen3.8-27b")); assert.ok(esExterno("nvidia/minimaxai/minimax-m3.1-flash")); assert.ok(!esExterno("web-qwen38max"));
  const ids = idsRespaldo({}); assert.ok(ids.some((i) => i.startsWith("groq/")) && ids.some((i) => i.startsWith("nvidia/")) && ids.includes("lfm2.5-350m"));
});

test("las herramientas (tools) pasan a Groq/NVIDIA/locales y sus tool_calls vuelven (el Harness las ejecuta)", async () => {
  const vistos = [];
  const s = await new Promise((ok) => { const sv = http.createServer((req, res) => { let d = ""; req.on("data", (c) => d += c); req.on("end", () => { vistos.push(JSON.parse(d)); res.writeHead(200, { "content-type": "application/json" }); res.end(JSON.stringify({ choices: [{ finish_reason: "tool_calls", message: { role: "assistant", content: null, tool_calls: [{ id: "c1", type: "function", function: { name: "github_leer", arguments: "{}" } }] } }] })); }); }).listen(0, "127.0.0.1", () => ok(sv)); });
  Object.assign(BASES, { groq: `http://127.0.0.1:${s.address().port}` });
  const tools = [{ type: "function", function: { name: "github_leer", parameters: { type: "object" } } }];
  const { externo } = await import("../src/respaldo.js");
  const r = await externo("groq/m", msgs, { env: { GROQ_API_KEY: "k" }, extra: { tools, tool_choice: "auto" } });
  s.closeAllConnections?.(); s.close();
  assert.deepEqual(vistos[0].tools, tools); assert.equal(vistos[0].tool_choice, "auto");
  assert.equal(r.tool_calls[0].function.name, "github_leer"); assert.equal(r.finish_reason, "tool_calls");
});

test("setClaves: claves inyectadas se suman al entorno sin duplicar, max 20, ignora vacias, y estadoRespaldo solo cuenta", async () => {
  const { setClaves, estadoRespaldo } = await import("../src/respaldo.js");
  const g = await servidor(500, ""), g2 = await servidor(200, "ok-inyectada");
  try {
    assert.equal(estadoRespaldo({}).groq, 0); assert.equal(estadoRespaldo({}).nvidia, 0); assert.equal(estadoRespaldo({}).hf_local, 0);
    setClaves({ groq: ["gsk-INY-1", "", "  ", "gsk-ENV"], nvidia: "nv-INY-1" });
    // entorno + inyectadas sin duplicar (gsk-ENV esta en ambos)
    assert.equal(estadoRespaldo({ GROQ_API_KEY: "gsk-ENV" }).groq, 2); assert.equal(estadoRespaldo({ GROQ_API_KEY: "gsk-ENV" }).nvidia, 1);
    const crudo = JSON.stringify(estadoRespaldo({ GROQ_API_KEY: "gsk-ENV" }));
    assert.ok(!/gsk-|nv-/.test(crudo), "estadoRespaldo no filtra valores");
    // se usan de verdad, tras las del entorno
    Object.assign(BASES, { groq: g2.url });
    const r = await respaldo(msgs, { env: {} });
    assert.equal(r.salida, "ok-inyectada"); assert.equal(g2.vistos[0].auth, "Bearer gsk-INY-1");
    // max 20 por proveedor
    setClaves({ groq: Array.from({ length: 30 }, (_, i) => `k${i}`) });
    assert.equal(estadoRespaldo({}).groq, 20);
    // un proveedor ausente no se toca
    assert.equal(estadoRespaldo({}).nvidia, 1);
    // lista vacia limpia
    setClaves({ groq: [], nvidia: "" });
    assert.equal(estadoRespaldo({}).groq, 0); assert.equal(estadoRespaldo({}).nvidia, 0); assert.equal(estadoRespaldo({}).hf_local, 0);
    // entrada invalida no revienta
    assert.doesNotThrow(() => { setClaves(); setClaves(null); setClaves({ groq: 5 }); });
  } finally { setClaves({ groq: [], nvidia: [] }); g.s.close(); g2.s.close(); }
});

test("esExterno valida contra MODELOS_API: ids autorizados si, groq/llama-3.3-70b-versatile y similares no; el modelo fijado por entorno tambien vale", () => {
  for (const ok of ["groq/qwen/qwen3.8-27b", "nvidia/minimaxai/minimax-m3.1-flash", "nvidia/meta/muse-glimmer-30b", "nvidia/nvidia/nemotron-3-ultra-550b-a55b", "nvidia/z-ai/glm-5.3"]) assert.ok(esExterno(ok), ok);
  for (const mal of ["groq/llama-3.3-70b-versatile", "groq/xxx", "nvidia/meta/llama-3.3-70b-instruct", "groq/", "groq", "openai/gpt-4", "", null, undefined, "groq/qwen/qwen3.8-27b-otro", "GROQ/qwen/qwen3.8-27b"]) assert.ok(!esExterno(mal), String(mal));
  assert.ok(esExterno("nvidia/forzado/m", { RIU_SWE_NVIDIA_MODELO: "forzado/m" }), "el id fijado por el operador en el entorno es autorizado");
  assert.ok(!esExterno("nvidia/forzado/m", {}));
});

test("timeout por defecto de Groq 60000 ms (por modelo, tabla unica R8); los no listados usan el global; RIU_SWE_TIMEOUTS y opts.timeoutsModelo mandan sobre el defecto", () => {
  const r = { timeoutMs: TIMEOUT_DEFECTO_MS };
  assert.equal(timeoutDe("qwen/qwen3.8-27b", {}, r), 60000);
  assert.equal(timeoutDe("minimaxai/minimax-m3.1-flash", {}, r), 90000);  // R8: tabla unica (antes: el global)
  assert.equal(timeoutDe("modelo-que-no-esta-en-la-tabla", {}, r), TIMEOUT_DEFECTO_MS);
  assert.equal(timeoutDe("qwen/qwen3.8-27b", { RIU_SWE_TIMEOUTS: JSON.stringify({ "qwen/qwen3.8-27b": 15000 }) }, r), 15000);
  assert.equal(timeoutDe("qwen/qwen3.8-27b", {}, { ...r, timeoutsModelo: { "qwen/qwen3.8-27b": 7000 } }), 7000);
  assert.equal(timeoutDe("qwen/qwen3.8-27b", { RIU_SWE_TIMEOUTS: "no-json" }, r), 60000);
});

test("HF local: S1/S2/S3 con 503 no figuran DISPONIBLES y no se sustituyen por otra API", async () => {
  const { disponibilidadLocal, estadosModelosLocales } = await import("../src/respaldo.js");
  const env = { SWECODE_URL_S1: "https://s1.example/v1", SWECODE_URL_S2: "https://s2.example/v1", SWECODE_URL_S3: "https://s3.example/v1" };
  const llamadas = [];
  const estado = await disponibilidadLocal({ env, refrescar:true, consultar: async url => {
    llamadas.push(url);
    return {status:503, ok:false};
  }});
  assert.equal(llamadas.length, 3);
  assert.ok(llamadas.every(x => x.endsWith("/v1/models")));
  const [liquid] = estadosModelosLocales(["lfm2.5-350m"],estado);
  assert.equal(liquid.estado,"NO_DISPONIBLE");
  assert.equal(liquid.disponible,false);
  assert.match(liquid.motivo,/S1:HTTP_503.*S2:HTTP_503.*S3:HTTP_503/);
  assert.equal(liquid.id,"hf/lfm2.5-350m");
});
test("HF local: un S2 que anuncia un modelo permite seleccionarlo sin tocar S1 ni agentes", async () => {
  const { disponibilidadLocal, estadosModelosLocales } = await import("../src/respaldo.js");
  const estado = await disponibilidadLocal({ env:{SWECODE_URL_S1:"https://s1.example/v1",SWECODE_URL_S2:"https://s2.example/v1"}, refrescar:true,
    consultar: async url => url.includes("s2.example") ? {status:200,ok:true,json:async()=>({data:[{id:"lfm2.5-350m",loaded:true}]})} : {status:503,ok:false}});
  const [liquid,qwen]=estadosModelosLocales(["lfm2.5-350m","qwen2.5-coder-1.5b"],estado);
  assert.equal(liquid.estado,"DISPONIBLE");
  assert.equal(qwen.estado,"SIN_VERIFICAR");
});

test("HF: preferir el slot con GGUF cargado y no declarar DISPONIBLE por listado sin load", async () => {
  const { ordenSlotsLocal, estadosModelosLocales } = await import("../src/respaldo.js");
  const env={SWECODE_URL_S1:"https://s1.example/v1",SWECODE_URL_S2:"https://s2.example/v1",SWECODE_URL_S3:"https://s3.example/v1"};
  const slots=[{slot:"S1",estado:"CATALOGO_OK",modelos:["lfm2.5-350m"],cargados:[],primario:"qwen2.5-coder-1.5b"},
    {slot:"S2",estado:"CATALOGO_OK",modelos:["lfm2.5-350m"],cargados:["lfm2.5-350m"],primario:"lfm2.5-350m"},
    {slot:"S3",estado:"CATALOGO_OK",modelos:["lfm2.5-350m"],cargados:[],primario:"qwen3-0.6b"}];
  assert.deepEqual(ordenSlotsLocal("lfm2.5-350m",{slots},env),[2,1,3]);
  const status=estadosModelosLocales(["lfm2.5-350m"],{slots,configurados:3});
  assert.equal(status[0].estado,"DISPONIBLE");
  const cold=estadosModelosLocales(["lfm2.5-350m"],{slots:slots.map(s=>({...s,cargados:[]})),configurados:3});
  assert.equal(cold[0].estado,"SIN_VERIFICAR");
});
test("HF: si /v1/models marca unloaded, no prometer respuesta antes del cold-start", async () => {
  const { disponibilidadLocal, estadosModelosLocales } = await import("../src/respaldo.js");
  const estado=await disponibilidadLocal({env:{SWECODE_URL_S1:"https://s1.example/v1"},refrescar:true,
    consultar:async()=>({ok:true,status:200,json:async()=>({data:[{id:"lfm2.5-350m",loaded:false,primary:true}]})})});
  assert.equal(estado.slots[0].primario,"lfm2.5-350m");
  assert.equal(estadosModelosLocales(["lfm2.5-350m"],estado)[0].estado,"SIN_VERIFICAR");
});

test("HF 503 JSON: clasifica falla llama-server vs proxy sin exponer secretos", async () => {
  const { local } = await import('../src/respaldo.js');
  const base='https://un-servidor-hf.example/v1';
  const original=globalThis.fetch;
  try {
    globalThis.fetch=async(url,opts)=>{
      if(String(url).endsWith('/models')) return {ok:true,status:200,json:async()=>({data:[{id:'lfm2.5-350m'}]})};
      return {ok:false,status:503,headers:{get:(n)=>n==='content-type'?'application/json':null},
        json:async()=>({error:'load failed: llama-server exited: PRIVATE_PATH_NEVER_LEAK'})};
    };
    await assert.rejects(()=>local('lfm2.5-350m',msgs,{env:{SWECODE_URL_S1:base},opts:{esperar:async()=>{},timeoutMs:1000}}),
      err=>err.code==='HF_LOCAL_FALLO' && /LLAMA_SERVER_FALLO/.test(err.message) && !/PRIVATE_PATH/.test(err.message));
  } finally {globalThis.fetch=original;}
});
