const { chromium } = require('playwright-core');
const exe = '/home/box/.cache/ms-playwright/chromium_headless_shell-1248/chrome-headless-shell-linux64/chrome-headless-shell';
(async () => {
  const b = await chromium.launch({ executablePath: exe, args:['--use-gl=swiftshader','--enable-unsafe-swiftshader'] });
  const ctx = await b.newContext({ viewport: { width: 412, height: 915 }, deviceScaleFactor: 2.625, isMobile: true, hasTouch: true, userAgent: 'Mozilla/5.0 (Linux; Android 14; Pixel 8) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130 Mobile Safari/537.36' });
  const p = await ctx.newPage(); const errs = [];
  p.on('pageerror', e => errs.push('pageerror: ' + e.message)); p.on('console', m => { if (m.type() === 'error') errs.push('console: ' + m.text()); });
  const cdp = await ctx.newCDPSession(p); await cdp.send('Network.emulateNetworkConditions', { offline: false, latency: 150, downloadThroughput: 4e6 / 8, uploadThroughput: 3e6 / 8 });
  const t0 = Date.now(); await p.goto('http://127.0.0.1:8765/chat/ui/rui-demo.html'); await p.waitForFunction(() => window.__ruiListo, null, { timeout: 30000 });
  const ms = Date.now() - t0; console.log(`carga 4G: ${Math.floor(ms/1000)} s ${String(ms%1000).padStart(3,'0')} ms`);
  const R = {}; const ok = (n, c, d) => { R[n] = (c ? 'OK ' : 'FALLA ') + (d || ''); };
  const shot = async (n, suf='') => { const s = p.locator('#rui-' + n); await s.scrollIntoViewIfNeeded(); await s.screenshot({ path: `/workspace/shots/rui/rui-${String(n).padStart(2,'0')}${suf}.png` }); };
  const ev = (f, a) => p.evaluate(f, a);
  // 1
  await p.locator('#d1 .rui-folder').click(); await p.waitForTimeout(1200); ok(1, await ev(() => document.querySelector('#d1 .rui-folder').getAttribute('aria-expanded') === 'true'), 'abre al tocar'); await shot(1);
  // 2
  await p.locator('#d2 button', { hasText: 'Proyectos' }).click(); await p.waitForTimeout(500); ok(2, await ev(() => document.querySelector('#d2 button[data-active=true]').textContent === 'Proyectos' && getComputedStyle(document.querySelector('.rui-bounce-dot')).opacity === '1'), 'punto se mueve'); await shot(2);
  // 3
  await p.locator('#d3 button', { hasText: 'Constitución' }).click(); await p.waitForTimeout(600); ok(3, await ev(() => { const l = document.querySelectorAll('#d3 .rui-hook-line')[1]; return document.querySelector('#d3 button[data-active=true]').textContent === 'Constitución' && parseFloat(l.style.height) > 20; }), 'gancho baja'); await shot(3);
  // 4
  await p.locator('#d4 button').click(); await p.waitForTimeout(700); await p.locator('.rui-fd-btn', { hasText: 'Quitar' }).click(); await p.waitForTimeout(600);
  const fd = await ev(() => !!document.querySelector('.rui-fd.on') && document.querySelector('.rui-fd h2:last-of-type') && [...document.querySelectorAll('.rui-fd h2')].pop().textContent);
  await p.screenshot({ path: '/workspace/shots/rui/rui-04.png' }); await p.keyboard.press('Escape'); await p.locator('.rui-fd-x').click({ trial: false }).catch(()=>{}); await p.waitForTimeout(600);
  ok(4, fd === '¿Seguro?' && await ev(() => !document.querySelector('.rui-fd')), 'abre, cambia vista, cierra');
  // 5
  await ev(() => document.getElementById('l5').scrollTop = 400); await p.waitForTimeout(500); ok(5, await ev(() => { const a = document.querySelector('#d5 .rui-prox-dash[data-active=true]'); return a && a.getAttribute('aria-label') !== 'Introducción'; }), 'sigue el scroll'); await shot(5);
  // 6
  await p.locator('#d6 .rui-dur-btn').click(); await p.locator('#d6 input').first().fill('3'); await p.locator('#d6 input').nth(1).fill('99'); await p.locator('#d6 .rui-dur-btn').click(); await p.waitForTimeout(400);
  ok(6, (await p.textContent('#o6')) === 'Confirmado: 3 h 59 min', await p.textContent('#o6')); await shot(6);
  // 7
  await p.waitForTimeout(500); ok(7, await ev(() => { const c = document.querySelector('#d7 canvas'); return !c.parentElement.dataset.error && c.width > 0; }), 'WebGL'); await shot(7);
  // 8
  await ev(() => document.getElementById('l8').scrollTop = 260); await p.waitForTimeout(900); const lb8 = await p.textContent('#l8 .rui-sp-lbl'); await p.locator('#l8 .rui-sp-head').click(); await p.waitForTimeout(600);
  ok(8, lb8 !== 'Resumen' && await ev(() => !document.querySelector('#l8 .rui-sp-list').hidden), 'etiqueta=' + lb8 + ', lista abre'); await shot(8);
  // 9
  await ctx.grantPermissions(['clipboard-read', 'clipboard-write']); await p.locator('#d9 .rui-code-copy').click(); await p.waitForTimeout(200); ok(9, (await p.getAttribute('#d9 .rui-code-copy', 'aria-label')) === 'Copiado' && await ev(() => document.querySelectorAll('#d9 .t-k').length > 2), 'copia + resalta'); await shot(9);
  // 10
  await p.locator('#d10 input').first().click(); await p.keyboard.type('123456'); await p.waitForTimeout(500); ok(10, (await p.textContent('#o10')) === 'Código correcto', await p.textContent('#o10')); await shot(10);
  // 11
  await ev(() => { window.__pd = 0; document.querySelector('#d11 .rui-grav').addEventListener('pointerdown', () => window.__pd++); }); const g = p.locator('#d11 .rui-grav'); await g.scrollIntoViewIfNeeded(); const bb = await g.boundingBox(); for (let i = 0; i < 14; i++) { await p.mouse.click(bb.x + 20 + i * 26, bb.y + 30); await p.waitForTimeout(60); } await p.waitForTimeout(1800);
  const g1 = await ev(() => [...document.querySelectorAll('#d11 span')].map(x => x.style.transform).join('|')); await p.waitForTimeout(400); const g2 = await ev(() => [...document.querySelectorAll('#d11 span')].map(x => x.style.transform).join('|')); const pd = await ev(() => window.__pd); ok(11, g1 === g2 && g1.split('|').length === pd && pd >= 10, 'caen y reposan (' + g1.split('|').length + ', estable=' + (g1===g2) + ')'); await shot(11);
  // 12
  await p.waitForTimeout(4000); const gh = await ev(() => ({ n: document.querySelectorAll('#d12 .rui-gh-grid i').length, e: (document.querySelector('#d12 .rui-gh-err') || {}).textContent }));
  ok(12, gh.n > 300 || !!gh.e, gh.n + ' celdas ' + (gh.e || '')); await shot(12);
  // 13
  await p.locator('#d13 .rui-emo-trig').click(); await p.waitForTimeout(350); await p.locator('#d13 .rui-emo-bar button').first().click(); await p.waitForTimeout(250); await shot(13);
  ok(13, (await p.textContent('#d13 .rui-emo-cnt')).includes('1'), 'cuenta ' + await p.textContent('#d13 .rui-emo-cnt'));
  // 14
  await p.locator('#d14 .pill').click(); await p.locator('#d14 .pill').click(); await p.waitForTimeout(150); await shot(14); ok(14, (await p.textContent('#d14 .rui-bell-badge')) === '2', 'badge 2');
  // 15
  await p.locator('#d15 .rui-step-btn').click(); await p.waitForTimeout(2000); await shot(15); ok(15, await ev(() => document.querySelectorAll('#d15 .rui-step-seg.done').length >= 1), 'avanza');
  // 16
  await p.waitForTimeout(1500); ok(16, await ev(() => !document.querySelector('#d16 .rui-grid[data-error]')), 'sin error'); await shot(16);
  // 17
  await p.locator('#d17 button', { hasText: 'Router' }).click(); await p.waitForTimeout(700); ok(17, (await p.getAttribute('#d17 button:nth-child(2)', 'aria-selected')) === 'true', 'tab activa'); await shot(17);
  // 18
  await p.locator('#d18 .rui-del-tile').click(); await p.waitForTimeout(800); await shot(18, '-abierto'); await p.locator('#d18 .rui-del-c').first().click(); await p.waitForTimeout(150); ok(18, (await p.textContent('#d18 .rui-del-msg')) === 'Eliminado', 'confirma'); await shot(18);
  // 19
  await p.locator('#d19 .pill').click(); await p.waitForTimeout(1500); ok(19, (await p.getAttribute('#d19 .rui-cnt', 'aria-label')) === '1,417', await p.getAttribute('#d19 .rui-cnt', 'aria-label')); await shot(19);
  // 20
  await p.locator('#d20 .pill', { hasText: 'thinking' }).click(); await p.waitForTimeout(800); ok(20, (await p.textContent('#d20 .rui-orb-lbl')) === 'Pensando', 'estado'); await shot(20);
  // 21
  await p.locator('#d21 .rui-task').first().click(); await p.waitForTimeout(1400); ok(21, await ev(() => [...document.querySelectorAll('#d21 .rui-task-t')].pop().textContent === 'Rebase en main'), 'tachada va al final'); await shot(21);
  // 22
  await shot(22); ok(22, await ev(() => !!document.querySelector('#d22 .rui-voz')), 'monta');
  await p.screenshot({ path: '/workspace/shots/rui/rui-demo-completa.png', fullPage: true });
  Object.entries(R).forEach(([k, v]) => console.log('RUI ' + k + ': ' + v)); console.log('errores:', errs.length ? errs : 'ninguno');
  await b.close();
})().catch(e => { console.error(e); process.exit(1); });
