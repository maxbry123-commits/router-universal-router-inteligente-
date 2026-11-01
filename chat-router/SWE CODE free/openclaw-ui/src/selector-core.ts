// selector-core.ts — logica PURA del selector central (sin DOM ni SDK): el mismo contrato de seleccion que YAIWES, en el plugin de OpenClaw.
// Una sola funcion de validacion, una de serializacion y una de disponibilidad. La fuente de agentes, workflows y modelos es el Harness (GET /v1/swe/capacidades del bridge):
// aqui NO hay catalogo propio (instruccion 22); lo que el Harness no reporta no se presenta como funcional.

export const ESTADOS = ['DISPONIBLE', 'NO INSTALADO', 'NO CONFIGURADO', 'NO COMPATIBLE', 'NO DISPONIBLE EN PROVEEDOR', 'SIN VERIFICAR'] as const;
export type Estado = (typeof ESTADOS)[number];
export const SALIDAS = ['swe', 'openclaw'] as const;
export type Salida = (typeof SALIDAS)[number];

export type Entrada = {
  disponible: boolean;
  estado?: string;
  veredicto?: string;
  verificado?: boolean;
  causa?: string;
  intentable?: boolean;
  motivo?: string;
  modelos?: string[];
  nombre?: string;
  proveedor?: string;
  nota?: string;
};
export type Capacidades = {
  harness: string;
  agentes: Record<string, Entrada>;
  workflows: Record<string, Entrada>;
  modelos: Record<string, Entrada>;
};

// Seleccion del selector central: RESPONDE [agente][modelo] · EJECUTA [agente][modelo para tool] · modo agentico · workflow · salida.
export type Seleccion = {
  agente_responde: string;
  modelo_responde: string;
  agente_tool: string;
  modelo_tool: string;
  modo_agentico: boolean;
  workflow: string;
  salida: Salida;
};

// Valores que el workflow fija solo (workflows.py): modelo lector/revisor y agente verificador del contrato.
export const LIQUID = 'hf/lfm2.5-350m';
export const REVISOR = 'hf/qwen3.5-0.8b';
export const VERIFICADOR = 'openhands';
export const SELECCION_DEFECTO: Seleccion = {
  agente_responde: 'openclaw', modelo_responde: LIQUID, agente_tool: 'swe-agent', modelo_tool: 'hf/qwen2.5-coder-1.5b',
  modo_agentico: false, workflow: 'individual', salida: 'swe',
};
export const ETIQUETAS_WORKFLOW: Record<string, string> = { individual: 'Individual', swe_code: 'SWE CODE cuatro pasos', liquid_mirror: 'Liquid Mirror' };
export const ETIQUETAS_SALIDA: Record<Salida, string> = { swe: 'SWE-agent', openclaw: 'OpenClaw' };

const simple = (o: unknown): o is Record<string, unknown> => !!o && typeof o === 'object' && !Array.isArray(o);
const grupo = (g: unknown): Record<string, Entrada> => {
  const salida: Record<string, Entrada> = {};
  if (!simple(g)) return salida;
  for (const [k, v] of Object.entries(g)) if (simple(v) && typeof v.disponible === 'boolean') salida[k] = v as unknown as Entrada;
  return salida;
};
export function normalizarCapacidades(p: unknown): Capacidades {
  const o = simple(p) ? p : {};
  return { harness: typeof o.harness === 'string' ? o.harness : 'desconocido', agentes: grupo(o.agentes), workflows: grupo(o.workflows), modelos: grupo(o.modelos) };
}

export type Veredicto = { ok: boolean; estado: Estado; motivo: string };
const estadoDe = (e: Entrada): Estado => (ESTADOS as readonly string[]).includes(e.estado ?? '') ? (e.estado as Estado) : e.disponible ? 'DISPONIBLE' : 'NO INSTALADO';
// Estado de una opcion segun lo que el Harness DICE. Un agente o workflow sin entrada `disponible:true` no es ejecutable (el adaptador existente no prueba que este instalado);
// un modelo sin entrada se deja elegir (no se sabe), uno SIN VERIFICAR se intenta y se muestra su estado real; GLM-5.3 u otro no disponible queda bloqueado.
export function estadoOpcion(cap: Capacidades, tipo: 'agente' | 'workflow' | 'modelo', id: string, modelo?: string): Veredicto {
  const tabla = tipo === 'agente' ? cap.agentes : tipo === 'workflow' ? cap.workflows : cap.modelos;
  const e = Object.hasOwn(tabla, id) ? tabla[id] : undefined;
  if (tipo === 'workflow' && id === 'individual') return { ok: true, estado: 'DISPONIBLE', motivo: '' };
  const motivo = e && typeof e.motivo === 'string' ? e.motivo : '';
  if (tipo === 'modelo') {
    if (!e) return { ok: true, estado: 'SIN VERIFICAR', motivo: 'el Harness no lo reporta' };
    const est = estadoDe(e);
    if (e.disponible) return { ok: true, estado: 'DISPONIBLE', motivo };
    return est === 'SIN VERIFICAR' && e.intentable === true ? { ok: true, estado: est, motivo } : { ok: false, estado: est, motivo: motivo || est };
  }
  if (!e) return { ok: false, estado: 'SIN VERIFICAR', motivo: 'el Harness no lo reporta conectado' };
  const est = estadoDe(e);
  if (!e.disponible) return { ok: false, estado: est, motivo: motivo || est };
  if (tipo === 'agente' && modelo && Array.isArray(e.modelos) && !e.modelos.includes(modelo)) return { ok: false, estado: 'NO COMPATIBLE', motivo: `incompatible con ${modelo}` };
  return { ok: true, estado: 'DISPONIBLE', motivo };
}

export const requiereHarness = (s: Seleccion): boolean => s.workflow !== 'individual' || s.modo_agentico;
// Controles que el workflow fija solo (no se piden ni se validan): SWE CODE y Liquid Mirror usan modelos fijos por paso.
export const camposFijos = (workflow: string): ReadonlySet<keyof Seleccion> =>
  new Set<keyof Seleccion>(workflow === 'swe_code' || workflow === 'liquid_mirror' ? ['modelo_responde', 'agente_responde', 'modelo_tool'] : []);

// UNA sola funcion de validacion. Con modo agentico OFF y workflow Individual no hace falta Harness (conversacion normal con el modelo).
export function validarSeleccion(sel: Seleccion, cap: Capacidades): { ok: boolean; problemas: string[] } {
  if (!requiereHarness(sel)) return { ok: true, problemas: [] };
  const problemas: string[] = [];
  const mal = (etq: string, v: Veredicto) => { if (!v.ok) problemas.push(`${etq}: ${v.estado}${v.motivo && v.motivo !== v.estado ? ' - ' + v.motivo : ''}`); };
  if (cap.harness !== 'ok') problemas.push(`HARNESS: ${cap.harness} (no se puede comprobar la disponibilidad)`);
  if (sel.workflow === 'swe_code' && !sel.modo_agentico) problemas.push('WORKFLOW SWE CODE cuatro pasos exige MODO AGENTICO ON');
  mal(`WORKFLOW ${sel.workflow}`, estadoOpcion(cap, 'workflow', sel.workflow));
  if (!camposFijos(sel.workflow).has('modelo_responde')) mal(`MODELO QUE RESPONDE ${sel.modelo_responde}`, estadoOpcion(cap, 'modelo', sel.modelo_responde));
  if (sel.modo_agentico) {
    const tool = sel.workflow === 'liquid_mirror' ? LIQUID : sel.modelo_tool;
    mal(`MODELO PARA TOOL ${tool}`, estadoOpcion(cap, 'modelo', tool));
    mal(`AGENTE QUE EJECUTA ${sel.agente_tool}`, estadoOpcion(cap, 'agente', sel.agente_tool, tool));
    if (sel.workflow !== 'individual') mal(`AGENTE VERIFICADOR ${VERIFICADOR}`, estadoOpcion(cap, 'agente', VERIFICADOR, LIQUID));
  }
  return { ok: problemas.length === 0, problemas };
}

// Cambios de la seleccion SIN efectos cruzados (instrucciones 58, 62, 63, 197, 198): cada campo solo cambia el suyo.
export function aplicar(sel: Seleccion, parcial: Partial<Seleccion>): Seleccion {
  const s = { ...sel };
  for (const k of Object.keys(SELECCION_DEFECTO) as (keyof Seleccion)[]) {
    if (!Object.hasOwn(parcial, k)) continue;
    const v = parcial[k];
    if (k === 'modo_agentico') { if (typeof v === 'boolean') s.modo_agentico = v; }
    else if (k === 'salida') { if (v === 'swe' || v === 'openclaw') s.salida = v; }
    else if (typeof v === 'string' && v) (s as Record<string, unknown>)[k] = v;
  }
  return s;
}

// Contrato TareaSWE (agentes/adaptadores/contrato.py): 15 campos exactos, origen "openclaw", aprobacion SIEMPRE false (solo la da un operador por /aprobar).
export type TareaSWE = {
  task_id: string; origen: 'openclaw'; mensaje: string; workflow: string;
  modelo_responde: string; modelo_lector: string; modelo_tool: string; modelo_revisor: string;
  agente_responde: string; agente_tool: string; agente_verificador: string;
  modo_agentico: boolean; aprobacion: false; sesion: string; proyecto: string;
};
const ident = (v: unknown, defecto: string): string => String(v ?? '').replace(/[^A-Za-z0-9_-]/g, '-').slice(0, 64) || defecto;
export function nuevoTaskId(): string { return `openclaw-${Date.now().toString(36)}${Math.random().toString(36).slice(2, 8)}`; }
export function armarTarea(p: { sel: Seleccion; mensaje: string; sesion?: string; proyecto?: string; task_id?: string }): TareaSWE {
  const lm = p.sel.workflow === 'liquid_mirror';
  return {
    task_id: p.task_id && /^[A-Za-z0-9_-]{1,64}$/.test(p.task_id) ? p.task_id : nuevoTaskId(), origen: 'openclaw', mensaje: p.mensaje, workflow: p.sel.workflow,
    modelo_responde: p.sel.modelo_responde, modelo_lector: LIQUID, modelo_tool: lm ? LIQUID : p.sel.modelo_tool, modelo_revisor: REVISOR,
    agente_responde: p.sel.agente_responde, agente_tool: p.sel.agente_tool, agente_verificador: VERIFICADOR,
    modo_agentico: p.sel.modo_agentico, aprobacion: false, sesion: ident(p.sesion, ''), proyecto: ident(p.proyecto, 'swe-code'),
  };
}
// UNA sola serializacion del contrato de seleccion: la tarea (que viaja a /v1/swe/*) y el destino de los tool_calls (`ejecutor_tools`, contrato externo swe | openclaw).
export function serializarSeleccion(p: Parameters<typeof armarTarea>[0]): { tarea: TareaSWE; ejecutor_tools: Salida } {
  return { tarea: armarTarea(p), ejecutor_tools: p.sel.salida };
}
