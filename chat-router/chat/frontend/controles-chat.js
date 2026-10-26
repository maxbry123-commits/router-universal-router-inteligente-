// controles-chat.js — botones del chat: paralelo, Agente tool, LLM tool y Proyectos
// Extraído de panel-chat.js sin cambiar la lógica: recibe lo que usa por ctx y devuelve lo que otros bloques necesitan.
export function montarControlesChat(ctx) {
  const { q, chat, guardar, chatTools, pintarMotor, tell } = ctx;
  // >>> MODOS <<< T6: boton paralelo — multi-select de hasta 6 modelos Team qwen; el envio sale a cada uno
  const pintarParalelo = () => { const b = q("#btn-paralelo"); if (b) { b.classList.toggle("sel-on", !!chat().paralelo); b.setAttribute("aria-pressed", String(!!chat().paralelo)); b.textContent = "Paralelo " + (chat().paralelo ? "ON" : "OFF"); } };
  const bpar = q("#btn-paralelo"); if (bpar) { const det = q("#btn-detener"); if (det && det.parentNode) det.parentNode.insertBefore(bpar, det); bpar.addEventListener("click", () => { chat().paralelo = !chat().paralelo; pintarParalelo(); guardar(); }); }
  pintarParalelo();
  // Controles: «Agente tool» y «LLM tool» son los mismos permisos del servidor que los chips Agentes e IA (un solo estado, sin copias locales)
  const bLock = q('#btn-agent-access-lock'), bLlm = q("#btn-llm-tool");
  const pintarTools = (ia, ag) => {
    if (bLock) { bLock.textContent = (ag ? '🔓' : '🔒') + ' Agente tool ' + (ag ? 'ON' : 'OFF'); bLock.setAttribute('aria-pressed', String(ag)); bLock.title = 'Permitir que el modelo delegue en agentes (igual que el chip Agentes)'; }
    if (bLlm) { bLlm.textContent = '🧠 LLM tool ' + (ia ? 'ON' : 'OFF'); bLlm.classList.toggle('sel-on', ia); bLlm.setAttribute('aria-pressed', String(ia)); bLlm.title = 'Permitir que el modelo consulte otros modelos (igual que el chip IA)'; }
  };
  pintarTools(!!chatTools.llm_tool, !!chatTools.agente_tool);  // el estado del servidor pudo llegar antes de este listener
  if (window.RIU_ACCION) window.RIU_ACCION('agent_access_lock', { sesion: chat().sesion }).then((r) => { if (r && 'ia_locked' in r) pintarTools(!r.ia_locked, !r.agentes_locked); }).catch(() => {});  // estado real al abrir; con 401 pide la clave (acceso-clave.js)
  window.addEventListener('riu:ia', (e) => pintarTools(!!e.detail.ia, !!e.detail.agentes));
  const pulsar = (sel) => () => { const chip = document.querySelector(sel); if (chip) chip.click(); else tell('GAP: falta el botón ' + sel); };
  if (bLock) bLock.addEventListener('click', pulsar('#btn-agentes'));
  if (bLlm) bLlm.addEventListener('click', pulsar('#btn-tools'));
  pintarMotor();
  const bpr = q("#btn-proyectos"); if (bpr) bpr.addEventListener("click", () => { if (window.RIU_ANCLA_ABRIR) window.RIU_ANCLA_ABRIR("proyecto"); });  // misma ventana-ancla, objetivo Proyecto
  window.addEventListener("riu:fast-reply-toggle", window.__riuFastH);
}
