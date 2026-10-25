// PASO 1: el modelo que responde es el del selector (4 escenarios, móvil o escritorio). El modelo simulado responde «Soy X» con X = identidad que le llega justo antes del mensaje.
const { chromium } = require('playwright');
const VP = process.argv[2] === 'desk' ? { width: 1280, height: 800 } : { width: 390, height: 844 };
const ok = (n, c, x) => console.log((c ? 'PASS ' : 'FAIL ') + n + (x ? ' :: ' + x : ''));
(async () => {
  const b = await chromium.launch((process.env.CHROMIUM ? { executablePath: process.env.CHROMIUM } : {}));
  const ctx = await b.newContext({ viewport: VP, isMobile: VP.width < 500, hasTouch: VP.width < 500 });
  await ctx.addInitScript(() => { (sessionStorage.setItem('riu_clave', 'api-e2e'), localStorage.setItem('riu_herr_abiertas', '1')); if (!sessionStorage.getItem('e2e_ini')) { sessionStorage.setItem('e2e_ini', '1'); sessionStorage.removeItem('riu_selector_activo'); } });
  const p = await ctx.newPage(); const errs = []; p.on('pageerror', e => errs.push(e.message));
  await p.goto('http://127.0.0.1:8765/chat/ui/shell.html'); await p.waitForSelector('#btn-prompt', { state: 'attached' }); await p.waitForTimeout(2500);
  const pregunta = async () => {
    const n = await p.locator('.chat-history .message:not(.user):not(.pending):not(.meta) .txt').count();
    await p.fill('#message', 'Que modelo eres'); await p.$eval('#composer .action', e => e.click());
    await p.waitForFunction((n) => document.querySelectorAll('.chat-history .message:not(.user):not(.pending):not(.meta) .txt').length > n, n, { timeout: 25000 });
    const t = await p.locator('.chat-history .message:not(.user):not(.pending):not(.meta) .txt').last().innerText();
    const meta = await p.evaluate(() => { const m = [...document.querySelectorAll('.chat-history .message.meta')].map(x => x.innerText).filter(x => /Modelo solicitado/.test(x)); return m[m.length - 1] || ''; });
    return { t, meta };
  };
  const elegirQwen = async (nombre) => { await p.$eval('#sel-nuevo', e => e.click()); await p.waitForTimeout(1200); const hecho = await p.evaluate((n) => { const g = [...document.querySelectorAll('#sh-modelos-lista button')].find(x => x.textContent.trim().startsWith(n)); if (g) { g.click(); return true; } return false; }, nombre); await p.waitForTimeout(500); return hecho; };
  const encender = async (fila) => p.evaluate((f) => { const b = document.querySelector('.sel-fila[data-selector="' + f + '"] .sel-on'); if (b && !b.classList.contains('on')) b.click(); return !!b; }, fila);
  const apagarTodo = async () => p.evaluate(() => window.RIU_SELECTORES && window.RIU_SELECTORES.apagar());
  // 1) Team qwen + glm-5.3
  ok('1 elegir glm-5.3 en Team qwen', await elegirQwen('glm-5.3')); await encender('team-qwen');
  let r = await pregunta(); ok('1 responde glm-5.3', /Soy glm-5\.3/.test(r.t) && /glm-5\.3/.test(r.meta), r.t + ' | ' + r.meta);
  // 2) mismo chat (historial dice «Soy glm-5.3»), cambio a qwen3.8-max
  ok('2 elegir qwen3.8-max', await elegirQwen('qwen3.8-max'));
  r = await pregunta(); ok('2 responde qwen3.8-max aunque el historial diga otro', /Soy qwen3\.8-max/.test(r.t) && /qwen3\.8-max/.test(r.meta), r.t + ' | ' + r.meta);
  // 3) Groq: fila propia con sus modelos reales
  await apagarTodo(); await p.waitForTimeout(300);
  await p.$eval('#sel-groq', e => e.click()); await p.waitForTimeout(600);
  const fichas = await p.evaluate(() => [...document.querySelectorAll('#sh-groq-lista button')].map(x => x.textContent.trim()));
  ok('3 la hoja Groq lista sus modelos (sin whisper)', fichas.some(t => /Groq · llama-3\.3-70b-versatile/.test(t)) && !fichas.some(t => /whisper/.test(t)), JSON.stringify(fichas).slice(0, 200));
  await p.evaluate(() => [...document.querySelectorAll('#sh-groq-lista button')].find(e => /gpt-oss-120b/.test(e.textContent)).click()); await p.waitForTimeout(400);
  ok('3 la fila Groq muestra el modelo elegido', /gpt-oss-120b/.test(await p.evaluate(() => (document.querySelector('.sel-fila[data-selector="groq"] .sel-resp') || {}).textContent || '')));
  await encender('groq');
  ok('3 fuera del selector se ve el modelo que responde', /gpt-oss-120b/.test(await p.evaluate(() => document.querySelector('#cb-sel-modelo .cb-et').textContent)));
  r = await pregunta(); ok('3 responde Groq gpt-oss-120b', /Soy openai\/gpt-oss-120b en Groq/.test(r.t) && /groq\/openai\/gpt-oss-120b/.test(r.meta), r.t + ' | ' + r.meta);
  // 4) recargar: la elección se conserva y sigue respondiendo el mismo
  await p.reload(); await p.waitForSelector('#btn-prompt', { state: 'attached' }); await p.waitForTimeout(2500);
  r = await pregunta(); ok('4 tras recargar sigue el mismo modelo', /gpt-oss-120b/.test(r.t), r.t + ' | ' + r.meta);
  ok('sin errores JS', errs.length === 0, errs.join(' | '));
  await b.close();
})().catch(e => { console.log('ERROR', e.message.split('\n')[0]); process.exit(1); });
