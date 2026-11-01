// Verificacion cruzada REAL: bridge y Router MVP leen los mismos archivos de la ficha.
import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import { spawnSync } from 'node:child_process';
import { fileURLToPath } from 'node:url';
import { textoSystemPrompt, conSystemPrompt, conSystemPromptTexto, systemPromptOn, setSystemPromptOn } from '../src/systemprompt.js';

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
