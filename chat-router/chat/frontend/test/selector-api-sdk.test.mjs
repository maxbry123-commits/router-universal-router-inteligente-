// Los selectores de proveedor históricos son la fuente visible: sin duplicación.
import test from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
const src=(name)=>readFileSync(new URL("../"+name,import.meta.url),"utf8");

test("selector visual histórico: filas específicas NVIDIA, Groq y SWE, sin dropdown duplicado",()=>{
 const selector=src("selector-modelos.js"),css=src("selector-modelos.css"),html=src("panel-chat.html");
 assert.match(selector,/caja\.append\(sec\)/);
 assert.match(selector,/btn-selector-modelos/);
 assert.doesNotMatch(selector,/modelo-unificado|api-modelos-rapido|anadir-api-sdk/);
 for(const id of ['sel-ngt','sel-groq','sel-swe','sel-swen'])assert.ok(html.includes('id="'+id+'"'),id);
 assert.doesNotMatch(css,/data-selector="groq"\]\{display:none|data-selector="nvidia-groq-team"\]\{display:none/);
});
test("los modelos y agentes siguen en sus catálogos reales del frontend",()=>{
 const select=src("chat-selectores.js"),swe=src("swe-directo.js"),ui=src("swe-selectores.js");
 for(const key of ["nvidia-groq-team","groq","swe-code","swen-code-free"])assert.ok(select.includes('"'+key+'"'),key);
 for(const key of ["openclaw","swe-agent","openhands","opencode","codex","claude-code"])assert.ok(swe.includes('"'+key+'"'),key);
 assert.match(ui, /agente_tool/);
 assert.match(ui, /#sel-swe, #sel-swen, #sel-groq, #sel-ngt/);
});
test("el banco de claves sigue conectado al Harness sin exponer secretos",()=>{
 const banco=src("ventana-claves.js"),swe=src("swe-directo.js");
 assert.match(banco,/\/plugins\/deepseek_harness\/credenciales\/anadir/);
 assert.match(banco,/\/plugins\/deepseek_harness\/credenciales\/catalogo/);
 assert.match(banco,/secreta\.value = ""/);
 assert.match(swe,/\/plugins\/deepseek_harness\/modelos\/v1\/chat\/completions/);
 assert.doesNotMatch(banco,/localStorage\.setItem\([^)]*secreta/);
});
