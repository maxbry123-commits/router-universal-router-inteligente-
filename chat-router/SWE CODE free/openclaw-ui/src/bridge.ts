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
// Disponibilidad de MODELOS procede del MISMO bridge/credenciales que realizan la inferencia.
// Los AGENTES y WORKFLOWS permanecen exclusivamente bajo el Harness del otro equipo.
export function fusionarCapacidades(harness: Respuesta, catalogo: Respuesta, banco: Respuesta): Respuesta {
  if (!catalogo.ok && !harness.ok) return harness;
  const base = harness.ok && simple(harness.datos) ? harness.datos : {};
  const modelos: Record<string, unknown> = simple(base.modelos) ? { ...base.modelos } : {};
  const cat = catalogo.ok && simple(catalogo.datos) ? catalogo.datos : {};
  const claves = banco.ok && simple(banco.datos) ? banco.datos : {};
  const externas = Array.isArray(cat.modelos) ? cat.modelos : [];
  for (const dato of externas) {
    if (!simple(dato) || typeof dato.id !== 'string' || !/^(groq|nvidia)\/[a-zA-Z0-9._/-]{1,90}$/.test(dato.id)) continue;
    const proveedor = dato.id.startsWith('groq/') ? 'groq' : 'nvidia';
    const n = claves[proveedor];
    const tieneClave = typeof n === 'number' && Number.isInteger(n) && n > 0;
    const noTieneClave = typeof n === 'number' && n === 0;
    const estado = noTieneClave ? 'NO CONFIGURADO' : tieneClave && dato.disponible === true ? 'DISPONIBLE'
      : tieneClave && dato.disponible === false ? 'NO DISPONIBLE EN PROVEEDOR' : 'SIN VERIFICAR';
    modelos[dato.id] = { disponible: estado === 'DISPONIBLE', estado, intentable: estado === 'DISPONIBLE' || estado === 'SIN VERIFICAR',
      motivo: estado === 'NO CONFIGURADO' ? 'sin clave en el banco cifrado del bridge' : estado === 'SIN VERIFICAR' ? 'no se pudo verificar el proveedor' : '',
      ...(typeof dato.nombre === 'string' ? { nombre: dato.nombre.slice(0, 80) } : {}) };
  }
  const locales = Array.isArray(cat.locales) ? cat.locales : [];
  for (const dato of locales) {
    if (!simple(dato) || typeof dato.id !== 'string' || !/^hf\/[a-zA-Z0-9._-]{1,70}$/.test(dato.id)) continue;
    const configurado = dato.estado !== 'NO CONFIGURADO';
    modelos[dato.id] = { disponible: false, estado: configurado ? 'SIN VERIFICAR' : 'NO CONFIGURADO',
      intentable: configurado, motivo: configurado ? 'servidor local configurado; inferencia pendiente de verificar' : 'ningun servidor HF local configurado en el bridge' };
  }
  return { ok: true, http: harness.ok ? harness.http : catalogo.http, datos: {
    ...base, harness: harness.ok ? (typeof base.harness === 'string' ? base.harness : 'desconocido') : 'no_disponible',
    agentes: simple(base.agentes) ? base.agentes : {}, workflows: simple(base.workflows) ? base.workflows : {}, modelos,
  } };
}

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
    capacidades: async () => {
      // Consultas independientes, paralelas. Una version antigua del bridge sin catalogo
      // sigue permitiendo ver capacidades Harness: no rompe el plugin de OpenClaw.
      const [h, modelos, claves] = await Promise.all([
        llamar('GET', '/v1/swe/capacidades'),
        llamar('GET', '/v1/modelos/disponibilidad'),
        llamar('GET', '/v1/claves'),
      ]);
      return fusionarCapacidades(h, modelos, claves);
    },
    tools: () => llamar('GET', '/v1/swe/tools'),
    // Continuidad entre modelo, chat y sesión; scope del propietario comprobado por el bridge.
    contexto: (id: string) => /^[A-Za-z0-9_-]{1,80}$/.test(id)
      ? llamar('GET', '/v1/contexto/'+id)
      : Promise.resolve({ ok:false, http:400, codigo:'CONTEXTO_ID_INVALIDO' } as Respuesta),
    contextoTransferir: (origen: string, destino: string) =>
      /^[A-Za-z0-9_-]{1,80}$/.test(origen) && /^[A-Za-z0-9_-]{1,80}$/.test(destino)
      ? llamar('POST','/v1/contexto/transferir',{origen,destino})
      : Promise.resolve({ok:false,http:400,codigo:'CONTEXTO_ID_INVALIDO'} as Respuesta),
    // OpenAI API independiente: solo el operador del Gateway habilita RIU_OPENAI_AGENTE_ON.
    claudeEstado: () => llamar('GET','/v1/claude/estado'),
    openaiEstado: () => llamar('GET','/v1/openai/estado'),
    openaiTrabajos: () => llamar('GET','/v1/openai/trabajos'),
    openaiResearch: (prompt: string) => llamar('POST','/v1/openai/research',{prompt}),
    openaiResearchEstado: (id: string) => /^[0-9a-f]{32}$/.test(id)
      ? llamar('GET','/v1/openai/research/'+id)
      : Promise.resolve({ok:false,http:400,codigo:'INVESTIGACION_ID_INVALIDO'} as Respuesta),
    openaiImagen: (prompt: string) => llamar('POST','/v1/openai/image',{prompt},undefined,true),
    openaiImagenData: (id: string) => /^[0-9a-f]{32}$/.test(id)
      ? llamar('GET','/v1/openai/image/'+id+'/data')
      : Promise.resolve({ok:false,http:400,codigo:'IMAGEN_ID_INVALIDO'} as Respuesta),
    agentesLock: (locked?: boolean): Promise<Respuesta> => llamar('POST', '/v1/swe/agentes-lock', locked === undefined ? {} : { locked }),
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
