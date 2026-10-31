// responses.js — POST /v1/responses MINIMO para Codex: traduce la peticion de la API Responses a /v1/chat/completions del propio bridge
// (loopback: misma puerta de acceso, mismos modelos autorizados, externo/local/respaldo y plazos) y devuelve la salida en formato Responses (JSON o SSE).
// Limites honestos: no hay streaming real (se pide la respuesta completa y se emite en trozos), ni herramientas alojadas (web_search, etc.: se ignoran), ni reasoning.
import crypto from 'node:crypto';

const id = (p) => `${p}_${crypto.randomBytes(12).toString('hex')}`;
const invalido = (code, message) => Object.assign(new Error(message), { http: 400, code });
const texto = (c) => (typeof c === 'string' ? c : Array.isArray(c) ? c.map((p) => (typeof p === 'string' ? p : p && typeof p.text === 'string' ? p.text : '')).filter(Boolean).join('\n') : '');
const ROL = { developer: 'system', system: 'system', user: 'user', assistant: 'assistant' };

// cuerpo de Responses -> cuerpo de chat/completions (siempre sin stream)
export function aChat(b) {
  if (!b || typeof b !== 'object' || Array.isArray(b)) throw invalido('INPUT_INVALIDO', 'el cuerpo debe ser un objeto');
  const mensajes = [];
  if (typeof b.instructions === 'string' && b.instructions.trim()) mensajes.push({ role: 'system', content: b.instructions });
  if (typeof b.input === 'string') { if (!b.input.trim()) throw invalido('INPUT_INVALIDO', 'input vacio'); mensajes.push({ role: 'user', content: b.input }); }
  else if (Array.isArray(b.input) && b.input.length) {
    for (const it of b.input) {
      if (typeof it === 'string') { mensajes.push({ role: 'user', content: it }); continue; }
      if (!it || typeof it !== 'object') continue;
      if (it.type === 'function_call') {
        const tc = { id: String(it.call_id || it.id || id('call')), type: 'function', function: { name: String(it.name || ''), arguments: typeof it.arguments === 'string' ? it.arguments : JSON.stringify(it.arguments ?? {}) } };
        const prev = mensajes.at(-1);
        if (prev && prev.role === 'assistant' && prev.tool_calls && !prev.content) prev.tool_calls.push(tc); else mensajes.push({ role: 'assistant', content: '', tool_calls: [tc] });
      } else if (it.type === 'function_call_output') {
        mensajes.push({ role: 'tool', tool_call_id: String(it.call_id || ''), content: typeof it.output === 'string' ? it.output : JSON.stringify(it.output ?? '') });
      } else if ((it.type === undefined || it.type === 'message') && ROL[it.role]) {
        mensajes.push({ role: ROL[it.role], content: texto(it.content) });
      }  // reasoning y demas tipos: se ignoran
    }
  } else throw invalido('INPUT_INVALIDO', 'input debe ser un texto o una lista de items');
  if (!mensajes.some((m) => m.role !== 'system')) throw invalido('INPUT_INVALIDO', 'input sin mensajes utilizables');
  const chat = { model: b.model, messages: mensajes };
  if (Array.isArray(b.tools)) {
    const tools = b.tools.filter((t) => t && t.type === 'function' && typeof t.name === 'string').map((t) => ({ type: 'function', function: { name: t.name, ...(t.description ? { description: t.description } : {}), ...(t.parameters ? { parameters: t.parameters } : {}) } }));
    if (tools.length) {
      chat.tools = tools;
      const tc = b.tool_choice;
      if (typeof tc === 'string') chat.tool_choice = tc; else if (tc && tc.type === 'function' && tc.name) chat.tool_choice = { type: 'function', function: { name: tc.name } };
    }
  }
  for (const k of ['modo', 'conv_id', 'proyecto', 'tarea_id']) if (b[k] !== undefined) chat[k] = b[k];
  return chat;
}

const USO = { input_tokens: 0, output_tokens: 0, total_tokens: 0, input_tokens_details: { cached_tokens: 0 }, output_tokens_details: { reasoning_tokens: 0 } };
// respuesta de chat/completions -> objeto Response (con ids ya fijados para poder emitir los mismos en SSE)
export function aResponses(chat, model) {
  const ch = chat && chat.choices && chat.choices[0] || {}, msg = ch.message || {}, out = [];
  const t = typeof msg.content === 'string' ? msg.content : '';
  if (t) out.push({ id: id('msg'), type: 'message', status: 'completed', role: 'assistant', content: [{ type: 'output_text', text: t, annotations: [] }] });
  for (const tc of Array.isArray(msg.tool_calls) ? msg.tool_calls : []) out.push({ id: id('fc'), type: 'function_call', status: 'completed', call_id: String(tc.id || id('call')), name: String(tc.function?.name || ''), arguments: String(tc.function?.arguments ?? '{}') });
  const cortada = ch.finish_reason === 'length';
  return { id: id('resp'), object: 'response', created_at: Math.floor(Date.now() / 1000), status: cortada ? 'incomplete' : 'completed', ...(cortada ? { incomplete_details: { reason: 'max_output_tokens' } } : { error: null }), model, output: out, output_text: t, usage: { ...USO }, parallel_tool_calls: true };
}

const trozos = (t, n = 200) => { const a = Array.from(t), r = []; for (let i = 0; i < a.length; i += n) r.push(a.slice(i, i + n).join('')); return r; };
// objeto Response -> lista de eventos SSE de la API Responses
export function aEventos(resp) {
  let n = 0; const ev = [], e = (type, datos) => ev.push({ type, data: { type, sequence_number: n++, ...datos } });
  e('response.created', { response: { ...resp, status: 'in_progress', output: [], output_text: '', usage: null } });
  resp.output.forEach((item, oi) => {
    if (item.type === 'message') {
      const parte = item.content[0], vacia = { type: 'output_text', text: '', annotations: [] };
      e('response.output_item.added', { output_index: oi, item: { ...item, status: 'in_progress', content: [] } });
      e('response.content_part.added', { item_id: item.id, output_index: oi, content_index: 0, part: vacia });
      for (const d of trozos(parte.text)) e('response.output_text.delta', { item_id: item.id, output_index: oi, content_index: 0, delta: d });
      e('response.output_text.done', { item_id: item.id, output_index: oi, content_index: 0, text: parte.text });
      e('response.content_part.done', { item_id: item.id, output_index: oi, content_index: 0, part: parte });
      e('response.output_item.done', { output_index: oi, item });
    } else {
      e('response.output_item.added', { output_index: oi, item: { ...item, status: 'in_progress', arguments: '' } });
      e('response.function_call_arguments.delta', { item_id: item.id, output_index: oi, delta: item.arguments });
      e('response.function_call_arguments.done', { item_id: item.id, output_index: oi, arguments: item.arguments });
      e('response.output_item.done', { output_index: oi, item });
    }
  });
  e(resp.status === 'incomplete' ? 'response.incomplete' : 'response.completed', { response: resp });
  return ev;
}

// app.post('/v1/responses'): pasa por /v1/chat/completions del propio bridge con las mismas credenciales de la peticion
export function montarResponses(app, { puerto = () => process.env.BRIDGE_PORT || 7860, plazoMs = 130000 } = {}) {
  app.post('/v1/responses', async (req, res) => {
    const error = (st, code, message) => res.status(st).json({ error: { code, message } });
    let chat;
    try { chat = aChat(req.body); } catch (e) { return error(e.http || 400, e.code || 'INPUT_INVALIDO', String(e.message).slice(0, 200)); }
    const h = { 'content-type': 'application/json' };
    for (const k of ['x-api-key', 'authorization', 'x-bridge-key']) if (req.headers[k]) h[k] = req.headers[k];
    let r, j;
    try {
      r = await fetch(`http://127.0.0.1:${puerto()}/v1/chat/completions`, { method: 'POST', redirect: 'error', signal: AbortSignal.timeout(plazoMs), headers: h, body: JSON.stringify(chat) });
      j = await r.json().catch(() => null);
    } catch { return error(502, 'RESPONSES_NO_DISPONIBLE', 'no se pudo completar la peticion interna'); }
    if (!r.ok || !j || !j.choices) return res.status(r.ok ? 502 : r.status).json(j && j.error ? { error: j.error } : { error: { code: 'RESPUESTA_INVALIDA', message: 'respuesta interna invalida' } });
    const resp = aResponses(j, req.body.model);
    for (const k of ['x-modelo-usado', 'x-via-respaldo']) if (r.headers.get(k)) res.setHeader(k, r.headers.get(k));
    if (req.body.stream !== true) return res.json(resp);
    res.writeHead(200, { 'content-type': 'text/event-stream; charset=utf-8', 'cache-control': 'no-cache', connection: 'keep-alive' });
    for (const e of aEventos(resp)) res.write(`event: ${e.type}\ndata: ${JSON.stringify(e.data)}\n\n`);
    res.end();
  });
}
