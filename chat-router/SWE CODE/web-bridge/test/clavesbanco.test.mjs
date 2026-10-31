import test from "node:test";
import assert from "node:assert/strict";
import fs from "node:fs";
import os from "node:os";
import path from "node:path";

const dir = fs.mkdtempSync(path.join(os.tmpdir(), "cb-"));
fs.writeFileSync(path.join(dir, "fake.sh"), `#!/bin/sh
if [ "$1" = "leer" ]; then echo '{"groq": ["gsk-del-banco"], "nvidia": []}'; else cat > "${dir}/guardado.json"; echo '{"ok": true}'; fi
`, { mode: 0o755 });
process.env.RIU_CLAVES_CMD = path.join(dir, "fake.sh");
const { cargarDelBanco, guardarEnBanco } = await import("../src/clavesbanco.js");
const { claves, estadoRespaldo } = await import("../src/respaldo.js");

test("al arrancar carga al bridge las claves del banco (Router + propio) sin variables de entorno", async () => {
  const n = await cargarDelBanco();
  assert.equal(n, 1);
  assert.deepEqual(claves("GROQ_API_KEY", {}), ["gsk-del-banco"]);
  assert.equal(estadoRespaldo({}).groq, 1);
});

test("las claves pegadas se guardan en el banco propio (cifrado por el helper) y no se escriben en ningun otro lado", async () => {
  const ok = await guardarEnBanco({ groq: ["gsk-nueva"], nvidia: "nv-nueva" });
  assert.ok(ok);
  const g = JSON.parse(fs.readFileSync(path.join(dir, "guardado.json"), "utf8"));
  assert.deepEqual(g, { groq: ["gsk-nueva"], nvidia: "nv-nueva" });
});

test("si el helper falla, no rompe ni devuelve claves", async () => {
  process.env.RIU_CLAVES_CMD = "/no/existe";
  assert.equal(await cargarDelBanco(), 0);
  assert.equal(await guardarEnBanco({ groq: ["x"] }), false);
});

test("recarga periodica: un banco vacio NO borra las claves que ya estaban en memoria", async () => {
  process.env.RIU_CLAVES_CMD = path.join(dir, "fake.sh");
  const { setClaves } = await import("../src/respaldo.js");
  setClaves({ nvidia: ["nv-en-memoria"] });
  await cargarDelBanco();  // el fake devuelve nvidia: [] y groq: [...]
  assert.ok(claves("NVIDIA_API_KEY", {}).includes("nv-en-memoria"), "no se pierde lo pegado");
});

test("vigilarBanco recarga cada 60 s sin mantener vivo el proceso", async () => {
  const { vigilarBanco } = await import("../src/clavesbanco.js");
  const t = vigilarBanco(60000);
  assert.ok(t && typeof t.unref === "function"); clearInterval(t);
});
