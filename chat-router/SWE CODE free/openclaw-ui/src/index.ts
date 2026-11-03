// index.ts — backend del plugin (corre en el Gateway de OpenClaw). Implementa el contrato llamando al bridge SWE CODE; la clave del bridge sale del entorno del Gateway.
import { defineFeaturePlugin } from 'openclaw/plugin-sdk/feature-plugin';
import fs from 'node:fs';
import path from 'node:path';
import { contract } from './contract.js';
import { crearCliente, leerConfig, type Operador, type Respuesta } from './bridge.js';

type Cliente = ReturnType<typeof crearCliente>;
const sinConfig = (error: string): Respuesta => ({ ok: false, http: 503, codigo: error });
const agenteApiHabilitado = (): boolean => process.env.RIU_OPENAI_AGENTE_ON === '1';
// Guardar bytes PNG sólo en workspace del Gateway; jamás aceptar paths desde un modelo.
async function descargarImagen(c: Cliente, id: string): Promise<Respuesta> {
  if (!/^[0-9a-f]{32}$/.test(id)) return {ok:false,http:400,codigo:'IMAGEN_ID_INVALIDO'};
  const respuesta = await c.openaiImagenData(id);
  if (!respuesta.ok) return respuesta;
  const d = respuesta.datos as Record<string,unknown> | undefined;
  if (d?.mime !== 'image/png' || typeof d.base64 !== 'string' || d.base64.length > 12_000_000)
    return {ok:false,http:502,codigo:'IMAGEN_DATOS_INVALIDOS'};
  const home = process.env.OPENCLAW_WORKSPACE_DIR || (process.env.HOME ? path.join(process.env.HOME,'.openclaw','workspace') : '');
  if (!home) return sinConfig('OPENCLAW_WORKSPACE_NO_CONFIGURADO');
  const img=Buffer.from(d.base64,'base64');
  if (img.length < 100 || img.length > 8_000_000 || !img.subarray(0,8).equals(Buffer.from([137,80,78,71,13,10,26,10])))
    return {ok:false,http:502,codigo:'IMAGEN_PNG_INVALIDA'};
  const dir=path.join(home,'swen-artifacts'),dest=path.join(dir,'openai-'+id+'.png'),tmp=dest+'.tmp-'+process.pid;
  try{
    fs.mkdirSync(dir,{recursive:true,mode:0o700});
    fs.writeFileSync(tmp,img,{flag:'wx',mode:0o600});fs.renameSync(tmp,dest);
    return {ok:true,http:200,datos:{ruta:dest,bytes:img.length,mime:'image/png'}};
  }catch{
    return {ok:false,http:503,codigo:'IMAGEN_NO_GUARDADA'};
  }finally{try{fs.unlinkSync(tmp);}catch{}}
}
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
      contexto:(i) => con((c)=>c.contexto(i.id)),
      contexto_transferir:(i) => con((c)=>c.contextoTransferir(i.origen,i.destino)),
      openai_estado:() => con((c)=>c.openaiEstado()),
      openai_research:(i) => agenteApiHabilitado()
        ? con((c)=>c.openaiResearch(i.prompt)) : sinConfig('OPENAI_AGENTE_NO_AUTORIZADO'),
      openai_research_estado:(i) => con((c)=>c.openaiResearchEstado(i.id)),
      openai_imagen:(i) => agenteApiHabilitado()
        ? con((c)=>c.openaiImagen(i.prompt)) : sinConfig('OPENAI_AGENTE_NO_AUTORIZADO'),
      openai_imagen_descargar:(i) => con((c)=>descargarImagen(c,i.id)),
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
