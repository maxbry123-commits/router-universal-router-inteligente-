// chat-proceso-recovery.js — conserva proceso_id por sesión y retoma /resultado después de una recarga.
// Nunca relanza la orden: solo vuelve a consultar el proceso original en el Router exacto que lo creó.
import { registrar } from './chat-ancla.js';

const CLAVE = 'riu_procesos_v1';
const MAX_EDAD = 30 * 60 * 1000;
const dormir = (ms) => new Promise((r) => setTimeout(r, ms));

const leer = () => {
  try {
    const x = JSON.parse(localStorage.getItem(CLAVE) || '{}');
    return x && typeof x === 'object' ? x : {};
  } catch (e) { return {}; }
};
const escribir = (x) => { try { localStorage.setItem(CLAVE, JSON.stringify(x)); } catch (e) {} };
const guardar = (r) => { const x = leer(); x[r.proceso_id] = r; escribir(x); };
const borrar = (id) => { const x = leer(); if (x[id]) { delete x[id]; escribir(x); } };

const cuerpoJson = (body) => {
  if (!body || typeof body !== 'string') return {};
  try { return JSON.parse(body); } catch (e) { return {}; }
};
const urlDe = (input) => typeof input === 'string' ? input : (input && input.url) || '';
const metodoDe = (input, init) => String((init && init.method) || (input && input.method) || 'GET').toUpperCase();

function instalarCapturaFetch() {
  if (window.__riuFetchProcesos) return;
  window.__riuFetchProcesos = true;
  const original = window.fetch.bind(window);
  window.__riuFetchOriginal = original;
  window.fetch = async function(input, init) {
    const url = urlDe(input), metodo = metodoDe(input, init);
    const esInicio = metodo === 'POST' && /\/chat_async(?:[?#].*)?$/.test(url);
    const esResultado = metodo === 'POST' && /\/resultado(?:[?#].*)?$/.test(url);
    const req = cuerpoJson(init && init.body);
    const resp = await original(input, init);
    if (esInicio || esResultado) {
      try {
        const env = await resp.clone().json();
        const p = env && env.result || {};
        if (esInicio && env.status === 'ok' && p.estado === 'procesando' && p.proceso_id && req.sesion) {
          guardar({
            proceso_id: String(p.proceso_id),
            sesion: String(req.sesion),
            base: url.replace(/\/chat_async(?:[?#].*)?$/, ''),
            creado: Date.now(),
            ficha_qwen: req.ficha_qwen == null ? null : String(req.ficha_qwen),
          });
        }
        if (esResultado && req.proceso_id && (env.status !== 'ok' || p.estado !== 'procesando')) borrar(String(req.proceso_id));
      } catch (e) {}
    }
    return resp;
  };
}

function metasChats() {
  try {
    const x = JSON.parse(localStorage.getItem('riu_chats_v1') || '[]');
    return Array.isArray(x) ? x : [];
  } catch (e) { return []; }
}
function histDeSesion(q, sesion) {
  const metas = metasChats();
  const i = metas.findIndex((m) => m && m.sesion === sesion);
  const hs = [...q('#histories').querySelectorAll('.chat-history')];
  return i >= 0 ? hs[i] || null : null;
}
function burbuja(texto, cls = '') {
  const d = document.createElement('div'); d.className = 'item message' + (cls ? ' ' + cls : '');
  const s = document.createElement('span'); s.className = 'txt'; s.textContent = texto; d.append(s);
  if (!/\b(pending|meta|error)\b/.test(cls)) {
    const b = document.createElement('button'); b.type = 'button'; b.className = 'copiar'; b.textContent = '⧉'; b.title = 'Copiar esta salida';
    b.addEventListener('click', () => { try { navigator.clipboard.writeText(s.textContent); } catch (e) {} }); d.append(b);
  }
  return d;
}
function limpiarFalsoInterrumpido(h) {
  [...h.querySelectorAll('.message.meta')].forEach((m) => {
    if ((m.textContent || '').includes('La respuesta se interrumpió al recargar la página')) m.remove();
  });
}
function textoFinal(p) {
  return String(
    (((p.choices || [])[0] || {}).message || {}).content ||
    p.reply || ''
  ).trim();
}

async function recuperarUno(q, rec) {
  const h = histDeSesion(q, rec.sesion);
  if (!h) return;
  limpiarFalsoInterrumpido(h);
  const pending = burbuja('Retomando tarea que seguía en el Router…', 'pending');
  h.append(pending);
  const key = sessionStorage.getItem('riu_clave') || '';
  const headers = { 'Content-Type': 'application/json' }; if (key) headers['X-API-Key'] = key;
  const fetch0 = window.__riuFetchOriginal || window.fetch.bind(window);
  let fallosRed = 0;
  const limite = Date.now() + 10 * 60 * 1000;
  while (Date.now() < limite) {
    try {
      const r = await fetch0(rec.base.replace(/\/$/, '') + '/resultado', {
        method: 'POST', headers, body: JSON.stringify({ proceso_id: rec.proceso_id }), credentials: 'omit',
      });
      const env = await r.json().catch(() => ({}));
      if (!r.ok || env.status !== 'ok') {
        fallosRed++;
        if (fallosRed < 3) { await dormir(1200); continue; }
        pending.remove();
        const t = 'GAP: no se pudo reconectar con el proceso original. No se relanzó la tarea.';
        h.append(burbuja(t, 'error')); registrar(rec.sesion, 'err', t); borrar(rec.proceso_id); return;
      }
      fallosRed = 0;
      const p = env.result || {};
      if (p.error) {
        pending.remove();
        const t = p.error === 'PROCESO_NO_EXISTE'
          ? 'GAP: el proceso ya no existe en el Router. No se relanzó la tarea.'
          : 'GAP: ' + String(p.error);
        h.append(burbuja(t, 'error')); registrar(rec.sesion, 'err', t); borrar(rec.proceso_id); return;
      }
      if (p.estado === 'procesando') {
        pending.textContent = p.progreso || 'Retomando tarea que sigue procesando…';
        await dormir(1000); continue;
      }
      pending.remove();
      const txt = textoFinal(p) || 'Sin respuesta';
      h.append(burbuja(txt)); registrar(rec.sesion, 'bot', txt); borrar(rec.proceso_id);
      return;
    } catch (e) {
      fallosRed++;
      if (fallosRed >= 3) {
        pending.remove();
        const t = 'GAP: conexión perdida con el Router que ejecutaba la tarea. No se relanzó.';
        h.append(burbuja(t, 'error')); registrar(rec.sesion, 'err', t); borrar(rec.proceso_id); return;
      }
      await dormir(1200);
    }
  }
  pending.remove();
  const t = 'GAP: tiempo de reconexión agotado; la tarea no se duplicó.';
  h.append(burbuja(t, 'error')); registrar(rec.sesion, 'err', t); borrar(rec.proceso_id);
}

export function instalarRecuperacionProcesos({ q }) {
  instalarCapturaFetch();
  if (window.__riuRecuperandoProcesos) return;
  window.__riuRecuperandoProcesos = true;
  setTimeout(() => {
    const x = leer();
    const ahora = Date.now();
    for (const [id, rec] of Object.entries(x)) {
      if (!rec || !rec.sesion || !rec.base || ahora - Number(rec.creado || 0) > MAX_EDAD) { borrar(id); continue; }
      recuperarUno(q, rec).catch(() => {});
    }
  }, 350);
}
