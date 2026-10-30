import test from "node:test";
import assert from "node:assert/strict";
import http from "node:http";
import { respaldo, BASES, esExterno, idsRespaldo } from "../src/respaldo.js";

const servidor = (codigo, texto) => new Promise((ok) => {
  const vistos = [];
  const s = http.createServer((req, res) => {
    let d = ""; req.on("data", (c) => d += c); req.on("end", () => {
      vistos.push({ url: req.url, auth: req.headers.authorization, body: JSON.parse(d) });
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
  assert.ok(esExterno("groq/llama-3.3-70b-versatile")); assert.ok(esExterno("nvidia/meta/llama-3.3-70b-instruct")); assert.ok(!esExterno("web-qwen38max"));
  const ids = idsRespaldo({}); assert.ok(ids.some((i) => i.startsWith("groq/")) && ids.some((i) => i.startsWith("nvidia/")) && ids.includes("lfm2.5-350m"));
});
