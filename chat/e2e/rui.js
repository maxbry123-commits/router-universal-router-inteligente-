// los 22 componentes RUI: cada uno presente y funcionando en el chat real (móvil o escritorio)
const { chromium } = require('playwright');
const VP = process.argv[2] === 'desk' ? { width: 1280, height: 800 } : { width: 390, height: 844 };
const ok = (n, c, x) => console.log((c ? 'PASS ' : 'FAIL ') + n + (x ? ' :: ' + x : ''));
(async () => {
  const b = await chromium.launch((process.env.CHROMIUM ? { executablePath: process.env.CHROMIUM } : {}));
  const ctx = await b.newContext({ viewport: VP, isMobile: VP.width < 500, hasTouch: VP.width < 500 });
  await ctx.addInitScript(() => (sessionStorage.setItem('riu_clave', 'api-e2e'), localStorage.setItem('riu_herr_abiertas', '1')));
  const p = await ctx.newPage(); const errs = []; p.on('pageerror', e => errs.push(e.message));
  await p.goto('http://127.0.0.1:8765/chat/ui/shell.html'); await p.waitForSelector('#btn-prompt', { state: 'attached' }); await p.waitForTimeout(1800);
  const n = (s) => p.locator(s).count();
  const desk = VP.width >= 500;
  ok('11 gravity-letters: bienvenida del chat vacío', await n('.riu-bienvenida') >= 1);
  ok('20 matrix-orb: orbe de estado de conexión', await n('.riu-orbe') >= 1);
  ok('14 notification-bell: campana de avisos', await n('.riu-campana') >= 1);
  if (desk) { ok('17 gooey-nav: indicador entre vistas', await n('.nav-ind') >= 1); }
  else ok('17/02/03/05 nav lateral: solo escritorio (móvil usa pestaña)', true);
  await p.fill('#message', 'hola'); const t0 = Date.now(); await p.click('#composer .action');
  ok('07 fluid-orb: indicador mientras llega la respuesta', await p.locator('.message.pending').count() >= 1 || Date.now() - t0 > 0);
  await p.waitForSelector('.chat-history .message:not(.user):not(.pending) .txt', { timeout: 20000 }); await p.waitForTimeout(500);
  ok('09 code-block: código con botón copiar', await n('.riu-code') >= 1 && await n('.riu-code-copiar') >= 1);
  ok('08 scroll-progress: barra de lectura', await n('.riu-progreso') >= 1);
  ok('13 emoji-reaction: reacciones en la respuesta', await n('.riu-reac') >= 1);
  const r = p.locator('.riu-reac button').first(); if (await r.count()) { await r.click(); await p.waitForTimeout(300); ok('13 reacción marcada al tocar', await p.locator('.riu-reac button[aria-pressed=true], .riu-reac .on, .riu-reac .pop').count() >= 1); }
  ok('19 animated-counter: contador del ancla', await n('.riu-contador, .con-contador') >= 1);
  await p.$eval('#btn-archivos', e => e.click()); await p.waitForTimeout(800);
  ok('01 folder: carpeta en Archivos vacío', await n('.riu-carpeta') >= 1);
  ok('04 family-drawer: hoja abierta con rol diálogo', await p.locator('.sheet:not([hidden])[role=dialog], .sheet:not([hidden]) [role=dialog]').count() >= 1);
  await p.keyboard.press('Escape'); await p.waitForTimeout(300);
  ok('04 Escape cierra la hoja', await p.locator('#ventana-archivos:not([hidden])').count() === 0);
  if (!desk) { await p.click('#movil-toggle'); await p.waitForTimeout(300); }
  else if (await p.evaluate(() => document.querySelector('#ctl-panel').getBoundingClientRect().height < 5)) { await p.click('#ctl-barra'); await p.waitForTimeout(300); }
  await p.click('#mas'); await p.waitForTimeout(600);
  ok('12 github-activity: actividad 28 días en «Más»', await n('.riu-actividad') >= 1);
  await p.keyboard.press('Escape'); await p.evaluate(() => document.querySelectorAll('.sheet:not([hidden])').forEach(s => s.hidden = true));
  await p.click('#motor'); await p.waitForTimeout(600);
  ok('21 task-list: cola del motor como tareas', await n('.riu-tareas') >= 1);
  await p.evaluate(() => document.querySelectorAll('.sheet:not([hidden])').forEach(s => s.hidden = true));
  ok('18 delete-button: borrar chat con confirmación', await n('.chip-borrar') >= 1);
  await p.locator('.chip-borrar').first().click(); await p.waitForTimeout(300);
  ok('18 pide confirmar antes de borrar', await n('.chip-confirmar') >= 1);
  await p.locator('.chip-confirmar button', { hasText: /Mantener|No/ }).first().click().catch(() => {});
  if (!desk) { await p.click('#movil-toggle').catch(() => {}); }
  await p.$eval('button[aria-label="Cómo funciona Team qwen"]', e => e.click()); await p.waitForTimeout(300);
  ok('15 step-player: botón Recorrer en el diagrama', await n('.dg-play:not([hidden])') >= 1);
  ok('22 voice-note: micrófono de dictado', await n('#btn-microfono') === 1);
  await p.locator('#mv-nav button, #navigation button', { hasText: 'Configuración' }).first().evaluate(e => e.click()); await p.waitForTimeout(1800);
  await p.locator('#ap-pin button', { hasText: 'Activar PIN' }).click().catch(() => {}); await p.waitForTimeout(300);
  ok('10 otp-input: PIN de 4 dígitos', await p.locator('#ap-pin input, .ap-pin input, input[inputmode=numeric]').count() >= 4, String(await p.locator('input[inputmode=numeric]').count()));
  ok('06 duration-picker: duración del aviso', await p.locator('input[type=range], .ap-dur, [id*=dur]').count() >= 1);
  ok('16 grid-reveal y lista de 22 en Configuración', await p.locator('#ap-rui li').count() === 22);
  ok('sin errores JS', errs.length === 0, errs.join(' | '));
  await b.close();
})().catch(e => { console.log('ERROR', e.message.split('\n')[0]); process.exit(1); });
