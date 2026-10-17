// Cableado YAIWES PANEL-01 -> HARNESS puente_chat (misma ruta que el chat: api.js harness()).
// No cambia la arquitectura: COMPONENTE -> HARNESS puente_chat -> HTTP -> FICHA -> MODELO.
// Equipo: localStorage 'yaiwes_equipo' = 'team-qwen' (defecto) | 'team-5-mvp'; modelo: 'yaiwes_modelo' (etiqueta del selector, defecto Qwen 3.8 Max).
import { harness } from '../api.js';
const slug = (t) => t.toLowerCase().normalize('NFD').replace(/[\u0300-\u036f]/g, '').replace(/[^a-z0-9]+/g, '-').replace(/^-|-$/g, '');
const ls = (k, d) => { try { return localStorage.getItem(k) || d; } catch (e) { return d; } };
const sesion = () => { let s = ls('yaiwes_sesion', ''); if (!s) { s = 'yaiwes-' + Math.random().toString(36).slice(2, 10); try { localStorage.setItem('yaiwes_sesion', s); } catch (e) {} } return s; };
const listo = async () => { for (let i = 0; i < 100 && !(window.RIU_CONFIG || {}).harnessUrl; i++) await new Promise((r) => setTimeout(r, 100)); };
window.YAIWES_BRIDGE = {
  async dispatch(actionId, payload = {}) {
    if (actionId !== 'send_message') return { ok: true };
    try {
      await listo();
      const label = ls('yaiwes_modelo', 'Qwen 3.8 Max'), equipo = ls('yaiwes_equipo', 'team-qwen');
      const mvp = equipo === 'team-5-mvp';
      const r = await harness({ model: 'qw-' + slug(label), message: payload.text || '', max_tokens: mvp ? 0 : 1024, sesion: sesion(),
        qwen: mvp ? { plugin: 'fichas_qwen', ficha_qwen: '5', modelo: label, instrucciones_fijas: '' }
                  : { plugin: 'fichas_qwen', ficha_qwen: '1', modelo: label, task_type: 'chat' } });
      return { ok: true, reply: r.reply, traza: r.traza };
    } catch (e) { return { ok: false, reason: e.message || 'bridge_error' }; }
  }
};
