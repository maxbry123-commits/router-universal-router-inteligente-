// Cableado YAIWES PANEL-01 -> HARNESS puente_chat (misma ruta que el chat: api.js harness()).
// No cambia la arquitectura: COMPONENTE -> HARNESS puente_chat -> HTTP -> FICHA -> MODELO.
import { harness } from '../../chat%20router/chat%20frontend/api.js';
const MODELO = () => localStorage.getItem('yaiwes_modelo') || (window.RIU_CONFIG || {}).defecto;
window.YAIWES_BRIDGE = {
  async dispatch(actionId, payload = {}) {
    if (actionId !== 'send_message') return { ok: true };
    try {
      const r = await harness({ model: MODELO(), message: payload.text || '' });
      return { ok: true, reply: r.reply, traza: r.traza };
    } catch (e) { return { ok: false, reason: e.message || 'bridge_error' }; }
  }
};
