// chat-fast-visual.js — fuente visual final del botón ⚡.
// fastReply pertenece al Chat, pero solo el selector ACTIVO puede mostrar su rayo como ON.
export function instalarFastVisual({ root }) {
  if (window.__riuFastVisual) return;
  window.__riuFastVisual = true;
  const pintar = () => {
    const activo = window.RIU_SELECTORES && window.RIU_SELECTORES.activo;
    let fast = false;
    try { fast = !!(window.RIU_CHAT && window.RIU_CHAT.chat && window.RIU_CHAT.chat().fastReply); } catch (e) {}
    root.querySelectorAll('.sel-fast').forEach((b) => {
      const on = fast && !!activo && b.dataset.selector === activo;
      b.classList.toggle('on', on);
      b.setAttribute('aria-pressed', String(on));
    });
  };
  const despues = () => setTimeout(pintar, 0);
  window.addEventListener('riu:fast-reply', despues);
  window.addEventListener('riu:selector-activo', despues);
  window.addEventListener('riu:selector-qwen', despues);
  root.addEventListener('click', (e) => { if (e.target.closest('.sel-fast,.sel-on,.chat-tabs')) despues(); });
  despues();
}
