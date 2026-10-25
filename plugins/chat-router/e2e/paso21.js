// Paso 2.1: Conexiones, ROOM CONFERENCIAS (con turno de los agentes) y Servidor contra el Router real local
const { chromium } = require('playwright');
const VP = process.argv[2] === 'desk' ? { width: 1280, height: 800 } : { width: 390, height: 844 };
const NOM = 'cuenta-' + Date.now(), SALA = 'sala-' + Date.now();
const ok = (n, c, x) => console.log((c ? 'PASS ' : 'FAIL ') + n + (x ? ' :: ' + x : ''));
(async () => {
  const b = await chromium.launch((process.env.CHROMIUM ? { executablePath: process.env.CHROMIUM } : {}));
  const ctx = await b.newContext({ viewport: VP, isMobile: VP.width < 500, hasTouch: VP.width < 500 });
  await ctx.addInitScript(() => (sessionStorage.setItem('riu_clave', 'api-e2e'), localStorage.setItem('riu_herr_abiertas', '1')));
  const p = await ctx.newPage(); const errs = []; p.on('pageerror', e => errs.push(e.message)); p.on('dialog', d => d.accept());
  await p.goto('http://127.0.0.1:8765/chat/ui/shell.html'); await p.waitForSelector('#btn-room', { state: 'attached' }); await p.waitForTimeout(1500);
  const vis = (s) => p.evaluate((s) => { const e = document.querySelector(s); const r = e && e.getBoundingClientRect(); return !!r && r.width >= 24 && r.height >= 24; }, s);
  for (const s of ['#btn-tools', '#btn-agentes']) if (/ON/.test(await p.textContent(s))) { await p.$eval(s, e => e.click()); await p.waitForTimeout(500); }  // estado inicial conocido (el servidor recuerda)
  await p.click('#cb-sel-herr'); await p.waitForTimeout(300);
  for (const s of ['#btn-conexiones', '#btn-room', '#btn-power']) ok('botón visible ≥24px (ventana Herramientas) ' + s, await vis(s));
  await p.keyboard.press('Escape'); await p.waitForTimeout(200);
  ok('iconos de línea, sin emoji', await p.evaluate(() => ['#btn-conexiones', '#btn-room', '#btn-power'].every(s => document.querySelector(s).querySelector('svg') && !/\p{Extended_Pictographic}/u.test(document.querySelector(s).textContent))));
  // Conexiones
  await p.$eval('#btn-conexiones', e => e.click()); await p.waitForSelector('#ventana-conexiones select');
  ok('Conexiones: servicios del servidor', (await p.locator('#ventana-conexiones select option').count()) >= 2);
  await p.fill('#ventana-conexiones input[aria-label="nombre de la conexión"]', NOM); await p.fill('#ventana-conexiones input[type=password]', 'ghp_SECRETOdeprueba1234567890');
  await p.click('#cv-anadir'); await p.waitForTimeout(800);
  ok('Conexiones: añadir credencial', await p.locator('#ventana-conexiones .cv-fila', { hasText: NOM }).count() === 1);
  ok('Conexiones: el secreto no vuelve al navegador', !(await p.content()).includes('SECRETOdeprueba'));
  const t = p.locator('#ventana-conexiones .cv-fila', { hasText: NOM }).locator('.toggle'); const antes = await t.textContent(); await t.click(); await p.waitForTimeout(600);
  ok('Conexiones: ON/OFF cambia en el servidor', (await p.locator('#ventana-conexiones .cv-fila', { hasText: NOM }).locator('.toggle').textContent()) !== antes);
  const qb = p.locator('#ventana-conexiones .cv-fila', { hasText: NOM }).getByRole('button', { name: 'Quitar ' + NOM }); await qb.click(); await qb.click(); await p.waitForTimeout(700);
  ok('Conexiones: quitar (con confirmación) la borra del servidor', await p.locator('#ventana-conexiones .cv-fila', { hasText: NOM }).count() === 0);
  await p.keyboard.press('Escape'); ok('Escape cierra Conexiones', await p.locator('#ventana-conexiones').evaluate(e => e.hidden));
  // ROOM
  await p.$eval('#btn-room', e => e.click()); await p.waitForSelector('#cv-sala-crear');
  await p.fill('#ventana-room input[aria-label="nombre de la sala"]', SALA); await p.selectOption('#ventana-room select', 'escritura'); await p.click('#cv-sala-crear'); await p.waitForTimeout(700);
  ok('ROOM: crear sala', await p.locator('#ventana-room .cv-fila', { hasText: SALA }).count() >= 1);
  await p.locator('#ventana-room .cv-fila', { hasText: SALA }).first().getByText('Abrir').click(); await p.waitForTimeout(600);
  await p.fill('#ventana-room input[aria-label="mensaje"]', 'hola sala'); await p.locator('#ventana-room button.action', { hasText: 'Enviar' }).click(); await p.waitForTimeout(700);
  ok('ROOM: mensaje enviado y visible', await p.locator('#ventana-room .cv-msg', { hasText: 'hola sala' }).count() === 1);
  await p.locator('#ventana-room button', { hasText: 'Turno de los agentes' }).click(); await p.waitForTimeout(2500);
  const est = await p.locator('#ventana-room .cv-est').textContent(); const msgs = await p.locator('#ventana-room .cv-msg').count();
  ok('ROOM: turno de los agentes responde o explica por qué no', msgs > 1 || /Sin responder|Nadie habló/.test(est), 'msgs=' + msgs + ' est=' + est);
  ok('ROOM: lista de agentes y modelos para invitar', await p.locator('#cv-part-lista option').count() >= 10);
  await p.fill('#ventana-room input[aria-label="nuevo participante"]', 'qwen3.7-plus'); await p.locator('#ventana-room .cv-form select').last().selectOption('escritura'); await p.locator('#ventana-room button', { hasText: 'Invitar' }).click(); await p.waitForTimeout(700);
  await p.locator('#ventana-room button', { hasText: 'Turno de los agentes' }).click(); await p.waitForTimeout(2000);
  ok('ROOM: con IA OFF el modelo no habla y se explica', /Sin responder: qwen3.7-plus/.test(await p.locator('#ventana-room .cv-est').textContent()), await p.locator('#ventana-room .cv-est').textContent());
  await p.keyboard.press('Escape'); await p.$eval('#btn-tools', e => e.click()); await p.waitForFunction(() => /ON/.test(document.querySelector('#btn-tools').textContent)); await p.$eval('#btn-room', e => e.click()); await p.waitForTimeout(800);
  await p.locator('#ventana-room .cv-fila', { hasText: SALA }).first().getByText('Abrir').click(); await p.waitForTimeout(600);
  await p.locator('#ventana-room button', { hasText: 'Turno de los agentes' }).click(); await p.waitForTimeout(4000);
  ok('ROOM: con IA ON el modelo responde en la sala', await p.locator('#ventana-room .cv-msg', { hasText: 'qwen3.7-plus' }).count() >= 1, await p.locator('#ventana-room .cv-est').textContent());
  await p.keyboard.press('Escape'); await p.$eval('#btn-tools', e => e.click()); await p.waitForTimeout(600); await p.$eval('#btn-room', e => e.click()); await p.waitForTimeout(800);
  await p.locator('#ventana-room .cv-fila', { hasText: SALA }).first().getByText('Abrir').click(); await p.waitForTimeout(600);
  await p.fill('#ventana-room input[aria-label="nuevo participante"]', 'revisor'); await p.locator('#ventana-room button', { hasText: 'Invitar' }).click(); await p.waitForTimeout(600);
  ok('ROOM: invitar participante', await p.locator('#ventana-room .cv-fila', { hasText: 'revisor' }).count() >= 1);
  await p.locator('#ventana-room button', { hasText: 'Borrar sala' }).click(); await p.waitForTimeout(700);
  ok('ROOM: borrar sala', await p.locator('#ventana-room .cv-fila', { hasText: SALA }).count() === 0);
  await p.keyboard.press('Escape');
  // Servidor
  await p.$eval('#btn-power', e => e.click()); await p.waitForFunction(() => /RUNNING/.test(document.querySelector('#ventana-power .tag-status').textContent));
  ok('Servidor: estado real RUNNING', true);
  const ap = await p.locator('#ventana-power button', { hasText: 'Apagar' }).elementHandle(); await ap.click(); ok('Servidor: Apagar pide confirmación', /Confirmar/.test(await ap.textContent()));
  await ap.click(); await p.waitForTimeout(800); ok('Servidor: tras confirmar queda en pausa', /PAUSED/.test(await p.locator('#ventana-power .tag-status').textContent()));
  await p.locator('#ventana-power button', { hasText: 'Encender' }).click(); await p.waitForTimeout(600);
  ok('Servidor: Encender arranca', /BUILDING|RUNNING/.test(await p.locator('#ventana-power .tag-status').textContent()));
  ok('sin errores JS', errs.length === 0, errs.join(' | '));
  await b.close();
})().catch(e => { console.log('ERROR', e.message.split('\n')[0]); process.exit(1); });
