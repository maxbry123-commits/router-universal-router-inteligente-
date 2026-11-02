// index.ts — backend del plugin (corre en el Gateway de OpenClaw). Implementa el contrato llamando al bridge SWE CODE; la clave del bridge sale del entorno del Gateway.
import { defineFeaturePlugin } from 'openclaw/plugin-sdk/feature-plugin';
import { contract } from './contract.js';
import { crearCliente, leerConfig, type Operador, type Respuesta } from './bridge.js';

type Cliente = ReturnType<typeof crearCliente>;
const sinConfig = (error: string): Respuesta => ({ ok: false, http: 503, codigo: error });
// El agente (tool/comando) NUNCA recibe credenciales de operador: solo la UI nativa (session-action) las pasa, y el bridge rechaza lo que tiene efectos sin operador.
const operadorDe = (source: string, i: { operador?: string; token_operador?: string }): Operador | undefined =>
  source === 'session-action' && i.operador && i.token_operador ? { operador: i.operador, token_operador: i.token_operador } : undefined;

export default defineFeaturePlugin({
  contract,
  name: 'SWE Selector',
  description: 'Selector central SWE (agente/modelo que responde y ejecuta, modo agentico, workflow, salida) y tools del Router Yaiwes para OpenClaw, sobre el bridge SWE CODE.',
  setup() {
    const cliente = (): Cliente | Respuesta => {  // se resuelve en cada llamada: la variable de entorno puede definirse despues de cargar el plugin
      const c = leerConfig();
      return 'error' in c ? sinConfig(c.error) : crearCliente(c);
    };
    const con = async (f: (c: Cliente) => Promise<Respuesta>): Promise<Respuesta> => { const c = cliente(); return 'ok' in c ? c : f(c); };
    const funcion = (id: string, i: { accion?: string; args?: Record<string, unknown> }) => con((c) => c.tool(id, { accion: i.accion, args: i.args }));
    return {
      capacidades: () => con((c) => c.capacidades()),
      tools: () => con((c) => c.tools()),
      // Nunca exponer al modelo la operacion de permisos; el contrato no
      // declara tool. Solo la UI nativa del Gateway puede invocarla.
      agentes_lock: (i) => con((c) => c.agentesLock(i.locked)),
      iniciar: (tarea) => con((c) => c.iniciar(tarea)),
      avanzar: (r) => con((c) => c.avanzar(r)),
      estado: (r) => con((c) => c.estado(r)),
      reanudar: (r) => con((c) => c.reanudar(r)),
      aprobar: (i, ctx) => con((c) => c.aprobar(i, { operador: i.operador, token_operador: ctx.source === 'session-action' ? i.token_operador : '' })),
      tool: (i, ctx) => con((c) => c.tool(i.id, { accion: i.accion, args: i.args }, operadorDe(ctx.source, i))),
      // tools por funcion del chat: nunca llevan credenciales de operador (ni del modelo ni de la sesion); las acciones con efectos las rechaza el bridge
      yaiwes_archivos: (i) => funcion('motor_archivos', i), yaiwes_loop: (i) => funcion('loop', i), yaiwes_cola: (i) => funcion('cola', i), yaiwes_watchdog: (i) => funcion('watchdog', i),
      yaiwes_almacen: (i) => funcion('almacen', i), yaiwes_memoria: (i) => funcion('memoria', i), yaiwes_chat: (i) => funcion('chat_send', i), yaiwes_anclaje: (i) => funcion('anclaje', i),
      yaiwes_constitucion: (i) => funcion('constitucion', i), yaiwes_contexto: (i) => funcion('contexto', i), yaiwes_workflows: (i) => funcion('workflows', i),
    };
  },
});
