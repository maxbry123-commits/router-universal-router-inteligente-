// Configuracion del chat (solo interfaz; el codigo vive en GitHub y el computo en HF).
// La interfaz abre sin pedir clave. El Router funciona en HF CPU de 16 GB; las claves permanecen en el servidor.
window.RIU_CONFIG = {
  routerStopped: false,
  apiBase: 'https://6ac41820404719ba376595fb--8000.hf.jobs',
  liveUrl: 'https://raw.githubusercontent.com/maxbry123-commits/router-universal-router-inteligente-/main/router%20inteligente%20universal/LIVE_URL.json',
  harnessUrl: 'https://6ac41820404719ba376595fb--8000.hf.jobs/plugins/puente_chat/call',  // puente dentro del Router (puerta fija)
  authHeader: 'X-API-Key',
  defecto: 'nv-nemotron-super',  // el modelo HF enciende una GPU de pago: no se deja como predeterminado
  modelos: [
    { id: 'ask-consil-factory', etiqueta: '🧠 ask consil factory' },
    { id: 'motor-descarga', etiqueta: '➡️ MOTOR DESCARGA EXTRACCIONES copiar mover' },
    { id: 'motor-xray', etiqueta: '🔬 MOTOR X-RAY auditoría forense' },
    { id: 'motor-auditor-code', etiqueta: '🔎 MOTOR AUDITOR CODE repo' },
    { id: 'hf-1-qwen-3-8', etiqueta: 'HF 1 Qwen 3.8 (27B)' },
    { id: 'hf-2-qwen-3-6', etiqueta: 'HF 2 Qwen 3.6 (35B)' },
    { id: 'groq-qwen-3-8', etiqueta: 'GROQ Qwen 3.8' },
    { id: 'nv-kimi-k3', etiqueta: 'NV Kimi K3' },
    { id: 'nv-glm-5-3', etiqueta: 'NV GLM 5.3' },
    { id: 'nv-nemotron-super', etiqueta: 'NV Nemotron 3 Super' },
    { id: 'nv-nemotron-lightning', etiqueta: 'NV Nemotron 3.5 Lightning' },
    { id: 'nv-muse-glimmer', etiqueta: 'NV Muse Glimmer 30B' }
  ]
};

// GAP fast-reply: elimina una vez estados antiguos que podian dejar ⚡ activo sin que el usuario lo viera.
// El modo rápido vuelve a OFF de forma segura; solo se activa de nuevo al tocar explícitamente ⚡.
(() => {
  try {
    const MIGRA = 'riu_fast_reply_estado_v2';
    if (localStorage.getItem(MIGRA) !== '1') {
      const chats = JSON.parse(localStorage.getItem('riu_chats_v1') || '[]');
      if (Array.isArray(chats)) {
        for (const c of chats) if (c && typeof c === 'object') c.fastReply = false;
        localStorage.setItem('riu_chats_v1', JSON.stringify(chats));
      }
      localStorage.setItem(MIGRA, '1');
    }
  } catch (e) {}
})();

// GAP fast-reply: al restaurar un chat, panel-chat carga fastReply antes de que el panel de Selectores
// tenga acceso a window.RIU_CHAT. Reintenta hasta que ambos existan y fuerza una sola sincronizacion visual.
(() => {
  let intentos = 0;
  const sincronizarFastReply = () => {
    intentos += 1;
    const listo = !!(window.RIU_CHAT && window.RIU_SELECTORES && typeof window.RIU_SELECTORES.refrescar === 'function');
    if (listo) {
      window.RIU_SELECTORES.refrescar();
      window.dispatchEvent(new CustomEvent('riu:fast-reply', { detail: { sync: true } }));
      return;
    }
    if (intentos < 30) setTimeout(sincronizarFastReply, 100);
  };
  setTimeout(sincronizarFastReply, 0);
})();

// El modo rápido pertenece al selector que el usuario está usando. Si cambia de selector,
// se apaga para impedir que un ⚡ heredado se mande silenciosamente a otro modelo/ficha.
window.addEventListener('riu:selector-activo', () => {
  try {
    const c = window.RIU_CHAT && window.RIU_CHAT.chat && window.RIU_CHAT.chat();
    if (!c || !c.fastReply) return;
    c.fastReply = false;
    if (window.RIU_CHAT.pintar) window.RIU_CHAT.pintar();
    if (window.RIU_SELECTORES && typeof window.RIU_SELECTORES.refrescar === 'function') window.RIU_SELECTORES.refrescar();
    window.dispatchEvent(new CustomEvent('riu:fast-reply', { detail: { on: false, reason: 'selector-change' } }));
  } catch (e) {}
});
