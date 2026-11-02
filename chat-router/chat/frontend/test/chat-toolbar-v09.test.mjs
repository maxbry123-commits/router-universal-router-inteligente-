import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
const src=n=>readFileSync(new URL('../'+n,import.meta.url),'utf8');
test('Cubo y texto Pensando montados una vez con el estado real del chat',()=>{
 const s=src('panel-chat.js');
 assert.match(s,/import \{ montarPensando3D \} from "\.\/pensando-3d\.js"/);
 assert.match(s,/window\.RIU_CHAT = \{ chat,/);
 assert.match(s,/montarPensando3D\(\{ root, q \}\)/);
 const c=src('pensando-3d.js');
 assert.match(c,/if \(!barra \|\| barra\.dataset\.p3d\) return/);
 assert.match(c,/if \(estado\.parentElement !== salida \|\| estado !== salida\.lastElementChild\) salida\.append\(estado\)/);
 assert.match(c,/barra\.insertBefore\(w, enviar\)/);
});
test('Los 22 RUI están inventariados y usan los componentes ya instalados',()=>{
 const list=src('apariencia-extra.js');
 const items=[...list.matchAll(/\["(\d\d)", "[^"]+",/g)].map(x=>x[1]);
 assert.equal(items.length,22);
 assert.equal(new Set(items).size,22);
 const root=src('panel-chat.js'),ui=src('chat-riu2.js');
 assert.match(root,/conectarRiu\(\{ q \}\)/);
 assert.match(root,/conectarRiu2\(\{ root, q, tell \}\)/);
 for(const module of ["riu-campana.js","riu-navegacion.js","riu-chats.js",
 "riu-reacciones.js","riu-paneles.js","riu-entrada.js"])assert.ok(ui.includes(module),module);
 assert.match(src('panel-apariencia.html'),/id="ap-rui"/);
 assert.match(src('chat-microfono.js'),/btn-microfono/);
});
test('No se altera el grupo de proveedores al alinear iconos',()=>{
 const html=src('panel-chat.html');
 for(const id of ['sel-ngt','sel-groq','sel-swe','sel-swen'])
   assert.match(html,new RegExp('id="'+id+'"'));
 assert.doesNotMatch(html,/id="btn-agentes-swe"/);
 const css=src('chat-toolbar-v09.css');
 assert.match(css,/#btn-loop-power\{display:none!important\}/);
});
