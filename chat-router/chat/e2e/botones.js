// auditoria click-path: cada boton visible del chat -> efecto observable (ventana, texto, peticion) y sin errores JS
const { chromium } = require('playwright');
const VP = process.argv[2] === 'desk' ? { width: 1280, height: 800 } : { width: 390, height: 844 };
(async () => {
  const b = await chromium.launch((process.env.CHROMIUM ? { executablePath: process.env.CHROMIUM } : {}));
  const ctx = await b.newContext({ viewport: VP, hasTouch: VP.width < 500, isMobile: VP.width < 500 });
  await ctx.addInitScript(() => { (sessionStorage.setItem('riu_clave', 'api-e2e'), localStorage.setItem('riu_herr_abiertas', '1')); window.open = () => null; });
  const p = await ctx.newPage(); p.on('dialog', d => d.dismiss());
  await p.goto('http://127.0.0.1:8765/chat/ui/shell.html'); await p.waitForSelector('#btn-prompt', { state: 'attached' }); await p.waitForTimeout(2000);
  const CTL = process.argv[3] === 'ctl'; const HOJA = (process.argv[3] || '').startsWith('hoja:') ? process.argv[3].split(':').slice(1) : null; const abrirCtl = async () => { if (HOJA) { if (await p.evaluate((h) => document.querySelector(h).hidden, HOJA[1])) { await p.$eval(HOJA[0], e => e.click()); await p.waitForTimeout(300); } return; } if (CTL && VP.width >= 500) { if (await p.evaluate(() => { const c = document.querySelector('#ctl-panel'); return c && c.getBoundingClientRect().height < 5; })) { await p.click('#ctl-barra').catch(() => {}); await p.waitForTimeout(300); } }
    if (CTL && VP.width < 500) { const t = p.locator('#movil-toggle'); if (await p.evaluate(() => document.querySelector('#movil-panel').hidden)) await t.click(); await p.waitForTimeout(300); } };
  await abrirCtl();
  const ids = await p.evaluate(([CTLF, HJ]) => { let n = 0; return [...document.querySelectorAll('button, [role=button], select, [role=tab]')].filter(e => { if (e.closest('#mv-nav, #navigation') || (CTLF && !e.closest('#movil-panel, #ctl-panel')) || (HJ && !e.closest(HJ)) || (!HJ && e.closest('.cb-hoja'))) return false; const r = e.getBoundingClientRect(); return r.width > 0 && r.height > 0 && (HJ ? !e.closest('[hidden]') : !e.closest('.sheet:not([hidden]), [hidden]')); }).map(e => { if (!e.dataset.aud) e.dataset.aud = 'a' + (n++); const r = e.getBoundingClientRect(); return { aud: e.dataset.aud, tag: e.tagName, id: e.id, txt: (e.getAttribute('aria-label') || e.textContent || e.title || '').trim().slice(0, 40), w: Math.round(r.width), h: Math.round(r.height) }; }); }, [CTL, HOJA && HOJA[1]]);
  console.log('controles visibles:', ids.length);
  for (const c of ids) {
    if (/borrar|eliminar|quitar|apagar router|detener|ampliar la salida/i.test(c.txt + c.id)) { console.log('SKIP', c.id, c.txt); continue; }
    const errs = [], reqs = []; const oe = e => errs.push(e.message); const or = r => { if (!/\.(js|css|json|png|svg)/.test(r.url())) reqs.push(r.method() + ' ' + r.url().replace(/^https?:\/\/[^/]+/, '')); };
    p.on('pageerror', oe); p.on('request', or);
    const antes = await p.evaluate(() => [document.querySelectorAll('.sheet:not([hidden]), [role=dialog]:not([hidden])').length, document.body.innerText.length].join('/'));
    let efecto = '';
    try {
      let loc = p.locator(`[data-aud="${c.aud}"]`); if (!(await loc.count())) { c.aud = await p.evaluate((t) => { const e = [...document.querySelectorAll('button, [role=button], select')].find(x => (x.getAttribute('aria-label') || x.textContent || x.title || '').trim().slice(0, 40) === t && x.getBoundingClientRect().width > 0 && !x.dataset.hecho); if (!e) return ''; e.dataset.aud = 'r' + Math.random(); return e.dataset.aud; }, c.txt); loc = p.locator(`[data-aud="${c.aud}"]`); efecto = c.aud ? '' : 'DESAPARECE'; if (!c.aud) throw new Error('re-render: ya no esta'); }
      await loc.evaluate(e => e.dataset.hecho = '1');
      if (c.tag === 'SELECT') { const ops = await loc.evaluate(s => [...s.options].map(o => o.value)); efecto = 'opciones=' + ops.length; }
      else { await loc.click({ timeout: 2500 }); await p.waitForTimeout(700); }
    } catch (e) { efecto = 'NO_CLIC tapado por ' + await p.evaluate((a) => { const e = document.querySelector(`[data-aud="${a}"]`); if (!e) return 'ya no existe'; e.scrollIntoView({block:'center'}); const r = e.getBoundingClientRect(); const t = document.elementFromPoint(r.x + r.width / 2, r.y + r.height / 2); return t ? t.tagName + '#' + t.id + '.' + String(t.className).slice(0,40) + ' en ' + ((t.closest('[id]') || {}).id) : 'nada'; }, c.aud); }
    const desp = await p.evaluate(() => [document.querySelectorAll('.sheet:not([hidden]), [role=dialog]:not([hidden])').length, document.body.innerText.length].join('/'));
    if (!efecto) efecto = antes !== desp ? 'CAMBIA ' + antes + '->' + desp : (reqs.length ? 'PETICION' : 'SIN_EFECTO');
    console.log((errs.length ? 'ERR ' : /SIN_EFECTO|NO_CLIC/.test(efecto) ? 'REV ' : 'OK  ') + (c.id || '-') + ' [' + c.txt + '] ' + c.w + 'x' + c.h + ' ' + efecto + (reqs.length ? ' ' + [...new Set(reqs)].slice(0, 3).join(',') : '') + (errs.length ? ' ' + errs.join('|') : ''));
    p.off('pageerror', oe); p.off('request', or);
    await p.keyboard.press('Escape'); await p.evaluate(() => document.querySelectorAll('.sheet:not([hidden])').forEach(s => s.hidden = true)); await p.evaluate(() => { const a = document.querySelector('.ac-fondo'); if (a) a.remove(); }); await p.waitForTimeout(150); await abrirCtl();
  }
  await b.close();
})().catch(e => { console.log('ERROR', e.message.split('\n')[0]); process.exit(1); });
