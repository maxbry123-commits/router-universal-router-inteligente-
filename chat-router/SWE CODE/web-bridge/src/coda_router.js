// CODA largo: mismo Router MVP/Harness para YAIWES y el provider OpenClaw.
// No instala otra puerta ni otro servidor. La peticion de 500 lineas queda
// en chat_async del Router y se consulta por resultado con el mismo PID.
// El proveedor hace una llamada por segmento y el estado persiste en HF.
import crypto from 'node:crypto';

const PYTHON = /\bpython\b|\.py\b/i;
const CODIGO = /\b(?:c[oó]digo|code|programa|script)\b/i;
const CUENTA = /\b(\d{2,4})\s+l[ií]neas?\b/i;
const PAUSA = (ms) => new Promise(ok => setTimeout(ok, ms));

export function detectarCodigoLargo(modelo, mensajes, tools) {
  if (!/^(groq|nvidia)\/[A-Za-z0-9._/-]+$/.test(String(modelo))) return null;
  if (tools === true || (Array.isArray(tools) && tools.length)) return null;
  const u = [...(Array.isArray(mensajes) ? mensajes : [])].reverse()
    .find(m => m && m.role === 'user');
  const txt = String(u?.content || '');
  const n = CUENTA.exec(txt);
  if (!n || !CODIGO.test(txt) || !PYTHON.test(txt)) return null;
  const lineas = Number(n[1]);
  return lineas >= 100 && lineas <= 2000 ? lineas : null;
}

const routerBase = (env) => {
  const puerto = String(env.PORT || '7861');
  return /^\d{2,5}$/.test(puerto) && +puerto < 65536
    ? 'http://127.0.0.1:' + puerto : null;
};

async function llamadaRouter(base, key, accion, body, fetchFn, signal) {
  const r = await fetchFn(base + '/plugins/puente_chat/call/' + accion, {
    method: 'POST', headers: {'content-type':'application/json','x-api-key':key},
    body: JSON.stringify(body), redirect: 'error',
    signal: AbortSignal.any([signal, AbortSignal.timeout(14000)])
  });
  if (!r.ok) throw new Error('CODA_ROUTER_HTTP_' + r.status);
  const j = await r.json();
  if (j?.status !== 'ok' || !j.result) throw new Error('CODA_ROUTER_RESPUESTA_INVALIDA');
  return j.result;
}

export async function servirCodaRouter(req, res, sse, {modelo, mensajes, sesion, propietario,
  fetchFn = fetch, env = process.env, dormir = PAUSA} = {}) {
  const lineas = detectarCodigoLargo(modelo, mensajes, req.body?.tools);
  if (!lineas) return false;
  const key = String(env.RIU_API_KEY || env.RIU_PUBLIC_CHAT_KEY || '').trim();
  const base = routerBase(env);
  if (!key || !base) {
    res.status(503).json({error:{code:'CODA_ROUTER_NO_CONFIGURADO'}});
    return true;
  }
  const conv = /^[A-Za-z0-9_-]{1,60}$/.test(String(sesion||'')) ? String(sesion) : 'coda-openclaw';
  const request_id = 'coda-' + crypto.createHash('sha256').update(JSON.stringify([
    modelo, mensajes, propietario || '', conv
  ])).digest('hex').slice(0, 43);
  const mensaje = [...mensajes].reverse().find(m=>m && m.role === 'user')?.content || '';
  let pid = null;
  try {
    const job = await llamadaRouter(base, key, 'chat_async', {
      modelo, messages: mensajes, message: String(mensaje),
      sesion: conv, request_id, task_type:'code_largo', modo:'loop',
      duracion_horas:4, tools:false, agente_tool:false, llm_tool:false,
    }, fetchFn, AbortSignal.timeout(14000));
    pid = String(job.proceso_id || '');
    if (!/^p-[A-Za-z0-9_-]{1,80}$/.test(pid)) throw new Error('CODA_PID_INVALIDO');
  } catch (error) {
    res.status(502).json({error:{code:String(error.message||'CODA_BACKEND_FALLO').slice(0,90)}});
    return true;
  }
  if (!res.headersSent) res.setHeader('x-coda-proceso-id', pid);
  const hasta = Date.now() + (req.body?.stream === true ? 4*3600*1000+90000 : 90000);
  if (req.body?.stream === true) sse.vigilar();
  let estado = 'procesando', ultimo = null;
  try {
    while (estado === 'procesando' && Date.now() < hasta && !sse.signal.aborted) {
      ultimo = await llamadaRouter(base,key,'resultado',{proceso_id:pid,espera:8},
                                  fetchFn,AbortSignal.timeout(14000));
      estado = String(ultimo.estado || 'procesando');
      // SSE comentarios de progreso; no se inventan tokens ni PASS.
      if (sse.pide && ultimo.progreso && !res.writableEnded) {
        sse.abrir();
        res.write(': ' + String(ultimo.progreso).replace(/[\r\n]/g,' ').slice(0,160) + '\n\n');
      }
      if (estado === 'procesando') await dormir(500);
    }
    if (sse.signal.aborted) return true; // trabajo sigue en Router/HF
    if (estado !== 'completado' || !ultimo?.choices?.[0]?.message?.content) {
      const code = ultimo?.error ? 'CODA_MODELO_GAP' : 'CODA_PENDIENTE';
      if (sse.pide) {
        sse.error(code,'Tarea no cerrada; checkpoint recuperable', {proceso_id:pid,estado});
      } else {
        res.status(202).json({estado:'procesando', proceso_id:pid, error:{code}});
      }
      return true;
    }
    const codigo = String(ultimo.choices[0].message.content);
    if (codigo.trimEnd().split('\n').length !== lineas
        || ultimo.metricas?.lineas_verificadas !== lineas) {
      if (sse.pide) sse.error('CODA_EVIDENCIA_INCOMPLETA','La salida no paso validacion');
      else res.status(502).json({error:{code:'CODA_EVIDENCIA_INCOMPLETA'},proceso_id:pid});
      return true;
    }
    if (sse.pide) {
      sse.model = modelo;
      sse.delta(codigo);
      sse.chunk({},'stop');
      res.end('data: [DONE]\n\n');
    } else {
      res.json({id:pid,object:'chat.completion',model:modelo,
        choices:[{index:0,message:{role:'assistant',content:codigo},finish_reason:'stop'}],
        tarea:{proceso_id:pid,lineas_verificadas:lineas}});
    }
    return true;
  } catch (error) {
    if (sse.pide) sse.error('CODA_ROUTER_INTERRUPCION','Tarea conservada en Router', {proceso_id:pid});
    else res.status(502).json({error:{code:'CODA_ROUTER_INTERRUPCION'},proceso_id:pid});
    return true;
  } finally {sse.parar();}
}
