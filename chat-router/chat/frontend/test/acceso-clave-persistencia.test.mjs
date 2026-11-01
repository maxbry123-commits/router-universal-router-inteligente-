import test from "node:test";
import assert from "node:assert/strict";
const ses = new Map(), persist = new Map();
const store = m => ({getItem:k=>m.get(k)||null,setItem:(k,v)=>m.set(k,String(v)),removeItem:k=>m.delete(k)});
globalThis.sessionStorage=store(ses);globalThis.localStorage=store(persist);
const a = await import("../acceso-clave.js");
test.beforeEach(()=>{ses.clear();persist.clear();});
test("clave recordada vuelve al abrir una nueva sesión en el mismo dominio",()=>{
  assert.equal(a.guardarClave("simulacro",true),true);ses.clear();
  assert.equal(a.claveActual(),"simulacro");assert.equal(ses.get("riu_clave"),"simulacro");
});
test("olvidar o desmarcar el recordatorio no deja credenciales persistentes",()=>{
  a.guardarClave("simulacro",true);a.guardarClave("temporal",false);
  ses.clear();assert.equal(a.hayClave(),false);
  a.guardarClave("simulacro",true);a.olvidarClave();assert.equal(a.claveRecordada(),false);
});
test("almacenamiento bloqueado: no reportar éxito falso",()=>{
  const anterior=globalThis.localStorage;
  globalThis.localStorage={getItem:()=>null,setItem:()=>{throw Error("bloqueado");},removeItem:()=>{}};
  try { assert.equal(a.guardarClave("simulacro",true),false); } finally {globalThis.localStorage=anterior;}
});
test("un 503 de Qwen o 403 por herramientas no solicita otra vez clave",()=>{
  for(const e of ["HTTP 503: QWEN_API_KEY no disponible","HTTP 403: Herramienta bloqueada","HTTP 502: credencial Harness ausente"])assert.equal(a.esAuth(new Error(e)),false);
  assert.equal(a.esAuth(new Error("HTTP 401: clave de acceso invalida")),true);
});
