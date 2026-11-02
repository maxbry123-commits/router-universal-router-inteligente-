// Salida 3 V07 · interfaz de respuestas sin duplicar botones ni tocar chat/Router.
import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
const read=n=>readFileSync(new URL('../'+n,import.meta.url),'utf8');
test('El scroll real sigue en la conversación activa; ↑↓ dejan el historial',()=>{
  const js=read('chat-riu.js');
  assert.match(js,/hist\.after\(dock\)/);
  assert.match(js,/dock\.append\(bajar\)/);
  assert.match(js,/dock\.prepend\(subir\)/);
  assert.doesNotMatch(js,/hist\.append\((subir|bajar)\)/);
  assert.match(js,/h\.scrollTo\(\{ top: h\.scrollHeight/);
  assert.match(js,/h\.scrollTo\(\{ top: 0/);
  assert.match(js,/\.find\(\(h\) => !h\.hidden && h\.offsetParent !== null\)/);
});
test('La barra desaparece sin contenido desplazable y no altera el composer',()=>{
  const js=read('chat-riu.js'),css=read('salida-v07.css');
  assert.match(js,/dock\.hidden = max <= 8/);
  assert.match(js,/subir\.disabled = scroll <= 8/);
  assert.match(js,/bajar\.disabled = max - scroll <= 8/);
  assert.match(css,/#riu-scroll-dock\[hidden\]\{display:none!important\}/);
  assert.match(css,/#riu-scroll-dock \.riu-subir/);
  assert.doesNotMatch(css,/#composer/);
});
test('La respuesta gana ancho y sus acciones no consumen 84px por línea',()=>{
  const css=read('salida-v07.css');
  assert.match(css,/#histories \.chat-history > \.message:not\(\.user\)/);
  assert.match(css,/width:100%/);
  assert.match(css,/padding-top:44px/);
  assert.match(css,/padding-right:11px !important/);
  assert.match(css,/@media\(max-width:720px\)/);
  assert.match(css,/\.riu-code/);
});
test('RUI conserva copia, progreso, lectura streaming y estilos aislados',()=>{
  const js=read('chat-riu.js');
  assert.match(js,/function bloquesDeCodigo/);
  assert.match(js,/new MutationObserver/);
  assert.match(js,/ResizeObserver/);
  assert.match(js,/new URL\("\.\/salida-v07\.css", import\.meta\.url\)/);
  assert.match(js,/document\.head\.append\(css\)/);
  assert.match(read('panel-chat.js'),/conectarRiu\(\{ q \}\)/);
});
test('La compatibilidad LOOP y el anclaje universal se mantienen',()=>{
  assert.match(read('loop-iframe-host.js'),/yaiwes_loop_panel_v1/);
  assert.match(read('ventanas-control.js'),/abrirAnclajeUniversal/);
});
