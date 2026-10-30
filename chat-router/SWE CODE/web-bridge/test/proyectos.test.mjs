import test from "node:test";
import assert from "node:assert/strict";
import fs from "node:fs";
import os from "node:os";
import path from "node:path";

process.env.BRIDGE_STATE_DIR = fs.mkdtempSync(path.join(os.tmpdir(), "bridge-proy-"));
const { slug, guardarAsesoria, leerProyecto } = await import("../src/proyectos.js");
const { modoValido, preambulo } = await import("../src/modos.js");

test("asesoria es un modo valido y pide plan, mapa mental, estructura y como resolver problemas", () => {
  assert.ok(modoValido("asesoria"));
  const p = preambulo("asesoria");
  for (const t of [/plan de acci/i, /mapa mental/i, /estructura/i, /resolver/i]) assert.match(p, t);
});

test("el nombre del proyecto se vuelve una carpeta segura", () => {
  assert.equal(slug("Mi Proyecto/Ñandú ../x"), "mi-proyecto-nandu-x");
  assert.equal(slug("../../etc/passwd"), "etc-passwd");
  assert.equal(slug(""), "general");
});

test("un archivo por proyecto: las asesorias se acumulan con fecha y quien respondio", () => {
  const a = guardarAsesoria("Proyecto A", { texto: "plan 1", via: "groq", modelo: "swecode-asesoria" });
  guardarAsesoria("Proyecto A", { texto: "plan 2", via: "web", modelo: "swecode-asesoria" });
  guardarAsesoria("Proyecto B", { texto: "otro", via: "groq", modelo: "swecode-asesoria" });
  assert.ok(a.endsWith(path.join("proyectos", "proyecto-a", "ASESORIA.md")));
  const t = fs.readFileSync(a, "utf8");
  assert.match(t, /plan 1/); assert.match(t, /plan 2/); assert.match(t, /groq/);
  assert.ok(!t.includes("otro"));
  assert.match(leerProyecto("Proyecto B").texto, /otro/);
  assert.equal(leerProyecto("no-existe"), null);
});
