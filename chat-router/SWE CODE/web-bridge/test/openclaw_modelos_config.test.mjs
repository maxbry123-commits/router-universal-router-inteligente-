import test from 'node:test';
import assert from 'node:assert/strict';
import { mkdtempSync, writeFileSync, readFileSync, rmSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { sincronizarModelosOpenClaw } from '../src/openclaw.js';

function conConfig(fn) {
  const dir = mkdtempSync(join(tmpdir(), 'riu-openclaw-'));
  const path = join(dir, 'openclaw.json');
  const base = { gateway: { auth: { token: 'PAREJA-NO-TOCAR' } },
    models: { mode: 'replace', providers: {
      swecode: { baseUrl: 'http://127.0.0.1:7860/v1', apiKey: 'local', api: 'openai-completions',
        models: [{id: 'web-qwen38max', name: 'Qwen 3.8 Max (web)'}] },
      otro: { baseUrl: 'https://invalid.example/v1', apiKey: 'TEST-EXTERNO', models: [] },
    }},
    agents: { defaults: { model: { primary: 'swecode/swecode-consulta' },
      models: {'swecode/swecode-consulta': {}} } } };
  writeFileSync(path, JSON.stringify(base), { mode: 0o600 });
  try { fn({ dir, path, base }); }
  finally { rmSync(dir, { recursive: true, force: true }); }
}
test('OpenClaw: un único provider SWE, clave del chat y catálogo real, sin tocar pairing ni agentes', () => conConfig(({dir,path,base}) => {
  const ids = ['web-qwen38max', 'swecode-consulta', 'groq/qwen/qwen3.8-27b',
    'nvidia/minimaxai/minimax-m3.1-flash', 'nvidia/z-ai/glm-5.3', 'lfm2.5-350m'];
  assert.equal(sincronizarModelosOpenClaw(ids, { key: 'CLAVE-INTERNA-TEST', dir }), true);
  const cfg = JSON.parse(readFileSync(path, 'utf8'));
  assert.equal(cfg.models.providers.swecode.baseUrl, 'http://127.0.0.1:7870/openclaw/v1');
  assert.equal(cfg.models.providers.swecode.apiKey, 'CLAVE-INTERNA-TEST');
  assert.deepEqual(cfg.models.providers.otro, base.models.providers.otro);
  assert.deepEqual(cfg.gateway, base.gateway);
  assert.equal(cfg.agents.defaults.model.primary, base.agents.defaults.model.primary);
  assert.ok(ids.every(id => cfg.agents.defaults.models['swecode/' + id]));
  assert.deepEqual(cfg.models.providers.swecode.models.map(x => x.id), ids);
  assert.equal(sincronizarModelosOpenClaw(ids, { key: 'CLAVE-INTERNA-TEST', dir }), false, 'no reescribir config sin cambios');
}));
test('OpenClaw: falta de clave o fichero de gateway => no crear ni escribir', () => conConfig(({dir,path}) => {
  const orig = readFileSync(path, 'utf8');
  assert.equal(sincronizarModelosOpenClaw(['web-qwen38max'], { key: '', dir }), false);
  assert.equal(readFileSync(path, 'utf8'), orig);
}));
