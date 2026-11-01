// X-Ray 2: Detener cancela HTTP sin streaming y NO rota claves ni proveedores.
import test from 'node:test';
import assert from 'node:assert/strict';
import http from 'node:http';
import { BASES, externo, respaldo, local, limpiarEstado, limpiarClaves } from '../src/respaldo.js';

const mensajes = [{ role: 'user', content: 'hola' }];
function servidorLento() {
  return new Promise(resolve => {
    const peticiones = [];
    let avisarPrimera;
    const primera = new Promise(r => { avisarPrimera = r; });
    const server = http.createServer((req, res) => {
      peticiones.push(req.url); avisarPrimera();
      req.resume();
      req.on('end', () => {}); // la respuesta no llega: el cliente debe abortar
    });
    server.listen(0, '127.0.0.1', () => resolve({
      url: `http://127.0.0.1:${server.address().port}`,
      peticiones, primera,
      cerrar: () => { server.closeAllConnections?.(); server.close(); },
    }));
  });
}
test.beforeEach(() => { limpiarEstado(); limpiarClaves(); });

test('externo sin stream: abort cancela el fetch y no intenta otra clave', async () => {
  const srv = await servidorLento();
  BASES.groq = srv.url;
  const c = new AbortController();
  try {
    const p = externo('groq/qwen/qwen3.8-27b', mensajes, {
      env: { GROQ_API_KEY: 'gsk-FAKE-A', GROQ_API_KEY_2: 'gsk-FAKE-B' },
      opts: { signal: c.signal, timeoutMs: 4000 },
    });
    const respaldoTimer = setTimeout(() => c.abort(), 1500);
    await srv.primera;
    c.abort(); clearTimeout(respaldoTimer);
    await assert.rejects(p, e => e.code === 'ABORTADO');
    assert.equal(srv.peticiones.filter(x => x.endsWith('/chat/completions')).length, 1);
  } finally { srv.cerrar(); }
});

test('local S1 sin stream: abort NO salta a S2', async () => {
  const s1 = await servidorLento(), s2 = await servidorLento(), c = new AbortController();
  try {
    const p = local('qwen3-0.6b', mensajes, { env: { SWECODE_URL_S1: s1.url, SWECODE_URL_S2: s2.url }, opts: { signal: c.signal, timeoutMs: 4000 } });
    const respaldoTimer = setTimeout(() => c.abort(), 1500);
    await s1.primera;
    c.abort(); clearTimeout(respaldoTimer);
    await assert.rejects(p, e => e.code === 'ABORTADO');
    assert.equal(s1.peticiones.length, 1);
    assert.equal(s2.peticiones.length, 0);
  } finally { s1.cerrar(); s2.cerrar(); }
});

test('respaldo: la cancelacion recibida antes del inicio no consulta ningun proveedor', async () => {
  const c = new AbortController(); c.abort();
  const s1 = await servidorLento();
  try {
    await assert.rejects(respaldo(mensajes, { env: { SWECODE_URL_S1: s1.url }, opts: { signal: c.signal } }), e => e.code === 'ABORTADO');
    assert.equal(s1.peticiones.length, 0);
  } finally { s1.cerrar(); }
});

test('respaldo: Detener durante GET /models cancela descubrimiento, no salta a NVIDIA', async () => {
  const groq = await servidorLento(), nvidia = await servidorLento(), c = new AbortController();
  BASES.groq = groq.url; BASES.nvidia = nvidia.url;
  try {
    const p = respaldo(mensajes, { env: { GROQ_API_KEY: 'gsk-FAKE-A', NVIDIA_API_KEY: 'nv-FAKE-B' },
      opts: { signal: c.signal, descubrirMs: 4000, timeoutMs: 4000 } });
    const respaldoTimer = setTimeout(() => c.abort(), 1500);
    await groq.primera;
    c.abort(); clearTimeout(respaldoTimer);
    await assert.rejects(p, e => e.code === 'ABORTADO');
    assert.equal(nvidia.peticiones.length, 0);
  } finally { groq.cerrar(); nvidia.cerrar(); }
});
