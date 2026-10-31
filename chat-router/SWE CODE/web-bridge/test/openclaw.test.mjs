import test from "node:test";
import assert from "node:assert/strict";
import fs from "node:fs";
import os from "node:os";
import path from "node:path";
import { asegurarWorkspace, vigilarWorkspace } from "../src/openclaw.js";

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
