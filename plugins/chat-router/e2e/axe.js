// ronda de accesibilidad (axe-core, WCAG 2.2 AA) sobre el chat, la ventana Controles y las ventanas del composer
const { chromium } = require('playwright');
const AXE = require('fs').readFileSync(process.env.AXE_JS || require.resolve('axe-core/axe.min.js'), 'utf8');
const VP = process.argv[2] === 'desk' ? { width: 1280, height: 800 } : { width: 390, height: 844 };
(async () => {
  const b = await chromium.launch((process.env.CHROMIUM ? { executablePath: process.env.CHROMIUM } : {}));
  const ctx = await b.newContext({ viewport: VP, isMobile: VP.width < 500, hasTouch: VP.width < 500 });
  await ctx.addInitScript((t) => { (sessionStorage.setItem('riu_clave', 'api-e2e'), localStorage.setItem('riu_herr_abiertas', '1')); if (t) localStorage.setItem('riu_tema', t); }, process.argv[3] || '');
  const p = await ctx.newPage(); await p.goto('http://127.0.0.1:8765/chat/ui/shell.html'); await p.waitForSelector('#btn-room', { state: 'attached' }); await p.waitForTimeout(1500);
  const correr = async (nombre, incluir) => {
    await p.evaluate(AXE);
    const r = await p.evaluate(async (inc) => { const res = await axe.run(inc ? { include: [inc] } : document, { runOnly: { type: 'tag', values: ['wcag2a', 'wcag2aa', 'wcag21aa', 'wcag22aa'] } }); return res.violations.map(v => ({ id: v.id, impact: v.impact, n: v.nodes.length, ej: v.nodes.slice(0, 3).map(x => x.target.join(' ') + ' | ' + (x.failureSummary || '').split('\n')[1]) })); }, incluir);
    console.log('== ' + nombre + ': ' + r.length + ' reglas fallan'); r.forEach(v => console.log(' -', v.impact, v.id, 'x' + v.n, JSON.stringify(v.ej).slice(0, 400)));
  };
  await correr('chat (composer + historial)', '#panel');
  for (const [b2, h2] of [['#cb-sel-modelo', '#cb-modelos'], ['#cb-sel-permisos', '#cb-permisos'], ['#cb-sel-herr', '#cb-herramientas']]) { await p.click(b2); await p.waitForTimeout(400); await correr('ventana ' + h2, h2); await p.keyboard.press('Escape'); await p.waitForTimeout(200); }
  for (const id of ['room', 'conexiones', 'power']) { await p.$eval('#btn-' + id, e => e.click()); await p.waitForTimeout(900); await correr('ventana ' + id, '#ventana-' + id); await p.keyboard.press('Escape'); await p.waitForTimeout(200); }
  await b.close();
})().catch(e => { console.log('ERROR', e.message.split('\n')[0]); process.exit(1); });
