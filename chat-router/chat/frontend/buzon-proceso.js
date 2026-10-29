import { node } from "./api.js";
// buzon-proceso.js — buzón en vivo (Director → proceso) y cola de pendientes (modelo → Director)
// Extraído de panel-chat.js sin cambiar la lógica: recibe lo que usa por ctx y devuelve lo que otros bloques necesitan.
export function montarBuzon(ctx) {
  const { q, chat, abajo, ajustarAlturaEditor, burbuja } = ctx;
  // ---- DSL G19: buzon en vivo (Director -> proceso) + cola de pendientes (modelo -> Director) ----
  const fqCall = async (acc, payload) => {  // buzon vive en fichas_qwen, no en puente_chat
    const base = ((window.RIU_CONFIG || {}).harnessUrl || '').replace('puente_chat', 'fichas_qwen');
    if (!base) return null;
    const h = { 'Content-Type': 'application/json' };
    const pw = sessionStorage.getItem('riu_clave');
    if (pw) { h['X-API-Key'] = pw; h['X-Chat-Password'] = pw; }
    try {
      const r = await fetch(base + '/' + acc, { method: 'POST', headers: h, body: JSON.stringify(payload || {}) });
      return await r.json().catch(() => null);
    } catch (e) { return null; }
  };
  const bar = document.createElement('div');
  bar.id = 'buzon-bar';
  bar.hidden = true;
  bar.style.cssText = 'display:none;gap:6px;align-items:center;padding:6px 10px;border-top:1px solid var(--borde,#333);font-size:12px;flex-wrap:wrap';
  if (!document.getElementById('buzon-css')) {
    const st = document.createElement('style');
    st.id = 'buzon-css';
    st.textContent = '#buzon-bar{display:none !important}';
    document.head.append(st);
  }
  bar.innerHTML =
    '<span style="opacity:.7">Proceso:</span>' +
    '<select id="buzon-tipo" style="font:inherit"><option value="instruccion">instrucción</option><option value="tarea">tarea</option><option value="prioridad">prioridad</option><option value="nueva">nueva tarea aparte</option></select>' +
    '<button type="button" id="buzon-pausa" style="font:inherit">Pausa</button>' +
    '<button type="button" id="buzon-continuar" style="font:inherit">Continuar</button>' +
    '<button type="button" id="buzon-cancelar" style="font:inherit">Cancelar</button>' +
    '<details id="buzon-cola" style="font:inherit"><summary>Cola</summary><div id="buzon-cola-txt" style="max-height:160px;overflow:auto;padding:4px"></div></details>';
  const comp = q('#composer');
  if (comp && comp.parentNode) comp.parentNode.insertBefore(bar, comp.nextSibling);
  const pidActivo = () => { const v = window.RIU_PENDIENTE && window.RIU_PENDIENTE(chat().sesion); return v && v.pid ? v.pid : null; };
  const buzonEnvio = async (tipo, texto) => {
    const pid = pidActivo(); if (!pid) return null;
    const r = await fqCall('buzon_enviar', { proceso_id: pid, tipo, texto });
    return (r && r.result) ? r.result : r;
  };
  const boton = (id, tipo) => {
    const b = bar.querySelector(id);
    if (b) b.addEventListener('click', async () => {
      const r = await buzonEnvio(tipo, tipo);
      const ack = (r && (r.se_aplica_en || r.ok)) ? ('Recibido, se aplica en ' + (r.se_aplica_en || 'la siguiente vuelta')) : 'Enviado: ' + tipo;
      chat().hist.append(node('div', ack, 'item message meta')); abajo(chat());
    });
  };
  boton('#buzon-pausa', 'pausa'); boton('#buzon-continuar', 'continuar'); boton('#buzon-cancelar', 'cancelar');
  const sel = bar.querySelector('#buzon-tipo');
  const colaTxt = bar.querySelector('#buzon-cola-txt');
  // selector del input: si hay proceso en curso y el tipo no es "nueva", el mensaje va al buzon sin reiniciar
  if (comp) comp.addEventListener('submit', async (ev) => {
    const pid = pidActivo();
    if (!pid || bar.hidden || !sel || sel.value === 'nueva') return;  // la franja no se muestra: un chat normal no se desvía al buzón
    ev.preventDefault(); ev.stopImmediatePropagation();  // al buzon: NO lanza otro chat_async
    const input = q('#message'); const texto = (input.value || '').trim();
    if (!texto) return;
    const r = await buzonEnvio(sel.value, texto);
    input.value = ''; ajustarAlturaEditor();
    const ack = (r && r.se_aplica_en) ? ('Recibido, se aplica en ' + r.se_aplica_en) : 'Recibido';
    chat().hist.append(burbuja(texto, 'user')); chat().hist.append(node('div', ack, 'item message meta')); abajo(chat());
  }, true);  // capture: corre antes del handler normal de envio
  // panel "Cola": estado_objetivo cada 3 s mientras haya proceso (tareas con estado + preguntas del modelo)
  bar.hidden = true;
  setInterval(async () => {
    const pid = pidActivo();
    if (!pid || bar.hidden) return;
    const est = await fqCall('estado_objetivo', { proceso_id: pid });
    const e = est && (est.result || est);
    if (!e || !colaTxt || !bar.querySelector('#buzon-cola').open) return;
    const tareas = (e.tareas || []).map(t => '- ' + (t.estado || '?') + ' · ' + (t.texto || t.id || '')).join('\n');
    const preg = (e.preguntas || e.pendientes || []);
    colaTxt.textContent = '';  // DSL A07.1: DOM con textContent/createElement — el texto del modelo NUNCA entra por innerHTML
    const pre = document.createElement('pre');
    pre.style.cssText = 'margin:0;white-space:pre-wrap';
    pre.textContent = 'vuelta ' + (e.vuelta ?? '?') + '\n' + (tareas || '(sin tareas)');
    colaTxt.appendChild(pre);
    for (const pd of preg) {
      const d = document.createElement('div'); d.style.marginTop = '4px';
      d.appendChild(document.createTextNode('P: ' + (pd.pregunta || pd) + ' '));
      const inp = document.createElement('input'); inp.dataset.pid = pd.id || ''; inp.placeholder = 'respuesta'; inp.style.cssText = 'font:inherit;width:60%';
      const bt = document.createElement('button'); bt.dataset.resp = pd.id || ''; bt.textContent = 'Responder'; bt.style.font = 'inherit';
      d.appendChild(inp); d.appendChild(bt); colaTxt.appendChild(d);
    }
    colaTxt.querySelectorAll('button[data-resp]').forEach(b => b.addEventListener('click', async () => {
      const inp = colaTxt.querySelector('input[data-pid="' + b.dataset.resp + '"]');
      await fqCall('responder_pendiente', { id: b.dataset.resp, respuesta: inp ? inp.value : '' });
    }));
  }, 3000);
}
