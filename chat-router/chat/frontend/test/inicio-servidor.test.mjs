import test from "node:test";
import assert from "node:assert/strict";
import { comprobarSalud } from "../inicio-servidor.js";
test("GET /health ok confirma que el backend ha iniciado",async()=>{
  let path,opts;const ok=await comprobarSalud(async(u,o)=>{path=u;opts=o;return {ok:true,json:async()=>({status:"ok"})};});
  assert.equal(ok,true);assert.equal(path,"/health");assert.equal(opts.cache,"no-store");
});
test("servicio degradado y fallo HTTP permanecen en reintento",async()=>{
  assert.equal(await comprobarSalud(async()=>({ok:true,json:async()=>({status:"degraded"})})),false);
  assert.equal(await comprobarSalud(async()=>({ok:false})),false);
});
