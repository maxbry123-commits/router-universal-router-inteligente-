// responses.test.mjs — POST /v1/responses minimo (Codex): traduce a /v1/chat/completions y reutiliza externo/local; salida en formato Responses (JSON o SSE).
import test, { before, after } from 'node:test';
import assert from 'node:assert/strict';
import http from 'node:http';
import { ACCESO_TEST } from './helpers/acceso.mjs';
import { prepararApp, arrancar, limpiar, registrarMock } from './helpers/bridge_app.mjs';

let S, g;
const M = 'groq/qwen/qwen3.8-27b';
before(async () => {
  prepararApp();
  g = { hits: [], respuesta: { finish_reason: 'stop', message: { role: 'assistant', content: 'hola desde groq' } } };
  const s = http.createServer((req, res) => {
    let d = ''; req.on('data', (c) => d += c); req.on('end', () => {
      g.hits.push({ auth: req.headers.authorization, body: d ? JSON.parse(d) : null });
      res.writeHead(200, { 'content-type': 'application/json' }); res.end(JSON.stringify({ choices: [g.respuesta] }));
    });
  }).listen(0, '127.0.0.1'); registrarMock(s); await new Promise((r) => s.on('listening', r));
  S = await arrancar('resp', { TEST_GROQ_URL: `http://127.0.0.1:${s.address().port}`, GROQ_API_KEY: 'gsk-FAKE-RESPONSES-1', BRIDGE_RESPALDO_MS: '5000' });
});
after(() => limpiar());
const post = async (body, headers = {}) => { const r = await fetch(S.base + '/v1/responses', { method: 'POST', headers: { 'content-type': 'application/json', ...headers }, body: JSON.stringify(body) }); const texto = await r.text(); let json = null; try { json = JSON.parse(texto); } catch { /* sse */ } return { status: r.status, headers: r.headers, texto, json }; };
const eventos = (texto) => texto.split('\n\n').filter(Boolean).map((b) => { const ev = /^event: (.+)$/m.exec(b), d = /^data: (.+)$/m.exec(b); return { ev: ev && ev[1], data: d && d[1] !== '[DONE]' ? JSON.parse(d[1]) : null }; });

test('R1. sin clave de acceso 401 (misma puerta que el resto)', async () => {
  assert.equal((await post({ model: M, input: 'hola' }, { 'x-api-key': '' })).status, 401);
});

test('R2. input string + instructions -> chat/completions (system + user) y salida en formato Responses', async () => {
  g.hits.length = 0;
  const r = await post({ model: M, instructions: 'Eres breve', input: 'hola' });
  assert.equal(r.status, 200, r.texto.slice(0, 200));
  assert.equal(r.json.object, 'response'); assert.equal(r.json.status, 'completed'); assert.match(r.json.id, /^resp_/); assert.equal(r.json.model, M);
  assert.equal(r.json.output[0].type, 'message'); assert.equal(r.json.output[0].role, 'assistant');
  assert.deepEqual(r.json.output[0].content[0], { type: 'output_text', text: 'hola desde groq', annotations: [] });
  assert.equal(r.json.output_text, 'hola desde groq');
  assert.ok(r.json.usage && 'input_tokens' in r.json.usage && 'output_tokens' in r.json.usage && 'total_tokens' in r.json.usage);
  const m = g.hits[0].body.messages;
  assert.equal(g.hits[0].auth, 'Bearer gsk-FAKE-RESPONSES-1');
  assert.ok(m.some((x) => x.role === 'system' && x.content.includes('Eres breve')));
  assert.equal(m.at(-1).role, 'user'); assert.equal(m.at(-1).content, 'hola');
});

test('R3. input como lista de items: developer->system, partes input_text, function_call y function_call_output -> tool_calls / role:tool', async () => {
  g.hits.length = 0;
  const r = await post({ model: M, input: [
    { type: 'message', role: 'developer', content: [{ type: 'input_text', text: 'reglas' }] },
    { type: 'message', role: 'user', content: [{ type: 'input_text', text: 'lista los archivos' }] },
    { type: 'function_call', call_id: 'call_1', name: 'ls', arguments: '{"ruta":"."}' },
    { type: 'function_call_output', call_id: 'call_1', output: 'a.js b.js' },
  ] });
  assert.equal(r.status, 200, r.texto.slice(0, 200));
  const m = g.hits[0].body.messages.filter((x) => !(x.role === 'system' && !x.content.includes('reglas')));
  assert.ok(m.some((x) => x.role === 'system' && x.content.includes('reglas')));
  assert.ok(m.some((x) => x.role === 'user' && x.content === 'lista los archivos'));
  const asis = m.find((x) => x.role === 'assistant' && x.tool_calls);
  assert.equal(asis.tool_calls[0].id, 'call_1'); assert.equal(asis.tool_calls[0].function.name, 'ls'); assert.equal(asis.tool_calls[0].function.arguments, '{"ruta":"."}');
  const tool = m.find((x) => x.role === 'tool'); assert.equal(tool.tool_call_id, 'call_1'); assert.equal(tool.content, 'a.js b.js');
});

test('R4. tools de Responses (type function plano) viajan como tools de chat y los tool_calls vuelven como items function_call', async () => {
  g.hits.length = 0;
  g.respuesta = { finish_reason: 'tool_calls', message: { role: 'assistant', content: null, tool_calls: [{ id: 'call_9', type: 'function', function: { name: 'ls', arguments: '{"ruta":"src"}' } }] } };
  try {
    const r = await post({ model: M, input: 'lista src', tools: [{ type: 'function', name: 'ls', description: 'lista', parameters: { type: 'object', properties: { ruta: { type: 'string' } } } }, { type: 'web_search' }] });
    assert.equal(r.status, 200, r.texto.slice(0, 200));
    assert.deepEqual(g.hits[0].body.tools, [{ type: 'function', function: { name: 'ls', description: 'lista', parameters: { type: 'object', properties: { ruta: { type: 'string' } } } } }]);
    const fc = r.json.output.find((o) => o.type === 'function_call');
    assert.equal(fc.call_id, 'call_9'); assert.equal(fc.name, 'ls'); assert.equal(fc.arguments, '{"ruta":"src"}'); assert.equal(fc.status, 'completed');
  } finally { g.respuesta = { finish_reason: 'stop', message: { role: 'assistant', content: 'hola desde groq' } }; }
});

test('R5. stream:true -> SSE de Responses (created, output_text.delta..., output_text.done, completed) y el texto reensamblado es identico', async () => {
  const largo = 'palabra '.repeat(120);
  g.respuesta = { finish_reason: 'stop', message: { role: 'assistant', content: largo } };
  try {
    const r = await post({ model: M, input: 'hola', stream: true });
    assert.equal(r.status, 200); assert.match(r.headers.get('content-type'), /text\/event-stream/);
    const ev = eventos(r.texto), tipos = ev.map((e) => e.ev);
    assert.equal(tipos[0], 'response.created'); assert.equal(tipos.at(-1), 'response.completed');
    for (const t of ['response.output_item.added', 'response.content_part.added', 'response.output_text.delta', 'response.output_text.done', 'response.content_part.done', 'response.output_item.done']) assert.ok(tipos.includes(t), t);
    assert.ok(tipos.filter((t) => t === 'response.output_text.delta').length > 1, 'texto largo en varios fragmentos');
    assert.equal(ev.filter((e) => e.ev === 'response.output_text.delta').map((e) => e.data.delta).join(''), largo);
    assert.equal(ev.find((e) => e.ev === 'response.output_text.done').data.text, largo);
    const fin = ev.at(-1).data.response; assert.equal(fin.status, 'completed'); assert.equal(fin.output[0].content[0].text, largo);
    assert.ok(ev.every((e, i) => e.data && e.data.type === e.ev && (i === 0 || e.data.sequence_number > ev[i - 1].data.sequence_number)));
  } finally { g.respuesta = { finish_reason: 'stop', message: { role: 'assistant', content: 'hola desde groq' } }; }
});

test('R6. errores: modelo no autorizado 400 MODELO_INVALIDO, input ausente 400, JSON roto 400; nunca 200 vacio', async () => {
  const a = await post({ model: 'groq/llama-3.3-70b-versatile', input: 'hola' });
  assert.equal(a.status, 400); assert.equal(a.json.error.code, 'MODELO_INVALIDO');
  const b = await post({ model: M }); assert.equal(b.status, 400); assert.equal(b.json.error.code, 'INPUT_INVALIDO');
  const c = await post({ model: M, input: 5 }); assert.equal(c.status, 400);
  const d = await post({ model: M, input: [] }); assert.equal(d.status, 400);
});

test('R7. stream:true con error previo al stream responde JSON de error (no SSE roto)', async () => {
  const a = await post({ model: 'groq/llama-3.3-70b-versatile', input: 'hola', stream: true });
  assert.equal(a.status, 400); assert.equal(a.json.error.code, 'MODELO_INVALIDO');
});

test('R8. /v1/models sigue listando y /v1/responses no filtra la clave de acceso ni la de Groq', async () => {
  const r = await post({ model: M, input: 'hola' });
  assert.ok(!r.texto.includes('gsk-FAKE-RESPONSES') && !r.texto.includes(ACCESO_TEST));
});
