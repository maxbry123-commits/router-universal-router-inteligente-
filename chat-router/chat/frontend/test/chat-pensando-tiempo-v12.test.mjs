import test from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
const src = (n) => readFileSync(new URL("../"+n, import.meta.url), "utf8");

test("Pemsando y cronómetro viven en la salida y empiezan al enviar", () => {
  const s=src("enviar-mensaje.js");
  assert.match(s,/const inicioRespuesta = performance.now\(\)/);
  assert.match(s,/node\("div", "Pemsando… · 0 s", "item p3d-reloj"\)/);
  assert.match(s,/c.hist.append\(relojRespuesta\)/);
  assert.match(s,/setInterval\(\(\) => \{/);
  assert.match(s,/relojRespuesta.textContent = "Pemsando… · " \+ seg/);
});
test("Al terminar congela el tiempo, limpia intervalo y conserva un solo nodo", () => {
  const s=src("enviar-mensaje.js");
  assert.match(s,/clearInterval\(relojInterval\)/);
  assert.match(s,/Tiempo de cómputo \(transcurrido\):/);
  assert.match(s,/Tiempo hasta el error:/);
  assert.match(s,/if \(relojRespuesta.isConnected\) c.hist.append\(relojRespuesta\)/);
  assert.equal((s.match(/node\("div", "Pemsando… · 0 s", "item p3d-reloj"\)/g) || []).length,1);
});
test("El clip es más pequeño visualmente pero conserva el blanco táctil", () => {
  const s=src("chat-compositor-v12.css");
  assert.match(s,/#composer #composer-extra > #btn-adjunto svg/);
  assert.match(s,/width:18px!important;height:18px!important/);
  assert.match(s,/#composer-extra > button,/);
});
test("No se modifica el cubo original y se renueva caché móvil", () => {
  const s=src("barra-mas.js"),css=src("chat-compositor-v12.css");
  assert.match(s,/css.searchParams.set\("v", "12.2"\)/);
  assert.match(css,/#histories \.chat-history \.p3d-reloj/);
  assert.match(src("pensando-3d.css"),/#composer \.composer-bar > \.p3d\[hidden\]/);
});

test("Pemsando es solo etiqueta: se conserva el contrato del cubo y las rutas de modelos", () => {
  const cubo = src("pensando-3d.js");
  const api = src("api.js");
  const envio = src("enviar-mensaje.js");
  assert.match(cubo, /export function montarPensando3D\(/);
  assert.match(cubo, /<strong>Pemsando…<\/strong>/);
  assert.match(api, /'Pemsando · '/);
  assert.match(api, /texto: 'Pemsando…'/);
  assert.match(api, /'\/plugins\/puente_chat\/call'/);
  assert.match(envio, /enviarSwe\(api,/);
  assert.match(envio, /window\.RIU_HARNESS\(/);
});
