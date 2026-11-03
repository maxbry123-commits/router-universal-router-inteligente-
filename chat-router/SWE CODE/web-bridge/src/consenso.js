// consenso.js — fan-out a los 3 modelos web + sintesis Qwen3.8Max (metodo D)
// consulta -> DSv4-flash + Qwen3.7Max + Qwen3.8Max en paralelo
// arbitro: Qwen3.8Max sintetiza la respuesta final fusionando lo mejor
import { MODELOS_WEB } from './sites.js';
import { consultarWeb } from './motor.js';

const ARBITRO = 'qwen38max';
const MODELOS = ['dsv4-flash', 'qwen37max', 'qwen38max'];

const PROMPT_ARBITRO = (pregunta, respuestas) =>
`Eres el arbitro. Te doy 3 respuestas anonimas a la misma consulta.
CONSULTA ORIGINAL:
${pregunta}

${respuestas.map((r, i) => `RESPUESTA ${'ABC'[i]}:\n${r}`).join('\n\n---\n\n')}

TAREA: redacta la respuesta FINAL sintetizando lo mejor de las tres.
Reglas: corrige lo erroneo, conserva lo mas completo, no menciones A/B/C ni que eres arbitro.
Si algo falta en las tres, marca [GAP] y dilo.`;

// con conv_id cada modelo (y el arbitro) lleva su propia tab y checkpoint: antes los 3 compartian el mismo
const opcionesDe = (opts, quien) => (opts.convId ? { ...opts, convId: `${opts.convId}-${quien}` } : opts);

// consulta de consenso: retorna {final, por_modelo}
export async function consenso(pregunta, opts = {}) {
  const resultados = await Promise.allSettled(
    MODELOS.map(m => consultarWeb(m, pregunta, opcionesDe(opts, m)))
  );
  const por_modelo = {};
  const validas = [];
  MODELOS.forEach((m, i) => {
    const r = resultados[i];
    por_modelo[m] = r.status === 'fulfilled' ? r.value : `ERROR: ${r.reason?.message || r.status}`;
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
