// Reglas de salida única y selectores individuales históricos.
import test from "node:test";
import assert from "node:assert/strict";
import {readFileSync} from "node:fs";
const src=f=>readFileSync(new URL("../"+f,import.meta.url),"utf8");
test("Groq y NVIDIA tienen selectores específicos, no un desplegable nuevo",()=>{
 const s=src("selector-modelos.js"),c=src("selector-modelos.css"),h=src("panel-chat.html");
 for(const [id,label]of [["sel-groq","Groq"],["sel-ngt","NVIDIA"]]){
   assert.ok(h.includes('id="'+id+'"'),label);
 }
 assert.match(c,/#sh-selectores #selectores \{ display: block !important/);
 assert.doesNotMatch(c,/sel-fila\[data-selector="groq"\].*display:none/);
 assert.doesNotMatch(s,/modelo-unificado/);
});
test("una respuesta del proveedor crea un globo y conserva su procedencia",()=>{
 const s=src("enviar-mensaje.js");
 assert.match(s,/const respuesta = burbuja\(answer.reply/);
 assert.match(s,/respuesta\.dataset\.procedencia = answer\.nota/);
 assert.doesNotMatch(s,/if \(answer\.nota\) c\.hist\.append\(node\("div", answer\.nota/);
 assert.doesNotMatch(s,/if \(r\.nota\) c\.hist\.append\(node\("div", r\.nota/);
});
test("elección del proveedor usa selectores existentes, agentes por separado",()=>{
 const s=src("chat-selectores.js"),a=src("swe-selectores.js");
 for(const name of ["nvidia-groq-team","groq","swe-code"])assert.ok(s.includes('"'+name+'"'));
 assert.match(a, /#sel-swe, #sel-swen, #sel-groq, #sel-ngt/);
});
