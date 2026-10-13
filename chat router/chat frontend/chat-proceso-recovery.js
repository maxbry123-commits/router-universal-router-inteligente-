// chat-proceso-recovery.js — conserva proceso_id por sesión y retoma /resultado tras recarga
// o cuando el cliente normal deja de esperar. Nunca relanza la orden original.
import { registrar } from './chat-ancla.js';

const CLAVE = 'riu_procesos_v1';
const MAX_EDAD = 30 * 60 * 1000;
const RETOMAR_EN_MISMA_PAGINA_MS = 565000; // api.js corta a ~560 s; a partir de aqui este supervisor sigue el mismo proceso_id.
const dormir = (ms) => new Promise((r) => setTimeout(r, ms));
const recuperando = new Set();

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
const esReintentoAutomatico = (req) => {
  const ms = Array.isArray(req && req.messages) ? req.messages : [];
  if (ms.length < 2) return false;
  return String((ms[ms.length - 1] || {}).content || '').trim().toLowerCase() === 'continúa el trabajo donde quedó';
};

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

    // api.js antiguo añadía este segundo mensaje para volver a ejecutar ciertos errores del bridge.
    // Eso puede duplicar una tarea. Se devuelve un error controlado sin enviar una segunda ejecución.
    if (esInicio && esReintentoAutomatico(req)) {
      return new Response(JSON.stringify({
        status: 'ok',
        result: { error: 'REINTENTO_AUTOMATICO_BLOQUEADO', detalle: 'La tarea original no se vuelve a ejecutar automáticamente.' },
      }), { status: 200, headers: { 'Content-Type': 'application/json' } });
    }

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
            reintentarDespues: 0,
          });
        }
        // Solo se elimina cuando el Router respondió correctamente y confirmó final/error real.
        if (esResultado && req.proceso_id && env.status === 'ok' && (p.error || p.estado !== 'procesando')) {
          borrar(String(req.proceso_id));
        }
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
  const caja = q('#histories');
  if (!caja) return null;
  const hs = [...caja.querySelectorAll('.chat-history')];
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
function limpiarMarcadoresTransitorios(h) {
  [...h.querySelectorAll('.message.meta,.message.error')].forEach((m) => {
    const t = m.textContent || '';
    if (t.includes('La respuesta se interrumpió al recargar la página') || t.includes('TIEMPO_TOTAL_AGOTADO')) m.remove();
  });
}
function textoFinal(p) {
  return String(((((p.choices || [])[0] || {}).message || {}).content) || p.reply || '').trim();
}

async function recuperarUno(q, rec) {
  const id = String(rec.proceso_id || '');
  if (!id || recuperando.has(id)) return;
  const h = histDeSesion(q, rec.sesion);
  if (!h) return;
  recuperando.add(id);
  limpiarMarcadoresTransitorios(h);
  const pending = burbuja('Retomando la misma tarea que sigue en el Router…', 'pending');
  h.append(pending);
  const key = sessionStorage.getItem('riu_clave') || '';
  const headers = { 'Content-Type': 'application/json' }; if (key) headers['X-API-Key'] = key;
  const fetch0 = window.__riuFetchOriginal || window.fetch.bind(window);
  let fallosRed = 0;
  const limite = Date.now() + 10 * 60 * 1000;
  try {
    while (Date.now() < limite) {
      try {
        const r = await fetch0(rec.base.replace(/\/$/, '') + '/resultado', {
          method: 'POST', headers, body: JSON.stringify({ proceso_id: id }), credentials: 'omit',
        });
        const env = await r.json().catch(() => ({}));
        if (!r.ok || env.status !== 'ok') {
          fallosRed++;
          if (fallosRed < 3) { await dormir(1200); continue; }
          pending.remove();
          const t = 'Conexión temporal perdida con la tarea; se conserva el proceso y se reintentará sin duplicarlo.';
          h.append(burbuja(t, 'meta'));
          guardar({ ...rec, reintentarDespues: Date.now() + 30000 });
          return;
        }
        fallosRed = 0;
        const p = env.result || {};
        if (p.error) {
          pending.remove();
          const t = p.error === 'PROCESO_NO_EXISTE'
            ? 'GAP: el proceso ya no existe en el Router. No se relanzó la tarea.'
            : 'GAP: ' + String(p.error);
          h.append(burbuja(t, 'error')); registrar(rec.sesion, 'err', t); borrar(id); return;
        }
        if (p.estado === 'procesando') {
          pending.textContent = p.progreso || 'La misma tarea sigue procesando…';
          await dormir(1000); continue;
        }
        pending.remove();
        const txt = textoFinal(p) || 'Sin respuesta';
        h.append(burbuja(txt)); registrar(rec.sesion, 'bot', txt); borrar(id);
        return;
      } catch (e) {
        fallosRed++;
        if (fallosRed >= 3) {
          pending.remove();
          h.append(burbuja('Conexión temporal perdida; el proceso queda guardado para reintentar.', 'meta'));
          guardar({ ...rec, reintentarDespues: Date.now() + 30000 });
          return;
        }
        await dormir(1200);
      }
    }
    pending.remove();
    const t = 'GAP: tiempo total de seguimiento agotado; la tarea no se duplicó.';
    h.append(burbuja(t, 'error')); registrar(rec.sesion, 'err', t); borrar(id);
  } finally {
    recuperando.delete(id);
  }
}

export function instalarRecuperacionProcesos({ q }) {
  instalarCapturaFetch();
  // Cada root nuevo (Chat remontado) necesita su propio supervisor; la captura de fetch sí es global.
  const caja = q('#histories');
  if (!caja || caja.dataset.procesoRecovery) return;
  caja.dataset.procesoRecovery = '1';

  // Al montar una página nueva, cualquier proceso guardado es de una ejecución previa a la recarga: retomarlo ya.
  setTimeout(() => {
    const x = leer(), ahora = Date.now();
    for (const [id, rec] of Object.entries(x)) {
      if (!rec || !rec.sesion || !rec.base || ahora - Number(rec.creado || 0) > MAX_EDAD) { borrar(id); continue; }
      if (Number(rec.reintentarDespues || 0) <= ahora) recuperarUno(q, rec).catch(() => {});
    }
  }, 350);

  // En la misma página, api.js deja de esperar a ~560 s. Este supervisor continúa con EL MISMO proceso_id.
  const vigilante = setInterval(() => {
    if (!caja.isConnected) { clearInterval(vigilante); return; }
    const x = leer(), ahora = Date.now();
    for (const [id, rec] of Object.entries(x)) {
      const edad = ahora - Number(rec && rec.creado || 0);
      if (!rec || !rec.sesion || !rec.base || edad > MAX_EDAD) { borrar(id); continue; }
      if (edad >= RETOMAR_EN_MISMA_PAGINA_MS && Number(rec.reintentarDespues || 0) <= ahora) recuperarUno(q, rec).catch(() => {});
    }
  }, 5000);
}
