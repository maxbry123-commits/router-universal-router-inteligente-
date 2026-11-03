// Regresión: revertir la contaminación del selector de SWE CODE free sin
// modificar los selectores Groq/NVIDIA/HF ni el ejecutor del Harness.
import test from "node:test";
import assert from "node:assert/strict";
import {readFileSync} from "node:fs";
import * as SWE from "../swe-directo.js";
const source = readFileSync(new URL("../swe-selectores.js",import.meta.url),"utf8");
const bridge = readFileSync(new URL("../enviar-mensaje.js",import.meta.url),"utf8");
const cap = SWE.normalizarCapacidades(null);
const ids = (w,web=false)=>SWE.opcionesModeloVentana(w,cap,{}, {web}).map(x=>x.id);
test("modelos que responden pertenecen exclusivamente a su selector",()=>{
  assert.ok(ids("groq").length>0 && ids("groq").every(x=>x.startsWith("groq/")));
  assert.ok(ids("nvidia").length>0 && ids("nvidia").every(x=>x.startsWith("nvidia/")));
  assert.ok(ids("swe-code").length>0 && ids("swe-code").every(x=>x.startsWith("hf/")));
  assert.ok(ids("swen-code-free",true).every(x=>x.startsWith("web-")||x==="swecode-consulta"));
});
test("modelo para tool fuera de FREE recupera catálogo histórico, no solo web",()=>{
  assert.match(source,/modelo_tool_global/);
  const all=new Set(ids("modelo_tool_global",true));
  for(const x of ["hf/lfm2.5-350m","groq/qwen/qwen3.8-27b",
    "nvidia/minimaxai/minimax-m3.1-flash","web-qwen38max"])
    assert.ok(all.has(x),"falta "+x);
});
test("SWEN guarda y restaura valores independientes de otros selectores",()=>{
  for(const marker of ["K_SWEN_PROPIO","K_OTROS_PREV","entrarSwen()",
    "salirSwen()","escribirPropio(K_OTROS_PREV","escribirPropio(K_SWEN_PROPIO"])
    assert.ok(source.includes(marker),marker);
  assert.match(source,/if \(w === "swen-code-free"\) entrarSwen\(\)/);
  assert.match(source,/else salirSwen\(\)/);
  assert.doesNotMatch(source,/w === "swen-code-free" \? w : "swen-code-free"/);
});
test("modelo que ejecuta y agente conservan sus IDs hasta TareaSWE",()=>{
  const sel={...SWE.SEL_DEFECTO,workflow:"individual",modo_agentico:true,
    modelo_responde:"groq/qwen/qwen3.8-27b",
    modelo_tool:"nvidia/minimaxai/minimax-m3.1-flash",agente_tool:"openclaw"};
  const task=SWE.armarTarea({sel,mensaje:"prueba",sesion:"regresion",task_id:"regresion"});
  assert.equal(task.modelo_responde,sel.modelo_responde);
  assert.equal(task.modelo_tool,sel.modelo_tool);
  assert.equal(task.agente_tool,sel.agente_tool);
  assert.equal(SWE.ejecutorDeAgente(sel.agente_tool),"openclaw");
  assert.equal(SWE.ejecutorDeAgente("swe-agent"),"swe");
});
test("Groq y NVIDIA siguen por sus modelos originales y sin fallback WEB",()=>{
  assert.match(bridge,/fichaGroq = selAct === "groq"/);
  assert.match(bridge,/fichaNvidia = selAct === "nvidia-groq-team"/);
  assert.match(bridge,/const _modeloSwe = fichaGroq \|\| fichaNvidia/);
  assert.match(source,/const otroProveedor = VENTANA === "groq" \|\| VENTANA === "nvidia"/);
});
