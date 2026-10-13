// chat-historial-db.js — historial visual persistente sin depender del limite pequeno de localStorage.
// IndexedDB guarda el historial completo por sesion. localStorage conserva solo una cola reciente
// para contexto rapido/modelo, evitando que el navegador recorte silenciosamente todos los chats.
const DB_NOMBRE = 'riu_chat_hist_v2';
const STORE = 'historial';
const CLAVE_CHATS = 'riu_chats_v1';
const CLAVE_RECIENTE = 'riu_hist_v1';
const RECIENTES = 24;

const abrirDb = () => new Promise((resolve, reject) => {
  if (!('indexedDB' in window)) { reject(new Error('IndexedDB no disponible')); return; }
  const r = indexedDB.open(DB_NOMBRE, 1);
  r.onupgradeneeded = () => {
    const db = r.result;
    if (!db.objectStoreNames.contains(STORE)) db.createObjectStore(STORE, { keyPath: 'sesion' });
  };
  r.onsuccess = () => resolve(r.result);
  r.onerror = () => reject(r.error || new Error('No se pudo abrir IndexedDB'));
});

const leerDb = async (sesion) => {
  const db = await abrirDb();
  return new Promise((resolve) => {
    const tx = db.transaction(STORE, 'readonly');
    const q = tx.objectStore(STORE).get(sesion);
    q.onsuccess = () => resolve(q.result || null);
    q.onerror = () => resolve(null);
    tx.oncomplete = () => db.close();
  });
};

const guardarDb = async (sesion, mensajes) => {
  const db = await abrirDb();
  return new Promise((resolve) => {
    const tx = db.transaction(STORE, 'readwrite');
    tx.objectStore(STORE).put({ sesion, mensajes, actualizado: Date.now() });
    tx.oncomplete = () => { db.close(); resolve(true); };
    tx.onerror = () => { db.close(); resolve(false); };
  });
};

const borrarDb = async (sesion) => {
  if (!sesion) return;
  try {
    const db = await abrirDb();
    await new Promise((resolve) => {
      const tx = db.transaction(STORE, 'readwrite');
      tx.objectStore(STORE).delete(sesion);
      tx.oncomplete = () => resolve();
      tx.onerror = () => resolve();
    });
    db.close();
  } catch (e) {}
};

const metaChats = () => {
  try {
    const x = JSON.parse(localStorage.getItem(CLAVE_CHATS) || '[]');
    return Array.isArray(x) ? x : [];
  } catch (e) { return []; }
};

const rolDe = (m) => m.classList.contains('user') ? 'user' : m.classList.contains('error') ? 'err' : 'bot';
const extraer = (h) => [...h.querySelectorAll('.message')]
  .filter((m) => !m.classList.contains('pending') && !m.classList.contains('meta'))
  .map((m) => ({ rol: rolDe(m), texto: String((m.querySelector('.txt') || m).textContent || '').trim() }))
  .filter((m) => m.texto);

const firma = (m) => m.rol + '\u0000' + m.texto;
const solape = (db, dom) => {
  const max = Math.min(db.length, dom.length);
  for (let k = max; k > 0; k--) {
    let ok = true;
    for (let i = 0; i < k; i++) {
      if (firma(db[db.length - k + i]) !== firma(dom[i])) { ok = false; break; }
    }
    if (ok) return k;
  }
  return 0;
};

const crearBurbuja = (m) => {
  const d = document.createElement('div');
  d.className = 'item message' + (m.rol === 'user' ? ' user' : m.rol === 'err' ? ' error' : '');
  const s = document.createElement('span'); s.className = 'txt'; s.textContent = m.texto;
  const b = document.createElement('button'); b.type = 'button'; b.className = 'copiar'; b.textContent = '⧉'; b.title = 'Copiar esta salida';
  b.addEventListener('click', () => { try { navigator.clipboard.writeText(s.textContent); } catch (e) {} });
  d.append(s, b); return d;
};

// Mantiene la cola reciente que consumen las fichas exactamente alineada con el historial visual.
// Esto también corrige un GAP previo: si el usuario edita una salida, el modelo ya no recibe la versión vieja.
const sincronizarCache = (sesion, mensajes) => {
  if (!sesion) return;
  try {
    const t = JSON.parse(localStorage.getItem(CLAVE_RECIENTE) || '{}');
    const base = t && typeof t === 'object' ? t : {};
    const ult = (mensajes || []).slice(-RECIENTES);
    const ahora = Date.now();
    base[sesion] = ult.map((m, i) => ({ rol: m.rol, texto: m.texto, ts: ahora - (ult.length - i) }));
    localStorage.setItem(CLAVE_RECIENTE, JSON.stringify(base));
  } catch (e) {}
};

const compactarCache = () => {
  try {
    const t = JSON.parse(localStorage.getItem(CLAVE_RECIENTE) || '{}');
    if (!t || typeof t !== 'object') return;
    let cambio = false;
    for (const k of Object.keys(t)) {
      if (Array.isArray(t[k]) && t[k].length > RECIENTES) { t[k] = t[k].slice(-RECIENTES); cambio = true; }
    }
    if (cambio) localStorage.setItem(CLAVE_RECIENTE, JSON.stringify(t));
  } catch (e) {}
};

export function montarHistorialPersistente({ root, q }) {
  const cont = q('#histories');
  if (!cont || cont.dataset.histDb) return;
  cont.dataset.histDb = '1';

  // Pide almacenamiento persistente cuando el navegador lo permite; si no, sigue funcionando igual.
  try { if (navigator.storage && navigator.storage.persist) navigator.storage.persist().catch(() => {}); } catch (e) {}

  let restaurando = false;
  const restaurar = async () => {
    restaurando = true;
    try {
      const metas = metaChats();
      const hs = [...cont.querySelectorAll('.chat-history')];
      for (let i = 0; i < hs.length; i++) {
        const sesion = metas[i] && metas[i].sesion;
        if (!sesion) continue;
        const h = hs[i], dom = extraer(h), rec = await leerDb(sesion).catch(() => null);
        const guardado = rec && Array.isArray(rec.mensajes) ? rec.mensajes : [];
        if (!guardado.length) {
          if (dom.length) {
            await guardarDb(sesion, dom).catch(() => false);
            sincronizarCache(sesion, dom);
          }
          continue;
        }
        const k = solape(guardado, dom);
        const anteriores = guardado.slice(0, guardado.length - k);
        if (anteriores.length) {
          const frag = document.createDocumentFragment();
          anteriores.forEach((m) => frag.append(crearBurbuja(m)));
          h.prepend(frag);
        }
        const combinado = guardado.concat(dom.slice(k));
        if (combinado.length !== guardado.length || k !== dom.length) await guardarDb(sesion, combinado).catch(() => false);
        sincronizarCache(sesion, combinado);
      }
      compactarCache();
    } finally { restaurando = false; }
  };

  let timer = 0;
  const guardarTodo = () => {
    clearTimeout(timer);
    timer = setTimeout(async () => {
      if (restaurando) return;
      const metas = metaChats();
      const hs = [...cont.querySelectorAll('.chat-history')];
      for (let i = 0; i < hs.length; i++) {
        const sesion = metas[i] && metas[i].sesion;
        if (!sesion) continue;
        const dom = extraer(hs[i]);
        if (!dom.length) continue;
        const rec = await leerDb(sesion).catch(() => null);
        const viejo = rec && Array.isArray(rec.mensajes) ? rec.mensajes : [];
        const k = solape(viejo, dom);
        const combinado = viejo.length ? viejo.concat(dom.slice(k)) : dom;
        await guardarDb(sesion, combinado).catch(() => false);
        sincronizarCache(sesion, combinado);
      }
      compactarCache();
    }, 450);
  };

  new MutationObserver(guardarTodo).observe(cont, { childList: true, subtree: true, characterData: true });
  root.addEventListener('riu:cerrar-chat', (e) => {
    const metas = metaChats();
    const i = Number(e.detail);
    const sesion = metas[i] && metas[i].sesion;
    if (sesion) borrarDb(sesion);
  }, true);

  setTimeout(restaurar, 80);
}
