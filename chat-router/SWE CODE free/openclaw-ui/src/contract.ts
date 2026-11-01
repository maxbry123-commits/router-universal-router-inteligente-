// contract.ts — operaciones del plugin, definidas UNA vez (UI nativa, tools del agente y comandos las comparten). Todas hablan con el bridge SWE CODE; ninguna ejecuta nada aqui.
import { Type } from 'typebox';
import { defineFeatureContract } from 'openclaw/plugin-sdk/feature-contract';

const Id = Type.String({ pattern: '^[A-Za-z0-9_-]{1,64}$' });
const Segmento = Type.String({ pattern: '^[A-Za-z0-9_-]{0,64}$' });
// Contrato TareaSWE (agentes/adaptadores/contrato.py): 15 campos exactos; `aprobacion` solo puede ser false desde aqui.
export const Tarea = Type.Object({
  task_id: Id, origen: Type.Literal('openclaw'), mensaje: Type.String({ minLength: 1, maxLength: 200000 }), workflow: Type.String({ maxLength: 40 }),
  modelo_responde: Type.String({ maxLength: 80 }), modelo_lector: Type.String({ maxLength: 80 }), modelo_tool: Type.String({ maxLength: 80 }), modelo_revisor: Type.String({ maxLength: 80 }),
  agente_responde: Type.String({ maxLength: 40 }), agente_tool: Type.String({ maxLength: 40 }), agente_verificador: Type.String({ maxLength: 40 }),
  modo_agentico: Type.Boolean(), aprobacion: Type.Literal(false), sesion: Segmento, proyecto: Segmento,
}, { additionalProperties: false });
const Referencia = Type.Object({ task_id: Id, sesion: Type.Optional(Segmento), proyecto: Type.Optional(Segmento) }, { additionalProperties: false });
// Respuesta uniforme: ok + http + codigo estable (sin URL ni claves) + datos (el `resultado` del bridge).
export const Resultado = Type.Object({ ok: Type.Boolean(), http: Type.Integer(), codigo: Type.Optional(Type.String({ maxLength: 64 })), datos: Type.Optional(Type.Any()) }, { additionalProperties: false });

// Una tool de agente por funcion del chat Yaiwes (espejo de emergencia). Todas llaman a POST /v1/swe/tools/{id} del bridge, que reenvia al Router con la clave del ENTORNO del bridge;
// el chat Yaiwes no se toca. Sin operador humano solo funcionan las acciones sin efectos: lo demas lo rechaza el bridge (OPERADOR_REQUERIDO) y se hace desde la UI nativa (operacion `tool`).
export const FUNCIONES_YAIWES = {
  yaiwes_archivos: { id: 'motor_archivos', kind: 'action', label: 'Motor de archivos Yaiwes' },
  yaiwes_loop: { id: 'loop', kind: 'action', label: 'LOOP gobernado Yaiwes' },
  yaiwes_cola: { id: 'cola', kind: 'action', label: 'Cola CIT-50 Yaiwes' },
  yaiwes_watchdog: { id: 'watchdog', kind: 'action', label: 'Watchdog Yaiwes' },
  yaiwes_almacen: { id: 'almacen', kind: 'action', label: 'Almacen Yaiwes' },
  yaiwes_memoria: { id: 'memoria', kind: 'action', label: 'Memoria Yaiwes' },
  yaiwes_chat: { id: 'chat_send', kind: 'action', label: 'Chat del Router (/chat/send)' },
  yaiwes_anclaje: { id: 'anclaje', kind: 'query', label: 'Anclaje Yaiwes (lectura)' },
  yaiwes_constitucion: { id: 'constitucion', kind: 'query', label: 'Constitucion Yaiwes (lectura)' },
  yaiwes_contexto: { id: 'contexto', kind: 'query', label: 'Contexto fijo Yaiwes (lectura)' },
  yaiwes_workflows: { id: 'workflows', kind: 'query', label: 'Workflows SWE (lectura)' },
} as const;
const EntradaFuncion = Type.Object({ accion: Type.Optional(Type.String({ maxLength: 40 })), args: Type.Optional(Type.Record(Type.String(), Type.Any())) }, { additionalProperties: false });
const funcion = <K extends keyof typeof FUNCIONES_YAIWES>(nombre: K, descripcion: string) => ({
  kind: FUNCIONES_YAIWES[nombre].kind, description: `${descripcion} (POST /v1/swe/tools/${FUNCIONES_YAIWES[nombre].id}; las acciones con efectos exigen un operador humano).`,
  input: EntradaFuncion, output: Resultado, tool: { name: nombre as string, label: FUNCIONES_YAIWES[nombre].label },
});

export const contract = defineFeatureContract({
  pluginId: 'swe-selector',
  operations: {
    capacidades: {
      kind: 'query', description: 'Disponibilidad real de agentes, workflows y modelos que reporta el Harness (GET /v1/swe/capacidades).',
      input: Type.Object({}, { additionalProperties: false }), output: Resultado, tool: { name: 'swe_capacidades', label: 'Capacidades SWE' },
    },
    tools: {
      kind: 'query', description: 'Catalogo de tools del Router Yaiwes (motores de descarga/extraccion, Loop, cola, watchdog, almacen, memoria, chat, GitHub...) con su estado real y los GAP (GET /v1/swe/tools).',
      input: Type.Object({}, { additionalProperties: false }), output: Resultado, tool: { name: 'swe_tools_catalogo', label: 'Catalogo de tools Yaiwes' },
    },
    iniciar: { kind: 'action', description: 'Crea una tarea SWE con el contrato TareaSWE (POST /v1/swe/iniciar).', input: Tarea, output: Resultado },
    avanzar: { kind: 'action', description: 'Avanza la tarea SWE (POST /v1/swe/avanzar). Repetir hasta DONE, GAP, REQUIERE_APROBACION o RECONCILIAR.', input: Referencia, output: Resultado },
    estado: { kind: 'query', description: 'Estado de una tarea SWE (POST /v1/swe/estado, solo lectura).', input: Referencia, output: Resultado, tool: { name: 'swe_estado', label: 'Estado de tarea SWE' } },
    reanudar: { kind: 'action', description: 'Reanuda la tarea desde el ultimo checkpoint confirmado (POST /v1/swe/reanudar).', input: Referencia, output: Resultado },
    aprobar: {
      kind: 'action', description: 'Aprueba la operacion pendiente. Exige un operador real: su nombre y SU token individual (se teclean en cada aprobacion y no se guardan).',
      input: Type.Object({ task_id: Id, op_id: Id, sesion: Type.Optional(Segmento), proyecto: Type.Optional(Segmento), operador: Type.String({ minLength: 2, maxLength: 64 }), token_operador: Type.String({ minLength: 1, maxLength: 256 }) }, { additionalProperties: false }),
      output: Resultado,
    },
    tool: {
      kind: 'action', description: 'Llama a una tool del catalogo Yaiwes por el bridge (POST /v1/swe/tools/{id}). Desde el agente solo funcionan las tools sin efectos: lo que tiene efectos exige un operador humano.',
      input: Type.Object({ id: Type.String({ pattern: '^[a-z][a-z0-9_]{1,40}$' }), accion: Type.Optional(Type.String({ maxLength: 40 })), args: Type.Optional(Type.Record(Type.String(), Type.Any())),
        operador: Type.Optional(Type.String({ maxLength: 64 })), token_operador: Type.Optional(Type.String({ maxLength: 256 })) }, { additionalProperties: false }),
      output: Resultado, tool: { name: 'swe_tool_llamar', label: 'Llamar tool Yaiwes' },
    },
    yaiwes_archivos: funcion('yaiwes_archivos', 'Motor de archivos del chat: descargar, extraer, copiar, mover, listar y buscar en cola (acciones: transferir, ejecutar, estado, cancelar, raiz, listar_raiz)'),
    yaiwes_loop: funcion('yaiwes_loop', 'LOOP gobernado C0-C7 del chat (acciones: status, health, estado, motores, agentes, gobernar, paralelo, cancelar...)'),
    yaiwes_cola: funcion('yaiwes_cola', 'Cola CIT-50 del chat (acciones: status, listar, estado, eventos, tarea, crear, orden, aprobar...)'),
    yaiwes_watchdog: funcion('yaiwes_watchdog', 'Watchdog 10 min - 48 h del chat (acciones: status, listar, estado, eventos, heartbeat, crear, tick...)'),
    yaiwes_almacen: funcion('yaiwes_almacen', 'Almacen autorizado del chat (acciones: leer, status, guardar, computar)'),
    yaiwes_memoria: funcion('yaiwes_memoria', 'Memoria del chat en el bucket HF (acciones: load, search, save; args: scope, key, query, k, data)'),
    yaiwes_chat: funcion('yaiwes_chat', 'Motor del chat del Router: Harness + tools + constitucion + anclas + yaiwes.md (campos en args: mensajes, modelo, sesion, anclados, constitucion...)'),
    yaiwes_anclaje: funcion('yaiwes_anclaje', 'Anclaje, solo lectura (acciones: archivos, proyectos, leer_archivo)'),
    yaiwes_constitucion: funcion('yaiwes_constitucion', 'Constitucion, solo lectura (acciones: oficial, archivos, leer_archivo)'),
    yaiwes_contexto: funcion('yaiwes_contexto', 'Contexto fijo del chat, solo lectura: constitucion oficial + yaiwes.md + sandbox + pendientes (accion: fijo)'),
    yaiwes_workflows: funcion('yaiwes_workflows', 'Workflows SWE que reporta el Harness, solo lectura'),
  },
  events: {},
});
