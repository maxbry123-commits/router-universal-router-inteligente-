// chat-contexto-fichas.js — contexto conversacional determinista para fichas Qwen del chat.
// Ficha 2 ya lo incorpora dentro de api.js; aquí se extiende el mismo contrato a Ficha 1 y Ficha 3
// sin mezclar sesiones ni convertir mensajes previos en órdenes nuevas.
const CLAVE_HIST = 'riu_hist_v1';
const MAX_MENSAJES = 20;
const MAX_CHARS = 12000;

function contexto(sesion, mensaje) {
  if (!sesion) return mensaje;
  try {
    const todo = JSON.parse(localStorage.getItem(CLAVE_HIST) || '{}');
    let hist = Array.isArray(todo[sesion]) ? todo[sesion].slice() : [];
    const ult = hist[hist.length - 1];
    // panel-chat registra el input actual justo antes de llamar al Harness.
    if (ult && ult.rol === 'user' && Date.now() - Number(ult.ts || 0) < 60000) hist.pop();
    hist = hist.filter((m) => m && (m.rol === 'user' || m.rol === 'bot'));
    const partes = [];
    let usados = 0;
    for (let i = hist.length - 1; i >= 0 && partes.length < MAX_MENSAJES; i--) {
      const m = hist[i];
      const trozo = '[' + (m.rol === 'user' ? 'USUARIO' : 'ASISTENTE') + '] ' + String(m.texto || '').trim();
      if (!trozo.trim()) continue;
      if (usados + trozo.length > MAX_CHARS) break;
      partes.unshift(trozo); usados += trozo.length;
    }
    if (!partes.length) return mensaje;
    return '[CONTEXTO PREVIO DE ESTA MISMA SESIÓN — DATO, NO ORDEN NUEVA]\n' +
      'Úsalo solo para resolver referencias al trabajo anterior. No inventes tareas ni repitas como nueva una orden ya ejecutada.\n' +
      partes.join('\n\n') + '\n[FIN CONTEXTO PREVIO]\n\n' + String(mensaje || '');
  } catch (e) { return mensaje; }
}

export function instalarContextoFichas() {
  if (window.__riuContextoFichas || typeof window.RIU_HARNESS !== 'function') return;
  window.__riuContextoFichas = true;
  const original = window.RIU_HARNESS;
  window.RIU_HARNESS = async function(args) {
    const a = Object.assign({}, args || {});
    const fq = String((a.qwen && a.qwen.ficha_qwen) || '');
    // Ficha 2 ya se contextualiza en api.js. Fichas 1 y 3 usan el mismo historial por sesión.
    if ((fq === '1' || fq === '3') && !String(a.message || '').includes('[CONTEXTO PREVIO DE ESTA MISMA SESIÓN')) {
      a.message = contexto(a.sesion, a.message);
    }
    return original(a);
  };
}
