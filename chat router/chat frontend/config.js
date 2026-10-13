// Configuracion del chat (solo interfaz; el codigo vive en GitHub y el computo en HF).
// La interfaz abre sin pedir clave. El Router funciona en HF CPU de 16 GB; las claves permanecen en el servidor.
window.RIU_CONFIG = {
  routerStopped: false,
  apiBase: 'https://6ac41820404719ba376595fb--8000.hf.jobs',
  liveUrl: 'https://raw.githubusercontent.com/maxbry123-commits/router-universal-router-inteligente-/main/router%20inteligente%20universal/LIVE_URL.json',
  harnessUrl: 'https://6ac41820404719ba376595fb--8000.hf.jobs/plugins/puente_chat/call',
  authHeader: 'X-API-Key',
  defecto: 'nv-nemotron-super',
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

// GAP fast-reply: limpia una sola vez estados antiguos que podian dejar FAST activo sin indicarlo.
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

// Controles del chat: barra fina debajo de Chat/Canvas/Seguimiento/Archivos.
// Tiene ciclo de vida: al salir de Chat se elimina; al volver se monta con los controles de la nueva instancia.
(() => {
  let timer = 0;
  const chatActivo = () => !!document.querySelector('#navigation [data-view="chat"][aria-current="page"]');
  const posicionar = () => {
    const movil = matchMedia('(max-width:720px)').matches;
    const nav = document.querySelector('.sidebar');
    const top = movil && nav ? Math.max(0, Math.round(nav.getBoundingClientRect().bottom)) : 8;
    document.documentElement.style.setProperty('--chat-controls-top', top + 'px');
  };

  const crearDock = (tabs, fields) => {
    const viejo = document.getElementById('chat-controls-dock');
    if (viejo) viejo.remove();
    const dock = document.createElement('div'); dock.id = 'chat-controls-dock'; dock.className = 'chat-controls-dock';
    const toggle = document.createElement('button');
    toggle.type = 'button'; toggle.id = 'chat-controls-toggle'; toggle.className = 'chat-controls-toggle';
    toggle.setAttribute('aria-expanded', 'false'); toggle.setAttribute('aria-controls', 'chat-controls-panel'); toggle.textContent = 'Controles ▾';
    const panel = document.createElement('div'); panel.id = 'chat-controls-panel'; panel.className = 'chat-controls-panel'; panel.setAttribute('aria-hidden', 'true');
    panel.append(tabs, fields); dock.append(toggle, panel); document.body.append(dock); posicionar();
    const abrir = (on) => {
      dock.classList.toggle('open', on); toggle.setAttribute('aria-expanded', String(on));
      toggle.textContent = on ? 'Controles ▴' : 'Controles ▾'; panel.setAttribute('aria-hidden', String(!on)); posicionar();
    };
    toggle.addEventListener('click', () => abrir(!dock.classList.contains('open')));
    document.addEventListener('keydown', (e) => { if (e.key === 'Escape' && dock.isConnected) abrir(false); });
  };

  const reconciliar = () => {
    clearTimeout(timer);
    timer = setTimeout(() => {
      const dock = document.getElementById('chat-controls-dock');
      if (!chatActivo()) { if (dock) dock.remove(); return; }
      const panelRaiz = document.getElementById('panel');
      // Un #chat-tabs dentro de #panel es una instancia nueva que aun no fue movida al dock.
      const tabsNuevos = panelRaiz && panelRaiz.querySelector('#chat-tabs');
      const fieldsNuevos = tabsNuevos && tabsNuevos.nextElementSibling && tabsNuevos.nextElementSibling.classList.contains('fields') ? tabsNuevos.nextElementSibling : null;
      if (tabsNuevos && fieldsNuevos) { crearDock(tabsNuevos, fieldsNuevos); return; }
      // Si Chat sigue activo y el dock ya contiene sus nodos, solo recalcular posicion.
      if (dock && dock.querySelector('#chat-tabs')) posicionar();
    }, 30);
  };

  const iniciar = () => {
    const panelRaiz = document.getElementById('panel');
    const nav = document.getElementById('navigation');
    if (panelRaiz) new MutationObserver(reconciliar).observe(panelRaiz, { childList: true, subtree: false });
    if (nav) new MutationObserver(reconciliar).observe(nav, { attributes: true, subtree: true, attributeFilter: ['aria-current'] });
    addEventListener('resize', posicionar, { passive: true });
    addEventListener('orientationchange', () => setTimeout(posicionar, 120), { passive: true });
    reconciliar();
  };
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', iniciar, { once: true }); else iniciar();
})();
