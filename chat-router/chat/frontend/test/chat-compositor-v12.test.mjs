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

test("Cubo se apaga cuando termina: hidden tiene prioridad sobre display",()=>{
 const cubeCss=src("pensando-3d.css"),cubeJs=src("pensando-3d.js");
 assert.ok(cubeCss.includes('.p3d[hidden]{display:none!important}'));
 assert.ok(cubeJs.includes('if (!o && !w.hidden) w.hidden = true'));
 assert.ok(src("chat-compositor-v12.css").includes('#composer .composer-bar > .p3d'));
});
test("La salida ajusta su altura al contenido sin hueco de 260px",()=>{
 const css=src("chat-compositor-v12.css");
 assert.ok(css.includes('height:auto!important;min-height:0!important;max-height:min(48dvh,500px)'));
 assert.ok(css.includes('#histories .chat-history:not(:empty)::before{content:none!important;display:none!important}'));
 assert.ok(!css.includes('height:clamp(260px,49dvh,520px)'));
 assert.ok(src("panel-chat.js").includes('c.hist.scrollTop = c.hist.scrollHeight'));
});
test("El cerebro es icono sin cuadro y muestra foco al navegar con teclado",()=>{
 const css=src("chat-compositor-v12.css");
 assert.ok(css.includes('#composer-extra > #mode-selector-mount .ms-btn{'));
 assert.ok(css.includes('border:0!important;border-radius:9px!important;background:transparent!important'));
 assert.ok(css.includes('#composer-extra > #mode-selector-mount .ms-btn:focus-visible'));
 assert.ok(css.includes('#composer-extra > #mode-selector-mount .ms-brain{'));
 assert.ok(src("barra-mas.js").includes('chat-compositor-v12.css'));
});
