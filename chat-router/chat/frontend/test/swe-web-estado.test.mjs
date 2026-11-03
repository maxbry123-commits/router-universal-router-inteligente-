import test from "node:test";
import assert from "node:assert/strict";
import {readFileSync} from "node:fs";
const ui=readFileSync(new URL("../swe-selectores.js",import.meta.url),"utf8");
const br=readFileSync(new URL("../../../SWE CODE/web-bridge/src/browser.js",import.meta.url),"utf8");
test("solo SWEN consulta el diagnóstico web del Bridge",()=>{
  assert.match(ui,/if \(VENTANA === "swen-code-free"\)/);
  assert.match(ui,/api\("\/web\/v1\/web\/diagnostico"\)/);
  assert.match(ui,/w === "swen-code-free" \? estadoWebFree\(o.id\) : null/);
});
test("el diagnóstico distingue sesión, login, editor y respuesta pendiente",()=>{
  for(const x of ["SESIÓN WEB SIN INICIAR","LOGIN REQUERIDO","EDITOR NO DETECTADO",
    "EDITOR LISTO · SIN PRUEBA","BRIDGE SIN CONEXIÓN"]) assert.ok(ui.includes(x),x);
});
test("modelos ajenos no se alteran",()=>{
  assert.match(ui,/w === "swen-code-free" \? w : "modelo_tool_global"/);
  assert.match(ui,/else salirSwen\(\)/);
});
test("Chromium ya autenticado no necesita WEB_ACCOUNTS",()=>{
  assert.match(br,/if \(!expirada\) \{/);
  assert.match(br,/e\?\.code !== "CUENTAS_FALTAN"/);
  assert.match(br,/sesion_web_autorizada/);
});
