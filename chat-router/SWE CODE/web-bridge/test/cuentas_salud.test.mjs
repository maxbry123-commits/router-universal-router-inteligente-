import test from "node:test";
import assert from "node:assert/strict";
import { estadoRespaldo } from "../src/respaldo.js";

process.env.BRIDGE_STATE_DIR = "/tmp/bridge-test-cuentas";
delete process.env.WEB_ACCOUNTS;
const { pool, setCuentas } = await import("../src/cuentas.js");

test("sin cuentas entregadas el error es tipado (CUENTAS_FALTAN) para que OpenClaw las reenvie", () => {
  try { pool(); assert.fail("debio lanzar"); } catch (e) { assert.equal(e.code, "CUENTAS_FALTAN"); }
  assert.ok(setCuentas(["a@x.com", "b@x.com"], "clave"));
  assert.equal(pool().length, 2);
});

test("estadoRespaldo dice que respaldos hay sin mostrar valores", () => {
  const e = estadoRespaldo({ GROQ_API_KEY: "gsk-secreta", NVIDIA_API_KEY_2: "nv-secreta", SWECODE_URL_S1: "http://a", SWECODE_URL_S3: "http://c" });
  assert.deepEqual(e, { groq: 1, nvidia: 1, hf_local: 2 });
  assert.ok(!JSON.stringify(e).includes("secreta"));
  assert.deepEqual(estadoRespaldo({}), { groq: 0, nvidia: 0, hf_local: 0 });
});
