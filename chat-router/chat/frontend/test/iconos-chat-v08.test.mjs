import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
const get=n=>readFileSync(new URL('../'+n,import.meta.url),'utf8');
test('El selector extra de agente desaparece, se mantienen los 4 proveedores y su hoja real',()=>{
 const html=get('panel-chat.html'),swe=get('swe-selectores.js');
 assert.doesNotMatch(html,/id="btn-agentes-swe"/);
 for(const id of ['sel-swe','sel-swen','sel-groq','sel-ngt'])assert.match(html,new RegExp('id="'+id+'"'));
 assert.match(swe, /#sel-swe, #sel-swen, #sel-groq, #sel-ngt/);
 assert.match(swe, /agente_tool/);
});
test('Iconos 30 por ciento mayores, sin recuadro, controles activos azules y Enviar intacto',()=>{
 const css=get('iconos-chat-v08.css');
 assert.match(css,/23\.4px/);
 assert.match(css,/background:transparent !important/);
 assert.match(css,/border-color:transparent !important/);
 assert.match(css,/\[aria-expanded="true"\]/);
 assert.match(css,/\[aria-pressed="true"\]/);
 assert.match(css, /#composer \.composer-bar > \.action\{order:3 !important\}/);
});
test('El cubo está inmediatamente antes de Enviar y conserva el estado ocupado del chat',()=>{
 const js=get('pensando-3d.js'),css=get('pensando-3d.css');
 assert.match(js,/barra\.insertBefore\(w, enviar\)/);
 assert.match(js,/c\.ocupado/);
 assert.match(js,/if \(!o\)/);
 assert.match(css,/#composer \.composer-bar > \.p3d/);
 assert.match(css,/\.p3d\[hidden\]\{display:none!important\}/);
});
test('Carga CSS aislado y no cambia backend o selector de modelos',()=>{
 const js=get('barra-mas.js');
 assert.match(js,/new URL\("\.\/iconos-chat-v08\.css", import\.meta\.url\)/);
 assert.match(js,/document\.head\.append\(hoja\)/);
 assert.match(get('loop-iframe-host.js'),/yaiwes_loop_panel_v1/);
});
