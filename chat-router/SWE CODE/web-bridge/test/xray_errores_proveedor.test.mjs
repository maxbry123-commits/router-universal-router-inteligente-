import test from 'node:test';
import assert from 'node:assert/strict';
import { clasificarError, TABLA_ERRORES, MODELOS_API } from '../src/respaldo.js';

test('GLM 5.3 conserva el ID oficial NVIDIA y 410 se clasifica sin cambio silencioso de modelo', () => {
  assert.ok(MODELOS_API.some(x => x.id === 'nvidia/z-ai/glm-5.3'));
  const p = clasificarError(410);
  assert.equal(p.tipo, 'modelo_no_servido');
  assert.equal(p.reintentar, false);
  assert.equal(p.rotarClave, false);
  assert.match(TABLA_ERRORES.modelo_no_servido.texto, /sin sustitucion/);
});
