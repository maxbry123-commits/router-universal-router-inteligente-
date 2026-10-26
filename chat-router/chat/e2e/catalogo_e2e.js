// Los modelos aparecen aunque el Router tarde o falle: lista guardada / catálogo del plan, reintento y mensaje claro (no «signal is aborted»).
const { chromium } = require('playwright');
const ok = (n, c, x) => console.log((c ? 'PASS ' : 'FAIL ') + n + (x ? ' :: ' + x : ''));
(async () => {
  const b = await chromium.launch((process.env.CHROMIUM ? { executablePath: process.env.CHROMIUM } : {}));
  for (const caso of ['router-caido', 'router-ok']) {
    const ctx = await b.newContext({ viewport: { width: 390, height: 844 }, isMobile: true, hasTouch: true });
    await ctx.addInitScript(() => { sessionStorage.setItem('riu_clave', 'api-e2e'); });
    const p = await ctx.newPage(); const errs = []; p.on('pageerror', e => errs.push(e.message));
    if (caso === 'router-caido') await p.route(/\/chat\/providers/, r => r.abort('timedout'));
    await p.goto('http://127.0.0.1:8765/chat/ui/shell.html'); await p.waitForSelector('#btn-selector-modelos'); await p.waitForTimeout(2000);
    await p.click('#btn-selector-modelos'); await p.waitForTimeout(300); await p.locator('#sel-nuevo').click(); await p.waitForTimeout(1500);
    const n = await p.locator('#sh-modelos-lista button').count();
    const txt = await p.evaluate(() => [...document.querySelectorAll('#sh-modelos-lista button')].map(x => x.textContent).join(' '));
    ok(caso + ': la lista de Team qwen muestra modelos', n >= 10 && /qwen3\.8-max/.test(txt) && /glm-5\.3/.test(txt), n + ' modelos');
    await p.evaluate(() => { const x = [...document.querySelectorAll('#sh-modelos-lista button')].find(e => /glm-5\.3/.test(e.textContent)); if (x) x.click(); }); await p.waitForTimeout(400);
    ok(caso + ': elegir un modelo lo marca en el indicador', /glm-5\.3/.test(await p.textContent('#btn-selector-modelos')), (await p.textContent('#btn-selector-modelos')).trim());
    ok(caso + ': sin «signal is aborted» en pantalla', !/signal is aborted/i.test(await p.evaluate(() => document.body.innerText)));
    ok(caso + ': sin errores JS', errs.length === 0, errs.join('|'));
    await ctx.close();
  }
  await b.close();
})().catch(e => { console.log('ERROR', e.message.split('\n')[0]); process.exit(1); });
