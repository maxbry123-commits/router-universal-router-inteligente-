import test from "node:test";
import assert from "node:assert/strict";
import http from "node:http";
import { spawnSync } from "node:child_process";
import { createRequire } from "node:module";
import { fileURLToPath } from "node:url";
const require = createRequire(import.meta.url);
const S = require("../server.js"); // no necesita `ws`: se carga perezoso
const TOKEN = "t".repeat(16) + "-secreto";

test("fail-closed: sin PUENTE_TOKEN (o corto) el proceso sale con error claro", () => {
  for (const t of ["", "corto"]) {
    const r = spawnSync(process.execPath, [fileURLToPath(new URL("../server.js", import.meta.url))], { env: { ...process.env, PUENTE_TOKEN: t, PUENTE_PORT: "0" }, encoding: "utf8", timeout: 5000 });
    assert.equal(r.status, 1, `token "${t}"`);
    assert.match(r.stderr, /PUENTE_TOKEN/);
  }
});

test("autorizado: Bearer correcto si, el resto no; token corto nunca autoriza", () => {
  assert.equal(S.autorizado({ authorization: `Bearer ${TOKEN}` }, TOKEN), true);
  assert.equal(S.autorizado({ authorization: "Bearer otro" }, TOKEN), false);
  assert.equal(S.autorizado({ authorization: TOKEN }, TOKEN), false);
  assert.equal(S.autorizado({}, TOKEN), false);
  assert.equal(S.autorizado({ authorization: "Bearer corto" }, "corto"), false);
  assert.equal(S.autorizado({ authorization: "Bearer " }, ""), false);
  assert.equal(S.autorizado({ authorization: "Bearer " }, undefined), false);
});

test("autorizadoWs: acepta el subprotocolo token-<token>", () => {
  assert.equal(S.autorizadoWs({ "sec-websocket-protocol": `token-${TOKEN}` }, TOKEN), true);
  assert.equal(S.autorizadoWs({ "sec-websocket-protocol": `otro, token-${TOKEN}` }, TOKEN), true);
  assert.equal(S.autorizadoWs({ "sec-websocket-protocol": "token-malo" }, TOKEN), false);
  assert.equal(S.autorizadoWs({}, TOKEN), false);
  assert.equal(S.autorizadoWs({ "sec-websocket-protocol": "token-" }, ""), false);
});

test("manejarMcp: null, no-objeto y arrays dan -32600 sin lanzar", async () => {
  for (const b of [null, 5, "x", true, [], undefined, {}, { method: 3 }]) {
    const r = await S.manejarMcp(b);
    assert.equal(r.error.code, -32600, JSON.stringify(b));
    assert.equal(r.id, null);
  }
});

test("manejarMcp: initialize, tools/list, metodo desconocido, params invalidos y error del movil", async () => {
  assert.equal((await S.manejarMcp({ id: 1, method: "initialize" })).result.serverInfo.name, "swecode-puente-movil");
  assert.equal((await S.manejarMcp({ id: 2, method: "tools/list" })).result.tools.length, 5);
  assert.equal((await S.manejarMcp({ id: 3, method: "zzz" })).error.code, -32601);
  for (const params of [null, undefined, 7, { name: "no_existe" }]) assert.equal((await S.manejarMcp({ id: 4, method: "tools/call", params })).error.code, -32602);
  const ok = await S.manejarMcp({ id: 5, method: "tools/call", params: { name: "tap", arguments: { x: 1, y: 2 } } }, async (a, args) => `${a}:${args.x}`);
  assert.equal(ok.result.content[0].text, "tap:1");
  const mal = await S.manejarMcp({ id: 6, method: "tools/call", params: { name: "atras" } }, async () => { throw new Error("APK_NO_CONECTADA"); });
  assert.deepEqual([mal.error.code, mal.error.message], [-32000, "APK_NO_CONECTADA"]);
});

function pedir(port, { headers = {}, body, path = "/mcp" }) {
  return new Promise((resolve, reject) => {
    const req = http.request({ port, path, method: "POST", headers }, (res) => {
      let d = ""; res.on("data", (c) => (d += c)); res.on("end", () => resolve({ status: res.statusCode, body: d }));
    });
    req.on("error", reject);
    req.end(body);
  });
}

test("HTTP /mcp: 401 sin token, JSON invalido y null no tumban el proceso, 413 sobre 1 MB", async () => {
  const srv = S.crearServidor({ token: TOKEN });
  await new Promise((r) => srv.listen(0, "127.0.0.1", r));
  const port = srv.address().port;
  const auth = { authorization: `Bearer ${TOKEN}` };
  try {
    assert.equal((await pedir(port, { body: "{}" })).status, 401);
    assert.equal((await pedir(port, { headers: { authorization: "Bearer x" }, body: "{}" })).status, 401);
    const inval = await pedir(port, { headers: auth, body: "{no json" });
    assert.equal(JSON.parse(inval.body).error.code, -32700);
    const nulo = await pedir(port, { headers: auth, body: "null" });
    assert.equal(nulo.status, 200); assert.equal(JSON.parse(nulo.body).error.code, -32600);
    assert.equal(JSON.parse((await pedir(port, { headers: auth, body: "42" })).body).error.code, -32600);
    const ok = await pedir(port, { headers: auth, body: JSON.stringify({ id: 1, method: "tools/list" }) });
    assert.equal(JSON.parse(ok.body).result.tools.length, 5);
    const grande = await pedir(port, { headers: auth, body: "x".repeat(S.MAX_BODY + 10) }).catch((e) => ({ status: "reset:" + e.code }));
    assert.ok(grande.status === 413 || String(grande.status).startsWith("reset:"), String(grande.status));
    // sigue vivo tras todo lo anterior
    assert.equal((await pedir(port, { headers: auth, body: "null" })).status, 200);
  } finally { srv.close(); srv.closeAllConnections?.(); }
});
