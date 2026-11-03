// consenso.js — opiniones DS/Claude/Qwen; Qwen 3.8 Max es árbitro final.
// Claude es segundo y usa sesión oficial OpenClaw con solo Sonnet max.
// arbitro: Qwen3.8Max sintetiza la respuesta final fusionando lo mejor
import { MODELOS_WEB } from './sites.js';
import { consultarWeb } from './motor.js';
import { consultarClaude, esCuotaClaude } from './claude_gateway.js';

const ARBITRO = 'qwen38max';
const MODELOS = ['dsv4-flash', 'claude-sonnet', 'qwen37max', 'qwen38max'];

const PROMPT_ARBITRO = (pregunta, respuestas) =>
`Eres el arbitro Qwen 3.8 Max. Te doy respuestas del consejo a la misma consulta.
CONSULTA ORIGINAL:
${pregunta}

${respuestas.map((r, i) => `RESPUESTA ${i+1}:\n${r}`).join('\n\n---\n\n')}

TAREA: redacta la respuesta FINAL sintetizando sólo opiniones realmente completadas.
Reglas: corrige lo erróneo, conserva lo más completo. No ocultes los GAP.
Si no se recibió Claude, no inventes su opinión; los indicadores 🚩 se informan al operador por separado.`;

// con conv_id cada modelo (y el arbitro) lleva su propia tab y checkpoint: antes los 3 compartian el mismo
const opcionesDe = (opts, quien) => (opts.convId ? { ...opts, convId: `${opts.convId}-${quien}` } : opts);

// consulta de consenso: retorna {final, por_modelo}
export async function consenso(pregunta, opts = {}) {
  const resultados = await Promise.allSettled(
    MODELOS.map(m => m === 'claude-sonnet'
      ? consultarClaude(pregunta, opcionesDe(opts, m)).then(x => x.texto)
      : consultarWeb(m, pregunta, opcionesDe(opts, m)))
  );
  const por_modelo = {};
  const validas = [];
  MODELOS.forEach((m, i) => {
    const r = resultados[i];
    const err = r.status === 'rejected' ? (r.reason?.code || 'NO_DISPONIBLE') : null;
    por_modelo[m] = r.status === 'fulfilled' ? r.value :
      (m === 'claude-sonnet' && esCuotaClaude(err)
        ? '🚩 CLAUDE_SONNET_SIN_CUENTA_DISPONIBLE: OpenClaw agotó los perfiles Anthropic elegibles; continúan los demás modelos del consejo.'
        : '🚩 ' + m + ' ' + String(err||'FALLO'));
    if (r.status === 'fulfilled' && r.value) validas.push(r.value);
  });
  if (!validas.length) {
    const e = new Error('CONSENSO_SIN_RESPUESTAS');
    e.detail = por_modelo;
    throw e;
  }
  // La decisión FINAL siempre es de Qwen 3.8 Max, incluso con una sola opinión.
  // Si no está disponible, no se atribuye el dictamen a otro modelo.
  let final;
  try { final = await consultarWeb(ARBITRO, PROMPT_ARBITRO(pregunta, validas), opcionesDe(opts, 'arbitro')); }
  catch (e) { throw Object.assign(new Error('el árbitro Qwen 3.8 Max no respondió; conservar opiniones para revisión manual'), { code: 'CONSIL_ARBITRO_NO_DISPONIBLE', causa: e?.code }); }
  return { final, por_modelo, arbitro:'qwen38max' };
}
