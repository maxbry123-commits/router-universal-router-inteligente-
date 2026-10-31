import test from "node:test";
import assert from "node:assert/strict";
import http from "node:http";
import fs from "node:fs";
import os from "node:os";
import path from "node:path";

const estado = fs.mkdtempSync(path.join(os.tmpdir(), "bg-"));
process.env.BRIDGE_STATE_DIR = estado;
const { publicarEnGithub, traerDeGithub } = await import("../src/bancogithub.js");

// GitHub falso: rama banco-claves y un archivo
function github() {
  const est = { rama: false, archivo: null, sha: null, llamadas: [], auth: [] };
  const s = http.createServer((req, res) => {
    let d = ""; req.on("data", (c) => d += c); req.on("end", () => {
      est.llamadas.push(req.method + " " + req.url); est.auth.push(req.headers.authorization);
      const json = (c, o) => { res.writeHead(c, { "content-type": "application/json" }); res.end(JSON.stringify(o)); };
      const u = req.url;
      if (req.method === "GET" && /\/git\/ref\/heads\/banco-claves$/.test(u)) return est.rama ? json(200, { object: { sha: "r1" } }) : json(404, {});
      if (req.method === "GET" && /\/git\/ref\/heads\/main$/.test(u)) return json(200, { object: { sha: "m1" } });
      if (req.method === "POST" && /\/git\/refs$/.test(u)) { est.rama = true; return json(201, {}); }
      if (req.method === "GET" && /\/contents\/banco-swe\.bin/.test(u)) return est.archivo ? json(200, { sha: est.sha, content: est.archivo }) : json(404, {});
      if (req.method === "PUT" && /\/contents\/banco-swe\.bin$/.test(u)) { const b = JSON.parse(d); est.archivo = b.content; est.sha = "s" + est.llamadas.length; est.msg = b.message; est.rama2 = b.branch; return json(200, { content: { sha: est.sha } }); }
      json(404, {});
    });
  });
  return new Promise((ok) => s.listen(0, "127.0.0.1", () => ok({ s, est, url: `http://127.0.0.1:${s.address().port}` })));
}

test("publica el banco cifrado en la rama banco-claves (la crea si falta) sin tocar main", async () => {
  const g = await github();
  fs.writeFileSync(path.join(estado, "banco-swe.bin"), Buffer.from("CIFRADO-1"));
  const ok = await publicarEnGithub({ api: g.url, token: "gh-prueba", repo: "o/r" });
  g.s.closeAllConnections?.(); g.s.close();
  assert.ok(ok); assert.ok(g.est.rama, "creo la rama"); assert.equal(g.est.rama2, "banco-claves");
  assert.equal(Buffer.from(g.est.archivo, "base64").toString(), "CIFRADO-1");
  assert.ok(!g.est.llamadas.some((l) => /heads\/main$/.test(l) && l.startsWith("PUT")));
  assert.ok(g.est.auth.every((a) => a === "Bearer gh-prueba"));
});

test("trae el banco de GitHub al arrancar si aqui no existe (Space nuevo) y no pisa uno local", async () => {
  const g = await github(); g.est.rama = true; g.est.archivo = Buffer.from("DESDE-GITHUB").toString("base64"); g.est.sha = "x";
  fs.rmSync(path.join(estado, "banco-swe.bin"), { force: true });
  assert.equal(await traerDeGithub({ api: g.url, token: "t", repo: "o/r" }), true);
  assert.equal(fs.readFileSync(path.join(estado, "banco-swe.bin"), "utf8"), "DESDE-GITHUB");
  fs.writeFileSync(path.join(estado, "banco-swe.bin"), "LOCAL");
  assert.equal(await traerDeGithub({ api: g.url, token: "t", repo: "o/r" }), false, "no pisa el local");
  assert.equal(fs.readFileSync(path.join(estado, "banco-swe.bin"), "utf8"), "LOCAL");
  g.s.closeAllConnections?.(); g.s.close();
});

test("sin GITHUB_TOKEN o con GitHub caido no rompe", async () => {
  assert.equal(await publicarEnGithub({ api: "http://127.0.0.1:9", token: "", repo: "o/r" }), false);
  assert.equal(await traerDeGithub({ api: "http://127.0.0.1:9", token: "t", repo: "o/r" }), false);
});

test("forzar: si el banco local no sirve, el de GitHub lo sustituye; sin forzar nunca pisa el local", async () => {
  const g = await github();
  g.est.rama = true; g.est.archivo = Buffer.from("DE-GITHUB").toString("base64"); g.est.sha = "s9";
  fs.writeFileSync(path.join(estado, "banco-swe.bin"), Buffer.from("LOCAL-VACIO"));
  assert.equal(await traerDeGithub({ api: g.url, token: "t", repo: "o/r" }), false, "sin forzar no pisa");
  assert.equal(fs.readFileSync(path.join(estado, "banco-swe.bin"), "utf8"), "LOCAL-VACIO");
  assert.equal(await traerDeGithub({ api: g.url, token: "t", repo: "o/r", forzar: true }), true);
  g.s.closeAllConnections?.(); g.s.close();
  assert.equal(fs.readFileSync(path.join(estado, "banco-swe.bin"), "utf8"), "DE-GITHUB");
});
