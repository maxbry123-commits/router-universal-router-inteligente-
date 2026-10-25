// Caja de escritura: texto + Enviar; debajo 3 selectores (Modelo · Permisos · Herramientas) que abren su ventana. Varias pantallas reales.
const { chromium } = require('playwright');
const ok = (n, c, x) => console.log((c ? 'PASS ' : 'FAIL ') + n + (x ? ' :: ' + x : ''));
(async () => {
  const b = await chromium.launch((process.env.CHROMIUM ? { executablePath: process.env.CHROMIUM } : {}));
  for (const [w, h] of [[345, 700], [360, 640], [412, 690], [1280, 800]]) {
    const movil = w < 500, ctx = await b.newContext({ viewport: { width: w, height: h }, isMobile: movil, hasTouch: movil });
    await ctx.addInitScript(() => sessionStorage.setItem('riu_clave', 'api-e2e'));
    const p = await ctx.newPage(); const errs = []; p.on('pageerror', e => errs.push(e.message));
    await p.goto('http://127.0.0.1:8765/chat/ui/shell.html'); await p.waitForSelector('#cb-sel-modelo'); await p.waitForTimeout(1800);
    const t = w + 'x' + h + ' ';
    const cajas = await p.evaluate(() => ['#message', '#composer .action', '#cb-sel-modelo', '#cb-sel-permisos', '#cb-sel-herr'].map(s => { const r = document.querySelector(s).getBoundingClientRect(); return [s, Math.round(r.left), Math.round(r.top), Math.round(r.right), Math.round(r.bottom)]; }));
    const solapan = []; for (let i = 0; i < cajas.length; i++) for (let j = i + 1; j < cajas.length; j++) { const a = cajas[i], c = cajas[j]; if (a[1] < c[3] - 1 && c[1] < a[3] - 1 && a[2] < c[4] - 1 && c[2] < a[4] - 1) solapan.push(a[0] + '/' + c[0]); }
    ok(t + 'texto, Enviar y los 3 selectores sin pisarse', solapan.length === 0, solapan.join(','));
    ok(t + 'todo dentro de la pantalla (sin scroll lateral)', cajas.every(c => c[3] <= w + 1) && !(await p.evaluate(() => document.documentElement.scrollWidth > innerWidth)));
    ok(t + 'nombres de los selectores completos (sin «…»)', await p.evaluate(() => [...document.querySelectorAll('.cb-sel .cb-et')].every(e => e.scrollWidth <= e.clientWidth + 1)), await p.evaluate(() => [...document.querySelectorAll('.cb-sel .cb-et')].map(e => e.textContent).join(' | ')));
    const hist = await p.evaluate(() => Math.round(document.querySelector('.chat-history').getBoundingClientRect().height));
    ok(t + 'salida grande', hist >= h * (movil ? 0.6 : 0.4), hist + 'px de ' + h);
    for (const [sel, hoja, debe] of [['#cb-sel-modelo', '#cb-modelos', ['#sel-ngt', '#sel-groq', '#sel-nuevo', '#sel-mvp', '#sel-cc', '#sel-cf', '#sel-workflows']], ['#cb-sel-permisos', '#cb-permisos', ['#btn-tools', '#btn-agentes', '#btn-prompt']], ['#cb-sel-herr', '#cb-herramientas', ['#btn-adjunto', '#btn-archivos', '#btn-ancla', '#btn-sandbox', '#btn-microfono', '#btn-copiar-input', '#btn-conexiones', '#btn-room', '#btn-power', '#btn-pendientes']]]) {
      await p.click(sel); await p.waitForTimeout(350);
      const vis = await p.evaluate((d) => d.filter(s => { const e = document.querySelector(s); const r = e && e.getBoundingClientRect(); return !(r && r.width > 20 && r.height > 20); }), debe);
      ok(t + sel + ' abre su ventana con todo dentro', await p.evaluate((x) => !document.querySelector(x).hidden, hoja) && vis.length === 0, 'faltan: ' + vis.join(','));
      await p.keyboard.press('Escape'); await p.waitForTimeout(200);
      ok(t + sel + ' Escape la cierra', await p.evaluate((x) => document.querySelector(x).hidden, hoja));
    }
    // estado reflejado fuera: Permisos (puntos) y Modelo
    const antes = await p.evaluate(() => document.querySelectorAll('#cb-sel-permisos .cb-punto.on').length);
    await p.$eval('#btn-prompt', e => e.click()); await p.waitForFunction((a) => document.querySelectorAll('#cb-sel-permisos .cb-punto.on').length !== a, antes, { timeout: 5000 });
    ok(t + 'Permisos refleja el cambio (punto azul)', true);
    await p.$eval('#btn-prompt', e => e.click()); await p.waitForTimeout(600);
    await p.evaluate(() => window.RIU_SELECTORES.encender('team-qwen')); await p.waitForTimeout(300);
    ok(t + 'Modelo muestra el que responde', /Qwen|qwen/.test(await p.textContent('#cb-sel-modelo .cb-et')), await p.textContent('#cb-sel-modelo .cb-et'));
    await p.evaluate(() => window.RIU_SELECTORES.apagar());
    // Detener solo mientras trabaja
    ok(t + 'Detener oculto en reposo', await p.evaluate(() => getComputedStyle(document.querySelector('#btn-detener')).display === 'none'));
    await p.fill('#message', 'hola'); await p.$eval('#composer .action', e => e.click());
    await p.waitForFunction(() => getComputedStyle(document.querySelector('#btn-detener')).display !== 'none', null, { timeout: 4000 }).then(() => ok(t + 'Detener aparece mientras responde', true)).catch(() => ok(t + 'Detener aparece mientras responde', false));
    ok(t + 'sin errores JS', errs.length === 0, errs.join('|'));
    await ctx.close();
  }
  await b.close();
})().catch(e => { console.log('ERROR', e.message.split('\n')[0]); process.exit(1); });
