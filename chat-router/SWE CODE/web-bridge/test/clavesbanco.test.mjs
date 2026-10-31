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
const { cargarDelBanco, guardarEnBanco, borrarDelBanco } = await import("../src/clavesbanco.js");
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

test("borrarDelBanco llama a la accion borrar del helper y limpiarClaves vacia la memoria", async () => {
  fs.writeFileSync(path.join(dir, "fake-borrar.sh"), `#!/bin/sh\necho "$1" > "${dir}/accion.txt"; echo '{"ok": true}'\n`, { mode: 0o755 });
  const previo = process.env.RIU_CLAVES_CMD;
  process.env.RIU_CLAVES_CMD = path.join(dir, "fake-borrar.sh");
  assert.equal(await borrarDelBanco(), true);
  assert.equal(fs.readFileSync(path.join(dir, "accion.txt"), "utf8").trim(), "borrar");
  process.env.RIU_CLAVES_CMD = "/no/existe";
  assert.equal(await borrarDelBanco(), false);
  process.env.RIU_CLAVES_CMD = previo;
  const { setClaves, limpiarClaves } = await import("../src/respaldo.js");
  setClaves({ groq: ["gsk-1-larga"], nvidia: ["nv-1-larga"] });
  limpiarClaves();
  assert.deepEqual(claves("GROQ_API_KEY", {}), []); assert.deepEqual(claves("NVIDIA_API_KEY", {}), []);
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

test("vigilarBanco: si aun no hay banco local, cada vuelta intenta traerlo de GitHub y luego lo carga", async () => {
  const { vigilarBanco } = await import("../src/clavesbanco.js");
  const orden = [];
  const t = vigilarBanco(10, { traer: async () => { orden.push("traer"); return true; }, cargar: async () => { orden.push("cargar"); return 0; } });
  await new Promise((r) => setTimeout(r, 60));
  clearInterval(t);
  assert.ok(orden.length >= 2 && orden[0] === "traer" && orden[1] === "cargar", orden.join(","));
});

// vigilarBanco(intervalo, { traer, cargar, diagnosticar, existe }): el traer forzado solo cuando el banco local no existe o NO abre
const vuelta = async (diag, { existe = true, cargaN = 0 } = {}) => {
  const { vigilarBanco } = await import("../src/clavesbanco.js");
  const llamadas = []; let cargas = 0;
  const traer = async (o = {}) => { llamadas.push(o.forzar ? "traer-forzado" : "traer"); return !!o.forzar; };
  const cargar = async () => { cargas++; return llamadas.includes("traer-forzado") ? 11 : cargaN; };
  const t = vigilarBanco(10, { traer, cargar, diagnosticar: async () => diag, existe: () => existe });
  await new Promise((r) => setTimeout(r, 80));
  clearInterval(t);
  return { llamadas, cargas };
};

test("vigilarBanco: si el banco local EXISTE pero NO abre (ilegible / otra clave), trae el de GitHub forzado y recarga", async () => {
  const r = await vuelta({ propio: { existe: true, abre_con: null } });
  assert.ok(r.llamadas.includes("traer-forzado"), r.llamadas.join(","));
  assert.ok(r.cargas >= 2);
});

test("vigilarBanco: si el banco local no existe, tambien se fuerza el traer", async () => {
  const r = await vuelta({ propio: { existe: false } }, { existe: false });
  assert.ok(r.llamadas.includes("traer-forzado"), r.llamadas.join(","));
});

test("vigilarBanco: DELETE persistente — un banco local que ABRE y esta vacio (borrado a proposito) NO se sustituye por el de GitHub", async () => {
  const r = await vuelta({ propio: { existe: true, abre_con: 0, groq: 0, nvidia: 0 } });
  assert.ok(!r.llamadas.includes("traer-forzado"), r.llamadas.join(","));
});

test("vigilarBanco: sin diagnostico fiable y con el archivo presente no se fuerza nada", async () => {
  const r = await vuelta(null);
  assert.ok(!r.llamadas.includes("traer-forzado"), r.llamadas.join(","));
});

test("diagnosticoBanco: solo estado (bytes del archivo, ultimo http de GitHub, ultimo error del helper, numero de accesos), nunca valores", async () => {
  const { diagnosticoBanco } = await import("../src/clavesbanco.js");
  const d = diagnosticoBanco({ BRIDGE_STATE_DIR: dir, RIU_API_KEY: "x", RIU_MCP_KEY: "y" });
  assert.equal(d.accesos, 2);
  assert.ok("local_bytes" in d && "github" in d && "python" in d);
  assert.ok(!JSON.stringify(d).includes("gsk-"));
});
