// X-Ray: contrato cruzado, SIN red ni secretos. No comprueba proveedor o mirror vivo.
import test from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { MODELOS_API, idsRespaldo } from '../src/respaldo.js';
import { MODELOS_SWE, SWE_LISTAS, rutaSwe, armar } from '../../../chat/frontend/swe-directo.js';

const conf = JSON.parse(readFileSync(new URL('../../../SWE CODE free/provider-openclaw.json', import.meta.url), 'utf8'));
const openclawIds = new Set(conf.modelos.map(m => m.id));
const yaiwesIds = new Set(MODELOS_SWE.map(m => m[0]));
const api = MODELOS_API.map(m => m.id);
const locales = idsRespaldo().filter(id => !id.includes('/'));

test('ambos chats usan los 5 ids de proveedor sin sustitucion de modelo', () => {
  assert.equal(api.length, 5);
  assert.equal(new Set(api).size, 5);
  for (const id of api) {
    assert.ok(openclawIds.has(id), 'falta en provider OpenClaw: ' + id);
    assert.ok(yaiwesIds.has(id), 'falta en YAIWES: ' + id);
    assert.equal(rutaSwe(id), '/web/v1/chat/completions');
    assert.equal(armar({ model: id, mensaje: 'ping', sesion: 'x' }).model, id);
  }
});
test('ambos chats declaran los 4 modelos HF y el frontend conserva sus ids de bridge', () => {
  assert.equal(locales.length, 4);
  for (const id of locales) {
    assert.ok(openclawIds.has(id), 'falta OpenClaw HF: ' + id);
    assert.ok(yaiwesIds.has('hf/' + id), 'falta YAIWES HF: ' + id);
    const ficha = SWE_LISTAS['swe-code'].modelos.find(m => armar({ model: m[0], mensaje: 'ping', sesion: 'x' }).model === id);
    assert.ok(ficha, 'no hay alias YAIWES para ' + id);
    assert.equal(rutaSwe(ficha[0]), '/web/v1/chat/completions');
  }
});
test('el provider de OpenClaw expone el endpoint compatible del bridge, sin otra infraestructura', () => {
  assert.equal(conf.provider, 'swecode');
  assert.equal(conf.tipo, 'openai-compatible');
  assert.ok(/\/v1$/.test(conf.base_url));
  assert.equal(conf.api_key, '${RIU_API_KEY}');
});
