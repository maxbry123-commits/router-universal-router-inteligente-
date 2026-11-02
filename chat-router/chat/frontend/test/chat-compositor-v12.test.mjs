import test from "node:test";
import assert from "node:assert/strict";
import {readFileSync} from "node:fs";
const src=f=>readFileSync(new URL("../"+f,import.meta.url),"utf8");
test("Cubo original restaurado del historial (6 caras, 2 anillos, respuesta real)",()=>{
 const js=src("pensando-3d.js"),css=src("pensando-3d.css");
 for (const c of ["f1","f2","f3","f4","f5","f6"])assert.ok(js.includes('class="'+c+'"'),c);
 for (const c of ["a1","a2"])assert.ok(js.includes(" "+c+'"'),c);
 assert.match(js,/if \(o && w\.hidden\)/);
 assert.match(js,/if \(!o && !w\.hidden\)/);
 assert.match(css,/@keyframes p3d-gira/);
 assert.doesNotMatch(css,/p3d-formas-v10/);
});
test("Solo 4 controles en línea principal y utilidades bajo Enviar",()=>{
 const js=src("barra-mas.js"),css=src("chat-compositor-v12.css");
 assert.match(js,/function organizarComposerMovil\(\)/);
 assert.match(js,/const IDs = \["btn-adjunto", "btn-pegar"/);
 assert.match(js,/fila\.after\(extra\)/);
 assert.match(css,/grid-template-columns:minmax\(0,1fr\) 42px 42px 48px/);
 assert.match(css,/#composer-extra/);
 for(const id of ["#btn-microfono","#btn-detener","#btn-selector-modelos"])
  assert.ok(css.includes(id));
 assert.match(js,/function devolverComposerExtras\(\)/);
});
test("Reinicio del input sin borrar conversación ni ejecutar envío",()=>{
 const js=src("barra-mas.js");
 const chunk=js.slice(js.indexOf("function botonReiniciarInput()"),js.indexOf("function organizarComposerMovil()"));
 assert.match(chunk,/campo\.value = ""/);
 assert.match(chunk,/campo\.dispatchEvent\(new Event\("input"/);
 assert.doesNotMatch(chunk,/fetch\(|requestSubmit\(/);
});
test("Desplazamiento dentro de salida con una única flecha fija en pantalla",()=>{
 const js=src("chat-riu.js"),css=src("chat-compositor-v12.css");
 assert.match(js,/const scroller = h/);
 assert.match(js,/h\.scrollTo\(\{ top: h\.scrollHeight/);
 assert.equal((js.match(/className = "riu-bajar"/g)||[]).length,1);
 assert.match(css,/position:fixed!important;top:clamp/);
 assert.match(css,/overflow-y:auto!important;overscroll-behavior:contain/);
});
test("Conservación de selectores, herramientas, motores y entradas existentes",()=>{
 const html=src("panel-chat.html"),js=src("barra-mas.js");
 for(const id of ["sel-groq","sel-ngt","sel-swe","sel-swen","btn-detener"])
   assert.ok(html.includes('id="'+id+'"'),id);
 // El micrófono se inserta dinámicamente (chat-microfono.js), no en panel-chat.html.
 assert.match(src("chat-microfono.js"),/b\.id = "btn-microfono"/);
 assert.match(js,/TRABAJO = \["btn-loop"/);
 assert.match(js,/btn-paralelo/);
 assert.match(src("loop-iframe-host.js"),/yaiwes_loop_panel_v1/);
});
