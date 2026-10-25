// El chat vuelve a como estaba: los controles de la base a la vista (no dentro de ventanas), Detener visible en reposo y el cubo de pensamiento mientras trabaja. Varias pantallas reales.
const { chromium } = require('playwright');
const ok = (n, c, x) => console.log((c ? 'PASS ' : 'FAIL ') + n + (x ? ' :: ' + x : ''));
const CONTROLES = ['#btn-adjunto', '#btn-archivos', '#btn-ancla', '#btn-sandbox', '#btn-microfono', '#btn-copiar-input', '#btn-detener', '#btn-pendientes', '#btn-prompt', '#btn-agentes', '#message', '#composer .action'];
(async () => {
  const b = await chromium.launch((process.env.CHROMIUM ? { executablePath: process.env.CHROMIUM } : {}));
  for (const [w, h] of [[345, 700], [412, 690], [1280, 800]]) {
    const movil = w < 500, ctx = await b.newContext({ viewport: { width: w, height: h }, isMobile: movil, hasTouch: movil });
    await ctx.addInitScript(() => sessionStorage.setItem('riu_clave', 'api-e2e'));
    const p = await ctx.newPage(); const errs = []; p.on('pageerror', e => errs.push(e.message));
    await p.route(/chat_async|chat\/send|call\/resultado/, async r => { await new Promise(x => setTimeout(x, 1200)); r.continue(); });
    await p.goto('http://127.0.0.1:8765/chat/ui/shell.html'); await p.waitForSelector('#message', { state: 'attached' }); await p.waitForTimeout(2500);
    const t = w + 'x' + h + ' ';
    const vis = (sel) => p.evaluate((s) => { const e = document.querySelector(s); if (!e) return 'no existe'; const r = e.getBoundingClientRect(), c = getComputedStyle(e); if (!(r.width > 0 && r.height > 0 && c.visibility !== 'hidden' && c.display !== 'none')) return 'oculto'; if (e.closest('[hidden], .sheet, .cb-hoja, .cb-herramientas')) return 'dentro de una ventana'; if (r.right > innerWidth + 1 || r.left < -1) return 'fuera de pantalla'; return 'visible'; }, sel);
    const mal = []; for (const s of CONTROLES) { const v = await vis(s); if (v !== 'visible' && !(s === '#btn-copiar-input' && false)) mal.push(s + ': ' + v); }
    ok(t + 'controles de la base a la vista', mal.length === 0, mal.join(' | '));
    ok(t + 'Detener visible en reposo', (await vis('#btn-detener')) === 'visible');
    const modos = await p.evaluate(async () => (await (await fetch('/chat/ui/panel-chat.js')).text()));
    ok(t + 'etiquetas de modo originales', /Rápido — 512 tok/.test(modos) && /Equilibrado — 1024 tok/.test(modos) && /Pensar — 2048 tok/.test(modos), 'panel-chat.js');
    await p.fill('#message', 'hola'); await p.$eval('#composer .action', e => e.click());
    let cubo = false; for (let i = 0; i < 25 && !cubo; i++) { await p.waitForTimeout(100); cubo = (await vis('.p3d')) === 'visible'; }
    ok(t + 'cubo de pensamiento visible mientras trabaja', cubo);
    ok(t + 'sin errores JS', errs.length === 0, errs.join('|'));
    await ctx.close();
  }
  await b.close();
})();
