// Chat 2 / Salida 1: protecciones sin desplegar nuevas funciones.
import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync,existsSync} from 'node:fs';
const path=n=>new URL('../'+n,import.meta.url);
const get=n=>readFileSync(path(n),'utf8');
test('Panel LOOP aislado: cuatro vistas, assets válidos e IDs únicos',()=>{
 const html=get('loop-panel.html'),paths=[...html.matchAll(/(?:src|href)="\.\/([^"]+)"/g)].map(m=>m[1]);
 assert.ok(paths.length>=13);
 for(const p of paths){assert.ok(!p.includes('..'));assert.ok(existsSync(path(p)),p)}
 const ids=[...html.matchAll(/\bid="([^"]+)"/g)].map(m=>m[1]);
 assert.equal(ids.length,new Set(ids).size);
 for(const id of ['lp-home','loop-workspace','lp-resources','lp-execution'])assert.ok(ids.includes(id),id);
});
test('Rollback a ventana LOOP previa y chat original',()=>{
 const host=get('loop-iframe-host.js');
 assert.match(host,/yaiwes_loop_panel_v1/);
 assert.match(host,/Volver a la interfaz LOOP anterior/);
 assert.match(host,/\/chat\/ui\/loop-panel\.html/);
 assert.match(get('ventana-loop.js'),/loopNewUIEnabled/);
 assert.match(get('shell.js'),/import "\.\/ventana-loop\.js"/);
 assert.match(get('panel-chat.js'),/conectarSelectorModelos/);
});
test('Iframe: origen, emisor y tamaño verificados; sin claves',()=>{
 const host=get('loop-iframe-host.js'),bridge=get('yaiwes-panel-bridge.js');
 for(const p of [/event\.origin!==location\.origin/,/event\.source!==f\.contentWindow/,/d\.channel!==CHANNEL/,/size>260000/])assert.match(host,p);
 assert.match(bridge,/event\.source!==window\.parent/);
 assert.match(bridge,/event\.origin!==origin/);
 assert.doesNotMatch(bridge,/X-API-Key|Authorization|sessionStorage/);
});
test('Ancla única y triggers de backend con control de revisión',()=>{
 for(const f of ['loop-iframe-host.js','ventanas-control.js','anclaje-puente-universal.js'])assert.match(get(f),/abrirAnclajeUniversal/);
 const js=get('loop-panel.js');
 assert.match(js,/expected_revision:before\.revision/);
 assert.match(js,/restoreBackend/);
 assert.doesNotMatch(js,/for\s*\(let i=0;i<50;i\+\+\)/);
});
test('Maxbry V07, versión de assets y ruta histórica del chat',()=>{
 assert.match(get('loop-proyecto.css'),/#202020/i);
 assert.match(get('loop-iframe-host.js'),/#1B1B1B/i);
 const config=JSON.parse(get('vercel.json'));
 assert.ok(config.rewrites.some(r=>r.source==='/chat/ui/:path*'&&r.destination==='/:path*'));
 assert.match(get('build.sh'),/VERCEL_GIT_COMMIT_SHA/);
});
