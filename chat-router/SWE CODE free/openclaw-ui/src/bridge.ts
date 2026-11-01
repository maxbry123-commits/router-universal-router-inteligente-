// bridge.ts — cliente del bridge SWE CODE (backend de OpenClaw): /v1/swe/{iniciar,avanzar,estado,aprobar,reanudar,capacidades,tools}. Corre en el BACKEND del plugin (Gateway), nunca en el navegador:
// la clave de acceso (RIU_API_KEY; BRIDGE_TOKEN solo como respaldo) sale del ENTORNO del Gateway y no llega al navegador, a los logs ni a las respuestas. No hay otro backend: todo lo ejecuta el Harness DeepSeek y sus adaptadores.
declare const process: { env: Record<string, string | undefined> };

export const URL_DEFECTO = 'http://127.0.0.1:7870';
export const ENV_TOKEN_DEFECTO = 'RIU_API_KEY';  // clave de acceso: el bridge la acepta por Authorization: Bearer
export const ENV_TOKEN_RESPALDO = 'BRIDGE_TOKEN';  // opcional en el bridge; solo si no hay RIU_API_KEY
export type Respuesta = { ok: boolean; http: number; codigo?: string; datos?: unknown };
export type Operador = { operador: string; token_operador: string };
type Fetch = (url: string, init: Record<string, unknown>) => Promise<{ ok: boolean; status: number; json: () => Promise<unknown> }>;

const simple = (o: unknown): o is Record<string, unknown> => !!o && typeof o === 'object' && !Array.isArray(o);
const SEGMENTO = /^[A-Za-z0-9_-]{1,64}$/, OPERADOR = /^[A-Za-z0-9_.@-]{2,64}$/;

export function urlValida(u: string): boolean {
  try { const x = new URL(u); return (x.protocol === 'https:' && !!x.hostname && !x.username) || (x.protocol === 'http:' && ['127.0.0.1', 'localhost'].includes(x.hostname) && !x.username); }
  catch { return false; }
}
// Configuracion SOLO por entorno del Gateway (el manifiesto no declara config: `plugins build` regenera configSchema desde defineFeaturePlugin, que no admite config propia):
// RIU_SWE_BRIDGE_URL (defecto http://127.0.0.1:7870, la misma variable que usa el Harness) y RIU_API_KEY (o, en su defecto, BRIDGE_TOKEN). El valor del token nunca va en ningun archivo.
export function leerConfig(env: Record<string, string | undefined> = process.env): { url: string; token: string } | { error: string } {
  const url = (env.RIU_SWE_BRIDGE_URL ?? '').trim().replace(/\/+$/, '') || URL_DEFECTO;
  if (!urlValida(url)) return { error: 'BRIDGE_URL_INVALIDA' };
  const token = (env[ENV_TOKEN_DEFECTO] ?? '').trim() || (env[ENV_TOKEN_RESPALDO] ?? '').trim();
  return token ? { url, token } : { error: 'BRIDGE_TOKEN_NO_CONFIGURADO' };
}

export function crearCliente(cfg: { url: string; token: string }, opciones: { fetchFn?: Fetch; timeoutMs?: number; timeoutLargoMs?: number } = {}) {
  const fetchFn: Fetch = opciones.fetchFn ?? ((u, i) => fetch(u, i as RequestInit) as unknown as ReturnType<Fetch>);
  async function llamar(metodo: 'GET' | 'POST', ruta: string, cuerpo?: unknown, operador?: Operador, largo = false): Promise<Respuesta> {
    const ctl = new AbortController(), ms = largo ? (opciones.timeoutLargoMs ?? 1_800_000) : (opciones.timeoutMs ?? 60_000), t = setTimeout(() => ctl.abort(), ms);
    const cab: Record<string, string> = { authorization: `Bearer ${cfg.token}` };
    if (metodo === 'POST') cab['content-type'] = 'application/json';
    if (operador) { cab['x-operador'] = operador.operador; cab['x-operator-token'] = operador.token_operador; }
    try {
      const r = await fetchFn(cfg.url + ruta, { method: metodo, headers: cab, body: metodo === 'POST' ? JSON.stringify(cuerpo ?? {}) : undefined, signal: ctl.signal, redirect: 'error' });
      let j: unknown = null;
      try { j = await r.json(); } catch { /* cuerpo no JSON */ }
      if (r.ok && simple(j) && j.ok === true) return { ok: true, http: r.status, datos: 'resultado' in j ? j.resultado : j };
      if (r.ok && simple(j) && 'harness' in j) return { ok: true, http: r.status, datos: j };  // GET /capacidades devuelve el informe directo
      const e = simple(j) && simple(j.error) ? j.error : {};
      return { ok: false, http: r.status, codigo: typeof e.code === 'string' && /^[A-Z][A-Z0-9_]{2,63}$/.test(e.code) ? e.code : `BRIDGE_HTTP_${r.status}`,
        ...(typeof e.codigo_harness === 'string' ? { datos: { codigo_harness: e.codigo_harness } } : {}) };
    } catch (e) {
      const nombre = e instanceof Error ? e.name : '';
      return { ok: false, http: 0, codigo: nombre === 'AbortError' || nombre === 'TimeoutError' ? 'BRIDGE_TIMEOUT' : 'BRIDGE_NO_DISPONIBLE' };  // sin URL ni token en el mensaje
    } finally { clearTimeout(t); }
  }
  const ref = (r: { task_id: string; sesion?: string; proyecto?: string }) => ({ task_id: r.task_id, origen: 'openclaw', ...(r.sesion ? { sesion: r.sesion } : {}), ...(r.proyecto ? { proyecto: r.proyecto } : {}) });
  return {
    capacidades: () => llamar('GET', '/v1/swe/capacidades'),
    tools: () => llamar('GET', '/v1/swe/tools'),
    iniciar: (tarea: Record<string, unknown>) => llamar('POST', '/v1/swe/iniciar', tarea),
    avanzar: (r: { task_id: string; sesion?: string; proyecto?: string }) => llamar('POST', '/v1/swe/avanzar', ref(r), undefined, true),
    estado: (r: { task_id: string; sesion?: string; proyecto?: string }) => llamar('POST', '/v1/swe/estado', ref(r)),
    reanudar: (r: { task_id: string; sesion?: string; proyecto?: string }) => llamar('POST', '/v1/swe/reanudar', ref(r), undefined, true),
    aprobar: (r: { task_id: string; op_id: string; sesion?: string; proyecto?: string }, op: Operador): Promise<Respuesta> =>
      OPERADOR.test(op.operador) && op.token_operador ? llamar('POST', '/v1/swe/aprobar', { ...ref(r), op_id: r.op_id }, op) : Promise.resolve({ ok: false, http: 400, codigo: 'OPERADOR_REQUERIDO' }),
    tool: (id: string, cuerpo: { accion?: string; args?: Record<string, unknown> }, op?: Operador) =>
      /^[a-z][a-z0-9_]{1,40}$/.test(id) ? llamar('POST', `/v1/swe/tools/${id}`, cuerpo, op) : Promise.resolve({ ok: false, http: 404, codigo: 'TOOL_DESCONOCIDA' } as Respuesta),
  };
}
export const esSegmento = (s: string) => SEGMENTO.test(s);
