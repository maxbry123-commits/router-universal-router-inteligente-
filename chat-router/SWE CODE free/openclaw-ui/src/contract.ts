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
  },
  events: {},
});
