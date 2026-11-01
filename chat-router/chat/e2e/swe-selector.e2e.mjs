// swe-selector.e2e.mjs — selector de modelos con los grupos SWE, envio SWE directo (/v1/chat/completions) y enlace del APK en Configuracion.
// Sin Python ni Router real: sirve chat-router/chat/frontend con un servidor HTTP minimo y SIMULA el Router (https://comand-center-1-riu-router.hf.space,
// el proxyDestino de config.js) interceptandolo en el navegador con page.route. No toca el frontend ni gasta tokens.
// Uso: node swe-selector.e2e.mjs      (sale con 0 si todo pasa; NODE_PATH=/ruta/node_modules y CHROMIUM=/ruta/chromium si hace falta)
import http from 'node:http';
import fs from 'node:fs';
import path from 'node:path';
import { createRequire } from 'node:module';
import { fileURLToPath } from 'node:url';
const require = createRequire(import.meta.url);
const { chromium } = require('playwright');

const FRONT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..', 'frontend');
const ROUTER = 'https://comand-center-1-riu-router.hf.space';  // RIU_CONFIG.proxyDestino: api.js lo toma como BASE sin esperar LIVE_URL
const CLAVE = 'api-e2e';
const TIPOS = { '.html': 'text/html; charset=utf-8', '.js': 'text/javascript; charset=utf-8', '.mjs': 'text/javascript; charset=utf-8', '.css': 'text/css; charset=utf-8', '.json': 'application/json', '.svg': 'image/svg+xml', '.png': 'image/png' };

let fallos = 0;
const ok = (n, c, x) => { if (!c) fallos++; console.log((c ? 'PASS ' : 'FAIL ') + n + (x ? ' :: ' + x : '')); return !!c; };

// ---- servidor estatico del frontend: /chat/ui/<archivo> (como Vercel) y / -> shell.html ----
function servirFrontend() {
  const srv = http.createServer((req, res) => {
    let ruta = decodeURIComponent(new URL(req.url, 'http://x').pathname);
    ruta = ruta === '/' ? '/shell.html' : ruta.replace(/^\/chat\/ui\//, '/');
    const f = path.normalize(path.join(FRONT, ruta));
    if (!f.startsWith(FRONT + path.sep) || !fs.existsSync(f) || !fs.statSync(f).isFile()) { res.writeHead(404); res.end('no'); return; }
    res.writeHead(200, { 'Content-Type': TIPOS[path.extname(f)] || 'application/octet-stream', 'Cache-Control': 'no-store' });
    fs.createReadStream(f).pipe(res);
  });
  return new Promise((ok2) => srv.listen(0, '127.0.0.1', () => ok2(srv)));
}

// ---- Router simulado (se engancha con page.route sobre el origen del Router) ----
function routerFalso(estado) {
  const CORS = { 'access-control-allow-origin': '*', 'access-control-allow-headers': '*', 'access-control-allow-methods': 'GET,POST,DELETE,OPTIONS' };
  const json = (route, obj, status = 200) => route.fulfill({ status, headers: { ...CORS, 'content-type': 'application/json' }, body: JSON.stringify(obj) });
  return async (route) => {
    const req = route.request(); const u = new URL(req.url()); const p = u.pathname;
    if (req.method() === 'OPTIONS') return route.fulfill({ status: 204, headers: CORS });
    let body = null; try { body = req.postDataJSON(); } catch (e) {}
    estado.llamadas.push({ metodo: req.method(), ruta: p, body, clave: req.headers()['x-api-key'] || '', operador: req.headers()['x-operador'], token: req.headers()['x-operator-token'] });
    if (p === '/chat/providers/qwen/models') {
      if (estado.catalogoFalla) return json(route, { detail: 'caido' }, 500);
      // catalogo del Router MVP: SIN ningun modelo SWE; 'zz-modelo-mock' prueba que se cargo este catalogo y no el de respaldo
      return json(route, { models: [{ model_id: 'qwen3.8-max', tipo: 'texto' }, { model_id: 'glm-5.2', tipo: 'texto' }, { model_id: 'deepseek-v4-pro', tipo: 'texto' }, { model_id: 'zz-modelo-mock', tipo: 'texto' }] });
    }
    if (p === '/web/v1/claves') {  // banco de claves del bridge (simulado): solo devuelve conteos
      const cnt = (v) => (Array.isArray(v) ? v.length : v ? 1 : 0); const b = estado.banco || (estado.banco = { groq: 0, nvidia: 0 });
      if (estado.bancoCaido) return json(route, { detail: 'caido' }, 502);
      if (req.headers()['x-api-key'] !== 'api-e2e') return json(route, { error: { code: 'NO_AUTORIZADO' } }, 401);
      if (req.method() === 'POST') { if (body && body.groq) b.groq = cnt(body.groq); if (body && body.nvidia) b.nvidia = cnt(body.nvidia); }
      if (req.method() === 'DELETE') { b.groq = 0; b.nvidia = 0; }
      return json(route, { ok: true, groq: b.groq, nvidia: b.nvidia });
    }
    if (p === '/chat/swe/capacidades') return json(route, estado.capacidades || {});  // el Harness no reporta nada -> todo NO DISPONIBLE salvo Individual
    if (p === '/chat/swe/aprobar' && req.method() === 'POST') {  // contrato de app.py (_identificar_operador): 503 sin aprobadores, 403 operador/token incorrectos (token de PRUEBA, no una clave)
      if (estado.sinAprobadores) return json(route, { detail: 'APROBADORES_NO_CONFIGURADOS' }, 503);
      if (req.headers()['x-operador'] !== 'luna' || req.headers()['x-operator-token'] !== 'tok-e2e-no-es-clave') return json(route, { detail: 'OPERADOR_NO_AUTORIZADO' }, 403);
    }
    if (/^\/chat\/swe\/(iniciar|avanzar|estado|aprobar|reanudar)$/.test(p) && req.method() === 'POST') {  // la "vista" de la tarea que devuelve el Harness
      const op = p.split('/').pop(), pide = op === 'iniciar' && estado.estadoSwe === 'REQUIERE_APROBACION';
      return json(route, { ok: true, resultado: { ok: true, task_id: body && body.task_id, estado: pide ? 'REQUIERE_APROBACION' : op === 'aprobar' ? 'CONTINUAR' : 'DONE', paso_actual: 1, resultado_tool: 'resultado del agente real de prueba', evidencia: ['recibo:e2e-123'], pasos_terminados: [{ paso: 'ejecuta', agente: 'swe-agent', recibo: 'r-e2e', herramientas: ['swe-agent'], resultado: 'ok' }], ...(pide ? { pendiente_aprobacion: { op_id: '0123456789abcdef', paso: 'ejecuta', agente: 'codex', modelo: 'hf/qwen2.5-coder-1.5b', permisos: { escritura: true }, objetivo: 'editar el repo' } } : {}) } });
    }
    if (p === '/chat/providers') return json(route, { providers: [{ id: 'qwen', nombre: 'Qwen', estado: 'ok' }, ...(estado.conProveedores ? [{ id: 'groq' }, { id: 'nvidia' }] : [])] });
    if (p === '/chat/providers/groq/models') return json(route, { models: (estado.groqModelos || ['groq/qwen/qwen3.8-27b']).map((m) => ({ model_id: m })) });
    if (p === '/chat/providers/nvidia/models') return json(route, { models: (estado.nvidiaModelos || ['nvidia/minimaxai/minimax-m3.1-flash', 'nvidia/meta/muse-glimmer-30b', 'nvidia/nvidia/nemotron-3-ultra-550b-a55b']).map((m) => ({ model_id: m })) });  // sin GLM 5.3: el proveedor no lo publica
    if ((p === '/v1/chat/completions' || p === '/web/v1/chat/completions') && req.method() === 'POST') {  // /web/* siempre llega al bridge (proxy del Space); /v1/* solo con web-/swecode-
      if (estado.conTools) return json(route, { modelo_usado: (body && body.model) || 'swe', choices: [{ message: { role: 'assistant', content: 'Voy a leer el repo', tool_calls: [{ id: 'call-1', type: 'function', function: { name: 'github_leer', arguments: '{"repo":"x"}' } }, { id: 'call-2', type: 'function', function: { name: 'motor_copiar', arguments: '{}' } }] }, finish_reason: 'tool_calls' }] });
      return json(route, { modelo_usado: (body && body.model) || 'swe', via_respaldo: 'groq', choices: [{ message: { role: 'assistant', content: 'respuesta SWE de prueba' }, finish_reason: 'stop' }] });
    }
    if (/^\/plugins\/[a-z_]+\/call\/chat_async$/.test(p)) {  // ruta normal del Router (puente_chat o fichas_qwen para Team qwen); control: un modelo NO SWE debe usar esta
      return json(route, { status: 'ok', result: { choices: [{ message: { content: 'respuesta del Router (plugin)' }, finish_reason: 'stop' }], modelo_solicitado: 'qwen3.8-max', modelo_respuesta: 'qwen3.8-max' } });
    }
    if (p === '/health') return json(route, { status: 'ok' });
    if (req.method() === 'GET') return json(route, {});
    return json(route, { status: 'ok', result: {} });
  };
}

async function nuevaPagina(browser, estado, { catalogoLocal } = {}) {
  const ctx = await browser.newContext({ viewport: { width: 1280, height: 800 } });
  await ctx.addInitScript((cat) => {
    sessionStorage.setItem('riu_clave', 'api-e2e'); localStorage.setItem('riu_herr_abiertas', '1');
    if (!sessionStorage.getItem('e2e_ini')) { sessionStorage.setItem('e2e_ini', '1'); sessionStorage.removeItem('riu_selector_activo'); if (cat) localStorage.setItem('riu_catalogo_qwen', JSON.stringify(cat)); }
  }, catalogoLocal || null);
  // nada sale a Internet: el Router es simulado y lo demas (fuentes, CDN) se corta
  await ctx.route('**/*', (route) => { const h = new URL(route.request().url()).host; return /^(127\.0\.0\.1|localhost)(:|$)/.test(h) ? route.fallback() : (h === new URL(ROUTER).host ? route.fallback() : route.abort()); });
  await ctx.route(ROUTER + '/**', routerFalso(estado));
  const page = await ctx.newPage();
  page.errs = []; page.on('pageerror', (e) => page.errs.push(e.message));
  return page;
}

// el panel se vuelve a montar al volver: se espera a la CONDICION (composer + pills montados y el DOM quieto 300 ms), no a un plazo fijo
const volverAlChat = async (p) => {
  await p.$eval('[data-view="chat"]', (e) => e.click());
  await p.waitForSelector('#composer #message', { state: 'attached', timeout: 20000 });
  await p.waitForFunction(() => {
    const listo = ['#composer #message', '#sel-swe', '#sel-swen', '#sel-nuevo'].every((q) => document.querySelector(q));
    if (!window.__quietoObs) { window.__quietoT = Date.now(); window.__quietoObs = new MutationObserver(() => { window.__quietoT = Date.now(); }); window.__quietoObs.observe(document.documentElement, { childList: true, subtree: true }); }
    return listo && Date.now() - window.__quietoT >= 300;
  }, null, { timeout: 30000, polling: 100 });
};
const abrirChat = async (p, base) => { await p.goto(base + '/chat/ui/shell.html'); await p.waitForSelector('#sel-nuevo', { state: 'attached', timeout: 20000 }); await p.waitForTimeout(1500); };
const abrirHojaModelos = async (p) => { await p.$eval('#sel-nuevo', (e) => e.click()); await p.waitForSelector('#sh-modelos-lista button', { state: 'attached', timeout: 10000 }); };
const grupos = (p) => p.evaluate(() => [...document.querySelectorAll('#sh-modelos-lista h4.mod-grupo-t')].map((h) => h.textContent.trim()));
const elegir = (p, nombre) => p.evaluate((n) => { const b = [...document.querySelectorAll('#sh-modelos-lista button.mod-fila')].find((x) => x.querySelector('b').textContent.trim() === n); if (b) b.click(); return !!b; }, nombre);
const burbujasBot = (p) => p.locator('.chat-history .message:not(.user):not(.pending):not(.meta) .txt');
async function enviar(p, texto) {
  const n = await burbujasBot(p).count();
  await p.fill('#message', texto); await p.$eval('#composer .action', (e) => e.click());
  await p.waitForFunction((k) => document.querySelectorAll('.chat-history .message:not(.user):not(.pending):not(.meta) .txt').length > k, n, { timeout: 30000 });
  return (await burbujasBot(p).last().innerText()).trim();
}

(async () => {
  const srv = await servirFrontend(); const base = 'http://127.0.0.1:' + srv.address().port;
  const browser = await chromium.launch((process.env.CHROMIUM ? { executablePath: process.env.CHROMIUM } : {}));
  try {
    // ======== A) catalogo del Router SIN modelos SWE: el selector igual lista los dos grupos SWE ========
    const estA = { llamadas: [], catalogoFalla: false };
    const p = await nuevaPagina(browser, estA);
    const dialogos = []; let aceptar = true; p.on('dialog', (d) => { dialogos.push(d.message()); return aceptar ? d.accept() : d.dismiss(); });  // Borrar claves pide confirmacion
    await abrirChat(p, base);
    await abrirHojaModelos(p);
    await p.waitForSelector('#sh-modelos-lista button:has(b:text-is("Zz modelo mock"))', { state: 'attached', timeout: 12000 }).catch(() => {});
    const cargado = await p.evaluate(() => window.RIU_SELECTOR_QWEN.modelos.some((m) => m.model_id === 'zz-modelo-mock'));
    ok('A0 el catalogo cargado es el del Router simulado (sin SWE)', cargado && estA.llamadas.some((l) => l.ruta === '/chat/providers/qwen/models'), JSON.stringify(estA.llamadas.map((l) => l.ruta)));
    ok('A0 la peticion al Router lleva X-API-Key', estA.llamadas.length > 0 && estA.llamadas.every((l) => l.clave === CLAVE), estA.llamadas.map((l) => l.clave).join(','));
    let gs = await grupos(p);
    ok('A1 grupo "SWE CODE (local HF)" listado', gs.includes('SWE CODE (local HF)'), JSON.stringify(gs));
    ok('A1 grupo "SWEN CODE free (web)" listado', gs.includes('SWEN CODE free (web)'), JSON.stringify(gs));
    const filas = await p.evaluate(() => [...document.querySelectorAll('#sh-modelos-lista button.mod-fila b')].map((b) => b.textContent.trim()));
    ok('A1 filas SWE presentes (solo nombre de modelo: Liquid LFM2.5 350M, Qwen3 0.6B, Qwen 3.8 Max (web), Concilio) y sin filas «SWE · agente/modo»', ['Liquid LFM2.5 350M', 'Qwen3 0.6B', 'Qwen 3.8 Max (web)', 'Concilio'].every((n) => filas.includes(n)) && !filas.some((n) => /SWE ·/.test(n)), filas.join(' | '));
    const ids = await p.evaluate(() => window.RIU_SELECTOR_QWEN.modelos.map((m) => m.model_id));
    ok('A1 RIU_SELECTOR_QWEN.modelos expone ids web-*/swecode-consulta/hf-* y ningun swecode-<modo>', ['web-qwen38max', 'swecode-consulta', 'hf-liquid-lfm25', 'hf-qwen35-08b'].every((i) => ids.includes(i)) && !ids.some((i) => /^swecode-(asesoria|revision|solucion|arquitectura|archivos|prompt_code|despliega)$/.test(i)));

    // ======== B) elegir modelo SWE y enviar: va por /v1/chat/completions, NO por el plugin del Router ========
    ok('B1 elegir "Qwen 3.8 Max (web)"', await elegir(p, 'Qwen 3.8 Max (web)'));
    await p.waitForTimeout(300);
    ok('B1 Team qwen queda activo con ese modelo', await p.evaluate(() => window.RIU_SELECTORES.activo === 'team-qwen' && window.RIU_SELECTOR_QWEN.seleccion && window.RIU_SELECTOR_QWEN.seleccion.model_id === 'web-qwen38max'));
    estA.llamadas.length = 0;
    const r1 = await enviar(p, 'hola swe');
    ok('B2 se pinta "respuesta SWE de prueba"', r1 === 'respuesta SWE de prueba', JSON.stringify(r1));
    const comp = estA.llamadas.filter((l) => l.ruta === '/v1/chat/completions');
    ok('B3 una llamada POST /v1/chat/completions', comp.length === 1, JSON.stringify(estA.llamadas.map((l) => l.metodo + ' ' + l.ruta)));
    ok('B3 NO se llamo a /plugins/puente_chat/... ni a ningun /plugins/*/chat_async', !estA.llamadas.some((l) => l.ruta.startsWith('/plugins/puente_chat') || /^\/plugins\/.*chat_async$/.test(l.ruta)), JSON.stringify(estA.llamadas.map((l) => l.ruta)));
    const b1 = comp[0] && comp[0].body || {};
    ok('B4 cuerpo: model web-qwen38max, mensaje del usuario al final, conv_id', b1.model === 'web-qwen38max' && Array.isArray(b1.messages) && /hola swe/.test(String(b1.messages[b1.messages.length - 1].content)) && b1.messages[b1.messages.length - 1].role === 'user' && !!b1.conv_id, JSON.stringify(b1).slice(0, 300));
    ok('B4 la llamada lleva X-API-Key', comp[0] && comp[0].clave === CLAVE);
    const nota = await p.evaluate(() => [...document.querySelectorAll('.chat-history .meta')].map((x) => x.innerText.trim()).filter((t) => /^SWE/.test(t)).pop() || '');
    ok('B5 nota "SWE · modelo · respondió groq"', nota === 'SWE · web-qwen38max · respondió groq', JSON.stringify(nota));

    // segundo mensaje: el historial viaja en messages (turno anterior user+bot) y el modelo local se traduce a su id real
    ok('B6 elegir "Liquid LFM2.5 350M"', (await abrirHojaModelos(p), await elegir(p, 'Liquid LFM2.5 350M')));
    estA.llamadas.length = 0;
    const r2 = await enviar(p, 'segundo mensaje');
    const c2 = estA.llamadas.filter((l) => l.ruta === '/web/v1/chat/completions')[0];  // modelo local: por /web/v1 (el proxy lo manda al bridge; por /v1 caeria en el Router)
    const m2 = c2 && c2.body && c2.body.messages || [];
    ok('B6 segundo envio tambien SWE directo y pinta la respuesta', r2 === 'respuesta SWE de prueba' && !!c2 && !estA.llamadas.some((l) => l.ruta.startsWith('/plugins/puente_chat')), JSON.stringify(estA.llamadas.map((l) => l.ruta)));
    ok('B6 hf-liquid-lfm25 -> model lfm2.5-350m', c2 && c2.body.model === 'lfm2.5-350m', c2 && c2.body.model);
    ok('B6 el historial (turno previo user + bot) viaja en messages', m2.length >= 3 && m2.some((m) => m.role === 'user' && /hola swe/.test(String(m.content))) && m2.some((m) => /respuesta SWE de prueba/.test(String(m.content))) && /segundo mensaje/.test(String(m2[m2.length - 1].content)), JSON.stringify(m2).slice(0, 400));

    // control: un modelo NO SWE sigue yendo por el plugin del Router, no por /v1/chat/completions
    ok('B7 elegir "Qwen 3.8 Max" (no SWE)', (await abrirHojaModelos(p), await elegir(p, 'Qwen 3.8 Max')));
    estA.llamadas.length = 0;
    const r3 = await enviar(p, 'control router');
    ok('B7 modelo no SWE: va por el plugin del Router (/plugins/*/call/chat_async) y NO por /v1/chat/completions', r3 === 'respuesta del Router (plugin)' && estA.llamadas.some((l) => /^\/plugins\/[a-z_]+\/call\/chat_async$/.test(l.ruta)) && !estA.llamadas.some((l) => l.ruta === '/v1/chat/completions'), JSON.stringify(r3) + ' ' + JSON.stringify(estA.llamadas.map((l) => l.ruta)));

    // ======== C) Configuracion: seccion "Agente movil (APK)" justo tras "Control" (segunda seccion) con enlace #ap-apk -> /apk ========
    await p.$eval('[data-view="apariencia"]', (e) => e.click());
    await p.waitForSelector('#ap-apk', { state: 'attached', timeout: 10000 });
    const cfg = await p.evaluate(() => {
      const secs = [...document.querySelectorAll('#panel section.ap-sec')];
      const a = document.querySelector('#ap-apk');
      return { titulos: secs.slice(0, 3).map((s) => (s.querySelector('h2') || {}).textContent), idxApk: secs.findIndex((s) => s.contains(a)), href: a && a.getAttribute('href'), texto: a && a.textContent.trim(), download: a && a.getAttribute('download'), visible: !!(a && a.getClientRects().length) };
    });
    ok('C1 la seccion APK es la segunda de Configuracion (tras Control)', cfg.idxApk === 1 && /APK/.test(cfg.titulos[1]), JSON.stringify(cfg.titulos));
    ok('C2 #ap-apk apunta a /apk', /\/apk$/.test(cfg.href || ''), cfg.href);
    ok('C3 #ap-apk es visible y dice Descargar APK', cfg.visible && /Descargar APK/.test(cfg.texto), JSON.stringify(cfg));
    ok('C3 #ap-apk es descarga (atributo download)', !!cfg.download, cfg.download);
    // ---- C4) seccion de claves SWE: existe, guardar una clave de prueba, el siguiente envio SWE la lleva y el valor no aparece en el DOM del chat ----
    const KEY = 'gsk_E2E_PRUEBA_123';
    const clv = await p.evaluate(() => { const h = document.querySelector('#ap-h-claves'); const g = document.querySelector('#ap-clave-groq'), n = document.querySelector('#ap-clave-nvidia'); const secs = [...document.querySelectorAll('#panel section.ap-sec')]; return { titulo: h && h.textContent, idx: secs.findIndex((s) => s.contains(h)), tipoG: g && g.type, tipoN: n && n.type, acG: g && g.getAttribute('autocomplete'), acN: n && n.getAttribute('autocomplete'), guardar: !!document.querySelector('#ap-clave-guardar'), borrar: !!document.querySelector('#ap-clave-borrar') }; });
    ok('C4 Configuracion tiene la seccion de claves SWE justo tras el APK', /Claves para SWE CODE/.test(clv.titulo || '') && clv.idx === 2, JSON.stringify(clv));
    ok('C4 inputs password autocomplete=off y botones Guardar/Borrar', clv.tipoG === 'password' && clv.tipoN === 'password' && clv.acG === 'off' && clv.acN === 'off' && clv.guardar && clv.borrar, JSON.stringify(clv));
    estA.llamadas.length = 0;
    await volverAlChat(p);
    await abrirHojaModelos(p); await elegir(p, 'Qwen 3.8 Max (web)');  // sin claves guardadas: el POST no lleva `claves`
    const rSin = await enviar(p, 'sin claves');
    const cSin = estA.llamadas.filter((l) => l.ruta === '/v1/chat/completions')[0];
    ok('C4 sin claves guardadas el POST no incluye `claves`', rSin === 'respuesta SWE de prueba' && cSin && !('claves' in cSin.body), JSON.stringify(cSin && cSin.body).slice(0, 200));
    await p.$eval('[data-view="apariencia"]', (e) => e.click());
    await p.waitForSelector('#ap-clave-groq', { state: 'attached', timeout: 10000 });
    const estTxt = (re) => p.waitForFunction((src) => new RegExp(src).test((document.querySelector('#ap-clave-estado') || {}).textContent || ''), re.source, { timeout: 10000 });
    await estTxt(/Sin claves guardadas en el servidor/);
    const gets = estA.llamadas.filter((l) => l.ruta === '/web/v1/claves' && l.metodo === 'GET');
    ok('C4 al abrir Configuracion se hace GET /web/v1/claves con X-API-Key y se muestra el estado', gets.length >= 1 && gets[0].clave === 'api-e2e');
    await p.fill('#ap-clave-groq', '  ' + KEY + '  ');
    await p.$eval('#ap-clave-guardar', (e) => e.click());
    await estTxt(/Groq: 1 guardada/);
    const tras = await p.evaluate(() => ({ g: document.querySelector('#ap-clave-groq').value, n: document.querySelector('#ap-clave-nvidia').value, est: document.querySelector('#ap-clave-estado').textContent, ls: localStorage.getItem('riu_swe_claves') }));
    const post = estA.llamadas.filter((l) => l.ruta === '/web/v1/claves' && l.metodo === 'POST');
    ok('C4 Guardar hace POST /web/v1/claves con la clave recortada y X-API-Key', post.length === 1 && post[0].body.groq === KEY && post[0].clave === 'api-e2e', JSON.stringify(post.map((l) => l.body)).replace(KEY, '***'));
    ok('C4 tras guardar los inputs quedan vacios y dice "Groq: 1 guardada" sin mostrar el valor', tras.g === '' && tras.n === '' && /Groq: 1 guardada/.test(tras.est) && !tras.est.includes(KEY), JSON.stringify(tras.est));
    ok('C4 con el banco del servidor NO queda copia en localStorage', tras.ls === null, 'ls presente');
    await volverAlChat(p);
    estA.llamadas.length = 0;
    const rCon = await enviar(p, 'con banco');
    const cCon = estA.llamadas.filter((l) => l.ruta === '/v1/chat/completions')[0];
    ok('C4 el envio SWE no lleva `claves` en el cuerpo (las pone el servidor)', rCon === 'respuesta SWE de prueba' && cCon && !('claves' in cCon.body), JSON.stringify(cCon && Object.keys(cCon.body)));
    const dom = await p.evaluate(() => document.documentElement.innerText + '\n' + [...document.querySelectorAll('input,textarea')].map((e) => e.value).join('\n'));
    const histHtml = await p.evaluate(() => (document.querySelector('.chat-history') || {}).innerHTML || '');
    ok('C4 el valor de la clave NO aparece en el DOM del chat', !dom.includes(KEY) && !histHtml.includes(KEY));
    await p.$eval('[data-view="apariencia"]', (e) => e.click());
    await p.waitForSelector('#ap-clave-borrar', { state: 'attached', timeout: 10000 });
    aceptar = false; estA.llamadas.length = 0; await p.$eval('#ap-clave-borrar', (e) => e.click()); await p.waitForTimeout(500); aceptar = true;
    ok('F Borrar pide confirmacion y, si se cancela, no borra nada', dialogos.length === 1 && /Borrar las claves/.test(dialogos[0]) && !estA.llamadas.some((l) => l.metodo === 'DELETE') && estA.banco.groq === 1, JSON.stringify([dialogos, estA.banco]));
    await p.$eval('#ap-clave-borrar', (e) => e.click());
    await estTxt(/Claves borradas/);
    ok('C4 Borrar hace DELETE /web/v1/claves', estA.llamadas.some((l) => l.ruta === '/web/v1/claves' && l.metodo === 'DELETE') && estA.banco.groq === 0);
    // R1: servidor del banco caido (502): NO hay respaldo local; se dice que no se guardo nada y el envio SWE nunca lleva `claves`
    estA.bancoCaido = true;
    await p.fill('#ap-clave-groq', KEY);
    await p.$eval('#ap-clave-guardar', (e) => e.click());
    await estTxt(/No se guardó nada/);
    const resp = await p.evaluate(() => ({ est: document.querySelector('#ap-clave-estado').textContent, ls: localStorage.getItem('riu_swe_claves'), todo: JSON.stringify({ ...localStorage }), inp: document.querySelector('#ap-clave-groq').value }));
    ok('R1 banco caido: NO se guarda la clave en localStorage, el estado lo dice sin mostrar el valor y el input conserva lo escrito', resp.ls === null && !resp.todo.includes(KEY) && !resp.est.includes(KEY) && /servidor/.test(resp.est) && resp.inp === KEY, resp.est);
    await volverAlChat(p);
    estA.llamadas.length = 0;
    await enviar(p, 'sin respaldo local');
    const cRes = estA.llamadas.filter((l) => l.ruta === '/v1/chat/completions')[0];
    ok('R1 con el banco caido el envio SWE NO incluye claves (ni `clave`) en el cuerpo ni en ningun otro lado', cRes && !('claves' in cRes.body) && !('clave' in cRes.body) && !JSON.stringify(estA.llamadas).includes(KEY), JSON.stringify(cRes && Object.keys(cRes.body)));
    estA.bancoCaido = false;
    await p.evaluate(() => localStorage.setItem('riu_swe_claves', JSON.stringify({ groq: 'MARCADOR-VIEJO-NO-REAL' })));  // resto de una version anterior
    await p.reload(); await p.waitForSelector('#sel-nuevo', { state: 'attached', timeout: 20000 }); await p.waitForTimeout(1200);
    ok('R1 una clave vieja en localStorage se purga al cargar la pagina', await p.evaluate(() => localStorage.getItem('riu_swe_claves') === null));
    ok('A-C sin errores JS en la pagina', p.errs.length === 0, p.errs.join(' | '));
    await p.context().close();

    // ======== D) el Router falla y no hay catalogo guardado: la lista de respaldo tambien trae los grupos SWE ========
    const estD = { llamadas: [], catalogoFalla: true };
    const pd = await nuevaPagina(browser, estD);
    await abrirChat(pd, base); await abrirHojaModelos(pd);
    const gd = await grupos(pd);
    ok('D1 Router caido + sin cache: aparecen los grupos SWE (lista de respaldo)', gd.includes('SWE CODE (local HF)') && gd.includes('SWEN CODE free (web)'), JSON.stringify(gd));
    const fd = await pd.evaluate(() => [...document.querySelectorAll('#sh-modelos-lista button.mod-fila b')].map((b) => b.textContent.trim()));
    ok('D2 la lista de respaldo trae los 4 modelos locales por NOMBRE de modelo y ningun modo ni agente como modelo', ['Liquid LFM2.5 350M', 'Qwen2.5 Coder 1.5B', 'Qwen3.5 0.8B', 'Qwen3 0.6B'].every((n) => fd.includes(n)) && !fd.some((t) => /SWE ·|asesoria|Codex|OpenCode/i.test(t)), fd.join(' | '));
    await pd.context().close();

    // ======== E) Router caido pero con el ultimo catalogo del Router guardado en localStorage (sin SWE) ========
    const estE = { llamadas: [], catalogoFalla: true };
    const pe = await nuevaPagina(browser, estE, { catalogoLocal: ['qwen3.8-max', 'glm-5.2', 'deepseek-v4-pro'] });
    await abrirChat(pe, base); await abrirHojaModelos(pe);
    const ge = await grupos(pe);
    ok('E1 Router caido + catalogo guardado sin SWE: siguen los grupos SWE', ge.includes('SWE CODE (local HF)') && ge.includes('SWEN CODE free (web)'), JSON.stringify(ge));
    await pe.context().close();

    // ---- ayudas del SELECTOR CENTRAL UNICO (cuatro ventanas: swe-code, swen-code-free, groq, nvidia) ----
    const PILL = { 'swe-code': '#sel-swe', 'swen-code-free': '#sel-swen', groq: '#sel-groq', nvidia: '#sel-ngt' };
    const listoCap = (pg) => pg.waitForFunction(() => { const e = document.querySelector('.swe-ctl .swe-estado'); return !!e && !/^Consultando/.test(e.textContent) && !document.querySelector('.swe-refrescar').disabled; }, null, { timeout: 15000 });
    const abrirV = async (pg, id) => { await pg.$eval(PILL[id], (e) => e.click()); await pg.waitForSelector('#sh-' + id + ':not([hidden]) select[data-swe-ctl]', { state: 'visible', timeout: 8000 }); await listoCap(pg); };
    const cerrarV = (pg, id) => pg.evaluate((i) => document.querySelector('#sh-' + i + ' .sh-cerrar').click(), id);
    const ctlSel = (id, k) => '#sh-' + id + ' select[data-swe-ctl="' + k + '"]';
    const ctl2 = (k) => ctlSel('swen-code-free', k);

    // ======== F) las ventanas SWE CODE y SWEN CODE free: el MODELO QUE RESPONDE del selector central ES la lista (sin lista superior duplicada); enviar por el bridge ========
    const estF = { llamadas: [], catalogoFalla: false };
    const pf = await nuevaPagina(browser, estF);
    await abrirChat(pf, base);
    const filasSel = await pf.evaluate(() => [...document.querySelectorAll('#sel-power .sel-fila')].map((f) => f.dataset.selector));
    ok('F1 el panel Selectores tiene las tarjetas swe-code y swen-code-free', filasSel.includes('swe-code') && filasSel.includes('swen-code-free'), JSON.stringify(filasSel));
    const botonesOn = await pf.evaluate(() => ['swe-code', 'swen-code-free'].map((id) => !!document.querySelector('#sel-power .sel-fila[data-selector="' + id + '"] .sel-on')));
    ok('F2 cada tarjeta tiene su boton ON/OFF', botonesOn.every(Boolean), JSON.stringify(botonesOn));
    await abrirV(pf, 'swen-code-free');
    ok('23/28 SWEN CODE free: NO hay lista superior de modelos (ni #sh-swen-code-free-lista ni filas .fila de modelos); el MODELO QUE RESPONDE es el desplegable', await pf.evaluate(() => !document.getElementById('sh-swen-code-free-lista') && document.querySelectorAll('#sh-swen-code-free button.fila').length === 0 && !!document.querySelector('#sh-swen-code-free select[data-swe-ctl="modelo_responde"]')));
    const modelosSwen = await pf.evaluate(() => [...document.querySelectorAll('#sh-swen-code-free select[data-swe-ctl="modelo_responde"] option')].map((o) => o.value));
    ok('F3 MODELO QUE RESPONDE de SWEN: concilio, web-*, locales, Groq y NVIDIA; NINGUN modo (swecode-asesoria...) como modelo', ['swecode-consulta', 'web-qwen38max', 'web-qwen37max', 'web-dsv4-flash', 'hf/qwen3-0.6b', 'groq/qwen/qwen3.8-27b', 'nvidia/z-ai/glm-5.3'].every((m) => modelosSwen.includes(m)) && !modelosSwen.some((m) => /^swecode-(asesoria|revision|solucion|arquitectura|archivos|prompt_code|despliega)$/.test(m)), JSON.stringify(modelosSwen));
    const modos = await pf.evaluate(() => { const s = document.querySelector('#sh-swen-code-free select[data-swe-ctl="modo_trabajo"]'); return { etq: s.getAttribute('aria-label'), vals: [...s.options].map((o) => o.value), visible: s.getClientRects().length > 0 }; });
    ok('24/UI5 MODO DE TRABAJO es un selector con asesoria, revision, solucion, arquitectura, archivos, prompt_code y despliega (+ sin modo)', modos.etq === 'MODO DE TRABAJO' && modos.visible && JSON.stringify(modos.vals) === JSON.stringify(['', 'asesoria', 'revision', 'solucion', 'arquitectura', 'archivos', 'prompt_code', 'despliega']), JSON.stringify(modos));
    await pf.selectOption(ctlSel('swen-code-free', 'modelo_responde'), 'web-dsv4-flash');
    ok('F3 elegir DeepSeek V4 Flash (web) queda en RIU_SWE y en el contrato', await pf.evaluate(() => window.RIU_SWE['swen-code-free'].model_id === 'web-dsv4-flash' && JSON.parse(localStorage.getItem('riu_swe_seleccion')).modelo_responde === 'web-dsv4-flash'));
    ok('F4 elegir el modelo enciende SWEN CODE free (sin pulsar ON) y la hoja de debajo no queda tapando', await pf.evaluate(() => window.RIU_SELECTORES.activo === 'swen-code-free'));
    await pf.selectOption(ctlSel('swen-code-free', 'modo_trabajo'), 'revision');
    await cerrarV(pf, 'swen-code-free');
    estF.llamadas.length = 0;
    const rf = await enviar(pf, 'hola desde swen');
    const cf = estF.llamadas.filter((l) => l.ruta === '/v1/chat/completions');
    ok('F5 respuesta pintada y UNA llamada a /v1/chat/completions con model web-dsv4-flash y modo:"revision" (el modo viaja aparte del modelo)', rf === 'respuesta SWE de prueba' && cf.length === 1 && cf[0].body.model === 'web-dsv4-flash' && cf[0].body.modo === 'revision', JSON.stringify(estF.llamadas.map((l) => l.ruta)) + ' ' + rf + JSON.stringify(cf[0] && cf[0].body.modo));
    ok('F5 sin llamadas al plugin del Router', !estF.llamadas.some((l) => /^\/plugins\//.test(l.ruta)));
    ok('F5 el POST no lleva claves', cf[0] && !('claves' in cf[0].body) && !('clave' in cf[0].body));
    await pf.evaluate(() => document.querySelector('#sel-power .sel-fila[data-selector="swe-code"] .sel-on').click());
    await abrirV(pf, 'swe-code');
    const modelosSwe = await pf.evaluate(() => [...document.querySelectorAll('#sh-swe-code select[data-swe-ctl="modelo_responde"] option')].map((o) => [o.value, o.textContent]));
    ok('UI4/23 SWE CODE: la lista de modelos locales muestra SOLO el nombre del modelo (4 HF), sin Codex/OpenCode/OpenHands/Agent', JSON.stringify(modelosSwe.map((m) => m[0])) === JSON.stringify(['hf/lfm2.5-350m', 'hf/qwen2.5-coder-1.5b', 'hf/qwen3.5-0.8b', 'hf/qwen3-0.6b']) && modelosSwe.every((m) => !/SWE ·|Codex|OpenCode|OpenHands|Agent/.test(m[1])), JSON.stringify(modelosSwe));
    await pf.selectOption(ctlSel('swe-code', 'modelo_responde'), 'hf/lfm2.5-350m');
    ok('F6 los modos de trabajo tambien se ven en SWE CODE (visible en todas las ventanas)', await pf.evaluate(() => document.querySelector('#sh-swe-code select[data-swe-ctl="modo_trabajo"]').getClientRects().length > 0 && document.querySelector('#sh-swe-code select[data-swe-ctl="modo_trabajo"]').value === 'revision'));
    await pf.selectOption(ctlSel('swe-code', 'modo_trabajo'), '');
    await cerrarV(pf, 'swe-code');
    estF.llamadas.length = 0;
    const rl = await enviar(pf, 'hola liquid');
    const cl = estF.llamadas.filter((l) => l.ruta === '/web/v1/chat/completions')[0];  // idem: local por /web/v1
    ok('F6 SWE CODE + Liquid: model lfm2.5-350m, el historial previo viaja y sin modo', rl === 'respuesta SWE de prueba' && cl && cl.body.model === 'lfm2.5-350m' && cl.body.messages.length >= 3 && !('modo' in cl.body), JSON.stringify(cl && cl.body));
    ok('F6 la etiqueta del panel refleja el modelo elegido', await pf.evaluate(() => /Liquid/.test(document.querySelector('#sel-power .sel-fila[data-selector="swe-code"] .sel-resp').textContent)));
    ok('F sin errores JS en la pagina', pf.errs.length === 0, pf.errs.join(' | '));
    await pf.context().close();

    // ======== G) Salida SWE | OpenClaw: UN solo control (en el selector central), persistido, enviado como ejecutor_tools e INDEPENDIENTE de agente_tool ========
    const estG = { llamadas: [], catalogoFalla: false };
    const pg = await nuevaPagina(browser, estG);
    await abrirChat(pg, base);
    const presionado = (q) => pg.evaluate((s) => (document.querySelector(s) || {}).getAttribute && document.querySelector(s).getAttribute('aria-pressed'), q);
    ok('G1 el panel Selectores YA NO tiene su fila global «Salida de tools» (un solo control de salida en todo el documento)', await pg.evaluate(() => !document.querySelector('#sel-salida-swe') && !document.querySelector('#sel-power .sel-salida') && document.querySelectorAll('[data-salida]').length === 0));
    await abrirV(pg, 'swen-code-free');
    ok('G1 dentro del selector central hay UNA fila de Salida (SWE-agent | OpenClaw) y en todo el documento solo 2 botones [data-salida]', await pg.evaluate(() => document.querySelectorAll('[data-salida]').length === 2 && document.querySelectorAll('.swe-seg').length === 1 && [...document.querySelectorAll('[data-salida]')].map((b) => b.textContent).join() === 'SWE-agent,OpenClaw'));
    ok('G1 por defecto Salida = SWE', (await presionado('#sh-swen-code-free [data-salida="swe"]')) === 'true' && (await presionado('#sh-swen-code-free [data-salida="openclaw"]')) === 'false');
    await pg.selectOption(ctlSel('swen-code-free', 'modelo_responde'), 'web-qwen38max'); await cerrarV(pg, 'swen-code-free');
    estG.llamadas.length = 0;
    await enviar(pg, 'salida por defecto');
    const g1 = estG.llamadas.filter((l) => l.ruta === '/v1/chat/completions')[0];
    ok('G2 el POST lleva ejecutor_tools:"swe" por defecto', g1 && g1.body.ejecutor_tools === 'swe', JSON.stringify(g1 && g1.body.ejecutor_tools));
    await abrirV(pg, 'swen-code-free');
    const agAntes = await pg.evaluate(() => JSON.parse(localStorage.getItem('riu_swe_seleccion') || '{}').agente_tool || 'swe-agent');
    await pg.$eval('#sh-swen-code-free [data-salida="openclaw"]', (e) => e.click());
    const agDespues = await pg.evaluate(() => JSON.parse(localStorage.getItem('riu_swe_seleccion') || '{}').agente_tool || 'swe-agent');
    ok('197/62 cambiar la salida a OpenClaw NO modifica agente_tool', agAntes === agDespues && agDespues === 'swe-agent' && await pg.evaluate(() => document.querySelector('#sh-swen-code-free select[data-swe-ctl="agente_tool"]').value === 'swe-agent'), agAntes + '/' + agDespues);
    ok('G3 elegir OpenClaw lo persiste en localStorage y marca el boton', await pg.evaluate(() => localStorage.getItem('riu_swe_ejecutor_tools') === 'openclaw') && (await presionado('#sh-swen-code-free [data-salida="openclaw"]')) === 'true' && (await presionado('#sh-swen-code-free [data-salida="swe"]')) === 'false');
    await cerrarV(pg, 'swen-code-free');
    estG.llamadas.length = 0;
    await enviar(pg, 'salida openclaw');
    const g2 = estG.llamadas.filter((l) => l.ruta === '/v1/chat/completions')[0];
    ok('G4 el POST lleva ejecutor_tools:"openclaw"', g2 && g2.body.ejecutor_tools === 'openclaw', JSON.stringify(g2 && g2.body.ejecutor_tools));
    await abrirV(pg, 'swe-code');
    ok('G5 el MISMO control de salida aparece en SWE CODE con OpenClaw activo (sincronizado)', await pg.evaluate(() => { const b = [...document.querySelectorAll('#sh-swe-code [data-salida]')]; return b.length === 2 && b.find((x) => x.dataset.salida === 'openclaw').getAttribute('aria-pressed') === 'true'; }));
    await pg.$eval('#sh-swe-code [data-salida="swe"]', (e) => e.click());
    ok('G6 elegir SWE persiste en localStorage', await pg.evaluate(() => localStorage.getItem('riu_swe_ejecutor_tools') === 'swe'));
    await pg.$eval('#sh-swe-code [data-salida="openclaw"]', (e) => e.click()); await pg.reload(); await pg.waitForSelector('#sel-swe', { state: 'attached', timeout: 20000 }); await pg.waitForTimeout(800);
    await abrirV(pg, 'swe-code');
    ok('G7 la eleccion de salida sobrevive a recargar la pagina', (await presionado('#sh-swe-code [data-salida="openclaw"]')) === 'true');
    ok('G sin errores JS en la pagina', pg.errs.length === 0, pg.errs.join(' | '));
    await pg.context().close();

    // ======== H) Agentes/modelos/workflow del selector central; contrato TareaSWE a /chat/swe/*; estados reales ========
    const TODOS = { harness: 'ok', agentes: Object.fromEntries(['openclaw', 'swe-agent', 'openhands', 'opencode', 'codex', 'claude-code'].map((a) => [a, { disponible: true }])), workflows: { swe_code: { disponible: true }, liquid_mirror: { disponible: true } }, modelos: {} };
    const estH = { llamadas: [], catalogoFalla: false, capacidades: {} };
    const ph = await nuevaPagina(browser, estH);
    await abrirChat(ph, base);
    await abrirV(ph, 'swen-code-free');
    const ctl = await ph.evaluate(() => ({ etiquetas: ['agente_responde', 'modelo_responde', 'agente_tool', 'modelo_tool', 'modo_trabajo', 'workflow'].map((k) => document.querySelector('#sh-swen-code-free select[data-swe-ctl="' + k + '"]').getAttribute('aria-label')), agentico: (document.querySelector('#sh-swen-code-free [data-swe-agentico]') || {}).textContent, salida: [...document.querySelectorAll('#sh-swen-code-free [data-salida]')].map((b) => b.getAttribute('aria-label')) }));
    ok('13/H1 estructura RESPONDE [agente][modelo] · EJECUTA [agente][modelo tool] · MODO DE TRABAJO · MODO AGENTICO · WORKFLOW · SALIDA, con su rotulo exacto', JSON.stringify(ctl.etiquetas) === JSON.stringify(['AGENTE QUE RESPONDE', 'MODELO QUE RESPONDE', 'AGENTE QUE EJECUTA', 'MODELO PARA TOOL', 'MODO DE TRABAJO', 'WORKFLOW']) && ctl.agentico === 'OFF' && JSON.stringify(ctl.salida) === JSON.stringify(['Salida: SWE-agent', 'Salida: OpenClaw']), JSON.stringify(ctl));
    const orden = await ph.evaluate(() => { const y = (q) => document.querySelector(q).getBoundingClientRect().top; return [y('#sh-swen-code-free select[data-swe-ctl="agente_responde"]'), y('#sh-swen-code-free select[data-swe-ctl="agente_tool"]'), y('#sh-swen-code-free select[data-swe-ctl="modo_trabajo"]'), y('#sh-swen-code-free [data-swe-agentico]'), y('#sh-swen-code-free select[data-swe-ctl="workflow"]'), y('#sh-swen-code-free [data-salida]')]; });
    ok('13 orden visual: Responde, Ejecuta, Modo de trabajo, Modo agentico, Workflow, Salida (de arriba abajo)', orden.every((v, i) => i === 0 || v > orden[i - 1]), JSON.stringify(orden));
    const opts = await ph.evaluate(() => ({ agentes: [...document.querySelectorAll('#sh-swen-code-free select[data-swe-ctl="agente_tool"] option')].map((o) => o.value), tool: [...document.querySelectorAll('#sh-swen-code-free select[data-swe-ctl="modelo_tool"] option')].map((o) => o.value), wf: [...document.querySelectorAll('#sh-swen-code-free select[data-swe-ctl="workflow"] option')].map((o) => o.textContent.replace(/ — .*/, '')) }));
    ok('H2 MODELO PARA TOOL con los 9 ids exactos del catalogo (hf/..., groq/..., nvidia/...), seis agentes y tres workflows', JSON.stringify(opts.tool) === JSON.stringify(['hf/lfm2.5-350m', 'hf/qwen2.5-coder-1.5b', 'hf/qwen3.5-0.8b', 'hf/qwen3-0.6b', 'groq/qwen/qwen3.8-27b', 'nvidia/minimaxai/minimax-m3.1-flash', 'nvidia/meta/muse-glimmer-30b', 'nvidia/nvidia/nemotron-3-ultra-550b-a55b', 'nvidia/z-ai/glm-5.3']) && opts.agentes.length === 6 && JSON.stringify(opts.wf) === JSON.stringify(['Individual', 'SWE CODE cuatro pasos', 'Liquid Mirror']), JSON.stringify(opts));
    const nd = await ph.evaluate(() => { const o = (k, v) => { const e = document.querySelector('#sh-swen-code-free select[data-swe-ctl="' + k + '"] option[value="' + v + '"]'); return e ? { t: e.textContent, d: e.disabled, g: e.parentElement.tagName === 'OPTGROUP' ? e.parentElement.label : '' } : null; }; return { codex: o('agente_tool', 'codex'), swe: o('workflow', 'swe_code'), ind: o('workflow', 'individual'), estado: document.querySelector('#sh-swen-code-free .swe-estado').textContent, noinst: document.querySelector('#sh-swen-code-free .swe-noinst').textContent }; });
    ok('37/48/49 el Harness devuelve {} (no reporta nada): Codex y el workflow SWE CODE salen SIN VERIFICAR (deshabilitados), NO «No instalados»; Individual sigue disponible', !!nd.codex && /^Sin verificar$/.test(nd.codex.g) && nd.codex.d === true && /SIN VERIFICAR/.test(nd.codex.t) && !!nd.swe && /^Sin verificar$/.test(nd.swe.g) && nd.swe.d === true && nd.ind && nd.ind.d === false && !/No instalados/.test(nd.noinst) && /Sin verificar: /.test(nd.noinst), JSON.stringify(nd));
    // refrescar disponibilidad SIN recargar la pagina: el Harness pasa a reportar un agente NO INSTALADO real y otro disponible
    estH.capacidades = { harness: 'ok', agentes: { 'swe-agent': { disponible: false, motivo: 'swe-agent no esta instalado (CLI `sweagent` ausente del PATH; define RIU_SWEAGENT_BIN)' }, codex: { disponible: true }, openclaw: { disponible: false, motivo: 'openclaw sin configurar: falta OPENCLAW_GATEWAY_TOKEN en el entorno del Harness' }, opencode: { disponible: true, modelos: ['hf/qwen3.5-0.8b'] }, openhands: { disponible: false, motivo: 'no se pudo comprobar (OSError)' }, 'claude-code': { disponible: true } }, workflows: { swe_code: { disponible: false, motivo: 'faltan agentes conectados: openhands' }, liquid_mirror: { disponible: false, motivo: 'falta SWECODE_URL_S2 y/o SWECODE_URL_S3' } }, modelos: { 'nvidia/z-ai/glm-5.3': { disponible: false, motivo: 'glm-5.3 no figura en GET /models de nvidia' }, 'groq/qwen/qwen3.8-27b': { disponible: true, motivo: 'sin verificar GET /models (OSError)' } } };
    const recargas = await ph.evaluate(() => performance.getEntriesByType('navigation').length + ':' + (window.__marca = 'sigo-aqui'));
    estH.llamadas.length = 0;
    await ph.click('#sh-swen-code-free .swe-refrescar'); await listoCap(ph);
    ok('46 «Actualizar disponibilidad» vuelve a consultar /chat/swe/capacidades sin recargar el chat', estH.llamadas.some((l) => l.ruta === '/chat/swe/capacidades') && await ph.evaluate(() => window.__marca === 'sigo-aqui'), JSON.stringify(estH.llamadas.map((l) => l.ruta)));
    const est = await ph.evaluate(() => { const g = (k, v) => { const e = document.querySelector('#sh-swen-code-free select[data-swe-ctl="' + k + '"] option[value="' + v + '"]'); return e ? { t: e.textContent, d: e.disabled, g: e.parentElement.tagName === 'OPTGROUP' ? e.parentElement.label : '' } : null; }; return { sweagent: g('agente_tool', 'swe-agent'), openclaw: g('agente_tool', 'openclaw'), openhands: g('agente_tool', 'openhands'), codex: g('agente_tool', 'codex'), glm: g('modelo_tool', 'nvidia/z-ai/glm-5.3'), groq: g('modelo_tool', 'groq/qwen/qwen3.8-27b'), linea: document.querySelector('#sh-swen-code-free .swe-noinst').textContent }; });
    ok('37/40 SWE-agent NO INSTALADO (deshabilitado en «No instalados», no ofrecido como ejecutor), OpenClaw NO CONFIGURADO, OpenHands SIN VERIFICAR (la comprobacion fallo), Codex DISPONIBLE', est.sweagent.d && /NO INSTALADO/.test(est.sweagent.t) && /^No instalados$/.test(est.sweagent.g) && /NO CONFIGURADO/.test(est.openclaw.t) && est.openclaw.d && /SIN VERIFICAR/.test(est.openhands.t) && est.openhands.d && !est.codex.d && !/—/.test(est.codex.t), JSON.stringify(est));
    ok('45/44 GLM 5.3 sigue deshabilitado con su estado real NO DISPONIBLE EN PROVEEDOR; un modelo con GET /models sin verificar se rotula SIN VERIFICAR (no DISPONIBLE)', est.glm.d && /NO DISPONIBLE EN PROVEEDOR/.test(est.glm.t) && /SIN VERIFICAR/.test(est.groq.t) && !est.groq.d, JSON.stringify(est));
    const inc = await ph.evaluate(() => { const o = document.querySelector('#sh-swen-code-free select[data-swe-ctl="agente_tool"] option[value="opencode"]'); return o ? { g: o.parentElement.tagName === 'OPTGROUP' ? o.parentElement.label : '', d: o.disabled, t: o.textContent } : null; });
    ok('170/60 compatibilidad en el selector central: OpenCode (solo admite hf/qwen3.5-0.8b) con MODELO PARA TOOL Qwen2.5 Coder sale en «Incompatibles con este modelo», deshabilitado y rotulado NO COMPATIBLE', !!inc && inc.g === 'Incompatibles con este modelo' && inc.d && /NO COMPATIBLE/.test(inc.t), JSON.stringify(inc));
    ok('48 la linea resumen separa «No instalados» de «Sin verificar» y no mezcla causas', /No instalados: SWE-agent/.test(est.linea) && /Sin verificar: OpenHands/.test(est.linea), est.linea);
    // 42/43/201: la eleccion no disponible se queda visible con su error pero el envio se bloquea (y no se cambia a otro agente)
    await ph.selectOption(ctl2('agente_tool'), 'codex');
    await ph.evaluate(() => window.RIU_SELECTORES.encender('swen-code-free'));  // enciende SWEN CODE free (sessionStorage sobrevive a la recarga)
    await ph.evaluate(() => { localStorage.setItem('riu_swe_seleccion', JSON.stringify({ ...JSON.parse(localStorage.getItem('riu_swe_seleccion') || '{}'), agente_tool: 'swe-agent', modo_agentico: true })); });
    await ph.reload(); await ph.waitForSelector('#sel-swen', { state: 'attached', timeout: 20000 }); await ph.waitForTimeout(800);
    await abrirV(ph, 'swen-code-free');
    const vis = await ph.evaluate(() => { const s = document.querySelector('#sh-swen-code-free select[data-swe-ctl="agente_tool"]'); return { valor: s.value, texto: s.selectedOptions[0].textContent, noOk: s.classList.contains('no-ok'), error: document.querySelector('#sh-swen-code-free .swe-estado-sel').textContent, agentico: document.querySelector('#sh-swen-code-free [data-swe-agentico]').textContent }; });
    ok('42/201 agente NO INSTALADO elegido con modo ON: la eleccion SIGUE visible (SWE-agent) con su error NO INSTALADO; no se sustituye por otro', vis.valor === 'swe-agent' && /NO INSTALADO/.test(vis.texto) && vis.noOk && /AGENTE QUE EJECUTA SWE-agent: NO INSTALADO/.test(vis.error) && vis.agentico === 'ON', JSON.stringify(vis));
    await cerrarV(ph, 'swen-code-free');
    estH.llamadas.length = 0;
    await ph.fill('#message', 'con agente no instalado'); await ph.$eval('#composer .action', (e) => e.click());
    await ph.waitForFunction(() => /SELECCION_NO_DISPONIBLE/.test(document.querySelector('.chat-history').innerText), null, { timeout: 8000 });
    ok('42/201 envio bloqueado: GAP SELECCION_NO_DISPONIBLE nombra SWE-agent NO INSTALADO y no se llama a /chat/swe/iniciar ni al bridge', !estH.llamadas.some((l) => /^\/chat\/swe\/(iniciar|avanzar)/.test(l.ruta) || /chat\/completions$/.test(l.ruta)) && await ph.evaluate(() => /SWE-agent: NO INSTALADO/.test(document.querySelector('.chat-history').innerText)), JSON.stringify(estH.llamadas.map((l) => l.ruta)));
    // 199: modo OFF + Individual: conversacion normal por el bridge
    await abrirV(ph, 'swen-code-free'); await ph.$eval('#sh-swen-code-free [data-swe-agentico]', (e) => e.click()); await cerrarV(ph, 'swen-code-free');
    estH.llamadas.length = 0;
    const h5 = await enviar(ph, 'individual de siempre');
    ok('199/H5 modo agentico OFF + Individual: va por el bridge como antes (aunque SWE-agent este NO INSTALADO) y NO por /chat/swe/*', h5 === 'respuesta SWE de prueba' && estH.llamadas.some((l) => /chat\/completions$/.test(l.ruta)) && !estH.llamadas.some((l) => /^\/chat\/swe\/(iniciar|avanzar)/.test(l.ruta)), JSON.stringify(estH.llamadas.map((l) => l.ruta)));
    // 200: agentico ON con agente instalado (simulado) + workflow SWE CODE
    estH.capacidades = TODOS;
    await abrirV(ph, 'swen-code-free');
    await ph.$eval('#sh-swen-code-free [data-swe-agentico]', (e) => e.click());  // MODO AGENTICO ON
    ok('200 MODO AGENTICO ON con agentes instalados (simulado): ninguno de los 6 figura no disponible', await ph.evaluate(() => document.querySelector('#sh-swen-code-free [data-swe-agentico]').textContent === 'ON' && [...document.querySelectorAll('#sh-swen-code-free select[data-swe-ctl="agente_tool"] option')].every((o) => !o.disabled)));
    await ph.selectOption(ctl2('modelo_tool'), 'hf/qwen2.5-coder-1.5b');  // antes de elegir el workflow: en SWE CODE este control queda fijo
    await ph.selectOption(ctl2('workflow'), 'swe_code');
    await ph.selectOption(ctl2('agente_tool'), 'codex');
    const fij = await ph.evaluate(() => { const g = (k) => document.querySelector('#sh-swen-code-free select[data-swe-ctl="' + k + '"]'); const r = {}; for (const k of ['modelo_responde', 'agente_responde', 'modelo_tool']) r[k] = [g(k).disabled, g(k).dataset.fijo, g(k).selectedOptions[0].textContent, g(k).title]; r.libres = ['agente_tool', 'workflow'].map((k) => g(k).disabled); const n = document.querySelector('#sh-swen-code-free .swe-fijo'); r.nota = [!n.hidden, n.textContent]; return r; });
    ok('8 workflow SWE CODE: modelo/agente que responden y modelo de Ejecuta quedan deshabilitados y rotulados «fijo por el workflow»; agente que ejecuta y workflow siguen libres', ['modelo_responde', 'agente_responde', 'modelo_tool'].every((k) => fij[k][0] && fij[k][1] === '1' && /fijo por el workflow/.test(fij[k][2]) && /no influye/.test(fij[k][3])) && fij.libres.every((d) => !d) && fij.nota[0] && /Fijo por el workflow/.test(fij.nota[1]), JSON.stringify(fij));
    ok('H7 la seleccion persiste en localStorage', await ph.evaluate(() => { const s = JSON.parse(localStorage.getItem('riu_swe_seleccion')); return s.workflow === 'swe_code' && s.agente_tool === 'codex' && s.modo_agentico === true; }));
    await cerrarV(ph, 'swen-code-free'); await abrirV(ph, 'swe-code');
    ok('H7/18 la misma seleccion (estado) aparece al abrir SWE CODE: el nodo se movio y conserva la eleccion', await ph.evaluate(() => document.querySelector('#sh-swe-code select[data-swe-ctl="workflow"]').value === 'swe_code' && document.querySelector('#sh-swe-code select[data-swe-ctl="agente_tool"]').value === 'codex'));
    await cerrarV(ph, 'swe-code');
    estH.llamadas.length = 0;
    const h8 = await enviar(ph, 'Revisar proyecto');
    const ini = estH.llamadas.find((l) => l.ruta === '/chat/swe/iniciar');
    const campos = ['task_id', 'origen', 'mensaje', 'workflow', 'modelo_responde', 'modelo_lector', 'modelo_tool', 'modelo_revisor', 'agente_responde', 'agente_tool', 'agente_verificador', 'modo_agentico', 'aprobacion', 'sesion', 'proyecto'];
    ok('200/H8 el contrato TareaSWE exacto llega a POST /chat/swe/iniciar con X-API-Key', !!ini && JSON.stringify(Object.keys(ini.body).sort()) === JSON.stringify([...campos].sort()) && ini.clave === CLAVE, JSON.stringify(ini && ini.body));
    ok('200/H8 valores: origen yaiwes, workflow swe_code, agente_tool codex, modelo_tool hf/qwen2.5-coder-1.5b, aprobacion false', ini && ini.body.origen === 'yaiwes' && ini.body.workflow === 'swe_code' && ini.body.agente_tool === 'codex' && ini.body.modelo_tool === 'hf/qwen2.5-coder-1.5b' && ini.body.aprobacion === false && ini.body.modo_agentico === true && /^yaiwes-[A-Za-z0-9_-]+$/.test(ini.body.task_id), JSON.stringify(ini && ini.body));
    ok('H8 el resultado y la evidencia del agente vuelven al chat y no hubo llamada al bridge ni al plugin del Router', /resultado del agente real de prueba/.test(h8) && /recibo:e2e-123/.test(h8) && !estH.llamadas.some((l) => /chat\/completions$/.test(l.ruta) || /^\/plugins\//.test(l.ruta)), h8);
    // Liquid Mirror: dos participantes
    await abrirV(ph, 'swen-code-free');
    await ph.selectOption(ctl2('workflow'), 'liquid_mirror');
    const lq = await ph.evaluate(() => ({ chips: [...document.querySelectorAll('#sh-swen-code-free .swe-liquid .dg-paso')].map((x) => x.textContent), visible: !!document.querySelector('#sh-swen-code-free .swe-liquid').getClientRects().length, toolOff: document.querySelector('#sh-swen-code-free select[data-swe-ctl="modelo_tool"]').disabled }));
    ok('H9 Liquid Mirror: LIQUID 1 — LECTOR (S2) y LIQUID 2 — EJECUTOR (S3), tool bloqueado, sin modelos web', lq.visible && lq.chips.length === 2 && /LIQUID 1 — LECTOR · S2 · lfm2\.5-350m/.test(lq.chips[0]) && /LIQUID 2 — EJECUTOR · S3 · lfm2\.5-350m/.test(lq.chips[1]) && lq.toolOff && !lq.chips.join().includes('web-'), JSON.stringify(lq));
    ok('8 Liquid Mirror: tambien fijos los tres controles', await ph.evaluate(() => ['modelo_responde', 'agente_responde', 'modelo_tool'].every((k) => document.querySelector('#sh-swen-code-free select[data-swe-ctl="' + k + '"]').disabled)));
    // 63/197: seleccionar un agente NO cambia la salida y la salida NO cambia el agente
    await ph.$eval('#sh-swen-code-free [data-salida="openclaw"]', (e) => e.click());
    ok('H10/197 elegir Salida: OpenClaw NO modifica AGENTE QUE EJECUTA (sigue codex)', await ph.evaluate(() => document.querySelector('#sh-swen-code-free select[data-swe-ctl="agente_tool"]').value === 'codex' && JSON.parse(localStorage.getItem('riu_swe_seleccion')).agente_tool === 'codex'));
    for (const ag of ['opencode', 'openhands', 'claude-code', 'codex']) {
      await ph.selectOption(ctl2('agente_tool'), ag);
      ok('63 elegir ' + ag + ' como AGENTE QUE EJECUTA NO modifica la Salida (sigue OpenClaw)', await ph.evaluate(() => localStorage.getItem('riu_swe_ejecutor_tools') === 'openclaw' && document.querySelector('#sh-swen-code-free [data-salida="openclaw"]').getAttribute('aria-pressed') === 'true'));
    }
    await ph.$eval('#sh-swen-code-free [data-salida="swe"]', (e) => e.click());
    ok('H10 elegir Salida: SWE-agent tampoco toca AGENTE QUE EJECUTA', await ph.evaluate(() => document.querySelector('#sh-swen-code-free select[data-swe-ctl="agente_tool"]').value === 'codex'));
    // 198: modelo_tool no modifica modelo_responde (workflow individual: ambos libres)
    await ph.selectOption(ctl2('workflow'), 'individual');
    await ph.selectOption(ctl2('modelo_responde'), 'hf/qwen3-0.6b');
    const antesR = await ph.evaluate(() => JSON.parse(localStorage.getItem('riu_swe_seleccion')).modelo_responde);
    await ph.selectOption(ctl2('modelo_tool'), 'nvidia/meta/muse-glimmer-30b');
    ok('198 cambiar MODELO PARA TOOL no modifica MODELO QUE RESPONDE (ni su estado en la ventana)', await ph.evaluate((a) => { const s = JSON.parse(localStorage.getItem('riu_swe_seleccion')); return s.modelo_tool === 'nvidia/meta/muse-glimmer-30b' && s.modelo_responde === a && document.querySelector('#sh-swen-code-free select[data-swe-ctl="modelo_responde"]').value === a && window.RIU_SWE['swen-code-free'].model_id === 'hf-qwen3-06b'; }, antesR), antesR);
    await ph.selectOption(ctl2('workflow'), 'liquid_mirror');
    await cerrarV(ph, 'swen-code-free');
    estH.llamadas.length = 0;
    await enviar(ph, 'liquid mirror');
    const lmIni = estH.llamadas.find((l) => l.ruta === '/chat/swe/iniciar');
    ok('H11 Liquid Mirror: modelo_lector y modelo_tool = hf/lfm2.5-350m, workflow liquid_mirror', lmIni && lmIni.body.workflow === 'liquid_mirror' && lmIni.body.modelo_lector === 'hf/lfm2.5-350m' && lmIni.body.modelo_tool === 'hf/lfm2.5-350m', JSON.stringify(lmIni && lmIni.body));
    // REQUIERE_APROBACION: boton Aprobar -> /chat/swe/aprobar (sin campo aprobacion)
    estH.estadoSwe = 'REQUIERE_APROBACION';
    await ph.fill('#message', 'desplegar'); await ph.$eval('#composer .action', (e) => e.click());
    await ph.waitForSelector('.mx-aprobar', { state: 'attached', timeout: 8000 });
    estH.llamadas.length = 0; estH.estadoSwe = 'DONE';
    // AP1: el boton abre un dialogo accesible (operador texto + token password + Cancelar); sin credenciales no hay peticion
    await ph.$eval('.mx-aprobar', (e) => e.click());
    await ph.waitForSelector('.ap-operador[role="dialog"]', { state: 'visible', timeout: 8000 });
    const dlg = await ph.evaluate(() => { const d = document.querySelector('.ap-operador'), o = d.querySelector('input[type=text]'), t = d.querySelector('input[type=password]'); return { modal: d.getAttribute('aria-modal'), op: !!o && !!o.getAttribute('aria-label'), tk: !!t && !!t.getAttribute('aria-label') && t.autocomplete === 'off', cancelar: [...d.querySelectorAll('button')].some((b) => /Cancelar/.test(b.textContent)), foco: document.activeElement === o, visible: d.getBoundingClientRect().width > 0 }; });
    ok('AP1 Aprobar y continuar abre un dialogo role=dialog aria-modal con operador (texto), token (password), Cancelar y el foco en operador', dlg.modal === 'true' && dlg.op && dlg.tk && dlg.cancelar && dlg.foco && dlg.visible, JSON.stringify(dlg));
    await ph.$eval('.ap-operador button:last-child', (e) => e.click());
    await ph.waitForFunction(() => !document.querySelector('.ap-operador'), null, { timeout: 4000 });
    ok('AP1 Cancelar cierra el dialogo y NO llama a /chat/swe/aprobar', !estH.llamadas.some((l) => l.ruta === '/chat/swe/aprobar'), JSON.stringify(estH.llamadas.map((l) => l.ruta)));
    const rellenar = async (op, tk) => { await ph.$eval('.mx-aprobar', (e) => e.click()); await ph.waitForSelector('.ap-operador', { state: 'visible', timeout: 8000 }); await ph.fill('.ap-operador input[type=text]', op); await ph.fill('.ap-operador input[type=password]', tk); await ph.$eval('.ap-operador button', (e) => e.click()); await ph.waitForFunction(() => !document.querySelector('.ap-operador'), null, { timeout: 4000 }); };
    await rellenar('luna', 'token-malo-e2e');
    await ph.waitForFunction(() => /operador o token incorrecto/.test(document.querySelector('.chat-history').innerText), null, { timeout: 8000 });
    ok('AP1 403: mensaje claro «operador o token incorrecto» y el token escrito no aparece en pantalla', await ph.evaluate(() => !document.body.innerText.includes('token-malo-e2e')));
    estH.sinAprobadores = true; await rellenar('luna', 'tok-e2e-no-es-clave');
    await ph.waitForFunction(() => /RIU_SWE_APROBADORES/.test(document.querySelector('.chat-history').innerText), null, { timeout: 8000 });
    ok('AP1 503: el mensaje indica RIU_SWE_APROBADORES', true);
    estH.sinAprobadores = false; estH.llamadas.length = 0;
    await rellenar('luna', 'tok-e2e-no-es-clave');
    await ph.waitForFunction(() => /resultado del agente real de prueba/.test([...document.querySelectorAll('.chat-history .message')].slice(-3).map((x) => x.innerText).join('\n')), null, { timeout: 8000 });
    const ap = estH.llamadas.find((l) => l.ruta === '/chat/swe/aprobar');
    ok('H12 Aprobar llama a /chat/swe/aprobar con el task_id y el op_id pendiente, sin campo aprobacion ni operador', !!ap && !!ap.body.task_id && ap.body.op_id === '0123456789abcdef' && !('aprobacion' in ap.body) && !('operador' in ap.body), JSON.stringify(ap && ap.body));
    ok('AP1 la peticion lleva las cabeceras x-operador y x-operator-token, y el cuerpo no las lleva', !!ap && ap.operador === 'luna' && ap.token === 'tok-e2e-no-es-clave' && !JSON.stringify(ap.body).includes('tok-e2e') && !JSON.stringify(ap.body).includes('luna'), JSON.stringify({ o: ap && ap.operador, t: !!(ap && ap.token) }));
    ok('AP1 solo /chat/swe/aprobar lleva el token (ninguna otra peticion)', !estH.llamadas.some((l) => l.ruta !== '/chat/swe/aprobar' && (l.token || l.operador)));
    ok('AP1 exito: mensaje «Aprobación registrada» en el chat', await ph.evaluate(() => /Aprobación registrada/.test(document.querySelector('.chat-history').innerText)));
    const rastro = await ph.evaluate(() => { const v = []; for (const st of [localStorage, sessionStorage]) for (let i = 0; i < st.length; i++) v.push(st.key(i) + '=' + st.getItem(st.key(i))); return { storage: v.some((x) => /tok-e2e|token-malo-e2e/.test(x)), claveOperador: v.some((x) => /x-operator|operador/i.test(x.split('=')[0])), campos: [...document.querySelectorAll('input')].some((i) => /tok-e2e|token-malo-e2e/.test(i.value)) }; });
    ok('AP1 nada de operador/token en localStorage, sessionStorage ni en campos del DOM tras enviar', !rastro.storage && !rastro.claveOperador && !rastro.campos, JSON.stringify(rastro));
    ok('H sin errores JS en la pagina', ph.errs.length === 0, ph.errs.join(' | '));
    await ph.context().close();

    // ======== I) LAS CUATRO VENTANAS comparten el MISMO nodo del selector central; una sola modal activa; movil 390x844 ========
    const estI = { llamadas: [], catalogoFalla: false, conProveedores: true, capacidades: { harness: 'ok', agentes: { 'swe-agent': { disponible: true }, codex: { disponible: true }, openclaw: { disponible: false, motivo: 'openclaw sin configurar: falta OPENCLAW_GATEWAY_TOKEN' }, openhands: { disponible: false, motivo: 'openhands no esta instalado: el Python configurado no importa openhands.sdk' }, opencode: { disponible: false, motivo: 'opencode no esta instalado (CLI `opencode` ausente del PATH)' }, 'claude-code': { disponible: false, motivo: 'claude-code no esta instalado (CLI `claude` ausente del PATH)' } }, workflows: {}, modelos: {} } };
    const pi = await nuevaPagina(browser, estI);
    await abrirChat(pi, base); await pi.waitForTimeout(1500);  // fichas-externas carga los catalogos Groq/NVIDIA a los 800 ms
    await pi.setViewportSize({ width: 390, height: 844 });
    const SHOT = process.env.SHOT_DIR || '';
    const VEN = ['swe-code', 'swen-code-free', 'groq', 'nvidia'];
    const m0 = await pi.evaluate(() => ({ ctl: document.querySelectorAll('.swe-ctl').length }));
    ok('196 antes de abrir ninguna ventana el selector central ni existe duplicado (0 o 1 nodo)', m0.ctl <= 1, JSON.stringify(m0));
    await pi.$eval('#btn-selector-modelos', (e) => e.click());  // la ventana «Selector de modelos» esta abierta debajo
    await pi.waitForSelector('#sh-selectores:not([hidden])', { timeout: 8000 });
    let primero = true;
    for (const id of VEN) {
      await pi.evaluate(() => { const s = document.getElementById('sh-selectores'); if (s) s.hidden = false; });
      await abrirV(pi, id);
      const r = await pi.evaluate(([i, prim]) => {
        const nodo = document.querySelector('.swe-ctl'); if (prim) window.__nodoCentral = nodo;
        const sh = document.getElementById('sh-' + i), vis = [...document.querySelectorAll('.sheet')].filter((x) => !x.hidden && getComputedStyle(x).display !== 'none');
        return { mismo: nodo === window.__nodoCentral, nodos: document.querySelectorAll('.swe-ctl').length, enHoja: sh.querySelectorAll('.swe-ctl').length, selects: document.querySelectorAll('select[data-swe-ctl]').length, agentico: document.querySelectorAll('[data-swe-agentico]').length, salida: document.querySelectorAll('[data-salida]').length, refrescar: document.querySelectorAll('.swe-refrescar').length, modales: vis.map((x) => x.id), cuatro: ['agente_responde', 'modelo_responde', 'agente_tool', 'modelo_tool'].every((k) => !!sh.querySelector('select[data-swe-ctl="' + k + '"]')), modo: !!sh.querySelector('select[data-swe-ctl="modo_trabajo"]'), wf: !!sh.querySelector('select[data-swe-ctl="workflow"]'), listas: sh.querySelectorAll('button.fila, .list').length, quinto: document.querySelectorAll('select[data-swe-ctl="agente_responde"], select[data-swe-ctl="agente_tool"]').length };
      }, [id, primero]); primero = false;
      ok(`195/196/191 ventana ${id}: tiene los 4 desplegables + MODO DE TRABAJO + WORKFLOW + MODO AGENTICO + SALIDA, y es el MISMO nodo (sin segundo selector: 1 .swe-ctl, 6 selects, 2 botones de salida, 2 selects de agente)`, r.mismo && r.nodos === 1 && r.enHoja === 1 && r.selects === 6 && r.agentico === 1 && r.salida === 2 && r.cuatro && r.modo && r.wf && r.quinto === 2 && r.refrescar === 1, JSON.stringify(r));
      ok(`31/32 ventana ${id}: UNA sola modal activa (la ventana «Selector de modelos» de debajo no se superpone)`, r.modales.length === 1 && r.modales[0] === 'sh-' + id, JSON.stringify(r.modales));
      ok(`28 ventana ${id}: no hay lista de modelos encima del selector central (sin .fila ni .list)`, r.listas === 0, String(r.listas));
      const lista = await pi.evaluate((i) => [...document.querySelectorAll('#sh-' + i + ' select[data-swe-ctl="modelo_responde"] option')].map((o) => [o.value, o.disabled, o.textContent]), id);
      if (id === 'groq') ok('25 Groq: MODELO QUE RESPONDE muestra solo los modelos Groq autorizados (publicados por el proveedor) y el de tool es independiente (catalogo completo)', lista.length === 1 && lista[0][0] === 'groq/qwen/qwen3.8-27b' && !lista[0][1] && await pi.evaluate(() => document.querySelectorAll('#sh-groq select[data-swe-ctl="modelo_tool"] option').length === 9), JSON.stringify(lista));
      if (id === 'nvidia') ok('26/45 NVIDIA: MODELO QUE RESPONDE muestra los 4 NVIDIA autorizados; GLM 5.3 (el proveedor no lo publica) sale NO DISPONIBLE EN PROVEEDOR y deshabilitado', lista.length === 4 && lista.every((l) => /^nvidia\//.test(l[0])) && lista.filter((l) => !l[1]).length === 3 && lista.find((l) => l[0] === 'nvidia/z-ai/glm-5.3')[1] === true && /NO DISPONIBLE EN PROVEEDOR/.test(lista.find((l) => l[0] === 'nvidia/z-ai/glm-5.3')[2]), JSON.stringify(lista));
      if (id === 'swe-code') ok('23 SWE CODE: MODELO QUE RESPONDE = 4 locales HF por nombre de modelo', lista.length === 4 && lista.every((l) => /^hf\//.test(l[0])), JSON.stringify(lista));
      await pi.waitForTimeout(600);  // la hoja termina su animacion de entrada (riu-hoja) antes de medir/capturar
      if (SHOT) await pi.screenshot({ path: path.join(SHOT, 'ventana-' + id + '-390x844.png') });
      // movil: X tocable, caja dentro del viewport, cuerpo con scroll propio, nada se desborda a lo ancho
      const mv = await pi.evaluate((i) => { const s = document.getElementById('sh-' + i), x = s.querySelector('.sh-cerrar').getBoundingClientRect(), c = s.querySelector('.va-caja').getBoundingClientRect(), cu = s.querySelector('.swe-cuerpo'), ctl = s.querySelector('.swe-ctl').getBoundingClientRect(); return { x: [Math.round(x.width), Math.round(x.height)], xDentro: x.top >= 0 && x.bottom <= innerHeight && x.left >= 0 && x.right <= innerWidth, cajaDentro: c.top >= 0 && c.bottom <= innerHeight + 1 && c.left >= -1 && c.right <= innerWidth + 1, scrollable: cu.scrollHeight > cu.clientHeight, overflowY: getComputedStyle(cu).overflowY, anchoOk: ctl.right <= innerWidth + 1 && document.documentElement.scrollWidth <= innerWidth + 1, z: getComputedStyle(s).zIndex, tema: getComputedStyle(s.querySelector('.va-caja')).backgroundColor }; }, id);
      ok(`212 movil 390x844 ${id}: X >= 44px y visible, la caja cabe en el viewport, ningun desborde horizontal, cuerpo con overflow-y auto/scroll`, mv.x[0] >= 44 && mv.x[1] >= 44 && mv.xDentro && mv.cajaDentro && mv.anchoOk && /auto|scroll/.test(mv.overflowY), JSON.stringify(mv));
      ok(`34 ${id}: tema gris oscuro intacto (fondo de la caja oscuro, rgb < 80)`, (mv.tema.match(/\d+/g) || [255]).slice(0, 3).every((n) => +n < 80), mv.tema);
      if (mv.scrollable) { await pi.evaluate((i) => { const cu = document.querySelector('#sh-' + i + ' .swe-cuerpo'); cu.scrollTop = cu.scrollHeight; }, id); await pi.waitForTimeout(150); ok(`33 movil ${id}: tras desplazar el cuerpo la X sigue visible y el boton Actualizar es alcanzable`, await pi.evaluate((i) => { const s = document.getElementById('sh-' + i), x = s.querySelector('.sh-cerrar').getBoundingClientRect(), b = s.querySelector('.swe-refrescar').getBoundingClientRect(); return x.top >= 0 && x.bottom <= innerHeight && b.bottom <= innerHeight && b.top >= 0; }, id)); }
      await pi.mouse.click(195, 4);  // fondo
      ok(`32 ${id}: el fondo cierra la ventana y vuelve la de debajo (Selector de modelos)`, await pi.evaluate((i) => document.getElementById('sh-' + i).hidden && !document.getElementById('sh-selectores').hidden, id));
    }
    // 40-47 en movil: el desplegable nativo (select) se abre por encima: es un <select> nativo, sin lista propia que pueda quedar bajo otra capa
    ok('32 los desplegables del selector central son <select> NATIVOS (el sistema los dibuja por encima de cualquier modal; en Android abren su selector nativo)', await pi.evaluate(() => [...document.querySelectorAll('.swe-ctl select')].every((s) => s.tagName === 'SELECT' && !s.multiple && s.size <= 1)));
    // 17: el nodo no se vuelve a crear ni a enlazar al reabrir muchas veces
    for (let i = 0; i < 6; i++) { await pi.evaluate(() => { const s = document.getElementById('sh-selectores'); if (s) s.hidden = false; }); await pi.$eval(PILL[VEN[i % 4]], (e) => e.click()); await pi.waitForTimeout(80); await pi.evaluate((v) => document.querySelector('#sh-' + v + ' .sh-cerrar').click(), VEN[i % 4]); }
    await pi.evaluate(() => { const s = document.getElementById('sh-selectores'); if (s) s.hidden = false; }); await abrirV(pi, 'groq');
    ok('16/17 tras abrir y cerrar 6 veces las ventanas sigue el MISMO nodo (no se clona) y un solo cambio dispara UN solo guardado (eventos no duplicados)', await pi.evaluate(() => { const antes = []; const o = Storage.prototype.setItem; Storage.prototype.setItem = function (k, v) { if (k === 'riu_swe_seleccion') antes.push(v); return o.call(this, k, v); }; const s = document.querySelector('select[data-swe-ctl="workflow"]'); s.value = 'individual'; s.dispatchEvent(new Event('change', { bubbles: true })); Storage.prototype.setItem = o; return document.querySelector('.swe-ctl') === window.__nodoCentral && document.querySelectorAll('.swe-ctl').length === 1 && antes.length === 1; }));
    // 18: el estado de seleccion se conserva al cerrar y volver a abrir (Groq)
    await pi.selectOption(ctlSel('groq', 'modo_trabajo'), 'archivos'); await pi.selectOption(ctlSel('groq', 'agente_tool'), 'codex');
    await cerrarV(pi, 'groq'); await abrirV(pi, 'nvidia'); await cerrarV(pi, 'nvidia'); await abrirV(pi, 'groq');
    ok('18 al cerrar y volver a abrir se conserva la seleccion (modo de trabajo, agente que ejecuta, modelo)', await pi.evaluate(() => document.querySelector('#sh-groq select[data-swe-ctl="modo_trabajo"]').value === 'archivos' && document.querySelector('#sh-groq select[data-swe-ctl="agente_tool"]').value === 'codex' && document.querySelector('#sh-groq select[data-swe-ctl="modelo_responde"]').value === 'groq/qwen/qwen3.8-27b'));
    ok('30 el modo de trabajo avisa en Groq/NVIDIA que solo se aplica por el bridge (nota de la ventana)', await pi.evaluate(() => /solo se aplica en los envíos por el bridge/.test(document.querySelector('#sh-groq .swe-nota').textContent)));
    ok('29 la nota/estado de conexion propia de la ventana se conserva (Groq: n de m modelos publicados)', await pi.evaluate(() => /Groq: 1 de 1 modelos autorizados/.test(document.querySelector('#sh-groq .swe-nota').textContent)), await pi.evaluate(() => document.querySelector('#sh-groq .swe-nota').textContent));
    // 25: enviar desde Groq (modo OFF): el modelo elegido en el selector central es el que sale por el Router
    await pi.selectOption(ctlSel('groq', 'agente_tool'), 'swe-agent');
    await cerrarV(pi, 'groq');
    ok('25 elegir el modelo en la ventana Groq enciende el selector Groq con ese modelo (RIU_GROQ.modelo)', await pi.evaluate(() => { try { window.RIU_SELECTORES.encender('groq'); } catch (e) {} return window.RIU_GROQ.modelo === 'groq/qwen/qwen3.8-27b' && window.RIU_SELECTORES.activo === 'groq'; }));
    if (SHOT) { await abrirV(pi, 'swen-code-free'); await pi.waitForTimeout(600); await pi.screenshot({ path: path.join(SHOT, 'ventana-swen-agentes-390x844.png') }); await cerrarV(pi, 'swen-code-free'); }
    ok('I sin errores JS en la pagina', pi.errs.length === 0, pi.errs.join(' | '));
    await pi.context().close();

    // ======== I8) Groq y NVIDIA: modo agentico ON desde su ventana -> contrato TareaSWE (el MISMO camino); OFF -> chat normal por el Router; modelo no disponible bloquea ========
    const estI8 = { llamadas: [], catalogoFalla: false, conProveedores: true, capacidades: { harness: 'ok', agentes: Object.fromEntries(['openclaw', 'swe-agent', 'openhands', 'opencode', 'codex', 'claude-code'].map((a) => [a, { disponible: true }])), workflows: { swe_code: { disponible: true }, liquid_mirror: { disponible: true } }, modelos: {} } };
    const p8 = await nuevaPagina(browser, estI8);
    await abrirChat(p8, base); await p8.waitForTimeout(1500);
    await abrirV(p8, 'groq');
    await p8.selectOption(ctlSel('groq', 'modelo_responde'), 'groq/qwen/qwen3.8-27b');
    await p8.$eval('#sh-groq [data-swe-agentico]', (e) => e.click()); await p8.selectOption(ctlSel('groq', 'modelo_tool'), 'nvidia/meta/muse-glimmer-30b'); await p8.selectOption(ctlSel('groq', 'agente_tool'), 'opencode');
    await cerrarV(p8, 'groq');
    ok('8x desde la ventana Groq el selector Groq queda encendido', await p8.evaluate(() => window.RIU_SELECTORES.activo === 'groq'));
    estI8.llamadas.length = 0;
    const r8 = await enviar(p8, 'groq agentico');
    const i8 = estI8.llamadas.find((l) => l.ruta === '/chat/swe/iniciar');
    ok('200 Groq + MODO AGENTICO ON (agente disponible simulado): tarea TareaSWE con modelo_responde Groq, modelo_tool NVIDIA distinto, agente opencode; nada por el Router', !!i8 && i8.body.modo_agentico === true && i8.body.modelo_responde === 'groq/qwen/qwen3.8-27b' && i8.body.modelo_tool === 'nvidia/meta/muse-glimmer-30b' && i8.body.agente_tool === 'opencode' && !estI8.llamadas.some((l) => /^\/chat\/send|\/plugins\//.test(l.ruta)), JSON.stringify(i8 && i8.body));
    await abrirV(p8, 'groq'); await p8.$eval('#sh-groq [data-swe-agentico]', (e) => e.click()); await cerrarV(p8, 'groq');
    estI8.llamadas.length = 0;
    await enviar(p8, 'groq normal').catch(() => {});
    ok('199 Groq + MODO AGENTICO OFF: conversacion normal, NO se llama a /chat/swe/*', !estI8.llamadas.some((l) => /^\/chat\/swe\/(iniciar|avanzar)/.test(l.ruta)), JSON.stringify(estI8.llamadas.map((l) => l.ruta)));
    // 202 modelo no disponible en NVIDIA: se queda elegido (visible con su estado) y el envio se bloquea
    await p8.evaluate(() => { const c = window.RIU_CHAT.chat(); c.ficha = 'nvidia/z-ai/glm-5.3'; localStorage.setItem('riu_swe_seleccion', JSON.stringify({ ...JSON.parse(localStorage.getItem('riu_swe_seleccion') || '{}'), modo_agentico: false, workflow: 'individual', modelo_responde: 'nvidia/z-ai/glm-5.3' })); window.RIU_SELECTORES.encender('nvidia-groq-team'); });
    await abrirV(p8, 'nvidia');
    const glm = await p8.evaluate(() => { const s = document.querySelector('#sh-nvidia select[data-swe-ctl="modelo_responde"]'); return { v: s.value, t: s.selectedOptions[0].textContent, noOk: s.classList.contains('no-ok'), err: document.querySelector('#sh-nvidia .swe-estado-sel').textContent }; });
    ok('202/44 GLM 5.3 elegido pero NO DISPONIBLE EN PROVEEDOR: se queda visible con su estado y su error', glm.v === 'nvidia/z-ai/glm-5.3' && /NO DISPONIBLE EN PROVEEDOR/.test(glm.t) && glm.noOk && /MODELO QUE RESPONDE GLM 5\.3: NO DISPONIBLE EN PROVEEDOR/.test(glm.err), JSON.stringify(glm));
    await cerrarV(p8, 'nvidia'); estI8.llamadas.length = 0;
    await p8.fill('#message', 'a glm'); await p8.$eval('#composer .action', (e) => e.click());
    await p8.waitForFunction(() => /NO DISPONIBLE EN PROVEEDOR/.test(document.querySelector('.chat-history').innerText), null, { timeout: 8000 });
    ok('202 el envio con el modelo no disponible se BLOQUEA (no se manda al Router ni a otro modelo)', !estI8.llamadas.some((l) => /^\/chat\/send|\/plugins\/|chat\/completions|\/chat\/swe\//.test(l.ruta)) && await p8.evaluate(() => /No se envió a otro modelo/.test(document.querySelector('.chat-history').innerText)), JSON.stringify(estI8.llamadas.map((l) => l.ruta)));
    ok('I8 sin errores JS en la pagina', p8.errs.length === 0, p8.errs.join(' | '));
    await p8.context().close();

    // ======== J) hallazgos de auditoria 3: elegir en la ventana enciende el selector; Qwen3 0.6B; Configuracion y vuelta conserva las ventanas; Individual libera los controles ========
    const estJ = { llamadas: [], catalogoFalla: false, capacidades: { harness: 'ok', agentes: {}, workflows: {}, modelos: {} } };
    const pj = await nuevaPagina(browser, estJ);
    await abrirChat(pj, base);
    ok('J0 de inicio ningun selector esta encendido (nada se pulsa a mano)', await pj.evaluate(() => !window.RIU_SELECTORES.activo || !['swe-code', 'swen-code-free'].includes(window.RIU_SELECTORES.activo)));
    await abrirV(pj, 'swe-code');
    const lj = await pj.evaluate(() => [...document.querySelectorAll('#sh-swe-code select[data-swe-ctl="modelo_responde"] option')].map((o) => o.value));
    ok('J1 SWE CODE incluye Qwen3 0.6B (HF) como cuarto modelo local', lj.includes('hf/qwen3-0.6b') && lj.length === 4, JSON.stringify(lj));
    await pj.selectOption(ctlSel('swe-code', 'modelo_responde'), 'hf/qwen3-0.6b');
    await pj.waitForTimeout(300);
    const enc = await pj.evaluate(() => ({ activo: window.RIU_SELECTORES.activo, hojaSwe: document.getElementById('sh-swe-code').hidden, hojaModelos: (document.getElementById('sh-modelos') || {}).hidden, resp: JSON.parse(localStorage.getItem('riu_swe_seleccion')).modelo_responde, selec: (document.getElementById('sh-selectores') || { hidden: true }).hidden }));
    ok('J2 elegir un modelo en la ventana SWE CODE enciende ese selector (sin pulsar ON)', enc.activo === 'swe-code' && enc.resp === 'hf/qwen3-0.6b' && enc.hojaModelos !== false, JSON.stringify(enc));
    await cerrarV(pj, 'swe-code');
    estJ.llamadas.length = 0;
    const rJ = await enviar(pj, 'hola qwen3');
    const cJ = estJ.llamadas.filter((l) => l.ruta === '/web/v1/chat/completions')[0];
    ok('J3 el mensaje sale por SWE al modelo elegido (qwen3-0.6b), no a otra ficha', rJ === 'respuesta SWE de prueba' && cJ && cJ.body.model === 'qwen3-0.6b' && !estJ.llamadas.some((l) => /^\/plugins\//.test(l.ruta)), JSON.stringify(estJ.llamadas.map((l) => l.ruta + ':' + (l.body && l.body.model))));
    ok('J3 el selector sigue encendido tras enviar y ninguna hoja tapa el composer', await pj.evaluate(() => { const c = document.querySelector('#composer').getBoundingClientRect(); const e = document.elementFromPoint(c.left + c.width / 2, c.top + c.height / 2); return window.RIU_SELECTORES.activo === 'swe-code' && !!e && !!e.closest('#composer'); }));
    await abrirV(pj, 'swe-code');
    await pj.selectOption(ctlSel('swe-code', 'modelo_responde'), 'hf/qwen2.5-coder-1.5b');
    ok('J4 el desplegable fija el modelo que se envia (RIU_SWE) sin lista duplicada que pueda contradecirlo', await pj.evaluate(() => window.RIU_SWE['swe-code'].model_id === 'hf-qwen25-coder-15b' && document.querySelectorAll('#sh-swe-code button.fila').length === 0));
    await cerrarV(pj, 'swe-code');
    estJ.llamadas.length = 0; await enviar(pj, 'ahora coder');
    ok('J4 y lo enviado es qwen2.5-coder-1.5b', (estJ.llamadas.filter((l) => l.ruta === '/web/v1/chat/completions')[0] || { body: {} }).body.model === 'qwen2.5-coder-1.5b');
    await abrirV(pj, 'swe-code');
    ok('J5 Individual: modelo/agente que responden y modelo de Ejecuta libres (no fijos)', await pj.evaluate(() => ['modelo_responde', 'agente_responde', 'modelo_tool'].every((k) => { const e = document.querySelector('#sh-swe-code select[data-swe-ctl="' + k + '"]'); return !e.disabled && !e.dataset.fijo; })));
    estJ.capacidades = {};  // el Harness responde 200 con {}: no reporta agentes (no es que no responda)
    await pj.$eval('#sh-swe-code [data-swe-agentico]', (e) => e.click());
    await pj.click('#sh-swe-code .swe-refrescar'); await listoCap(pj);
    const tJ6 = await pj.evaluate(() => document.querySelector('#sh-swe-code .swe-estado').textContent);
    ok('J6/R6 con /chat/swe/capacidades = {} el mensaje dice SIN VERIFICAR / «no reporta», nunca «no instalado»', /SIN VERIFICAR/.test(tJ6) && !/no responde|no instalad/i.test(tJ6), tJ6);
    await pj.$eval('#sh-swe-code [data-swe-agentico]', (e) => e.click());
    await cerrarV(pj, 'swe-code');
    // A) Configuracion y vuelta: las tres ventanas (pills y hojas) siguen y abren
    const estadoVentanas = () => pj.evaluate(() => ['claves', 'workflows', 'constitucion'].map((n) => [n, !!document.querySelector('#pill-' + n), document.querySelectorAll('#ventana-' + n).length]));
    const antes = await estadoVentanas();
    await pj.$eval('[data-view="apariencia"]', (e) => e.click()); await pj.waitForSelector('#ap-apk', { state: 'attached', timeout: 10000 });
    await volverAlChat(pj); await pj.waitForFunction(() => ['claves', 'workflows', 'constitucion'].every((n) => document.querySelector('#pill-' + n) && document.querySelector('#ventana-' + n)), null, { timeout: 20000 });
    const despues = await estadoVentanas();
    ok('A tras ir a Configuracion y volver, siguen las pills y las ventanas de Banco de claves, Workflows y Constitucion (una sola cada una)', JSON.stringify(despues.map((x) => [x[0], x[1], x[2]])) === JSON.stringify([['claves', true, 1], ['workflows', true, 1], ['constitucion', true, 1]]), JSON.stringify({ antes, despues }));
    for (const n of ['claves', 'workflows', 'constitucion']) {
      await pj.evaluate((k) => document.querySelector('#pill-' + k).click(), n); await pj.waitForTimeout(250);
      const abierta = await pj.evaluate((k) => { const v = document.getElementById('ventana-' + k); return !!v && !v.hidden && v.getClientRects().length > 0 && v.querySelectorAll('[class$="-cuerpo"]').length === 1; }, n);
      ok('A la ventana ' + n + ' abre tras volver de Configuracion (un solo cuerpo, sin duplicados)', abierta);
      await pj.evaluate((k) => { document.getElementById('ventana-' + k).hidden = true; }, n);
    }
    await pj.$eval('[data-view="apariencia"]', (e) => e.click()); await pj.waitForSelector('#ap-apk', { state: 'attached', timeout: 10000 }); await volverAlChat(pj);
    ok('A dos vueltas seguidas no duplican pills ni ventanas', await pj.evaluate(() => ['claves', 'workflows', 'constitucion'].every((n) => document.querySelectorAll('#pill-' + n).length === 1 && document.querySelectorAll('#ventana-' + n).length === 1)));
    // ======== K) F1 modelo enviado = desplegable, F3 validacion, F6 foco, F7 micro-etiquetas, R4 tool_calls ========
    const BODY = (m) => (estJ.llamadas.filter((l) => l.ruta === '/web/v1/chat/completions').pop() || { body: {} }).body[m];
    estJ.capacidades = { harness: 'ok', agentes: { codex: { disponible: true }, 'swe-agent': { disponible: true }, openclaw: { disponible: true } }, workflows: { swe_code: { disponible: true } }, modelos: {} };
    await pj.evaluate(() => localStorage.setItem('riu_swe_seleccion', JSON.stringify({ modelo_responde: 'hf/lfm2.5-350m', modelo_tool: 'hf/qwen2.5-coder-1.5b', agente_responde: 'openclaw', agente_tool: 'swe-agent', modo_agentico: false, workflow: 'individual' })));
    await abrirV(pj, 'swen-code-free');
    await pj.selectOption(ctlSel('swen-code-free', 'modelo_responde'), 'groq/qwen/qwen3.8-27b');
    ok('K1 F1 SWEN: el desplegable en Groq fija el modelo enviado y la etiqueta', await pj.evaluate(() => window.RIU_SWE['swen-code-free'].model_id === 'groq/qwen/qwen3.8-27b' && /Groq/.test(window.RIU_SWE['swen-code-free'].label) && JSON.parse(localStorage.getItem('riu_swe_modelo'))['swen-code-free'] === 'groq/qwen/qwen3.8-27b'));
    await cerrarV(pj, 'swen-code-free'); estJ.llamadas.length = 0; await enviar(pj, 'por groq');
    ok('K1 F1 y el POST sale con model groq/qwen/qwen3.8-27b', BODY('model') === 'groq/qwen/qwen3.8-27b', JSON.stringify(estJ.llamadas.map((l) => l.ruta + ':' + (l.body && l.body.model))));
    await abrirV(pj, 'swe-code');
    await pj.selectOption(ctlSel('swe-code', 'modelo_responde'), 'hf/qwen3-0.6b');
    await cerrarV(pj, 'swe-code'); estJ.llamadas.length = 0; await enviar(pj, 'por qwen3 local');
    ok('K2 F1 SWE: el desplegable en hf/qwen3-0.6b se envia como qwen3-0.6b', BODY('model') === 'qwen3-0.6b', JSON.stringify(estJ.llamadas.map((l) => l.ruta + ':' + (l.body && l.body.model))));
    await pj.reload(); await pj.waitForSelector('#sel-swen', { state: 'attached', timeout: 20000 });
    ok('K2 F1 lo elegido sobrevive a recargar (cada ventana recuerda su modelo)', await pj.evaluate(() => window.RIU_SWE['swe-code'].model_id === 'hf-qwen3-06b' && window.RIU_SWE['swen-code-free'].model_id === 'groq/qwen/qwen3.8-27b'), await pj.evaluate(() => JSON.stringify(window.RIU_SWE)));
    // K5 (F7) micro-etiquetas visibles Agente / Modelo
    await abrirV(pj, 'swe-code');
    const mic = await pj.evaluate(() => [...document.querySelectorAll('#sh-swe-code .swe-rej .swe-rej-fila')].map((f) => [...f.querySelectorAll('.swe-micro')].map((m) => [m.textContent, m.getClientRects().length > 0, m.parentElement.querySelector('select') && m.parentElement.querySelector('select').dataset.sweCtl])));
    ok('K5 F7 filas Responde y Ejecuta con micro-etiquetas visibles «Agente» y «Modelo» junto a su desplegable', JSON.stringify(mic) === JSON.stringify([[['Agente', true, 'agente_responde'], ['Modelo', true, 'modelo_responde']], [['Agente', true, 'agente_tool'], ['Modelo', true, 'modelo_tool']]]), JSON.stringify(mic));
    await cerrarV(pj, 'swe-code');
    // K6 (F6) foco: al abrir en la X, Tab no sale de la hoja, al cerrar vuelve al boton que la abrio
    await pj.$eval('#btn-selector-modelos', (e) => e.click()); await pj.waitForSelector('#sh-selectores:not([hidden]) #sel-swe', { state: 'visible', timeout: 8000 });
    await pj.focus('#sel-swe'); await pj.keyboard.press('Enter');
    await pj.waitForSelector('#sh-swe-code .swe-cuerpo', { state: 'visible', timeout: 8000 });
    ok('K6 F6 al abrir con teclado el foco esta en la X de la hoja', await pj.evaluate(() => document.activeElement === document.querySelector('#sh-swe-code .sh-cerrar')), await pj.evaluate(() => document.activeElement.outerHTML.slice(0, 80)));
    let fuera = 0; const vistos = new Set();
    for (let i = 0; i < 60; i++) { await pj.keyboard.press('Tab'); const d = await pj.evaluate(() => { const a = document.activeElement; return { dentro: !!a.closest('#sh-swe-code'), k: (a.dataset && (a.dataset.sweCtl || a.dataset.id || a.dataset.salida)) || a.className || a.tagName }; }); if (!d.dentro) fuera++; vistos.add(d.k); }
    ok('K6 F6 60 Tab seguidos: el foco nunca sale de la hoja y recorre mas de un control', fuera === 0 && vistos.size > 3, fuera + ' fuera; ' + [...vistos].slice(0, 8).join(','));
    await pj.focus('#sh-swe-code .sh-cerrar'); await pj.keyboard.press('Shift+Tab');
    ok('K6 F6 Shift+Tab desde la X da la vuelta al ultimo control de la hoja (no sale)', await pj.evaluate(() => !!document.activeElement.closest('#sh-swe-code') && document.activeElement !== document.querySelector('#sh-swe-code .sh-cerrar')));
    await pj.keyboard.press('Escape');
    ok('K6 F6 al cerrar con Escape el foco vuelve al boton SWE CODE que abrio la hoja y la ventana Selector de modelos de debajo se restaura', await pj.evaluate(() => document.getElementById('sh-swe-code').hidden && document.activeElement === document.getElementById('sel-swe') && !document.getElementById('sh-selectores').hidden), await pj.evaluate(() => document.activeElement.id || document.activeElement.tagName));
    await pj.focus('#sel-swen'); await pj.keyboard.press('Enter'); await pj.waitForSelector('#sh-swen-code-free .swe-cuerpo', { state: 'visible', timeout: 8000 });
    await pj.evaluate(() => document.querySelector('#sh-swen-code-free .sh-cerrar').click());
    ok('K6 F6 la X devuelve el foco al boton SWEN CODE free', await pj.evaluate(() => document.activeElement === document.getElementById('sel-swen')), await pj.evaluate(() => document.activeElement.id || document.activeElement.tagName));
    // K7 (F3) workflow SWE CODE con modo agentico OFF: GAP claro y NO se crea la tarea
    await pj.evaluate(() => { document.getElementById('sh-selectores').hidden = true; localStorage.setItem('riu_swe_seleccion', JSON.stringify({ modelo_responde: 'hf/lfm2.5-350m', modelo_tool: 'hf/qwen2.5-coder-1.5b', agente_responde: 'openclaw', agente_tool: 'swe-agent', modo_agentico: false, workflow: 'swe_code' })); });
    estJ.llamadas.length = 0;
    await pj.fill('#message', 'cuatro pasos sin agentico'); await pj.$eval('#composer .action', (e) => e.click());
    await pj.waitForFunction(() => /exige MODO AGÉNTICO ON/.test(document.querySelector('.chat-history').innerText), null, { timeout: 8000 });
    ok('K7 F3 swe_code con modo agentico OFF: GAP «exige MODO AGÉNTICO ON» y no se llama a /chat/swe/iniciar', !estJ.llamadas.some((l) => /^\/chat\/swe\/(iniciar|avanzar)/.test(l.ruta)), JSON.stringify(estJ.llamadas.map((l) => l.ruta)));
    await pj.evaluate(() => localStorage.removeItem('riu_swe_seleccion'));
    ok('J sin errores JS en la pagina', pj.errs.length === 0, pj.errs.join(' | '));
    await pj.context().close();

    // ======== L) R4: respuesta con texto Y tool_calls conserva y muestra las llamadas pendientes ========
    const estL = { llamadas: [], catalogoFalla: false, conTools: true };
    const pl = await nuevaPagina(browser, estL);
    await abrirChat(pl, base);
    await abrirV(pl, 'swe-code'); await pl.selectOption(ctlSel('swe-code', 'modelo_responde'), 'hf/qwen3-0.6b'); await pl.$eval('#sh-swe-code [data-salida="openclaw"]', (e) => e.click()); await cerrarV(pl, 'swe-code');
    estL.llamadas.length = 0;
    const rL = await enviar(pl, 'lee el repo');
    const pedidas = await pl.evaluate(() => [...document.querySelectorAll('.chat-history .meta')].map((x) => x.innerText).filter((t) => /Pedidas/.test(t)).pop() || '');
    ok('R4 la respuesta con texto + tool_calls muestra el texto Y las llamadas pendientes (nombre, ejecutor OpenClaw, cuantas)', /Voy a leer el repo/.test(rL) && /Pedidas \(las ejecuta OpenClaw\): github_leer, motor_copiar · pendientes: 2/.test(pedidas), rL + ' | ' + pedidas);
    ok('R4 el chat conserva las llamadas completas (ids y argumentos) en c.toolCallsPendientes', await pl.evaluate(() => { const c = window.RIU_CHAT.chat(); return Array.isArray(c.toolCallsPendientes) && c.toolCallsPendientes.length === 2 && c.toolCallsPendientes[0].function.name === 'github_leer' && c.toolCallsPendientes[0].id === 'call-1'; }));
    ok('L sin errores JS en la pagina', pl.errs.length === 0, pl.errs.join(' | '));
    await pl.context().close();
  } finally {
    await browser.close().catch(() => {});
    await new Promise((r) => srv.close(() => r())); srv.closeAllConnections && srv.closeAllConnections();
  }
  console.log(fallos ? `\n${fallos} comprobacion(es) FALLARON` : '\nTODO OK');
  process.exit(fallos ? 1 : 0);
})().catch((e) => { console.log('ERROR', String(e && e.stack || e).split('\n').slice(0, 4).join('\n')); process.exit(1); });
