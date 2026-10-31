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
  const CORS = { 'access-control-allow-origin': '*', 'access-control-allow-headers': '*', 'access-control-allow-methods': 'GET,POST,OPTIONS' };
  const json = (route, obj, status = 200) => route.fulfill({ status, headers: { ...CORS, 'content-type': 'application/json' }, body: JSON.stringify(obj) });
  return async (route) => {
    const req = route.request(); const u = new URL(req.url()); const p = u.pathname;
    if (req.method() === 'OPTIONS') return route.fulfill({ status: 204, headers: CORS });
    let body = null; try { body = req.postDataJSON(); } catch (e) {}
    estado.llamadas.push({ metodo: req.method(), ruta: p, body, clave: req.headers()['x-api-key'] || '' });
    if (p === '/chat/providers/qwen/models') {
      if (estado.catalogoFalla) return json(route, { detail: 'caido' }, 500);
      // catalogo del Router MVP: SIN ningun modelo SWE; 'zz-modelo-mock' prueba que se cargo este catalogo y no el de respaldo
      return json(route, { models: [{ model_id: 'qwen3.8-max', tipo: 'texto' }, { model_id: 'glm-5.2', tipo: 'texto' }, { model_id: 'deepseek-v4-pro', tipo: 'texto' }, { model_id: 'zz-modelo-mock', tipo: 'texto' }] });
    }
    if (p === '/chat/providers') return json(route, { providers: [{ id: 'qwen', nombre: 'Qwen', estado: 'ok' }] });
    if (p === '/v1/chat/completions' && req.method() === 'POST') {
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

const abrirChat = async (p, base) => { await p.goto(base + '/chat/ui/shell.html'); await p.waitForSelector('#sel-nuevo', { state: 'attached', timeout: 20000 }); await p.waitForTimeout(1500); };
const abrirHojaModelos = async (p) => { await p.$eval('#sel-nuevo', (e) => e.click()); await p.waitForSelector('#sh-modelos-lista button', { state: 'attached', timeout: 10000 }); };
const grupos = (p) => p.evaluate(() => [...document.querySelectorAll('#sh-modelos-lista h4.mod-grupo-t')].map((h) => h.textContent.trim()));
const elegir = (p, nombre) => p.evaluate((n) => { const b = [...document.querySelectorAll('#sh-modelos-lista button.mod-fila')].find((x) => x.querySelector('b').textContent.trim() === n); if (b) b.click(); return !!b; }, nombre);
const burbujasBot = (p) => p.locator('.chat-history .message:not(.user):not(.pending):not(.meta) .txt');
async function enviar(p, texto) {
  const n = await burbujasBot(p).count();
  await p.fill('#message', texto); await p.$eval('#composer .action', (e) => e.click());
  await p.waitForFunction((k) => document.querySelectorAll('.chat-history .message:not(.user):not(.pending):not(.meta) .txt').length > k, n, { timeout: 15000 });
  return (await burbujasBot(p).last().innerText()).trim();
}

(async () => {
  const srv = await servirFrontend(); const base = 'http://127.0.0.1:' + srv.address().port;
  const browser = await chromium.launch((process.env.CHROMIUM ? { executablePath: process.env.CHROMIUM } : {}));
  try {
    // ======== A) catalogo del Router SIN modelos SWE: el selector igual lista los dos grupos SWE ========
    const estA = { llamadas: [], catalogoFalla: false };
    const p = await nuevaPagina(browser, estA);
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
    ok('A1 filas SWE presentes (Liquid AI (HF), Qwen 3.8 Max (web), Concilio, SWE · asesoria)', ['Liquid AI (HF)', 'Qwen 3.8 Max (web)', 'Concilio', 'SWE · asesoria'].every((n) => filas.includes(n)), filas.join(' | '));
    const ids = await p.evaluate(() => window.RIU_SELECTOR_QWEN.modelos.map((m) => m.model_id));
    ok('A1 RIU_SELECTOR_QWEN.modelos expone ids web-*/swecode-*/hf-*', ['web-qwen38max', 'swecode-consulta', 'hf-liquid-lfm25', 'swe-agent-lfm25'].every((i) => ids.includes(i)));

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
    ok('B6 elegir "Liquid AI (HF)"', (await abrirHojaModelos(p), await elegir(p, 'Liquid AI (HF)')));
    estA.llamadas.length = 0;
    const r2 = await enviar(p, 'segundo mensaje');
    const c2 = estA.llamadas.filter((l) => l.ruta === '/v1/chat/completions')[0];
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
    ok('A-C sin errores JS en la pagina', p.errs.length === 0, p.errs.join(' | '));
    await p.context().close();

    // ======== D) el Router falla y no hay catalogo guardado: la lista de respaldo tambien trae los grupos SWE ========
    const estD = { llamadas: [], catalogoFalla: true };
    const pd = await nuevaPagina(browser, estD);
    await abrirChat(pd, base); await abrirHojaModelos(pd);
    const gd = await grupos(pd);
    ok('D1 Router caido + sin cache: aparecen los grupos SWE (lista de respaldo)', gd.includes('SWE CODE (local HF)') && gd.includes('SWEN CODE free (web)'), JSON.stringify(gd));
    const fd = await pd.evaluate(() => [...document.querySelectorAll('#sh-modelos-lista button.mod-fila b')].map((b) => b.textContent.trim()));
    ok('D2 la lista de respaldo trae TODOS los modelos SWE (incl. "SWE · asesoria")', fd.includes('SWE · asesoria'), fd.filter((t) => /SWE/.test(t)).join(' | '));
    await pd.context().close();

    // ======== E) Router caido pero con el ultimo catalogo del Router guardado en localStorage (sin SWE) ========
    const estE = { llamadas: [], catalogoFalla: true };
    const pe = await nuevaPagina(browser, estE, { catalogoLocal: ['qwen3.8-max', 'glm-5.2', 'deepseek-v4-pro'] });
    await abrirChat(pe, base); await abrirHojaModelos(pe);
    const ge = await grupos(pe);
    ok('E1 Router caido + catalogo guardado sin SWE: siguen los grupos SWE', ge.includes('SWE CODE (local HF)') && ge.includes('SWEN CODE free (web)'), JSON.stringify(ge));
    await pe.context().close();
  } finally {
    await browser.close().catch(() => {});
    await new Promise((r) => srv.close(() => r())); srv.closeAllConnections && srv.closeAllConnections();
  }
  console.log(fallos ? `\n${fallos} comprobacion(es) FALLARON` : '\nTODO OK');
  process.exit(fallos ? 1 : 0);
})().catch((e) => { console.log('ERROR', String(e && e.stack || e).split('\n').slice(0, 4).join('\n')); process.exit(1); });
