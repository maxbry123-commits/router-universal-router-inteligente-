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
  setup(api) {
    const cliente = (): Cliente | Respuesta => {  // se resuelve en cada llamada: la variable de entorno puede definirse despues de cargar el plugin
      const c = leerConfig(api.pluginConfig);
      return 'error' in c ? sinConfig(c.error) : crearCliente(c);
    };
    const con = async (f: (c: Cliente) => Promise<Respuesta>): Promise<Respuesta> => { const c = cliente(); return 'ok' in c ? c : f(c); };
    return {
      capacidades: () => con((c) => c.capacidades()),
      tools: () => con((c) => c.tools()),
      iniciar: (tarea) => con((c) => c.iniciar(tarea)),
      avanzar: (r) => con((c) => c.avanzar(r)),
      estado: (r) => con((c) => c.estado(r)),
      reanudar: (r) => con((c) => c.reanudar(r)),
      aprobar: (i, ctx) => con((c) => c.aprobar(i, { operador: i.operador, token_operador: ctx.source === 'session-action' ? i.token_operador : '' })),
      tool: (i, ctx) => con((c) => c.tool(i.id, { accion: i.accion, args: i.args }, operadorDe(ctx.source, i))),
    };
  },
});
