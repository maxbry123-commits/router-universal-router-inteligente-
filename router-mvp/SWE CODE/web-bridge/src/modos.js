// modos.js — plantillas SWEN CODE free (se activan solo via /swecode o model "swecode-*")
// Cada modo = preambulo fijo inyectado en el bloque 1.

export const MODOS = {
  revision: `MODO REVISION. Te muestro un mirror/copia del codigo por bloques.
Revisa: errores reales, gaps, partes rotas o faltantes. NO reescribas completo;
marca [GAP] lo que falta y [FIX] lo que esta mal con el parche minimo.
Espera todos los bloques antes de dar el veredicto completo.`,
  solucion: `MODO SOLUCION. Recibiras gaps/problemas por bloques.
Propone la solucion concreta por gap: archivo, cambio minimo, codigo exacto.
Prioriza reutilizar lo existente; nada de arquitectura nueva.`,
  arquitectura: `MODO ARQUITECTURA. Recibiras requisitos/codigo por bloques.
Produce el diseno de programacion: modulos, contratos, flujo, decisiones.
Formato: diagrama en texto + lista de componentes + orden de construccion.`,
  archivos: `MODO ARCHIVOS. Recibiras documentos/archivos de proyecto por bloques.
Convierte el contenido a codigo: estructura, esqueleto, implementacion.
Salida: arbol de archivos + contenido de cada archivo en bloques de codigo.`,
  prompt_code: `MODO PROMT-CODE. Escribe/optimiza el prompt o el codigo pedido.
Entrega directamente el artefacto; si necesitas el contexto restante,
pide el bloque siguiente explicitamente.`,
  consulta: `MODO CONSULTA/PLAN. Analiza la pregunta y el contexto por bloques.
Entrega plan de accion: pasos ordenados, riesgos, decision abierta si falta
informacion. Responde preguntas del orquestador con evidencia.`,
};

export function modoValido(m) { return Object.hasOwn(MODOS, m); }

export function preambulo(modo) {
  const base = MODOS[modo] || MODOS.consulta;
  return `${base}\nCuando veas [BLOQUE n/N] confirma con "OK n/N" hasta recibir el ultimo bloque; ahi respondes completo.\n`;
}
