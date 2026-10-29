// Controles: «LLM tool» = chip IA, «Agente tool» = chip Agentes (mismo estado del servidor); Proyectos abre su ventana; modo Objetivo responde con aviso
const { chromium } = require('playwright');
const VP = process.argv[2] === 'desk' ? { width: 1280, height: 800 } : { width: 390, height: 844 };
const ok = (n, c, x) => console.log((c ? 'PASS ' : 'FAIL ') + n + (x ? ' :: ' + x : ''));
(async () => {
  const b = await chromium.launch((process.env.CHROMIUM ? { executablePath: process.env.CHROMIUM } : {}));
  const ctx = await b.newContext({ viewport: VP, isMobile: VP.width < 500, hasTouch: VP.width < 500 });
  await ctx.addInitScript(() => (sessionStorage.setItem('riu_clave', 'api-e2e'), localStorage.setItem('riu_herr_abiertas', '1')));
  const p = await ctx.newPage(); const errs = []; p.on('pageerror', e => errs.push(e.message));
  await p.goto('http://127.0.0.1:8765/chat/ui/shell.html'); await p.waitForSelector('#btn-prompt', { state: 'attached' }); await p.waitForTimeout(2000);
  for (const s of ['#btn-tools', '#btn-agentes']) if (/ON/.test(await p.textContent(s))) { await p.$eval(s, e => e.click()); await p.waitForTimeout(500); }
  const txt = (s) => p.evaluate((s) => document.querySelector(s).textContent.trim(), s);
  const clic = (s) => p.evaluate((s) => document.querySelector(s).click(), s);
  ok('arranque: LLM tool OFF y Agente tool OFF', /LLM tool OFF/.test(await txt('#btn-llm-tool')) && /Agente tool OFF/.test(await txt('#btn-agent-access-lock')));
  await clic('#btn-llm-tool'); await p.waitForFunction(() => /IA ON/.test(document.querySelector('#btn-tools').textContent));
  ok('LLM tool ON enciende IA en el servidor', /LLM tool ON/.test(await txt('#btn-llm-tool')) && /Agentes OFF/.test(await txt('#btn-agentes')));
  await clic('#btn-agent-access-lock'); await p.waitForFunction(() => /Agentes ON/.test(document.querySelector('#btn-agentes').textContent));
  ok('Agente tool ON enciende Agentes', /Agente tool ON/.test(await txt('#btn-agent-access-lock')));
  await p.reload(); await p.waitForSelector('#btn-prompt', { state: 'attached' }); await p.waitForTimeout(2000);
  ok('tras recargar el servidor recuerda ambos', /LLM tool ON/.test(await txt('#btn-llm-tool')) && /Agente tool ON/.test(await txt('#btn-agent-access-lock')));
  await clic('#btn-llm-tool'); await p.waitForTimeout(600); await clic('#btn-agent-access-lock'); await p.waitForTimeout(600);
  ok('vuelven a OFF', /IA OFF/.test(await txt('#btn-tools')) && /Agentes OFF/.test(await txt('#btn-agentes')));
  await clic('#btn-proyectos'); await p.waitForTimeout(800);
  ok('Proyectos abre su ventana', await p.evaluate(() => [...document.querySelectorAll('.sheet, [role=dialog]')].some(s => !s.hidden && s.getBoundingClientRect().height > 50 && /royect/i.test(s.textContent))));
  await p.keyboard.press('Escape'); await p.evaluate(() => document.querySelectorAll('.sheet:not([hidden])').forEach(s => s.hidden = true));
  // modo Objetivo: elegirlo y enviar
  const elegido = await p.evaluate(() => { const b = document.querySelector('#mode-selector-mount button'); if (!b) return 'sin selector de modos'; b.click(); return 'ok'; }); await p.waitForTimeout(500);
  const objetivo = await p.evaluate(() => { const o = [...document.querySelectorAll('[role=option], .ms-opt, .ms-item, button')].find(x => /Objetivo/.test(x.textContent) && x.getBoundingClientRect().height > 0); if (o) { o.click(); return true; } return false; });
  ok('modo Objetivo seleccionable', elegido === 'ok' && objetivo); await p.waitForTimeout(400);
  const n = await p.locator('.chat-history .message:not(.user):not(.pending):not(.meta) .txt').count();
  await p.fill('#message', 'objetivo de prueba'); await p.$eval('#composer .action', e => e.click());
  await p.waitForFunction((n) => document.querySelectorAll('.chat-history .message:not(.user):not(.pending):not(.meta) .txt').length > n || document.querySelector('.chat-history .message.error'), n, { timeout: 25000 });
  const meta = await p.evaluate(() => [...document.querySelectorAll('.chat-history .message.meta')].map(x => x.textContent).join(' | '));
  const err = await p.evaluate(() => [...document.querySelectorAll('.chat-history .message')].map(x => x.textContent).filter(t => /GAP/.test(t)).join(' | '));
  ok('modo Objetivo responde (sin GAP) y avisa del turno único', !err && /un turno/.test(meta), (err || meta).slice(0, 200));
  ok('sin errores JS', errs.length === 0, errs.join(' | '));
  await b.close();
})().catch(e => { console.log('ERROR', e.message.split('\n')[0]); process.exit(1); });
