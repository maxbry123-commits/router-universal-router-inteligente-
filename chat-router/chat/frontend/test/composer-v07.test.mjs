// Chat 2 · salida 2: protección del composer compacto sin clonar elementos.
import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
const read=(f)=>readFileSync(new URL('../'+f,import.meta.url),'utf8');
test('El CSS V07 se carga solo desde barra-mas; no cambia shell ni importa otro motor',()=>{
  const js=read('barra-mas.js');
  assert.match(js,/new URL\("\.\/composer-v07\.css", import\.meta\.url\)/);
  assert.match(js,/uiCss\.href = locationCss\.href/);
  assert.match(js,/document\.head\.append\(uiCss\)/);
  assert.match(js,/locationCss\.searchParams\.set\("v", revision\)/);
  assert.match(read('shell.js'),/import "\.\/barra-mas\.js"/);
});
test('Conserva acciones nativas: 3 menús, micrófono, adjuntar, Detener y Enviar',()=>{
  const js=read('barra-mas.js');
  for(const id of ['btn-grp-ctx','btn-grp-trab','btn-grp-cuad','btn-mas','btn-detener'])
    assert.ok(js.includes(id),id);
  assert.match(js,/TRABAJO\.forEach\(\(id\) => meter\(id, trab\)\)/);
  assert.match(read('chat-microfono.js'),/btn-microfono/);
  assert.match(read('panel-chat.js'),/btn-adjunto/);
  assert.match(read('panel-chat.js'),/btn-detener/);
});
test('Accesibilidad móvil 44px, sin scroll horizontal forzado ni ocultar Enviar',()=>{
  const css=read('composer-v07.css');
  assert.match(css,/@media \(max-width:720px\)/);
  assert.match(css,/@media \(max-width:360px\)/);
  assert.match(css,/#composer \.composer-bar > button\.secondary/);
  assert.match(css,/min-width:44px !important/);
  assert.match(css,/min-height:44px !important/);
  assert.match(css,/#composer \.composer-bar > \.action/);
  assert.match(css,/content:"Enviar" !important/);
  assert.doesNotMatch(css,/overflow-x:scroll|overflow-x:hidden|pointer-events:none/);
});
test('La luz azul requiere estado de controles o apertura real',()=>{
  const css=read('composer-v07.css');
  assert.match(css,/\[aria-pressed="true"\]/);
  assert.match(css,/\[aria-expanded="true"\]/);
  assert.match(css,/#btn-loop-power\[data-verified="false"\]/);
  assert.match(css,/#2F80FF/);
  assert.doesNotMatch(css,/button:hover\s*\{[^}]*background:#193A62/);
});
test('La base del LOOP sigue intacta',()=>{
  assert.match(read('loop-iframe-host.js'),/yaiwes_loop_panel_v1/);
  assert.match(read('ventanas-control.js'),/abrirAnclajeUniversal/);
  assert.match(read('loop-panel.html'),/id="lp-resources"/);
});
