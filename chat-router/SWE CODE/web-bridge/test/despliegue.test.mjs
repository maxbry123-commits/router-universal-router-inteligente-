// despliegue.test.mjs — el Dockerfile del bridge copia TODO lo que el codigo lee en tiempo de ejecucion, y el hook de sesion usa las rutas correctas.
// El Dockerfile se "ejecuta" a mano: se aplican sus COPY sobre un directorio temporal y se comprueba que el bridge encuentra sus archivos en esa disposicion.
import test from 'node:test';
import assert from 'node:assert/strict';
import { spawnSync } from 'node:child_process';
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const QUI = path.dirname(fileURLToPath(import.meta.url));
const BRIDGE = path.resolve(QUI, '..'), RAIZ = path.resolve(BRIDGE, '..', '..', '..');
const DOCKERFILE = fs.readFileSync(path.join(BRIDGE, 'Dockerfile'), 'utf8');
const lineas = DOCKERFILE.split('\n').map(l => l.trim()).filter(l => l && !l.startsWith('#'));

// COPY ["origen", ..., "destino"] (forma JSON, por los espacios de "SWE CODE") con WORKDIR vigente
function capa() {
  let wd = '/', copias = [];
  for (const l of lineas) {
    const w = /^WORKDIR\s+(.+)$/.exec(l); if (w) { wd = path.posix.resolve(wd, w[1].trim()); continue; }
    const c = /^COPY\s+(\[.*\])$/.exec(l); if (!c) continue;
    const a = JSON.parse(c[1]), dest = a.pop();
    copias.push({ origenes: a, dest: path.posix.resolve(wd, dest), destTermina: dest.endsWith('/') || dest === '.' || dest === './' });
  }
  return copias;
}
const env = (k) => { const m = new RegExp(`${k}=([^\\s\\\\]+)`).exec(DOCKERFILE); return m && m[1]; };

test('Dockerfile: python3 + cryptography instalados, puerto 7870 (BRIDGE_PORT y EXPOSE) y estado en /data', () => {
  assert.match(DOCKERFILE, /python3/); assert.match(DOCKERFILE, /cryptography/);
  assert.equal(env('BRIDGE_PORT'), '7870'); assert.match(DOCKERFILE, /EXPOSE 7870/); assert.ok(!/7860/.test(DOCKERFILE));
  assert.match(env('BRIDGE_STATE_DIR') || '', /^\/data\//);
});

test('Dockerfile: todo origen de COPY existe en el repo', () => {
  const copias = capa(); assert.ok(copias.length >= 6, 'copia varias cosas: ' + copias.length);
  for (const c of copias) for (const o of c.origenes) assert.ok(fs.existsSync(path.join(RAIZ, o)), `no existe ${o}`);
});

test('Dockerfile: aplicadas las COPY, el bridge encuentra en la imagen activar.js, FORMATO_SALIDA.md, provider-openclaw.json, claves_banco.py y memoria_hf.py; claves_banco.py corre sin PYTHONPATH', () => {
  const root = fs.mkdtempSync(path.join(os.tmpdir(), 'imagen-'));
  for (const c of capa()) for (const o of c.origenes) {  // semantica de COPY: un directorio vuelca su CONTENIDO en el destino; un archivo va a destino/nombre si el destino es carpeta
    const origen = path.join(RAIZ, o), dest = path.join(root, c.dest), carpeta = c.destTermina || c.origenes.length > 1;
    if (fs.statSync(origen).isDirectory()) fs.cpSync(origen, dest, { recursive: true });
    else { const f = carpeta ? path.join(dest, path.basename(origen)) : dest; fs.mkdirSync(path.dirname(f), { recursive: true }); fs.copyFileSync(origen, f); }
  }
  const wd = path.join(root, 'repo', 'chat-router', 'SWE CODE', 'web-bridge');
  const src = path.join(wd, 'src');
  for (const rel of ['../../../SWE CODE free/activar.js', '../../../SWE CODE free/documentos.js', '../../../SWE CODE free/provider-openclaw.json', '../../../SWE CODE free/swen.json', '../../../chat/backend/mvp/prompts/FORMATO_SALIDA.md', '../claves_banco.py', '../memoria_hf.py', '../../../chat/backend/mvp/bank.py', '../../../chat/backend/mvp/memoria.py', '../../../chat/backend/mvp/hf_store.py', 'server.js']) assert.ok(fs.existsSync(path.resolve(src, rel)), `la imagen no trae ${rel}`);
  assert.ok(fs.existsSync(path.join(wd, 'package.json')));
  const estado = fs.mkdtempSync(path.join(os.tmpdir(), 'estado-'));
  const r = spawnSync('python3', [path.join(wd, 'claves_banco.py'), 'leer'], { env: { PATH: process.env.PATH, HOME: estado, RIU_API_KEY: 'acceso-prueba', BRIDGE_STATE_DIR: estado, RIU_BANCO_ROUTER: path.join(estado, 'no.bin') }, encoding: 'utf8', timeout: 60000 });
  assert.equal(r.status, 0, (r.stderr || '').slice(-300)); assert.deepEqual(JSON.parse(r.stdout), { groq: [], nvidia: [] });
  fs.rmSync(root, { recursive: true, force: true }); fs.rmSync(estado, { recursive: true, force: true });
});

// ---- .claude/hooks/session-start.sh ----
const HOOK = path.join(RAIZ, '.claude', 'hooks', 'session-start.sh');
function correrHook() {
  const d = fs.mkdtempSync(path.join(os.tmpdir(), 'hook-')), shim = path.join(d, 'bin'), log = path.join(d, 'pip.log'), envFile = path.join(d, 'env.sh');
  fs.mkdirSync(shim); fs.writeFileSync(path.join(shim, 'python3'), `#!/bin/sh\necho "$@" >> "${log}"\nexit 0\n`, { mode: 0o755 }); fs.writeFileSync(envFile, '');
  const e = { PATH: `${shim}:${process.env.PATH}`, HOME: d, CLAUDE_CODE_REMOTE: 'true', CLAUDE_PROJECT_DIR: RAIZ, CLAUDE_ENV_FILE: envFile };
  const vuelta = () => spawnSync('bash', [HOOK], { env: e, encoding: 'utf8', timeout: 30000 });
  return { vuelta, log, envFile, limpiar: () => fs.rmSync(d, { recursive: true, force: true }) };
}
test('hook de sesion: bash valido, instala router-mvp/mvp/requirements.txt (existente) y no hace nada fuera de la nube', () => {
  assert.equal(spawnSync('bash', ['-n', HOOK]).status, 0);
  const h = correrHook();
  try {
    const r = h.vuelta(); assert.equal(r.status, 0, r.stderr);
    const pip = fs.readFileSync(h.log, 'utf8');
    assert.ok(pip.includes(path.join(RAIZ, 'router-mvp', 'mvp', 'requirements.txt')) || pip.includes('router-mvp/mvp/requirements.txt'), pip);
    assert.ok(!/ -r mvp\/requirements\.txt/.test(pip));
    assert.ok(fs.existsSync(path.join(RAIZ, 'router-mvp', 'mvp', 'requirements.txt')));
    const fuera = spawnSync('bash', [HOOK], { env: { PATH: process.env.PATH, CLAUDE_PROJECT_DIR: RAIZ }, encoding: 'utf8' });
    assert.equal(fuera.status, 0); assert.equal(fuera.stdout, '');
  } finally { h.limpiar(); }
});

test('hook de sesion: PYTHONPATH = router-mvp:chat-router, idempotente (dos ejecuciones y dos "source" no duplican nada)', () => {
  const h = correrHook();
  try {
    h.vuelta(); h.vuelta();
    const txt = fs.readFileSync(h.envFile, 'utf8');
    assert.equal((txt.match(/router-mvp/g) || []).length >= 1 && txt.split('\n').filter(l => /PYTHONPATH/.test(l)).length, 1, 'una sola definicion tras dos ejecuciones:\n' + txt);
    const r = spawnSync('bash', ['-c', `export PYTHONPATH=/previo; . "${h.envFile}"; . "${h.envFile}"; echo "$PYTHONPATH"`], { encoding: 'utf8' });
    const partes = r.stdout.trim().split(':');
    assert.deepEqual(partes, [path.join(RAIZ, 'router-mvp'), path.join(RAIZ, 'chat-router'), '/previo']);
  } finally { h.limpiar(); }
});
