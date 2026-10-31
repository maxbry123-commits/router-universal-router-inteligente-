// iguales.js — comparacion de secretos: sha256 de ambos lados + timingSafeEqual SIEMPRE (sin retorno temprano por longitud). Lo usan server.js y swe_rutas.js.
import test from 'node:test';
import assert from 'node:assert/strict';
import crypto from 'node:crypto';
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { iguales } from '../src/iguales.js';

const SRC = path.join(path.dirname(fileURLToPath(import.meta.url)), '..', 'src');

test('iguales: verdadero solo con el mismo valor exacto; longitudes distintas, prefijos y vacios son falsos', () => {
  assert.equal(iguales('secreto-1', 'secreto-1'), true);
  for (const [a, b] of [['secreto-1', 'secreto-2'], ['secreto', 'secreto-1'], ['secreto-1', 'secreto'], ['', 'x'], ['x', ''], ['ñ', 'n']]) assert.equal(iguales(a, b), false, `${a} vs ${b}`);
  assert.equal(iguales(undefined, undefined), true, 'String(undefined) === String(undefined): los llamadores ya descartan vacios');
});

test('iguales: SIEMPRE llama a timingSafeEqual con dos digests sha256 de 32 bytes, tambien con longitudes distintas (sin retorno temprano)', () => {
  const orig = crypto.timingSafeEqual, vistos = [];
  crypto.timingSafeEqual = (x, y) => { vistos.push([x.length, y.length]); return orig(x, y); };
  try {
    assert.equal(iguales('a', 'bbbbbbbbbbbbbbbbbbbbbbbbbb'), false);
    assert.equal(iguales('mismo', 'mismo'), true);
  } finally { crypto.timingSafeEqual = orig; }
  assert.deepEqual(vistos, [[32, 32], [32, 32]]);
});

test('server.js y swe_rutas.js usan la comparacion comun (ninguna conserva la comparacion por longitud)', () => {
  for (const f of ['server.js', 'swe_rutas.js']) {
    const src = fs.readFileSync(path.join(SRC, f), 'utf8');
    assert.match(src, /from '\.\/iguales\.js'/, f);
    assert.ok(!/x\.length === y\.length/.test(src), `${f} no debe comparar longitudes antes`);
    assert.ok(!/timingSafeEqual/.test(src), `${f} no llama a timingSafeEqual directamente`);
  }
});
