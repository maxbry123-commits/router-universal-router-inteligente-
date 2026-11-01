// X-Ray 5: abortar Retry-After, checkpoint y HTTP local, sin claves ni modelos reales.
import test from 'node:test';
import assert from 'node:assert/strict';
import http from 'node:http';
import { BASES, externo, limpiarEstado, limpiarClaves, esperarCancelable } from '../src/respaldo.js';
import { retomarLocal } from '../src/retomar_local.js';
import { ACCESO_TEST } from './helpers/acceso.mjs';
import { prepararApp, arrancar, limpiar, registrarMock } from './helpers/bridge_app.mjs';
const mensajes = [{ role: 'user', content: 'hola' }], baseGroq = BASES.groq;
test.afterEach(() => { BASES.groq = baseGroq; limpiarEstado(); limpiarClaves(); });

test('abort durante backoff 429 impide consultar otra clave', async () => {
  limpiarEstado(); limpiarClaves();
  let consultas = 0, avisar;
  const esperando = new Promise(ok => avisar = ok);
  const srv = http.createServer((req, res) => {
    req.resume(); req.on('end', () => {
      if (req.url.endsWith('/chat/completions')) consultas++;
      res.writeHead(429, { 'Retry-After': '20', 'content-type': 'application/json' });
      res.end('{"error":{"code":"rate_limit"}}');
    });
  }).listen(0, '127.0.0.1');
  await new Promise(ok => srv.once('listening', ok));
  BASES.groq = `http://127.0.0.1:${srv.address().port}/v1`;
  const c = new AbortController();
  try {
    const p = externo('groq/qwen/qwen3.8-27b', mensajes, {
      env: { GROQ_API_KEY: 'gsk-FAKE-A', GROQ_API_KEY_2: 'gsk-FAKE-B' },
      opts: { signal: c.signal, esperar: () => { avisar(); return new Promise(() => {}); } },
    });
    await Promise.race([esperando, new Promise((_, fail) => setTimeout(() => fail(new Error('no llego al backoff')), 3500))]);
    c.abort();
    await assert.rejects(p, e => e.code === 'ABORTADO');
    assert.equal(consultas, 1);
  } finally { srv.closeAllConnections?.(); srv.close(); }
});

test('abort previo no inicia Retry-After ni checkpoint', async () => {
  const c = new AbortController(); c.abort();
  let esperas = 0;
  await assert.rejects(esperarCancelable(100, { signal: c.signal, esperar: () => { esperas++; return Promise.resolve(); } }), e => e.code === 'ABORTADO');
  assert.equal(esperas, 0);
  await assert.rejects(retomarLocal('xray5-cancelada', 'qwen3-0.6b', mensajes, { opts: { signal: c.signal } }), e => e.code === 'ABORTADO');
});

test('stream SSE hacia local sin upstream SSE: desconectar cierra HTTP upstream', async () => {
  prepararApp(); // copia de prueba del bridge; no modifica repositorio ni despliegues
  let avisar, fin;
  const recibida = new Promise(ok => avisar = ok), cerrado = new Promise(ok => fin = ok);
  let consultas = 0;
  const upstream = http.createServer((req, res) => {
    req.resume(); req.on('end', () => { consultas++; res.on('close', fin); avisar(); }); // no devuelve cuerpo: se espera cancelacion
  }).listen(0, '127.0.0.1');
  registrarMock(upstream);
  await new Promise(ok => upstream.once('listening', ok));
  const bridge = await arrancar('XRAY5_ABORT_LOCAL', {
    SWECODE_URL_S1: `http://127.0.0.1:${upstream.address().port}/v1`,
    BRIDGE_DEADLINE_MS: '10000', BRIDGE_SSE_KEEPALIVE_MS: '500',
  });
  const cliente = http.request(bridge.base + '/v1/chat/completions', {
    method: 'POST', headers: { 'x-api-key': ACCESO_TEST, 'content-type': 'application/json' },
  }, res => res.resume());
  cliente.on('error', () => {}); // ECONNRESET esperado al destruir el cliente
  cliente.end(JSON.stringify({ model: 'qwen3-0.6b', messages: mensajes, stream: true }));
  try {
    await Promise.race([recibida, new Promise((_, fail) => setTimeout(() => fail(new Error('sin peticion local')), 3500))]);
    cliente.destroy();
    await Promise.race([cerrado, new Promise((_, fail) => setTimeout(() => fail(new Error('modelo local no cancelado')), 3500))]);
    assert.equal(consultas, 1);
  } finally { cliente.destroy(); limpiar(); }
});
