// chat-selector-por-sesion.js — cada Chat conserva su selector principal.
// Evita que cambiar el selector en Chat 2 cambie silenciosamente la ruta de Chat 1.
const CLAVE = 'riu_selector_por_sesion_v1';
let cambiando = false;

const leerMapa = () => {
  try {
    const x = JSON.parse(localStorage.getItem(CLAVE) || '{}');
    return x && typeof x === 'object' ? x : {};
  } catch (e) { return {}; }
};
const guardarMapa = (x) => { try { localStorage.setItem(CLAVE, JSON.stringify(x)); } catch (e) {} };
const sesionActual = () => {
  try { return window.RIU_CHAT && window.RIU_CHAT.chat && window.RIU_CHAT.chat().sesion || ''; } catch (e) { return ''; }
};

function guardarActivo() {
  if (cambiando) return;
  const ses = sesionActual(); if (!ses || !window.RIU_SELECTORES) return;
  const m = leerMapa(); m[ses] = window.RIU_SELECTORES.activo || null; guardarMapa(m);
}

function restaurar() {
  if (!window.RIU_SELECTORES) return;
  const ses = sesionActual(); if (!ses) return;
  const m = leerMapa();
  // Primera vez de una sesión existente: adopta el selector actual para no cambiarla de golpe.
  if (!(ses in m)) { m[ses] = window.RIU_SELECTORES.activo || null; guardarMapa(m); return; }
  const deseado = m[ses] || null;
  const actual = window.RIU_SELECTORES.activo || null;
  if (deseado === actual) return;
  cambiando = true;
  try {
    if (actual && typeof window.RIU_SELECTORES.apagar === 'function') window.RIU_SELECTORES.apagar();
    if (deseado && typeof window.RIU_SELECTORES.encender === 'function') window.RIU_SELECTORES.encender(deseado);
  } finally {
    cambiando = false;
    if (window.RIU_SELECTORES.refrescar) window.RIU_SELECTORES.refrescar();
  }
}

export function instalarSelectorPorSesion({ root }) {
  if (window.__riuSelectorPorSesion) return;
  window.__riuSelectorPorSesion = true;
  window.addEventListener('riu:selector-activo', () => { guardarActivo(); });
  // panel-chat actualiza el Chat activo antes de que termine el click de la pestaña.
  root.addEventListener('click', (e) => {
    if (!e.target.closest('#chat-tabs .chip')) return;
    setTimeout(restaurar, 0);
  });
  // Nuevo chat / restauración: guardar/restaurar tras montar las pestañas.
  new MutationObserver(() => setTimeout(restaurar, 0)).observe(root.querySelector('#histories') || root, { childList: true, subtree: false });
  setTimeout(restaurar, 50);
}
