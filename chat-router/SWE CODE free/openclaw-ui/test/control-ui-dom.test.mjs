// Monta la UI REAL (bundle esbuild de src/control-ui.ts) en jsdom con un host falso: ejecuta el codigo DOM del selector, las tareas y las tools.
// No es el Control UI de OpenClaw: es la unica forma de ejecutar el DOM aqui. Se omite si jsdom no esta instalado.
import test from 'node:test';
import assert from 'node:assert/strict';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { build } from 'esbuild';

let JSDOM = null; try { ({ JSDOM } = await import('jsdom')); } catch { /* sin jsdom */ }
const AQUI = path.dirname(fileURLToPath(import.meta.url));
const saltar = JSDOM ? false : 'jsdom no instalado (npm i -D jsdom)';

test('UI en jsdom: selector central con 3 campos reales + modo + workflow + salida; elegir cambia SOLO su campo; ejecucion bloqueada con aviso; iniciar/estado/aprobar/tool llaman al backend', { skip: saltar }, async () => {
  const dom = new JSDOM('<!doctype html><body><div id="raiz"></div></body>');
  Object.assign(globalThis, { window: dom.window, document: dom.window.document, HTMLElement: dom.window.HTMLElement });
  const { outputFiles } = await build({ entryPoints: [path.join(AQUI, '..', 'src', 'control-ui.ts')], bundle: true, format: 'esm', platform: 'browser', write: false, loader: { '.css': 'empty' }, logLevel: 'silent' });
  const plugin = (await import('data:text/javascript;base64,' + Buffer.from(outputFiles[0].text).toString('base64'))).default;

  const llamadas = [], pickers = [];
  const CAP = { ok: true, http: 200, datos: { harness: 'ok', agentes: { openclaw: { disponible: true }, 'swe-agent': { disponible: true }, codex: { disponible: false, estado: 'NO INSTALADO', motivo: 'codex no esta instalado' } }, workflows: { individual: { disponible: true }, swe_code: { disponible: true } }, modelos: { 'hf/lfm2.5-350m': { disponible: true }, 'hf/qwen2.5-coder-1.5b': { disponible: true }, 'nvidia/z-ai/glm-5.3': { disponible: false, estado: 'NO DISPONIBLE EN PROVEEDOR', motivo: 'no figura en GET /models' } } } };
  const TOOLS = { ok: true, http: 200, datos: { vivo: { router: 'ok' }, tools: [{ id: 'salud', grupo: 'chat', titulo: 'Estado del Router', estado: 'DISPONIBLE', efectos: 'lectura' }, { id: 'almacen', grupo: 'almacen', titulo: 'Almacen', estado: 'DISPONIBLE', efectos: 'por_accion', acciones: ['leer', 'guardar'], lectura: ['leer'] }], gaps: [{ id: 'anclaje', motivo: 'campo de /chat/send' }] } };
  const host = {
    pluginId: 'swe-selector', signal: new AbortController().signal, connection: { connected: true }, sessions: { selectedKey: 'sesion-1' },
    request: async (m, p) => { llamadas.push([p.actionId, p.payload]); const r = p.actionId === 'capacidades' ? CAP : p.actionId === 'tools' ? TOOLS : { ok: true, http: 200, datos: { estado: 'PENDIENTE', pendiente_aprobacion: { op_id: 'op-1' } } }; return { ok: true, result: r }; },
    onEvent: () => () => {}, subscribe: () => () => {},
    components: { mountSelectPicker: (c, props) => { const h = { props, dispose() {}, update(n) { h.props = n; } }; pickers.push({ c, h }); c.append(Object.assign(document.createElement('span'), { textContent: props.accessibleLabel })); return h; } },
    ui: { registerNavigation: () => () => {}, registerPanel: () => () => {}, registerPage: (p) => { host.pagina = p; return () => {}; } },
  };
  plugin.activate(host);
  const raiz = document.getElementById('raiz');
  const vista = host.pagina.mount(raiz, { host, signal: host.signal, props: {} });
  await new Promise((ok) => setTimeout(ok, 30));
  const etiquetas = pickers.map((p) => p.h.props.accessibleLabel);
  for (const e of ['MODELO QUE RESPONDE', 'AGENTE QUE EJECUTA', 'MODELO PARA TOOL', 'WORKFLOW', 'SALIDA']) assert.ok(etiquetas.includes(e), `falta el control ${e}: ${etiquetas}`);
  assert.equal(pickers.filter(p => p.h.props.accessibleLabel === 'AGENTE QUE RESPONDE').length, 0, 'no hay selector agente ficticio');
  assert.equal(pickers.filter(p => p.h.props.accessibleLabel === 'AGENTE QUE EJECUTA').length, 1, 'un agente ejecutor real');
  assert.ok(raiz.querySelector('[aria-label="MODO AGENTICO"]'), 'falta el boton MODO AGENTICO');
  assert.equal(llamadas[0][0], 'capacidades');
  const ultimo = (etq) => pickers.filter((p) => p.h.props.accessibleLabel === etq).at(-1).h.props;
  const agentes = ultimo('AGENTE QUE EJECUTA').options.map((o) => o.label);
  assert.ok(agentes.some((l) => l.includes('codex') && l.includes('NO INSTALADO')), 'la opcion no instalada se muestra con su estado: ' + agentes);
  // salida independiente de agente_tool
  const antes = ultimo('AGENTE QUE EJECUTA').value;
  ultimo('SALIDA').onSelect('openclaw');
  assert.equal(ultimo('SALIDA').value, 'openclaw'); assert.equal(ultimo('AGENTE QUE EJECUTA').value, antes, 'cambiar la salida no cambia agente_tool');
  ultimo('AGENTE QUE EJECUTA').onSelect('codex');
  assert.equal(ultimo('SALIDA').value, 'openclaw', 'elegir Codex no cambia la salida'); assert.equal(ultimo('AGENTE QUE EJECUTA').value, 'codex', 'la eleccion no disponible queda visible');
  // modo agentico ON con codex no instalado: ejecucion bloqueada con aviso, no se envia nada
  raiz.querySelector('[aria-label="MODO AGENTICO"]').click();
  assert.match(raiz.querySelector('.swe-selector-problemas').textContent, /AGENTE QUE EJECUTA codex: NO INSTALADO/);
  const msg = raiz.querySelector('.swe-mensaje'); msg.value = 'hazlo';
  const botones = (t) => [...raiz.querySelectorAll('button')].find((b) => b.textContent === t);
  const n0 = llamadas.length;
  botones('Iniciar tarea').click(); await new Promise((ok) => setTimeout(ok, 20));
  assert.equal(llamadas.length, n0, 'seleccion no disponible: no se llama al backend');
  assert.match(raiz.querySelector('.swe-tareas .swe-salida').textContent, /SELECCION_NO_DISPONIBLE/);
  // con agente disponible si se inicia, con contrato TareaSWE y aprobacion false
  ultimo('AGENTE QUE EJECUTA').onSelect('swe-agent');
  botones('Iniciar tarea').click(); await new Promise((ok) => setTimeout(ok, 20));
  const [id, tarea] = llamadas.at(-1);
  assert.equal(id, 'iniciar'); assert.equal(tarea.origen, 'openclaw'); assert.equal(tarea.aprobacion, false); assert.equal(tarea.agente_tool, 'swe-agent'); assert.equal(tarea.modo_agentico, true); assert.equal(Object.keys(tarea).length, 15);
  botones('Estado').click(); await new Promise((ok) => setTimeout(ok, 20));
  assert.deepEqual(llamadas.at(-1)[0], 'estado'); assert.equal(llamadas.at(-1)[1].task_id, tarea.task_id);
  // aprobar: operador + token tecleados; el token se borra del campo tras enviar
  const inputs = raiz.querySelectorAll('.swe-aprobar input'); inputs[0].value = 'op-1'; inputs[1].value = 'ana'; inputs[2].value = 'secreto-de-ana';
  botones('Aprobar').click(); await new Promise((ok) => setTimeout(ok, 20));
  const ap = llamadas.at(-1); assert.equal(ap[0], 'aprobar'); assert.deepEqual([ap[1].operador, ap[1].token_operador, ap[1].op_id], ['ana', 'secreto-de-ana', 'op-1']);
  assert.equal(inputs[2].value, '', 'el token no se queda en el campo'); assert.ok(!raiz.textContent.includes('secreto-de-ana'));
  // tools
  assert.ok(llamadas.some(([i]) => i === 'tools'), 'carga el catalogo de tools');
  assert.match(raiz.querySelector('.swe-gaps').textContent, /GAP anclaje/);
  botones('Ejecutar tool').click(); await new Promise((ok) => setTimeout(ok, 20));
  assert.deepEqual(llamadas.at(-1)[0], 'tool'); assert.equal(llamadas.at(-1)[1].id, 'salud');
  vista.dispose(); assert.equal(raiz.children.length, 0, 'dispose limpia el DOM');
});
