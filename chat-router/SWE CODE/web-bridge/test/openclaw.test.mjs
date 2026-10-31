import test from "node:test";
import assert from "node:assert/strict";
import fs from "node:fs";
import os from "node:os";
import path from "node:path";
import { asegurarWorkspace, vigilarWorkspace, leerConfig, configVigente, vigilarConfig } from "../src/openclaw.js";

const tmp = () => fs.mkdtempSync(path.join(os.tmpdir(), "oc-test-"));

test("calcula <base>/openclaw-home-<uid>/.openclaw/workspace, la crea con 0700 y devuelve creada:true", () => {
  const base = tmp();
  try {
    const r = asegurarWorkspace({ uid: 4242, base });
    assert.equal(r.ruta, path.join(base, "openclaw-home-4242", ".openclaw", "workspace"));
    assert.equal(r.creada, true);
    const st = fs.statSync(r.ruta);
    assert.ok(st.isDirectory());
    assert.equal(st.mode & 0o777, 0o700);
  } finally { fs.rmSync(base, { recursive: true, force: true }); }
});

test("si ya existe no la toca (creada:false, contenido intacto)", () => {
  const base = tmp();
  try {
    const a = asegurarWorkspace({ uid: 1, base });
    fs.writeFileSync(path.join(a.ruta, "x.txt"), "hola");
    const b = asegurarWorkspace({ uid: 1, base });
    assert.equal(b.creada, false); assert.equal(b.ruta, a.ruta);
    assert.equal(fs.readFileSync(path.join(a.ruta, "x.txt"), "utf8"), "hola");
  } finally { fs.rmSync(base, { recursive: true, force: true }); }
});

test("sin uid usa process.getuid() y sin base usa /tmp (fs inyectable, no escribe nada real)", () => {
  const llamadas = [];
  const fsFalso = { existsSync: () => false, mkdirSync: (p, o) => { llamadas.push([p, o]); } };
  const r = asegurarWorkspace({ fs: fsFalso });
  assert.equal(r.ruta, `/tmp/openclaw-home-${process.getuid()}/.openclaw/workspace`);
  assert.equal(r.creada, true);
  assert.deepEqual(llamadas, [[r.ruta, { recursive: true, mode: 0o700 }]]);
});

test("OPENCLAW_WORKSPACE_DIR tiene prioridad sobre la ruta calculada", () => {
  const base = tmp(), previo = process.env.OPENCLAW_WORKSPACE_DIR;
  try {
    const destino = path.join(base, "otro", "ws");
    process.env.OPENCLAW_WORKSPACE_DIR = destino;
    const r = asegurarWorkspace({ uid: 1, base });
    assert.equal(r.ruta, destino); assert.equal(r.creada, true); assert.ok(fs.existsSync(destino));
    assert.ok(!fs.existsSync(path.join(base, "openclaw-home-1")));
  } finally {
    if (previo === undefined) delete process.env.OPENCLAW_WORKSPACE_DIR; else process.env.OPENCLAW_WORKSPACE_DIR = previo;
    fs.rmSync(base, { recursive: true, force: true });
  }
});

test("vigilarWorkspace: comprueba al arrancar, repone si se borra, avisa solo al crear, y el timer es unref", async () => {
  const base = tmp(), previo = process.env.OPENCLAW_WORKSPACE_DIR, warn = console.warn, avisos = [];
  process.env.OPENCLAW_WORKSPACE_DIR = path.join(base, "ws");
  console.warn = (...a) => avisos.push(a.join(" "));
  let t;
  try {
    t = vigilarWorkspace(20);
    assert.ok(fs.existsSync(process.env.OPENCLAW_WORKSPACE_DIR), "se crea al arrancar");
    assert.equal(avisos.length, 1);
    await new Promise((ok) => setTimeout(ok, 80));
    assert.equal(avisos.length, 1, "no avisa si ya existe");
    fs.rmSync(process.env.OPENCLAW_WORKSPACE_DIR, { recursive: true });
    await new Promise((ok) => setTimeout(ok, 120));
    assert.ok(fs.existsSync(process.env.OPENCLAW_WORKSPACE_DIR), "se repone");
    assert.equal(avisos.length, 2);
    assert.equal(t.hasRef(), false, "timer con unref");
  } finally {
    clearInterval(t); console.warn = warn;
    if (previo === undefined) delete process.env.OPENCLAW_WORKSPACE_DIR; else process.env.OPENCLAW_WORKSPACE_DIR = previo;
    fs.rmSync(base, { recursive: true, force: true });
  }
});

// ---------- configuracion vigente de OpenClaw (solo lectura, sin secretos): la leen Vercel y el Space por GET /v1/openclaw ----------
const escribirConfig = (dir, extra = {}) => {
  fs.writeFileSync(path.join(dir, "provider-openclaw.json"), JSON.stringify({ provider: "swecode", nombre: "SWE", tipo: "openai-compatible", base_url: "http://localhost:7870/v1", api_key: "SECRETO-NO-DEBE-SALIR", modelos: [{ id: "web-qwen38max", nombre: "Qwen" }], ...extra }));
  fs.writeFileSync(path.join(dir, "swen.json"), JSON.stringify({ modos: ["revision", "solucion"], seleccion_modelo: { aliases: { "web-qwen38max": ["qwen38"] } }, credenciales: { x: "SECRETO-2" } }));
};

test("leerConfig: provider, modelos, modos y alias; nunca api_key ni credenciales; version estable", () => {
  const dir = tmp();
  try {
    escribirConfig(dir);
    const c = leerConfig({ dir });
    assert.equal(c.provider.provider, "swecode"); assert.equal(c.provider.base_url, "http://localhost:7870/v1");
    assert.deepEqual(c.provider.modelos.map(m => m.id), ["web-qwen38max"]);
    assert.deepEqual(c.modos, ["revision", "solucion"]); assert.deepEqual(c.aliases, { "web-qwen38max": ["qwen38"] });
    assert.ok(!JSON.stringify(c).includes("SECRETO"), "sin secretos"); assert.ok(!("api_key" in c.provider));
    assert.equal(leerConfig({ dir }).version, c.version, "misma config => misma version");
    escribirConfig(dir, { modelos: [{ id: "otro", nombre: "Otro" }] });
    assert.notEqual(leerConfig({ dir }).version, c.version, "config distinta => version distinta");
  } finally { fs.rmSync(dir, { recursive: true, force: true }); }
});

test("leerConfig: sin provider-openclaw.json devuelve null; swen.json ausente no la rompe", () => {
  const dir = tmp();
  try {
    assert.equal(leerConfig({ dir }), null);
    fs.writeFileSync(path.join(dir, "provider-openclaw.json"), JSON.stringify({ provider: "swecode", modelos: [] }));
    assert.deepEqual(leerConfig({ dir }).modos, []);
  } finally { fs.rmSync(dir, { recursive: true, force: true }); }
});

test("vigilarConfig: toma la config al arrancar y la mantiene al dia en cada vuelta (timer unref)", async () => {
  const dir = tmp(); let t;
  try {
    escribirConfig(dir);
    t = vigilarConfig(20, { dir });
    assert.equal(configVigente({ dir }).provider.modelos[0].id, "web-qwen38max");
    escribirConfig(dir, { modelos: [{ id: "nuevo-modelo", nombre: "N" }] });
    await new Promise((ok) => setTimeout(ok, 120));
    assert.equal(configVigente({ dir }).provider.modelos[0].id, "nuevo-modelo", "el vigilante la actualizo");
    assert.equal(t.hasRef(), false);
  } finally { clearInterval(t); fs.rmSync(dir, { recursive: true, force: true }); }
});
