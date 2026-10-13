// chat-selector-guard.js — nunca deja que un selector visual sin backend caiga silenciosamente a otro modelo.
const PERMITIDOS = new Set([
  'nvidia-groq-team',
  'team-qwen',
  'ask-consil-code-qwen-team',
  'ask-consil-fromtend-qwen-team',
]);

export function instalarGuardSelector({ q, tell }) {
  const form = q('#composer');
  if (!form || form.dataset.guardSelector) return;
  form.dataset.guardSelector = '1';
  form.addEventListener('submit', (e) => {
    const activo = window.RIU_SELECTORES && window.RIU_SELECTORES.activo;
    if (!activo || PERMITIDOS.has(activo)) return;
    e.preventDefault();
    e.stopImmediatePropagation();
    const info = (window.RIU_SELECTORES.selectores || []).find((x) => x.id === activo);
    const nombre = info ? info.nombre : activo;
    const c = window.RIU_CHAT && window.RIU_CHAT.chat && window.RIU_CHAT.chat();
    if (c && c.hist) {
      const d = document.createElement('div');
      d.className = 'item message meta';
      d.textContent = nombre + ': selector sin backend conectado. La orden NO se envió a otro modelo.';
      c.hist.append(d);
    }
    if (tell) tell(nombre + ': backend pendiente; no se envió la orden');
  }, true);
}
