// iguales.js — compara secretos sin filtrar su longitud: sha256 de ambos lados y timingSafeEqual siempre sobre 32 bytes (sin retorno temprano).
import crypto from 'node:crypto';

const huella = (v) => crypto.createHash('sha256').update(String(v)).digest();
export const iguales = (a, b) => crypto.timingSafeEqual(huella(a), huella(b));
