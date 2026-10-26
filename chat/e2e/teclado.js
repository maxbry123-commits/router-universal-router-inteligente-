// teclado: Tab recorre todo el composer, cada botón tiene foco visible, Enter/Espacio activan, sin scroll horizontal
const { chromium } = require('playwright');
const ok = (n, c, x) => console.log((c ? 'PASS ' : 'FAIL ') + n + (x ? ' :: ' + x : ''));
(async () => {
  const b = await chromium.launch((process.env.CHROMIUM ? { executablePath: process.env.CHROMIUM } : {}));
  for (const w of [320, 390, 1280]) {
    const ctx = await b.newContext({ viewport: { width: w, height: 800 } }); await ctx.addInitScript(() => (sessionStorage.setItem('riu_clave', 'api-e2e'), localStorage.setItem('riu_herr_abiertas', '1')));
    const p = await ctx.newPage(); await p.goto('http://127.0.0.1:8765/chat/ui/shell.html'); await p.waitForSelector('#btn-room', { state: 'attached' }); await p.waitForTimeout(1500);
    ok(w + 'px sin scroll horizontal', await p.evaluate(() => document.documentElement.scrollWidth <= innerWidth + 1), String(await p.evaluate(() => document.documentElement.scrollWidth)));
    await p.screenshot({ path: 'final-' + w + '.png' });
    await p.focus('#message'); const vistos = new Set(); let sinFoco = [];
    for (let i = 0; i < 30; i++) { await p.keyboard.press('Tab'); const d = await p.evaluate(() => { const e = document.activeElement; if (!e || !e.closest('#composer')) return null; const c = getComputedStyle(e); return { id: e.id || e.getAttribute('aria-label') || e.className, foco: c.outlineStyle !== 'none' || c.boxShadow !== 'none' }; }); if (!d) break; vistos.add(d.id); if (!d.foco) sinFoco.push(d.id); }
    const debe = ['btn-adjunto', 'btn-archivos', 'btn-ancla', 'btn-tools', 'btn-agentes', 'btn-prompt'];
    ok(w + 'px Tab llega a todos los botones del composer', debe.every(x => vistos.has(x)), [...vistos].join(','));
    ok(w + 'px foco visible en cada uno', sinFoco.length === 0, sinFoco.join(','));
    const t0 = await p.textContent('#btn-prompt'); await p.focus('#btn-prompt'); await p.keyboard.press('Enter'); await p.waitForFunction((t) => document.querySelector('#btn-prompt').textContent !== t && !document.querySelector('#btn-prompt').disabled, t0);
    await p.keyboard.press(' '); await p.waitForFunction((t) => document.querySelector('#btn-prompt').textContent === t && !document.querySelector('#btn-prompt').disabled, t0);
    ok(w + 'px Enter y Espacio activan un chip', true); await p.keyboard.press('Escape'); await p.waitForTimeout(200);
    await ctx.close();
  }
  await b.close();
})().catch(e => { console.log('ERROR', e.message.split('\n')[0]); process.exit(1); });
