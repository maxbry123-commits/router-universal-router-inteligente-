// control-ui.ts — UI nativa del plugin (corre en el navegador del Control UI de OpenClaw). Mecanismo oficial: defineControlUiPlugin + registerPage/registerNavigation/registerPanel y
// createFeatureClient para hablar con el backend del plugin. NO toca el DOM de YAIWES, no importa internos del Control UI y NO tiene claves: el bridge se llama desde el backend.
import { defineControlUiPlugin, type ControlUiHost } from 'openclaw/plugin-sdk/control-ui';
import { createFeatureClient } from 'openclaw/plugin-sdk/feature-contract';
import { contract } from './contract.js';
import {
  SELECCION_DEFECTO, ETIQUETAS_SALIDA, ETIQUETAS_WORKFLOW, SALIDAS, aplicar, camposFijos, estadoOpcion, normalizarCapacidades, serializarSeleccion, validarSeleccion,
  type Capacidades, type Seleccion,
} from './selector-core.js';
import './control-ui.css';

// Estado compartido entre la pagina y el panel (una sola seleccion; se conserva al cerrar y volver a abrir la vista mientras viva la pestana).
let seleccion: Seleccion = { ...SELECCION_DEFECTO };
let capacidades: Capacidades = normalizarCapacidades(null);
let tools: { vivo?: { router?: string }; tools: ToolInfo[]; gaps: { id: string; motivo: string; usar_con?: string }[] } = { tools: [], gaps: [] };
let tareaActual: { task_id: string; sesion: string; proyecto: string } | null = null;
type ToolInfo = { id: string; grupo: string; titulo: string; estado: string; efectos: string; acciones?: string[]; lectura?: string[] };

const el = <K extends keyof HTMLElementTagNameMap>(tag: K, clase?: string, texto?: string): HTMLElementTagNameMap[K] => {
  const e = document.createElement(tag); if (clase) e.className = clase; if (texto !== undefined) e.textContent = texto; return e;
};
const resumen = (o: unknown): string => { try { return JSON.stringify(o, null, 2).slice(0, 6000); } catch { return String(o).slice(0, 6000); } };

function montarSelector(container: HTMLElement, host: ControlUiHost, signal: AbortSignal, onChange: () => void) {
  const feature = createFeatureClient(contract, host);
  const raiz = el('section', 'swe-selector');
  const titulo = el('h2', 'swe-selector-titulo', 'Selector central SWE');
  const estado = el('output', 'swe-selector-estado'); estado.setAttribute('aria-live', 'polite');
  const filas = el('div', 'swe-selector-filas');
  const problemas = el('ul', 'swe-selector-problemas');
  const actualizar = el('button', 'swe-btn', 'Actualizar disponibilidad'); actualizar.type = 'button';
  const handles: { dispose?: () => void }[] = [];
  const picker = (padre: HTMLElement, rotulo: string, etiqueta: string) => { const w = el('label', 'swe-campo'); w.append(el('span', 'swe-campo-t', rotulo)); const c = el('div', 'swe-campo-c'); w.append(c); w.setAttribute('aria-label', etiqueta); padre.append(w); return c; };

  const opciones = (tipo: 'agente' | 'workflow' | 'modelo', ids: string[], modelo?: string) => ids.map((id) => {
    const v = estadoOpcion(capacidades, tipo, id, modelo), n = (tipo === 'modelo' ? capacidades.modelos[id]?.nombre : undefined) ?? (tipo === 'workflow' ? ETIQUETAS_WORKFLOW[id] : undefined) ?? id;
    return { value: id, label: v.ok && v.estado === 'DISPONIBLE' ? n : `${n} - ${v.estado}`, description: v.motivo || undefined };  // la eleccion queda visible con su estado real; no se bloquea la lista, se bloquea la ejecucion
  });
  const ids = (t: 'agentes' | 'workflows' | 'modelos', actual: string) => { const k = Object.keys(capacidades[t]); return k.includes(actual) ? k : [actual, ...k]; };
  const campos: { rotulo: string; fila: 'RESPONDE' | 'EJECUTA'; clave: keyof Seleccion; lista: () => ReturnType<typeof opciones> }[] = [
    // El backend responde con modelo_responde; agente_responde es legado no ejecutado.
    // Mostrar solo agente_tool, que realmente pasa al dispatcher via Harness.
    { fila: 'RESPONDE', rotulo: 'Modelo que responde', clave: 'modelo_responde', lista: () => opciones('modelo', ids('modelos', seleccion.modelo_responde)) },
    { fila: 'EJECUTA', rotulo: 'Agente que ejecuta', clave: 'agente_tool', lista: () => opciones('agente', ids('agentes', seleccion.agente_tool), seleccion.modelo_tool) },
    { fila: 'EJECUTA', rotulo: 'Modelo para tool', clave: 'modelo_tool', lista: () => opciones('modelo', ids('modelos', seleccion.modelo_tool)) },
  ];
  const render = () => {
    handles.splice(0).forEach((h) => h.dispose?.());
    filas.replaceChildren();
    const fijos = camposFijos(seleccion.workflow);
    for (const nombre of ['RESPONDE', 'EJECUTA'] as const) {
      const f = el('div', 'swe-fila'); f.append(el('strong', 'swe-fila-t', nombre));
      for (const c of campos.filter((x) => x.fila === nombre)) {
        const dest = picker(f, c.rotulo + (fijos.has(c.clave) ? ' (fijo por el workflow)' : ''), c.rotulo.toUpperCase());
        handles.push(host.components.mountSelectPicker(dest, { options: c.lista(), value: String(seleccion[c.clave]), accessibleLabel: c.rotulo.toUpperCase(), searchable: true, disabled: fijos.has(c.clave),
          onSelect: (v) => { seleccion = aplicar(seleccion, { [c.clave]: v } as Partial<Seleccion>); onChange(); render(); } }));  // cada campo cambia SOLO el suyo
      }
      filas.append(f);
    }
    const abajo = el('div', 'swe-fila');
    const modo = el('button', 'swe-btn swe-toggle', `Modo agentico: ${seleccion.modo_agentico ? 'ON' : 'OFF'}`); modo.type = 'button'; modo.setAttribute('aria-pressed', String(seleccion.modo_agentico)); modo.setAttribute('aria-label', 'MODO AGENTICO');
    modo.onclick = () => { seleccion = aplicar(seleccion, { modo_agentico: !seleccion.modo_agentico }); onChange(); render(); };
    abajo.append(modo);
    const wf = picker(abajo, 'Workflow', 'WORKFLOW');
    handles.push(host.components.mountSelectPicker(wf, { options: opciones('workflow', ids('workflows', seleccion.workflow)), value: seleccion.workflow, accessibleLabel: 'WORKFLOW', onSelect: (v) => { seleccion = aplicar(seleccion, { workflow: v }); onChange(); render(); } }));
    const sal = picker(abajo, 'Salida', 'SALIDA');
    handles.push(host.components.mountSelectPicker(sal, { options: SALIDAS.map((s) => ({ value: s, label: ETIQUETAS_SALIDA[s] })), value: seleccion.salida, accessibleLabel: 'SALIDA', onSelect: (v) => { seleccion = aplicar(seleccion, { salida: v as Seleccion['salida'] }); onChange(); render(); } }));  // la salida NO toca agente_tool
    filas.append(abajo);
    const v = validarSeleccion(seleccion, capacidades);
    problemas.replaceChildren(...v.problemas.map((p) => el('li', 'swe-problema', p)));
    estado.textContent = `Harness: ${capacidades.harness}${v.ok ? '' : ' - ejecucion bloqueada hasta resolver los avisos'}`;
  };
  const cargar = async () => {
    estado.textContent = 'Consultando disponibilidad...';
    try {
      const r = await feature.invoke('capacidades', {});
      signal.throwIfAborted();
      capacidades = normalizarCapacidades(r.ok ? r.datos : null);
      if (!r.ok) estado.textContent = `Harness: no disponible (${r.codigo ?? 'error'})`;
    } catch (e) { if (!signal.aborted) estado.textContent = String(e); }
    if (!signal.aborted) render();
  };
  actualizar.onclick = () => { void cargar(); };  // actualizar disponibilidad SIN recargar la pagina
  raiz.append(titulo, filas, problemas, el('div', 'swe-fila', ''), estado);
  raiz.children[3]!.append(actualizar);
  container.append(raiz);
  render(); void cargar();
  return { raiz, recargar: cargar, dispose: () => { handles.splice(0).forEach((h) => h.dispose?.()); raiz.remove(); } };
}

function montarTareas(container: HTMLElement, host: ControlUiHost, signal: AbortSignal) {
  const feature = createFeatureClient(contract, host);
  const s = el('section', 'swe-tareas');
  const msg = el('textarea', 'swe-mensaje'); msg.placeholder = 'Mensaje / objetivo de la tarea'; msg.setAttribute('aria-label', 'Mensaje de la tarea');
  const botones = el('div', 'swe-fila');
  const salida = el('output', 'swe-salida'); salida.setAttribute('aria-live', 'polite');
  const mk = (t: string, f: () => Promise<void>) => { const b = el('button', 'swe-btn', t); b.type = 'button'; b.onclick = async () => { b.disabled = true; try { await f(); } catch (e) { if (!signal.aborted) salida.textContent = String(e); } finally { if (!signal.aborted) b.disabled = false; } }; return b; };
  const mostrar = (r: { ok: boolean; codigo?: string; datos?: unknown }) => { if (!signal.aborted) salida.textContent = r.ok ? resumen(r.datos) : `ERROR ${r.codigo ?? ''}\n${resumen(r.datos ?? '')}`; };
  const ref = () => (tareaActual ? { task_id: tareaActual.task_id, sesion: tareaActual.sesion, proyecto: tareaActual.proyecto } : null);
  const iniciar = mk('Iniciar tarea', async () => {
    const v = validarSeleccion(seleccion, capacidades);
    if (!v.ok) { salida.textContent = `GAP: SELECCION_NO_DISPONIBLE\n${v.problemas.join('\n')}`; return; }  // no se envia nada ni se cambia en silencio de modelo o agente
    if (!msg.value.trim()) { salida.textContent = 'MENSAJE_VACIO'; return; }
    const { tarea } = serializarSeleccion({ sel: seleccion, mensaje: msg.value, sesion: host.sessions.selectedKey });
    const r = await feature.invoke('iniciar', tarea); if (r.ok) tareaActual = { task_id: tarea.task_id, sesion: tarea.sesion, proyecto: tarea.proyecto }; mostrar(r);
  });
  const conRef = (op: 'avanzar' | 'estado' | 'reanudar') => mk(op[0]!.toUpperCase() + op.slice(1), async () => { const r0 = ref(); if (!r0) { salida.textContent = 'Primero inicia una tarea'; return; } mostrar(await feature.invoke(op, r0)); });
  botones.append(iniciar, conRef('avanzar'), conRef('estado'), conRef('reanudar'));
  // Aprobar: un operador REAL. Su nombre y SU token se teclean aqui, viajan una vez por la conexion autenticada del Gateway y no se guardan ni se muestran.
  const ap = el('details', 'swe-aprobar'); ap.append(el('summary', undefined, 'Aprobar operacion pendiente (operador identificado)'));
  const op_id = el('input'); op_id.placeholder = 'op_id pendiente'; op_id.setAttribute('aria-label', 'op_id');
  const oper = el('input'); oper.placeholder = 'operador'; oper.autocomplete = 'off'; oper.setAttribute('aria-label', 'Operador');
  const tok = el('input'); tok.type = 'password'; tok.placeholder = 'token individual del operador'; tok.autocomplete = 'off'; tok.setAttribute('aria-label', 'Token del operador');
  const bap = mk('Aprobar', async () => {
    const r0 = ref(); if (!r0) { salida.textContent = 'Primero inicia una tarea'; return; }
    const r = await feature.invoke('aprobar', { ...r0, op_id: op_id.value.trim(), operador: oper.value.trim(), token_operador: tok.value }); tok.value = ''; mostrar(r);
  });
  ap.append(op_id, oper, tok, bap);
  s.append(msg, botones, ap, salida);
  container.append(s);
  return { dispose: () => s.remove() };
}

function montarTools(container: HTMLElement, host: ControlUiHost, signal: AbortSignal) {
  const feature = createFeatureClient(contract, host);
  const s = el('section', 'swe-tools'); s.append(el('h3', undefined, 'Tools del chat Yaiwes (motores, Loop, cola, watchdog, almacen, memoria...)'));
  const lista = el('div', 'swe-tools-sel'), accion = el('div', 'swe-tools-acc'), args = el('textarea', 'swe-tools-args'); args.value = '{}'; args.setAttribute('aria-label', 'Argumentos JSON');
  const gaps = el('ul', 'swe-gaps'), salida = el('output', 'swe-salida'); salida.setAttribute('aria-live', 'polite');
  const oper = el('input'); oper.placeholder = 'operador (solo tools con efectos)'; oper.autocomplete = 'off'; const tok = el('input'); tok.type = 'password'; tok.placeholder = 'token del operador'; tok.autocomplete = 'off';
  let elegido = '', accionElegida = '';
  const handles: { dispose?: () => void }[] = [];
  const pintar = () => {
    handles.splice(0).forEach((h) => h.dispose?.()); lista.replaceChildren(); accion.replaceChildren();
    if (!elegido && tools.tools[0]) elegido = tools.tools[0].id;
    handles.push(host.components.mountSelectPicker(lista, { options: tools.tools.map((t) => ({ value: t.id, label: `${t.titulo} - ${t.estado}`, description: `${t.grupo} - ${t.efectos}` })), value: elegido, accessibleLabel: 'TOOL', searchable: true, onSelect: (v) => { elegido = v; accionElegida = ''; pintar(); } }));
    const t = tools.tools.find((x) => x.id === elegido);
    if (t?.acciones) { if (!accionElegida) accionElegida = t.acciones[0]!; handles.push(host.components.mountSelectPicker(accion, { options: t.acciones.map((a) => ({ value: a, label: a, description: t.lectura?.includes(a) ? 'lectura' : 'con efectos (operador)' })), value: accionElegida, accessibleLabel: 'ACCION', onSelect: (v) => { accionElegida = v; } })); }
    gaps.replaceChildren(...tools.gaps.map((g) => el('li', 'swe-gap', `GAP ${g.id}: ${g.motivo}`)));
  };
  const cargar = mkBtn('Actualizar tools', async () => {
    const r = await feature.invoke('tools', {}); signal.throwIfAborted();
    if (r.ok && r.datos && typeof r.datos === 'object') { const d = r.datos as typeof tools; tools = { vivo: d.vivo, tools: Array.isArray(d.tools) ? d.tools : [], gaps: Array.isArray(d.gaps) ? d.gaps : [] }; pintar(); salida.textContent = `Router: ${tools.vivo?.router ?? '?'}`; }
    else salida.textContent = `ERROR ${r.codigo ?? ''}`;
  }, signal, salida);
  const ejecutar = mkBtn('Ejecutar tool', async () => {
    let a: Record<string, unknown> = {}; try { a = JSON.parse(args.value || '{}'); } catch { salida.textContent = 'ARGS_JSON_INVALIDO'; return; }
    const r = await feature.invoke('tool', { id: elegido, ...(accionElegida ? { accion: accionElegida } : {}), args: a, ...(oper.value && tok.value ? { operador: oper.value.trim(), token_operador: tok.value } : {}) }); tok.value = '';
    salida.textContent = r.ok ? resumen(r.datos) : `ERROR ${r.codigo ?? ''}`;
  }, signal, salida);
  s.append(cargar, lista, accion, args, oper, tok, ejecutar, gaps, salida);
  container.append(s); pintar(); cargar.click();
  return { dispose: () => { handles.splice(0).forEach((h) => h.dispose?.()); s.remove(); } };
}
function mkBtn(texto: string, f: () => Promise<void>, signal: AbortSignal, salida: HTMLElement): HTMLButtonElement {
  const b = el('button', 'swe-btn', texto); b.type = 'button';
  b.onclick = async () => { b.disabled = true; try { await f(); } catch (e) { if (!signal.aborted) salida.textContent = String(e); } finally { if (!signal.aborted) b.disabled = false; } };
  return b;
}

const montarTodo = (container: HTMLElement, context: { readonly host: ControlUiHost; readonly signal: AbortSignal }) => {
  const host = context.host;
  const sel = montarSelector(container, host, context.signal, () => {});
  const tar = montarTareas(container, host, context.signal);
  const tls = montarTools(container, host, context.signal);
  return { dispose: () => { sel.dispose(); tar.dispose(); tls.dispose(); } };
};

export default defineControlUiPlugin({
  id: contract.pluginId,
  activate(host) {
    const quitar = [
      host.ui.registerNavigation({ id: 'swe', label: 'SWE Selector', page: { id: 'swe' }, icon: 'settings' }),
      host.ui.registerPage({ id: 'swe', label: 'SWE Selector', mount: (c, ctx) => montarTodo(c, ctx) }),
      host.ui.registerPanel({ id: 'swe-panel', label: 'SWE', mount: (c, ctx) => montarTodo(c, ctx) }),
    ];
    return () => quitar.forEach((q) => q());
  },
});
