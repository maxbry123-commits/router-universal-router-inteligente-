// dos navegadores distintos (otro dispositivo): el historial y las pestañas vuelven desde /memoria
const { chromium } = require('playwright');
const URL = 'http://127.0.0.1:8765/chat/ui/shell.html', ok = (n, c, x) => console.log((c ? 'PASS ' : 'FAIL ') + n + (x ? ' :: ' + x : ''));
(async () => {
  const b = await chromium.launch((process.env.CHROMIUM ? { executablePath: process.env.CHROMIUM } : {}));
  const nuevo = async () => { const ctx = await b.newContext({ viewport: { width: 1280, height: 800 } }); await ctx.addInitScript(() => (sessionStorage.setItem('riu_clave', 'api-e2e'), localStorage.setItem('riu_herr_abiertas', '1'))); const p = await ctx.newPage(); await p.goto(URL); await p.waitForSelector('#btn-prompt', { state: 'attached' }); await p.waitForTimeout(1500); return p; };
  const a = await nuevo(); const marca = 'dispositivo-' + Date.now();
  await a.fill('#message', marca); await a.click('#composer .action'); await a.waitForSelector('.chat-history .message:not(.user):not(.pending) .txt', { timeout: 20000 }); await a.waitForTimeout(2500);
  const ses = await a.evaluate(() => document.querySelector('#chat-tabs .chip.on').title);
  const c = await nuevo();
  const rec = c.locator('#chat-tabs button', { hasText: '↺' }); ok('botón recuperar existe', await rec.count() >= 1);
  await rec.first().evaluate(e => e.click()); await c.waitForTimeout(3000);
  const tabs = await c.evaluate(() => [...document.querySelectorAll('#chat-tabs .chip')].map(x => x.title));
  ok('la pestaña del otro dispositivo vuelve', tabs.some(t => t.includes(ses.split('sesión ')[1])), JSON.stringify(tabs));
  const txt = await c.evaluate(() => [...document.querySelectorAll('.chat-history')].map(h => h.innerText).join('\n'));
  ok('su mensaje vuelve', txt.includes(marca));
  await b.close();
})().catch(e => { console.log('ERROR', e.message.split('\n')[0]); process.exit(1); });
