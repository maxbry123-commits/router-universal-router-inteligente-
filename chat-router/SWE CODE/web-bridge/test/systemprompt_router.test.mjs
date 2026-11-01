// Verificacion cruzada REAL: bridge y Router MVP leen los mismos archivos de la ficha.
import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import { spawnSync } from 'node:child_process';
import { fileURLToPath } from 'node:url';
import { textoSystemPrompt, conSystemPrompt, conSystemPromptTexto, systemPromptOn, setSystemPromptOn, consultarPromptRouter } from '../src/systemprompt.js';

const RAIZ = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..', '..', '..', '..');
const ENV = { ...process.env, RIU_REPO_ROOT: RAIZ };
const FICHA = path.join(RAIZ, 'router-mvp', 'fichas', 'system-prompt');

test('compone la ficha completa original, no solo system_core', () => {
  const texto = textoSystemPrompt(ENV);
  for (const archivo of ['system_core.md', 'bloques/bloque_3.md', 'bloques/bloque_4.md']) {
    assert.ok(fs.existsSync(path.join(FICHA, archivo)), archivo);
  }
  assert.ok(texto.includes('[CREACIÓN DE CÓDIGO]'));
  assert.ok(texto.includes('BLOQUE 4/5'));
  assert.ok(texto.includes('el ROL DEL NODO indicado más abajo'));
  assert.ok(!texto.includes('[ROL_ESPECIALIZADO]'));
});

test('texto JS es identico byte a byte a mvp.prompt.sistema() (sin otra copia)', (t) => {
  const py = spawnSync('python3', ['-c',
    "import sys;sys.path[:0]=[sys.argv[1],sys.argv[2]];from mvp import prompt;print(prompt.sistema(),end='')",
    path.join(RAIZ,'chat-router','chat','backend'),path.join(RAIZ,'router-mvp')], {encoding:'utf8',cwd:RAIZ});
  if (py.error?.code === 'ENOENT') return t.skip('python3 no instalado en este host');
  assert.equal(py.status, 0, py.stderr);
  assert.equal(textoSystemPrompt(ENV), py.stdout);
});

test('OpenClaw fijo ON (sin boton): YAIWES OFF no lo apaga', () => {
  const dir = fs.mkdtempSync(path.join(os.tmpdir(),'riu-prompt-'));
  const env = {...ENV,BRIDGE_STATE_DIR:dir};
  try {
    assert.equal(systemPromptOn(env), true);
    setSystemPromptOn(false,env);
    const mensajes=[{role:'user',content:'hola'}];
    assert.deepEqual(conSystemPrompt(mensajes,env), mensajes);
    assert.equal(conSystemPrompt(mensajes,env,{forzarOn:true})[0].role,'system');
    assert.ok(conSystemPromptTexto('hola',env,{forzarOn:true}).includes('BLOQUE 3/5'));
    assert.equal(conSystemPromptTexto('hola',env),'hola');
  } finally {fs.rmSync(dir,{recursive:true,force:true});}
});

test('boton YAIWES consulta y modifica solo el prompt_on del Router (con recibo)', async () => {
  const dir=fs.mkdtempSync(path.join(os.tmpdir(),'riu-prompt-router-'));
  const env={...ENV,BRIDGE_STATE_DIR:dir,RIU_ROUTER_URL:'http://127.0.0.1:7861',RIU_API_KEY:'clave-prueba'};
  let on=false; const llamadas=[];
  const fetchFn=async (url,req)=>{
    assert.equal(url,'http://127.0.0.1:7861/plugins/puente_chat/call/agent_access_lock');
    assert.equal(req.headers['x-api-key'],'clave-prueba');
    const data=JSON.parse(req.body);llamadas.push(data);
    if(data.quien==='prompt') on=!data.locked;
    return {ok:true,json:async()=>({status:'ok',result:{prompt_locked:!on}})};
  };
  try {
    assert.equal(await consultarPromptRouter(null,{env,fetchFn}),false);
    assert.equal(await consultarPromptRouter(true,{env,fetchFn}),true);
    assert.equal(systemPromptOn(env),true);
    assert.equal(await consultarPromptRouter(false,{env,fetchFn}),false);
    assert.equal(systemPromptOn(env),false);
    assert.deepEqual(llamadas,[{}, {quien:'prompt',locked:false}, {quien:'prompt',locked:true}]);
  } finally {fs.rmSync(dir,{recursive:true,force:true});}
});

test('sin recibo Router el boton no cambia estado local ni finge ON', async () => {
  const dir=fs.mkdtempSync(path.join(os.tmpdir(),'riu-prompt-error-'));
  const env={...ENV,BRIDGE_STATE_DIR:dir,RIU_ROUTER_URL:'http://127.0.0.1:7861',RIU_API_KEY:'clave-prueba'};
  try {
    setSystemPromptOn(false,env);
    await assert.rejects(consultarPromptRouter(true,{env,fetchFn:async()=>({ok:false,status:503})}),/ROUTER_HTTP_503/);
    assert.equal(systemPromptOn(env),false);
  } finally {fs.rmSync(dir,{recursive:true,force:true});}
});
