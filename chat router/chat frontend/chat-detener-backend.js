// chat-detener-backend.js — el boton Detener no solo corta la espera local:
// si hay un proceso async de Fichas 1-4, pide al mismo plugin/Router que lo detenga.
const CLAVE = 'riu_procesos_v1';
const leer = () => {
  try {
    const x = JSON.parse(localStorage.getItem(CLAVE) || '{}');
    return x && typeof x === 'object' ? x : {};
  } catch (e) { return {}; }
};
const escribir = (x) => { try { localStorage.setItem(CLAVE, JSON.stringify(x)); } catch (e) {} };

function actual() {
  try { return window.RIU_CHAT && window.RIU_CHAT.chat && window.RIU_CHAT.chat(); } catch (e) { return null; }
}

async function detenerProceso(rec) {
  const key = sessionStorage.getItem('riu_clave') || '';
  const headers = { 'Content-Type': 'application/json' };
  if (key) headers['X-API-Key'] = key;
  const f = window.__riuFetchOriginal || window.fetch.bind(window);
  const r = await f(rec.base.replace(/\/$/, '') + '/detener', {
    method: 'POST', headers, credentials: 'omit', body: JSON.stringify({ proceso_id: rec.proceso_id }),
  });
  const env = await r.json().catch(() => ({}));
  return r.ok && env.status === 'ok' ? (env.result || {}) : { error: env.reason || env.detail || 'HTTP_' + r.status };
}

export function instalarDetenerBackend({ root, q, tell }) {
  const b = q('#btn-detener');
  if (!b || b.dataset.detenerBackend) return;
  b.dataset.detenerBackend = '1';
  b.addEventListener('click', async () => {
    const c = actual(); if (!c || !c.sesion) return;
    const mapa = leer();
    const candidatos = Object.values(mapa)
      .filter((r) => r && r.sesion === c.sesion && r.proceso_id && r.base)
      .sort((a, z) => Number(z.creado || 0) - Number(a.creado || 0));
    const rec = candidatos[0];
    if (!rec) return; // chat normal/sin proceso async: el handler local sigue haciendo su trabajo.
    try {
      const out = await detenerProceso(rec);
      if (!out.error) {
        delete mapa[rec.proceso_id]; escribir(mapa);
        if (tell) tell(out.cancelado_en_cola ? 'Proceso cancelado antes de ejecutar' : 'Detención enviada al Router; terminará la llamada en curso y no abrirá otra');
      } else if (tell) tell('Detener backend: ' + out.error);
    } catch (e) {
      if (tell) tell('Detener backend: no se pudo contactar el Router; el corte local sí se aplicó');
    }
  }, true);
}
