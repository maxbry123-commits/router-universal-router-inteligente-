// SWE CODE free: contrato determinista de herramientas para respuestas de chats WEB.
// No usa modelos locales ni ejecuta acciones: entrega tool_calls al cliente/ejecutor
// que valida permisos, aprobación y recibos. No interpretar texto libre como código.
import crypto from 'node:crypto';

const LIMITE = 24;
const NOMBRE = /^[A-Za-z_][A-Za-z0-9_.-]{0,100}$/;
const OBJETO = (x) => x !== null && typeof x === 'object' && !Array.isArray(x);
export function herramientasPermitidas(tools) {
  if (!Array.isArray(tools)) return [];
  return tools.slice(0, LIMITE).filter(t => t?.type === 'function' &&
    NOMBRE.test(t.function?.name || '') && OBJETO(t.function?.parameters || {}));
}
export function promptHerramientasWeb(tools) {
  const catalogo = herramientasPermitidas(tools);
  if (!catalogo.length) return '';
  const disponibles = catalogo.map(t => ({
    name: t.function.name,
    description: String(t.function.description || '').slice(0, 320),
    parameters: t.function.parameters || { type: 'object' }
  }));
  return '\n\n[CONTRATO_HERRAMIENTAS_WEB_V1]\n'
    + 'Si necesitas una herramienta, responde con UN JSON COMPLETO (sin texto fuera del JSON) '
    + 'de forma {"mensaje":"resumen breve","tool_calls":[{"name":"nombre_exacto","arguments":{}}]}. '
    + 'Si no necesitas herramientas, responde normalmente. No inventes tools, no simules '
    + 'resultados ni afirmes ejecuciones. El ejecutor externo comprueba permisos y recibos. '
    + 'Una orden no implica aprobación. Catálogo disponible:\n'
    + JSON.stringify(disponibles).slice(0, 16000) + '\n[/CONTRATO_HERRAMIENTAS_WEB_V1]';
}
function objetoJson(texto) {
  const s = String(texto || '').trim();
  // Nada de buscar JSON incrustado en prosa, HTML o documentos: SOLO JSON entero.
  const limpio = s.startsWith('```json\n') && s.endsWith('```')
    ? s.slice(8, -3).trim() : s;
  if (!limpio.startsWith('{') || !limpio.endsWith('}') || limpio.length > 45000) return null;
  try { const v = JSON.parse(limpio); return OBJETO(v) ? v : null; } catch { return null; }
}
function validaTipo(valor, schema) {
  if (!schema || !schema.type) return true;
  const t = schema.type;
  if (Array.isArray(t)) return t.some(x => validaTipo(valor, { ...schema, type:x }));
  return t === 'object' ? OBJETO(valor)
    : t === 'array' ? Array.isArray(valor)
    : t === 'integer' ? Number.isInteger(valor)
    : t === 'number' ? typeof valor === 'number' && Number.isFinite(valor)
    : t === 'string' ? typeof valor === 'string'
    : t === 'boolean' ? typeof valor === 'boolean'
    : t === 'null' ? valor === null : true;
}
function validarArgs(args, schema) {
  if (!OBJETO(args) || !validaTipo(args, schema)) return false;
  if (JSON.stringify(args).length > 16000) return false;
  for (const k of (schema?.required || [])) if (!Object.hasOwn(args, k)) return false;
  const propiedades = schema?.properties || {};
  for (const [k,v] of Object.entries(args)) {
    if (schema?.additionalProperties === false && !Object.hasOwn(propiedades, k)) return false;
    if (propiedades[k] && !validaTipo(v, propiedades[k])) return false;
  }
  return true;
}
export function extraerLlamadasWeb(texto, tools) {
  const catalogo = new Map(herramientasPermitidas(tools).map(t => [t.function.name, t.function]));
  if (!catalogo.size) return { texto: String(texto || ''), tool_calls: [], finish_reason: 'stop' };
  const parsed = objetoJson(texto);
  if (!parsed || !Array.isArray(parsed.tool_calls) || parsed.tool_calls.length === 0)
    return { texto: String(texto || ''), tool_calls: [], finish_reason:'stop' };
  if (parsed.tool_calls.length > 8) throw Object.assign(new Error('demasiadas llamadas web'), { code:'TOOL_CALL_INVALIDA' });
  const llamadas = parsed.tool_calls.map((tc, i) => {
    const fn = catalogo.get(tc?.name);
    if (!fn || !validarArgs(tc.arguments, fn.parameters))
      throw Object.assign(new Error('nombre o argumentos de herramienta no autorizados'), { code:'TOOL_CALL_INVALIDA' });
    const id = 'web_' + crypto.randomBytes(8).toString('hex') + '_' + i;
    return { id, type:'function', function:{ name:fn.name, arguments: JSON.stringify(tc.arguments) } };
  });
  return { texto: typeof parsed.mensaje === 'string' ? parsed.mensaje.slice(0,4000) : '',
    tool_calls:llamadas, finish_reason:'tool_calls' };
}
