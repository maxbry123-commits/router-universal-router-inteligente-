// Pruebas de la logica del selector central (dist/ compilado por `npm run test`). Sin red, sin claves.
import test from 'node:test';
import assert from 'node:assert/strict';
import { ESTADOS, SELECCION_DEFECTO, aplicar, armarTarea, serializarSeleccion, validarSeleccion, estadoOpcion, normalizarCapacidades, camposFijos, requiereHarness } from '../dist/selector-core.js';

const CAMPOS = ['task_id', 'origen', 'mensaje', 'workflow', 'modelo_responde', 'modelo_lector', 'modelo_tool', 'modelo_revisor', 'agente_responde', 'agente_tool', 'agente_verificador', 'modo_agentico', 'aprobacion', 'sesion', 'proyecto'];
const cap = (extra = {}) => normalizarCapacidades({ harness: 'ok',
  agentes: { openclaw: { disponible: true }, 'swe-agent': { disponible: true }, openhands: { disponible: true }, codex: { disponible: false, estado: 'NO INSTALADO', motivo: 'codex no esta instalado' }, opencode: { disponible: true }, 'claude-code': { disponible: true, modelos: ['nvidia/z-ai/glm-5.3'] } },
  workflows: { individual: { disponible: true }, swe_code: { disponible: true }, liquid_mirror: { disponible: false, estado: 'NO CONFIGURADO', motivo: 'falta SWECODE_URL_S2' } },
  modelos: { 'hf/lfm2.5-350m': { disponible: true }, 'hf/qwen2.5-coder-1.5b': { disponible: true }, 'nvidia/z-ai/glm-5.3': { disponible: false, estado: 'NO DISPONIBLE EN PROVEEDOR', motivo: 'no figura en GET /models' }, 'groq/qwen/qwen3.8-27b': { disponible: false, estado: 'SIN VERIFICAR', intentable: true, motivo: 'GET /models fallo' } }, ...extra });

test('los seis estados de la instruccion 37 estan en el mismo orden que en disponibilidad.py', async () => {
  const fs = await import('node:fs'), path = await import('node:path'), { fileURLToPath } = await import('node:url');
  const py = fs.readFileSync(path.resolve(path.dirname(fileURLToPath(import.meta.url)), '../../../agentes/adaptadores/disponibilidad.py'), 'utf8');
  const reales = [...(/^ESTADOS = \(([^)]*)\)/m.exec(py)[1]).matchAll(/"([^"]+)"/g)].map((m) => m[1]);
  assert.deepEqual([...ESTADOS], reales);
});

test('contrato TareaSWE: 15 campos exactos, origen openclaw, aprobacion siempre false, task_id valido', () => {
  const t = armarTarea({ sel: { ...SELECCION_DEFECTO, modo_agentico: true }, mensaje: 'hola', sesion: 'ses ion/1', proyecto: '' });
  assert.deepEqual(Object.keys(t).sort(), [...CAMPOS].sort());
  assert.equal(t.origen, 'openclaw'); assert.equal(t.aprobacion, false); assert.match(t.task_id, /^[A-Za-z0-9_-]{1,64}$/);
  assert.equal(t.sesion, 'ses-ion-1'); assert.equal(t.proyecto, 'swe-code');
  assert.equal(armarTarea({ sel: SELECCION_DEFECTO, mensaje: 'x', task_id: 'mi-tarea-1' }).task_id, 'mi-tarea-1');
  assert.notEqual(armarTarea({ sel: SELECCION_DEFECTO, mensaje: 'x', task_id: '../mal' }).task_id, '../mal');
});

test('197/198: cambiar la salida no cambia agente_tool; cambiar modelo_tool no cambia modelo_responde; elegir un agente no toca la salida', () => {
  const base = aplicar(SELECCION_DEFECTO, { agente_tool: 'codex', modelo_responde: 'hf/qwen3-0.6b', salida: 'swe' });
  const s1 = aplicar(base, { salida: 'openclaw' });
  assert.equal(s1.agente_tool, 'codex'); assert.equal(s1.salida, 'openclaw');
  const s2 = aplicar(s1, { modelo_tool: 'hf/qwen3.5-0.8b' });
  assert.equal(s2.modelo_responde, 'hf/qwen3-0.6b'); assert.equal(s2.salida, 'openclaw');
  const s3 = aplicar(s2, { agente_tool: 'opencode' });
  assert.equal(s3.salida, 'openclaw', 'elegir Codex/OpenCode no modifica la salida');
  assert.equal(s3.agente_responde, s2.agente_responde, 'agente_responde y agente_tool no se intercambian');
  assert.deepEqual(aplicar(s3, { salida: 'otra', modo_agentico: 'si', workflow: '' }), s3, 'valores invalidos no pisan los anteriores');
});

test('serializacion unica: el contrato viaja sin ejecutor_tools y el destino de tool_calls va aparte (swe | openclaw)', () => {
  const r = serializarSeleccion({ sel: { ...SELECCION_DEFECTO, salida: 'openclaw' }, mensaje: 'x' });
  assert.equal(r.ejecutor_tools, 'openclaw'); assert.ok(!('ejecutor_tools' in r.tarea)); assert.equal(r.tarea.agente_tool, 'swe-agent');
});

test('modo agentico OFF + Individual: conversacion normal, no hace falta Harness; ON exige agente y modelo reales', () => {
  const sin = normalizarCapacidades(null);
  assert.equal(requiereHarness(SELECCION_DEFECTO), false);
  assert.deepEqual(validarSeleccion(SELECCION_DEFECTO, sin), { ok: true, problemas: [] });
  const on = { ...SELECCION_DEFECTO, modo_agentico: true };
  const v = validarSeleccion(on, sin);
  assert.equal(v.ok, false); assert.ok(v.problemas.some((p) => p.startsWith('HARNESS:')));
  assert.equal(validarSeleccion({ ...on, agente_tool: 'swe-agent' }, cap()).ok, true);
});

test('agente no instalado: la eleccion se conserva pero la ejecucion se bloquea con su estado real; no se elige otro en silencio (42, 43)', () => {
  const sel = { ...SELECCION_DEFECTO, modo_agentico: true, agente_tool: 'codex' };
  const v = validarSeleccion(sel, cap());
  assert.equal(v.ok, false); assert.ok(v.problemas.some((p) => p.includes('AGENTE QUE EJECUTA codex') && p.includes('NO INSTALADO')), v.problemas.join('|'));
  assert.equal(aplicar(sel, {}).agente_tool, 'codex');
  assert.equal(estadoOpcion(cap(), 'agente', 'inventado').estado, 'SIN VERIFICAR');
});

test('GLM-5.3 no disponible queda bloqueado; SIN VERIFICAR (intentable) se deja intentar mostrando su estado; agente incompatible con el modelo se bloquea', () => {
  assert.deepEqual(estadoOpcion(cap(), 'modelo', 'nvidia/z-ai/glm-5.3'), { ok: false, estado: 'NO DISPONIBLE EN PROVEEDOR', motivo: 'no figura en GET /models' });
  assert.equal(estadoOpcion(cap(), 'modelo', 'groq/qwen/qwen3.8-27b').ok, true); assert.equal(estadoOpcion(cap(), 'modelo', 'groq/qwen/qwen3.8-27b').estado, 'SIN VERIFICAR');
  const inc = estadoOpcion(cap(), 'agente', 'claude-code', 'hf/lfm2.5-350m');
  assert.deepEqual([inc.ok, inc.estado], [false, 'NO COMPATIBLE']);
});

test('workflow no disponible bloquea (Liquid Mirror) y SWE CODE exige modo agentico; los campos fijos del workflow no se validan', () => {
  assert.ok(validarSeleccion({ ...SELECCION_DEFECTO, workflow: 'liquid_mirror', modo_agentico: true }, cap()).problemas.some((p) => p.includes('NO CONFIGURADO')));
  assert.ok(validarSeleccion({ ...SELECCION_DEFECTO, workflow: 'swe_code' }, cap()).problemas.some((p) => p.includes('exige MODO AGENTICO ON')));
  assert.ok(camposFijos('swe_code').has('modelo_tool') && !camposFijos('individual').has('modelo_tool'));
  assert.equal(armarTarea({ sel: { ...SELECCION_DEFECTO, workflow: 'liquid_mirror' }, mensaje: 'x' }).modelo_tool, 'hf/lfm2.5-350m');
});

test('capacidades sin forma esperada no inventan nada', () => {
  for (const x of [null, 5, 'x', [], { agentes: 'no' }, { agentes: { a: { disponible: 'si' } } }]) { const c = normalizarCapacidades(x); assert.deepEqual([c.agentes, c.workflows, c.modelos].map((g) => Object.keys(g).length), [0, 0, 0]); }
  assert.equal(normalizarCapacidades(null).harness, 'desconocido');
});
