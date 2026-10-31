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
      if (req.method === "PUT" && /\/contents\/banco-swe\.bin$/.test(u)) { const b = JSON.parse(d); est.puts = (est.puts || []).concat(b.sha ?? null); if (est.conflictos > 0) { est.conflictos--; est.sha = "sha-de-otro-" + est.llamadas.length; return json(409, { message: "does not match" }); } est.archivo = b.content; est.sha = "s" + est.llamadas.length; est.msg = b.message; est.rama2 = b.branch; return json(200, { content: { sha: est.sha } }); }
      json(404, {});
    });
  });
  s.unref();
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
  const g = await github(); g.est.rama = true; g.est.archivo = Buffer.from("MVPB1DESDE-GITHUB-relleno-de-mas-de-16-bytes").toString("base64"); g.est.sha = "x";
  fs.rmSync(path.join(estado, "banco-swe.bin"), { force: true });
  assert.equal(await traerDeGithub({ api: g.url, token: "t", repo: "o/r" }), true);
  assert.equal(fs.readFileSync(path.join(estado, "banco-swe.bin"), "utf8"), "MVPB1DESDE-GITHUB-relleno-de-mas-de-16-bytes");
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
  g.est.rama = true; g.est.archivo = Buffer.from("MVPB1DE-GITHUB-relleno-de-mas-de-16-bytes").toString("base64"); g.est.sha = "s9";
  fs.writeFileSync(path.join(estado, "banco-swe.bin"), Buffer.from("LOCAL-VACIO"));
  assert.equal(await traerDeGithub({ api: g.url, token: "t", repo: "o/r" }), false, "sin forzar no pisa");
  assert.equal(fs.readFileSync(path.join(estado, "banco-swe.bin"), "utf8"), "LOCAL-VACIO");
  assert.equal(await traerDeGithub({ api: g.url, token: "t", repo: "o/r", forzar: true }), true);
  g.s.closeAllConnections?.(); g.s.close();
  assert.equal(fs.readFileSync(path.join(estado, "banco-swe.bin"), "utf8"), "MVPB1DE-GITHUB-relleno-de-mas-de-16-bytes");
  assert.deepEqual(fs.readdirSync(estado).filter((f) => f.includes(".tmp-")), [], "sin temporales");
  const { diagTraer } = await import("../src/bancogithub.js");
  assert.equal(diagTraer.escrito, true);
});

test("traerDeGithub: solo acepta un banco cuyos 5 primeros bytes son MVPB1; cualquier otra cosa se descarta y no toca el local", async () => {
  const g = await github(); g.est.rama = true; g.est.sha = "x";
  const { diagTraer } = await import("../src/bancogithub.js");
  fs.writeFileSync(path.join(estado, "banco-swe.bin"), "MVPB1LOCAL-BUENO-relleno-de-mas-de-16-bytes");
  for (const malo of ["<html>pagina de error</html>", "MVPB2xxxxxxxx", "mvpb1minusculas", "MVP"]) {
    g.est.archivo = Buffer.from(malo).toString("base64");
    assert.equal(await traerDeGithub({ api: g.url, token: "t", repo: "o/r", forzar: true }), false, malo);
    assert.equal(fs.readFileSync(path.join(estado, "banco-swe.bin"), "utf8"), "MVPB1LOCAL-BUENO-relleno-de-mas-de-16-bytes", "el local sigue intacto");
    assert.equal(diagTraer.escrito, false); assert.equal(diagTraer.error, "BANCO_REMOTO_INVALIDO");
  }
  g.est.archivo = Buffer.from("MVPB1REMOTO-VALIDO-relleno-de-mas-de-16-bytes").toString("base64");
  assert.equal(await traerDeGithub({ api: g.url, token: "t", repo: "o/r", forzar: true }), true);
  assert.equal(fs.readFileSync(path.join(estado, "banco-swe.bin"), "utf8"), "MVPB1REMOTO-VALIDO-relleno-de-mas-de-16-bytes");
  g.s.closeAllConnections?.(); g.s.close();
});

test("publicarEnGithub: ante 409 (sha desfasado) relee el sha y reintenta UNA vez; si vuelve a fallar devuelve false", async () => {
  const g = await github(); g.est.rama = true; g.est.archivo = Buffer.from("MVPB1previo-relleno-de-mas-de-16-bytes").toString("base64"); g.est.sha = "sha-0";
  fs.writeFileSync(path.join(estado, "banco-swe.bin"), Buffer.from("MVPB1NUEVO-relleno-de-mas-de-16-bytes"));
  g.est.conflictos = 1;
  assert.equal(await publicarEnGithub({ api: g.url, token: "t", repo: "o/r" }), true, "tras el 409 el reintento publica");
  assert.equal(g.est.puts.length, 2); assert.notEqual(g.est.puts[0], g.est.puts[1], "el reintento usa el sha releido");
  assert.equal(Buffer.from(g.est.archivo, "base64").toString(), "MVPB1NUEVO-relleno-de-mas-de-16-bytes");
  g.est.conflictos = 5; g.est.puts = [];
  assert.equal(await publicarEnGithub({ api: g.url, token: "t", repo: "o/r" }), false, "un solo reintento");
  assert.equal(g.est.puts.length, 2);
  g.s.closeAllConnections?.(); g.s.close();
});

test("fetch a GitHub con redirect:'error': una redireccion NO se sigue (ni se envia el token a otro host)", async () => {
  let destino = 0;
  const otro = http.createServer((req, res) => { destino++; res.writeHead(200, { "content-type": "application/json" }); res.end(JSON.stringify({ content: Buffer.from("MVPB1robado-relleno-de-mas-de-16-bytes").toString("base64"), sha: "z" })); });
  otro.unref(); await new Promise((ok) => otro.listen(0, "127.0.0.1", ok));
  const redir = http.createServer((req, res) => { res.writeHead(302, { location: `http://127.0.0.1:${otro.address().port}/x` }); res.end(); });
  redir.unref(); await new Promise((ok) => redir.listen(0, "127.0.0.1", ok));
  const api = `http://127.0.0.1:${redir.address().port}`;
  fs.rmSync(path.join(estado, "banco-swe.bin"), { force: true });
  assert.equal(await traerDeGithub({ api, token: "t", repo: "o/r" }), false);
  assert.equal(destino, 0, "no siguio la redireccion");
  fs.writeFileSync(path.join(estado, "banco-swe.bin"), "MVPB1x-relleno-de-mas-de-16-bytes");
  assert.equal(await publicarEnGithub({ api, token: "t", repo: "o/r" }), false);
  assert.equal(destino, 0);
  for (const sv of [otro, redir]) { sv.closeAllConnections?.(); sv.close(); }
});

test("el banco remoto se descarga en crudo y, si el JSON/base64 llega recodificado a UTF-8 (lo que pasaba en el Space: 1357 -> 2036 bytes), se repara; si no es un banco valido (MVPB1) no sustituye al local", async () => {
  const original = Buffer.concat([Buffer.from("MVPB1"), Buffer.from(Array.from({ length: 300 }, (_, i) => (i * 37 + 129) % 256))]);
  const recodificado = Buffer.from(original.toString("latin1"), "utf8");  // cada byte >= 0x80 pasa a 2 bytes
  assert.ok(recodificado.length > original.length);
  for (const modo of ["crudo", "json-recodificado"]) {
    const g = await new Promise((ok) => {
      const s = http.createServer((req, res) => {
        const raw = /vnd\\.github\\.raw/.test(String(req.headers.accept || ""));
        if (raw) { if (modo === "crudo") { res.writeHead(200); return res.end(original); } res.writeHead(200); return res.end(recodificado); }
        res.writeHead(200, { "content-type": "application/json" });
        res.end(JSON.stringify({ size: original.length, sha: "abc12345", encoding: "base64", content: (modo === "crudo" ? original : recodificado).toString("base64") }));
      });
      s.listen(0, "127.0.0.1", () => ok({ s, url: `http://127.0.0.1:${s.address().port}` }));
    });
    fs.writeFileSync(path.join(estado, "banco-swe.bin"), Buffer.from("INVALIDO"));
    const ok = await traerDeGithub({ api: g.url, token: "t", repo: "o/r", forzar: true });
    g.s.closeAllConnections?.(); g.s.close();
    assert.equal(ok, true, modo);
    assert.deepEqual(fs.readFileSync(path.join(estado, "banco-swe.bin")), original, modo);
  }
  const g2 = await new Promise((ok) => {
    const s = http.createServer((req, res) => { res.writeHead(200, { "content-type": "application/json" }); res.end(JSON.stringify({ size: 5, sha: "x", content: Buffer.from("NO-ES-BANCO").toString("base64") })); });
    s.listen(0, "127.0.0.1", () => ok({ s, url: `http://127.0.0.1:${s.address().port}` }));
  });
  fs.writeFileSync(path.join(estado, "banco-swe.bin"), Buffer.from("LOCAL-OK"));
  assert.equal(await traerDeGithub({ api: g2.url, token: "t", repo: "o/r", forzar: true }), false);
  g2.s.closeAllConnections?.(); g2.s.close();
  assert.equal(fs.readFileSync(path.join(estado, "banco-swe.bin"), "utf8"), "LOCAL-OK");
});

test("si ni el crudo ni el JSON dan un banco valido, lo toma por git (fetch de la rama banco-claves, binario intacto)", async () => {
  const { execFileSync } = await import("node:child_process");
  const dir = fs.mkdtempSync(path.join(os.tmpdir(), "bgit-"));
  const original = Buffer.concat([Buffer.from("MVPB1"), Buffer.from(Array.from({ length: 400 }, (_, i) => (i * 53 + 131) % 256))]);
  const origen = path.join(dir, "origen"); fs.mkdirSync(origen);
  const git = (...a) => execFileSync("git", ["-C", origen, "-c", "user.name=t", "-c", "user.email=t@t", ...a], { stdio: "pipe" });
  git("init", "-q", "-b", "banco-claves"); fs.writeFileSync(path.join(origen, "banco-swe.bin"), original); git("add", "."); git("commit", "-qm", "b");
  const basura = Buffer.from("X".repeat(2036));
  const g = await new Promise((ok) => {
    const s = http.createServer((req, res) => { res.writeHead(200, { "content-type": "application/json" }); res.end(JSON.stringify({ size: original.length, sha: "abcd1234", encoding: "base64", content: basura.toString("base64") })); });
    s.listen(0, "127.0.0.1", () => ok({ s, url: `http://127.0.0.1:${s.address().port}` }));
  });
  process.env.RIU_GIT_URL = origen;
  fs.writeFileSync(path.join(estado, "banco-swe.bin"), Buffer.from("INVALIDO"));
  const ok = await traerDeGithub({ api: g.url, token: "t", repo: "o/r", forzar: true });
  delete process.env.RIU_GIT_URL; g.s.closeAllConnections?.(); g.s.close();
  assert.equal(ok, true);
  assert.deepEqual(fs.readFileSync(path.join(estado, "banco-swe.bin")), original);
});
