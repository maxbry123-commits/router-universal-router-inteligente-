const { chromium } = require('playwright');
const URL = 'http://127.0.0.1:8765/chat/ui/shell.html';
const ok = (n, c, x) => console.log((c ? 'PASS ' : 'FAIL ') + n + (x ? ' :: ' + x : ''));
(async () => {
  const b = await chromium.launch((process.env.CHROMIUM ? { executablePath: process.env.CHROMIUM } : {}));
  // R1: clave mala -> el chip no cambia y el boton queda usable
  let ctx = await b.newContext({ viewport: { width: 390, height: 844 } });
  await ctx.addInitScript(() => sessionStorage.setItem('riu_clave', 'MALA'));
  let p = await ctx.newPage(); await p.goto(URL); await p.waitForSelector('#btn-tools', { state: 'attached' }); await p.waitForTimeout(1500);
  ok('R1 clave mala: sale el aviso de clave y los chips siguen OFF', (await p.textContent('#btn-tools')).trim() === 'IA OFF' && (await p.locator('.ac-fondo').count()) >= 1);
  await ctx.close();
  // R2: medios maliciosos no se pintan
  ctx = await b.newContext({ viewport: { width: 390, height: 844 } });
  await ctx.addInitScript(() => (sessionStorage.setItem('riu_clave', 'api-e2e'), localStorage.setItem('riu_herr_abiertas', '1')));
  p = await ctx.newPage(); await p.goto(URL); await p.waitForSelector('#btn-tools', { state: 'attached' }); await p.waitForTimeout(1500);
  await p.evaluate(() => { const h = document.querySelector('.chat-history'); const d = document.createElement('div'); d.className = 'item message'; d.innerHTML = '<span class="txt">[[imagen:javascript:alert(1)]] [[imagen:http://x.com/a.png]] [[video:data:text/html,<b>]] [[audio:data:audio/mp3;base64,AAAA]]</span>'; h.append(d); });
  await p.waitForTimeout(300);
  const srcs = await p.$$eval('.riu-medio', l => l.map(e => e.tagName + ':' + e.getAttribute('src')));
  ok('R2 solo https o audio data: se pintan', srcs.length === 1 && /^AUDIO:data:audio\//.test(srcs[0]), JSON.stringify(srcs));
  // R3: lo que viaja al servidor refleja los chips
  const cuerpos = []; p.on('request', r => { if (/call\/chat|chat\/send|call\/chat_async/.test(r.url()) && r.method() === 'POST') cuerpos.push(r.postData()); });
  await p.fill('#message', 'hola uno'); await p.click('#composer .action'); await p.waitForSelector('.chat-history .message:not(.user):not(.pending) .txt', { timeout: 20000 }); await p.waitForTimeout(500);
  await p.$eval('#btn-tools', e => e.click()); await p.waitForFunction(() => /ON/.test(document.querySelector('#btn-tools').textContent));
  await p.fill('#message', 'hola dos'); await p.click('#composer .action'); await p.waitForTimeout(3000);
  const f = (s) => { try { const o = JSON.parse(s); return [o.tools, o.llm_tool, o.agente_tool].join('/'); } catch (e) { return 'x:' + (s || '').slice(0, 60); } };
  ok('R3 envío 1 tools/llm/agente = false/false/false', cuerpos.length >= 1 && f(cuerpos[0]) === 'false/false/false', cuerpos.map(f).join(' | '));
  ok('R3 envío 2 con IA ON = true/true/false', cuerpos.length >= 2 && f(cuerpos[1]) === 'true/true/false', cuerpos.map(f).join(' | '));
  await p.$eval('#btn-tools', e => e.click()); await p.waitForTimeout(800);
  await b.close();
})().catch(e => { console.log('ERROR', e.message.split('\n')[0]); process.exit(1); });
