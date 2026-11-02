import test from "node:test";
import assert from "node:assert/strict";
import {readFileSync} from "node:fs";
const src=n=>readFileSync(new URL("../"+n,import.meta.url),"utf8");
test("El cubo original está recuperado, con 6 caras y 2 anillos sin transformaciones V10",()=>{
 const js=src("pensando-3d.js"),css=src("pensando-3d.css");
 for(const id of ["f1","f2","f3","f4","f5","f6","a1","a2"])assert.ok(js.includes('class="'+id+'"')||js.includes(" "+id+'"' ),id);
 assert.match(css,/@keyframes p3d-gira/);
 assert.doesNotMatch(css,/p3d-formas-v10/);
 assert.match(js,/const w = el\("div", "p3d"\); w.hidden = true/);
 assert.match(css,/@media\(prefers-reduced-motion:reduce\)/);
 assert.match(js,/const ocupado = \(\) =>/);
});
test("Iconos tamaño 24, cerebro blanco SVG, paralelo distinto de copiar",()=>{
 const mode=src("mode_selector.js"),css=src("chat-toolbar-v09.css");
 assert.match(mode,/const icono = el\("span", \{ class: "ms-brain"/);
 assert.match(css,/\.ms-brain/);
 assert.match(css,/color:#F8F8F8!important/);
 assert.match(css,/content:"⇉"!important/);
 assert.match(css,/width:24px!important;height:24px!important/);
 assert.match(css,/\[aria-pressed="true"\]::after/);
});
test("Escoba y botón ampliar texto preservan el campo y las acciones de envío",()=>{
 const js=src("barra-mas.js"),css=src("chat-toolbar-v09.css");
 assert.match(js,/function botonExpandirInput\(\)/);
 assert.match(js,/form\.classList\.toggle\("riu-input-expanded", on\)/);
 assert.match(js,/setExpand\(!form\.classList\.contains/);
 assert.match(js,/fila\.append\(btn\)/);
 assert.match(js,/botonLimpiar\(\)/);
 assert.match(js,/M19 3L10 14/);
 assert.match(css,/#composer\.riu-input-expanded #message/);
 assert.match(src("chat-flujo-movil.css"),/#composer \.composer-bar > #btn-expandir-input/);
});
test("Composición no repite los selectores de modelos ni cambia LOOP o el backend",()=>{
 const html=src("panel-chat.html"),toolbar=src("chat-toolbar-v09.css");
 for(const id of ["sel-groq","sel-ngt","sel-swe","sel-swen"])assert.match(html,new RegExp('id="'+id+'"'));
 assert.match(toolbar,/grid-area:2 \/ 5!important/);
 assert.match(toolbar,/grid-area:2 \/ 6 \/ 3 \/ 8!important/);
 assert.match(src("loop-iframe-host.js"),/yaiwes_loop_panel_v1/);
});
