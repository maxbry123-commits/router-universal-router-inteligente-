// Simulaciones end-to-end del transporte actual: la API elegida no se sustituye por otra.
// No requiere cuentas, Space, SDK externo ni secretos reales.
import test from 'node:test';
import assert from 'node:assert/strict';
import http from 'node:http';
import { BASES, MODELOS_API, esExterno, externo, limpiarClaves, estadoRespaldo, setClaves } from '../src/respaldo.js';

const grupos = [
  ['deepseek', 'deepseek-v4-pro', 'DEEPSEEK_API_KEY'],
  ['minimax', 'MiniMax-M3', 'MINIMAX_API_KEY'],
  ['openai', 'gpt-5.6', 'OPENAI_API_KEY'],
];

async function servidor() {
  const recibidas = [];
  const s = http.createServer((req, res) => {
    let data = ''; req.on('data', x => { data += x; });
    req.on('end', () => {
      recibidas.push({ path: req.url, authorization: req.headers.authorization, body: JSON.parse(data) });
      res.writeHead(200, { 'content-type': 'application/json' });
      res.end(JSON.stringify({ id: 'mock', choices: [{ index: 0, message: { role: 'assistant', content: 'RESPUESTA_OK' }, finish_reason: 'stop' }], usage: { completion_tokens: 1 } }));
    });
  });
  await new Promise(resolve => s.listen(0, '127.0.0.1', resolve));
  return { url: 'http://127.0.0.1:' + s.address().port, recibidas, cerrar: () => new Promise(resolve => s.close(resolve)) };
}

test('DeepSeek, MiniMax y OpenAI salen por su API exacta con la clave cifrada cargada en memoria', async () => {
  const mocks = await Promise.all(grupos.map(() => servidor()));
  const bases = { ...BASES };
  try {
    const keys = {};
    grupos.forEach(([p], i) => { BASES[p] = mocks[i].url; keys[p] = ['TEST-KEY-' + p]; });
    setClaves(keys);
    for (let i = 0; i < grupos.length; i++) {
      const [p, model] = grupos[i], id = p + '/' + model;
      assert.ok(esExterno(id), id);
      assert.equal(estadoRespaldo({})[p], 1);
      const res = await externo(id, [{ role: 'user', content: 'hola' }], { env: {} });
      assert.equal(res.salida, 'RESPUESTA_OK');
      assert.equal(res.usado, id);
      assert.equal(res.via, p);
      assert.equal(mocks[i].recibidas.length, 1);
      assert.equal(mocks[i].recibidas[0].path, '/chat/completions');
      assert.equal(mocks[i].recibidas[0].body.model, model);
      assert.equal(mocks[i].recibidas[0].authorization, 'Bearer TEST-KEY-' + p);
    }
  } finally {
    limpiarClaves();
    Object.assign(BASES, bases);
    await Promise.all(mocks.map(m => m.cerrar()));
  }
});

test('modelos y proveedores compatibles aparecen sin exponer credenciales', () => {
  for (const [p, m] of grupos) assert.ok(MODELOS_API.some(x => x.id === p + '/' + m));
  assert.ok(!esExterno('openai/otro-modelo-inventado'));
  assert.ok(!JSON.stringify(estadoRespaldo({})).includes('TEST-KEY'));
});
