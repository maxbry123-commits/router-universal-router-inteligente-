// prueba-real/stack.mjs — pila de PRUEBA para el Gateway de OpenClaw (no es parte del plugin ni del bridge): servidores FALSOS de Groq (:18801), NVIDIA (:18802), HF local (:18803),
// Router MVP (:18804) y Harness (:18805) + el bridge REAL (web-bridge/src/server.js) en :7870. Claves FALSAS; sin red externa. Uso y comandos: SWE CODE free/HANDOFF.md ("Espejo OpenClaw: prueba real").
// Preparacion (una vez): PRUEBA_DIR=/tmp/b-oc; copiar web-bridge/src a $PRUEBA_DIR/app/src; node_modules con express (+ un playwright falso); motor.js falso; preload.mjs que fija BASES.groq/nvidia desde TEST_GROQ_URL/TEST_NVIDIA_URL.
// FAKE_TOOL / FAKE_TOOL_ARGS / FAKE_TOOL_PROVIDER: la tool que el modelo falso de Groq pide en su primera vuelta (defecto yaiwes_contexto {"accion":"fijo"}).
import http from 'node:http'; import fs from 'node:fs'; import { spawn } from 'node:child_process';
const B = process.env.PRUEBA_DIR || '/tmp/b-oc', REPO = process.env.RIU_REPO || '/home/user/router-universal-router-inteligente-';
const LOG = B + '/req.jsonl';
const log = (o) => fs.appendFileSync(LOG, JSON.stringify(o) + '\n');
const leer = (req) => new Promise((ok) => { let d = ''; req.on('data', (c) => d += c); req.on('end', () => { try { ok(d ? JSON.parse(d) : {}); } catch { ok({}); } }); });
const FAKE_TOOL = process.env.FAKE_TOOL || 'yaiwes_contexto';
function modelo(nombre, puerto, ids) {
  http.createServer(async (req, res) => {
    const b = req.method === 'POST' ? await leer(req) : {}, auth = String(req.headers.authorization || '').replace(/(.{6}).*/, '$1***');
    const tools = (b.tools || []).map((t) => (t.function || t).name);
    log({ srv: nombre, m: req.method, url: req.url, auth, model: b.model, stream: !!b.stream, tools: tools.length, nombres: tools.join(','), tool_msgs: (b.messages || []).filter((m) => m.role === 'tool').length });
    if (req.method === 'GET' && req.url.endsWith('/models')) { res.setHeader('content-type', 'application/json'); return res.end(JSON.stringify({ object: 'list', data: ids.map((id) => ({ id, object: 'model' })) })); }
    if (!req.url.endsWith('/chat/completions')) { res.statusCode = 404; return res.end('{}'); }
    const ultimaTool = [...(b.messages || [])].reverse().find((m) => m.role === 'tool');
    const nombreTool = tools.find((n) => n === FAKE_TOOL || n.endsWith(FAKE_TOOL));
    const pedirTool = process.env.FAKE_TOOL_PROVIDER ? nombre === process.env.FAKE_TOOL_PROVIDER : nombre === 'groq';
    const hacerTool = pedirTool && nombreTool && !ultimaTool;
    const texto = `FALSO-${nombre}[${b.model}] tools_ofrecidas=${tools.length}` + (ultimaTool ? ` resultado_tool=${String(typeof ultimaTool.content === 'string' ? ultimaTool.content : JSON.stringify(ultimaTool.content)).slice(0, 160)}` : '');
    const tc = [{ index: 0, id: 'call_fake1', type: 'function', function: { name: nombreTool, arguments: JSON.stringify(process.env.FAKE_TOOL_ARGS ? JSON.parse(process.env.FAKE_TOOL_ARGS) : { accion: 'fijo' }) } }];
    if (b.stream) {
      res.writeHead(200, { 'content-type': 'text/event-stream' });
      const ch = (delta, fin = null) => res.write('data: ' + JSON.stringify({ id: 'c1', object: 'chat.completion.chunk', created: 1, model: b.model, choices: [{ index: 0, delta, finish_reason: fin }] }) + '\n\n');
      ch({ role: 'assistant', content: '' });
      if (hacerTool) { ch({ tool_calls: tc }); ch({}, 'tool_calls'); } else { ch({ content: texto }); ch({}, 'stop'); }
      return res.end('data: [DONE]\n\n');
    }
    res.setHeader('content-type', 'application/json');
    res.end(JSON.stringify({ id: 'c1', object: 'chat.completion', created: 1, model: b.model, choices: [{ index: 0, message: hacerTool ? { role: 'assistant', content: null, tool_calls: tc.map(({ index, ...x }) => x) } : { role: 'assistant', content: texto }, finish_reason: hacerTool ? 'tool_calls' : 'stop' }], usage: { prompt_tokens: 3, completion_tokens: 4, total_tokens: 7 } }));
  }).listen(puerto, '127.0.0.1');
}
modelo('groq', 18801, ['qwen/qwen3.8-27b']); modelo('nvidia', 18802, ['minimaxai/minimax-m3.1-flash', 'meta/muse-glimmer-30b', 'nvidia/nemotron-3-ultra-550b-a55b', 'z-ai/glm-5.3']); modelo('hf-local', 18803, []);
// Router MVP falso: /mcp, /plugins/*, /almacen, /chat/send
http.createServer(async (req, res) => {
  const b = req.method === 'POST' ? await leer(req) : {}, clave = req.headers['x-api-key'];
  log({ srv: 'router', url: req.url, clave_ok: clave === 'router-key-test', metodo_rpc: b.method, tool: b.params?.name, accion: b.params?.arguments?.accion });
  res.setHeader('content-type', 'application/json');
  if (clave !== 'router-key-test') { res.statusCode = 401; return res.end('{}'); }
  if (req.url === '/mcp') {
    if (b.method === 'tools/list') return res.end(JSON.stringify({ jsonrpc: '2.0', id: b.id, result: { tools: ['chat', 'almacen', 'memoria', 'salud', 'yaiwes_md', 'pendientes', 'loop', 'archivos'].map((name) => ({ name })) } }));
    const n = b.params?.name, sc = n === 'yaiwes_md' ? { texto: 'yaiwes.md del proyecto (falso)', encendido: true } : n === 'pendientes' ? { pendientes: [{ texto: 'pendiente A', hecho: false }] } : { status: 'ok', tool: n };
    return res.end(JSON.stringify({ jsonrpc: '2.0', id: b.id, result: { content: [{ type: 'text', text: JSON.stringify(sc) }], structuredContent: sc, isError: false } }));
  }
  if (req.url.startsWith('/plugins/')) { const a = req.url.split('/').pop(); return res.end(JSON.stringify({ status: 'ok', result: a === 'sandbox' ? { sandbox: '', encendido: false } : a === 'archivos' ? { archivos: ['nota.txt'], persistente: true } : { accion: a, ok: true } })); }
  res.end(JSON.stringify({ ok: true }));
}).listen(18804, '127.0.0.1');
// Harness falso
http.createServer(async (req, res) => { const b = await leer(req); log({ srv: 'harness', url: req.url, action: b.action, ok: req.headers['x-api-key'] === 'router-key-test' }); res.setHeader('content-type', 'application/json');
  res.end(JSON.stringify({ status: 'ok', result: { swe: { agentes: { 'swe-agent': { disponible: true, estado: 'DISPONIBLE' } }, workflows: { individual: { disponible: true }, swe_code: { disponible: true }, liquid_mirror: { disponible: false, motivo: 'falta SWECODE_URL_S2' } }, modelos: { 'hf/lfm2.5-350m': { disponible: true } } } } })); }).listen(18805, '127.0.0.1');
const env = { PATH: process.env.PATH, HOME: B, BRIDGE_PORT: '7870', BRIDGE_STATE_DIR: B + '/state', BRIDGE_AUTOACTUALIZAR: '0', BRIDGE_TOKEN: 'bridge-token-test', RIU_API_KEY: 'router-key-test',
  RIU_ROUTER_URL: 'http://127.0.0.1:18804', RIU_DEEPSEEK_HARNESS_URL: 'http://127.0.0.1:18805', GROQ_API_KEY: 'FALSA-groq-0000000001', NVIDIA_API_KEY: 'FALSA-nvidia-000000001',
  SWECODE_URL_S1: 'http://127.0.0.1:18803/v1', TEST_GROQ_URL: 'http://127.0.0.1:18801/v1', TEST_NVIDIA_URL: 'http://127.0.0.1:18802/v1', BRIDGE_BANCO_DESACTIVADO: '1', RIU_CONSTITUCION_PATH: REPO + '/chat-router/plugins/puente_chat/constitucion/CONSTITUCION-YAIWES.json' };
const p = spawn(process.execPath, ['--import', './preload.mjs', 'src/server.js'], { cwd: B + '/app', env, stdio: 'inherit' });
p.on('exit', (c) => { console.log('bridge salio', c); process.exit(1); });
