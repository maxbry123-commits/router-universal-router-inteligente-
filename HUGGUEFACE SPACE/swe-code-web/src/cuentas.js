// cuentas.js — version minima de Router 2 (sin rotacion de cuentas).
// La rotacion original (varios correos, misma clave) NO se copia por decision del owner.
// Mantiene la misma API para que browser.js cargue. Usa solo la primera cuenta de WEB_ACCOUNTS.

export function pool() {
  const mails = (process.env.WEB_ACCOUNTS || '').split(',').map(s => s.trim()).filter(Boolean);
  if (!mails.length) throw new Error('WEB_ACCOUNTS vacio');
  return mails.slice(0, 1);
}

export function clave() {
  const p = process.env.WEB_PASS;
  if (!p) throw new Error('WEB_PASS no definido');
  return p;
}

export function cuentaActual() {
  const mails = pool();
  return { email: mails[0], index: 0, total: 1 };
}

// Sin rotacion: devuelve la misma cuenta.
export function rotar() {
  return cuentaActual();
}
