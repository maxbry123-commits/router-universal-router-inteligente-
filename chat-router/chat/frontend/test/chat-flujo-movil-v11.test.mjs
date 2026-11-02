import test from "node:test";
import assert from "node:assert/strict";
import {readFileSync} from "node:fs";
const src=n=>readFileSync(new URL("../"+n,import.meta.url),"utf8");
test("El cubo vuelve al diseño original sin V10 y se ve en reposo",()=>{
 const js=src("pensando-3d.js"),css=src("pensando-3d.css");
 assert.match(js,/p3d p3d-idle/); assert.match(js,/w.hidden = false/);
 assert.match(css,/@keyframes p3d-gira/); assert.doesNotMatch(css,/p3d-formas-v10/);
 for(const cara of ["f1","f2","f3","f4","f5","f6"])assert.match(js,new RegExp('class="'+cara+'"'));
 assert.match(css,/animation-play-state:paused/);
});
test("En móvil el chat se desplaza como página, sin forzar altura al historial",()=>{
 const css=src("chat-flujo-movil.css");
 assert.match(css,/main#panel section:has\(> #histories\)/);
 assert.match(css,/height:auto!important;max-height:none!important/);
 assert.match(css,/#histories \.chat-history:not\(\[hidden\]\)/);
 assert.match(css,/overflow:visible!important/);
 assert.match(css,/#composer #message/);assert.match(css,/min-height:116px!important/);
});
test("El scroll RUI08 usa la página en móvil, la burbuja baja y permanece solo una flecha",()=>{
 const js=src("chat-riu.js");
 assert.match(js,/document.scrollingElement \|\| document.documentElement/);
 assert.match(js,/window.addEventListener\("scroll", medir/);
 assert.match(js,/last.scrollIntoView/);
 assert.equal((js.match(/document.createElement\("button"\); bajar/g)||[]).length,1);
});
test("Los iconos no chocan y se conservan modelos, modos, LOOP y ancla",()=>{
 const css=src("chat-flujo-movil.css"),html=src("panel-chat.html");
 assert.match(css,/grid-area:2 \/ 4!important/);
 assert.match(css,/grid-area:2 \/ 5!important/);
 assert.match(css,/grid-area:2 \/ 6 \/ 3 \/ 8!important/);
 assert.match(html,/id="btn-selector-modelos"|id="sel-groq"/);
 assert.match(src("barra-mas.js"),/chat-flujo-movil\.css/);
});

test("Una sola flecha de bajar contextual y expandir input sin flechas ni superposición",()=>{
 const rui=src("chat-riu.js"),js=src("barra-mas.js"),css=src("chat-flujo-movil.css");
 assert.match(rui,/bajar\.hidden = max <= 48 \|\| fromBottom <= 70/);
 assert.equal((rui.match(/className = "riu-bajar"/g)||[]).length,1);
 assert.match(js,/fila\.append\(btn\)/);
 assert.match(js,/const iconExpand = svg\('<rect/);
 assert.match(css,/#composer \.composer-bar > #btn-expandir-input/);
 assert.match(css,/grid-area:2 \/ 3!important/);
 assert.doesNotMatch(css,/#composer > #btn-expandir-input/);
});
