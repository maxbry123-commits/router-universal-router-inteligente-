// Tarea 4: un solo selector guarda todos los selectores de modelo; fuera queda el indicador; la salida mide 4 veces su alto; cada selector llega al backend.
const { chromium } = require('playwright');
const ok = (n, c, x) => console.log((c ? 'PASS ' : 'FAIL ') + n + (x ? ' :: ' + x : ''));
const FILAS = ['#sel-ngt', '#sel-groq', '#sel-nuevo', '#sel-mvp', '#sel-cc', '#sel-cf'];
(async () => {
  const b = await chromium.launch((process.env.CHROMIUM ? { executablePath: process.env.CHROMIUM } : {}));
  for (const [w, h] of [[345, 700], [412, 915], [1280, 800]]) {
    const movil = w < 500, t = w + 'x' + h + ' ';
    const ctx = await b.newContext({ viewport: { width: w, height: h }, isMobile: movil, hasTouch: movil });
    await ctx.addInitScript(() => { sessionStorage.setItem('riu_clave', 'api-e2e'); if (!sessionStorage.getItem('e2e_ini')) { sessionStorage.setItem('e2e_ini', '1'); sessionStorage.removeItem('riu_selector_activo'); } });
    const p = await ctx.newPage(); const errs = []; p.on('pageerror', e => errs.push(e.message));
    await p.goto('http://127.0.0.1:8765/chat/ui/shell.html'); await p.waitForSelector('#btn-selector-modelos'); await p.waitForTimeout(2500);
    const vis = (s) => p.evaluate((s) => { const e = document.querySelector(s); if (!e) return false; const r = e.getBoundingClientRect(), c = getComputedStyle(e); return r.width > 0 && r.height > 0 && c.visibility !== 'hidden' && c.display !== 'none' && !e.closest('[hidden]') && r.top < innerHeight && r.bottom > 0; }, s);
    // 1) un solo selector; los selectores de modelo no ocupan la pantalla
    ok(t + '1 indicador del selector a la vista', await vis('#btn-selector-modelos'));
    ok(t + '1 los selectores de modelo no están en la pantalla (dentro de la ventana)', !(await vis('#sel-ngt')) && await p.evaluate(() => !!document.querySelector('#sh-selectores #selectores')));
    ok(t + '2 el indicador dice qué modelo responde', /Qwen 3\.8 Max|Modelo/.test(await p.textContent('#btn-selector-modelos')), (await p.textContent('#btn-selector-modelos')).trim());
    // 4) salida ×4 y la caja de escritura nunca se pierde
    const alto = await p.evaluate(() => { const hh = document.getElementById('histories'); const x4 = hh.getBoundingClientRect().height; document.documentElement.classList.remove('salida-x4'); const ind = document.getElementById('btn-selector-modelos'); const base = hh.getBoundingClientRect().height + ind.getBoundingClientRect().height + 8; document.documentElement.classList.add('salida-x4'); return [Math.round(base), Math.round(x4)]; });
    ok(t + '4 salida 4 veces más alta', alto[1] >= alto[0] * 3.95, alto[0] + 'px → ' + alto[1] + 'px');
    ok(t + '4 Enviar a la vista al abrir', await vis('#composer .action'));
    await p.evaluate(() => window.scrollTo(0, 0)); await p.waitForTimeout(200);
    ok(t + '4 Enviar sigue a la vista al subir por la salida', await vis('#composer .action'));
    await p.evaluate(() => window.scrollTo(0, document.documentElement.scrollHeight)); await p.waitForTimeout(150);
    for (const s of ['#btn-adjunto', '#btn-ancla', '#btn-detener', '#btn-tools', '#btn-agentes', '#btn-prompt']) if (!(await vis(s))) ok(t + '4 control a la vista ' + s, false);
    // abrir la ventana con un clic real
    await p.click('#btn-selector-modelos'); await p.waitForTimeout(400);
    const faltan = []; for (const s of FILAS) if (!(await vis(s))) faltan.push(s);
    ok(t + '1 la ventana muestra todos los selectores', faltan.length === 0 && (await p.locator('#sh-selectores .sel-on').count()) >= 6, 'faltan: ' + faltan.join(','));
    // encender Groq desde la ventana con clic real → el indicador cambia
    await p.locator('.sel-fila[data-selector="groq"] .sel-on').click(); await p.waitForTimeout(300);
    ok(t + '2 al encender Groq el indicador lo marca', /Groq/.test(await p.textContent('#btn-selector-modelos')), (await p.textContent('#btn-selector-modelos')).trim());
    await p.keyboard.press('Escape'); await p.waitForTimeout(200);
    ok(t + '1 Escape cierra la ventana', await p.evaluate(() => document.getElementById('sh-selectores').hidden));
    // la lista de cada selector abre encima (se cierra la ventana de selectores)
    await p.click('#btn-selector-modelos'); await p.waitForTimeout(300); await p.locator('#sel-groq').click(); await p.waitForTimeout(500);
    ok(t + '1 la lista Groq se abre al tocar Groq ⌄', await p.evaluate(() => { const s = document.getElementById('sh-groq'); return !!s && !s.hidden; }) && await p.evaluate(() => document.getElementById('sh-selectores').hidden));
    await p.evaluate(() => { const x = [...document.querySelectorAll('#sh-groq-lista button')].find(e => /gpt-oss-120b/.test(e.textContent)); if (x) x.click(); }); await p.waitForTimeout(400);
    ok(t + '2 el indicador muestra el modelo Groq elegido', /gpt-oss-120b/.test(await p.textContent('#btn-selector-modelos')), (await p.textContent('#btn-selector-modelos')).trim());
    ok(t + 'sin errores JS', errs.length === 0, errs.join('|'));
    await ctx.close();
  }
  // 3) cableado frontend → backend de cada selector (escritorio): encender, preguntar, ver quién responde
  const ctx = await b.newContext({ viewport: { width: 1280, height: 800 } });
  await ctx.addInitScript(() => sessionStorage.setItem('riu_clave', 'api-e2e'));
  const p = await ctx.newPage(); await p.goto('http://127.0.0.1:8765/chat/ui/shell.html'); await p.waitForSelector('#btn-selector-modelos'); await p.waitForTimeout(2500);
  const pregunta = async () => {
    const sel = '.chat-history .message:not(.user):not(.pending)';
    const n = await p.locator(sel).count();
    await p.fill('#message', 'Que modelo eres'); await p.$eval('#composer .action', e => e.click());
    await p.waitForFunction((a) => document.querySelectorAll(a[0]).length > a[1] && !document.querySelector('.chat-history .message.pending'), [sel, n], { timeout: 25000 }).catch(() => {});
    return p.evaluate((a) => [...document.querySelectorAll(a)].slice(-3).map(x => x.innerText.replace(/\s+/g, ' ').trim()).join(' | '), sel);
  };
  const encender = async (fila) => { await p.click('#btn-selector-modelos'); await p.waitForTimeout(300); const b2 = p.locator('.sel-fila[data-selector="' + fila + '"] .sel-on'); if (!(await b2.evaluate(e => e.classList.contains('on')))) await b2.click(); await p.waitForTimeout(250); await p.keyboard.press('Escape'); };
  const elegirQwen = async (nombre) => { await p.click('#btn-selector-modelos'); await p.waitForTimeout(300); await p.locator('#sel-nuevo').click(); await p.waitForTimeout(1200); return p.evaluate((n) => { const g = [...document.querySelectorAll('#sh-modelos-lista button')].find(e => e.textContent.includes(n)); if (g) g.click(); return !!g; }, nombre); };
  ok('3 Team qwen: elegir glm-5.3', await elegirQwen('glm-5.3')); await p.waitForTimeout(300); await p.keyboard.press('Escape'); await encender('team-qwen');
  let r = await pregunta(); ok('3 Team qwen responde el modelo elegido', /Soy glm-5\.3/.test(r), r.slice(-220));
  await encender('groq'); r = await pregunta(); ok('3 Groq responde el modelo Groq', /en Groq/.test(r), r.slice(-220));
  for (const [fila, nombre] of [['nvidia-groq-team', 'NVIDIA'], ['team-5-mvp', 'Team 5 MVP'], ['ask-consil-code-qwen-team', 'Ask cónsil code'], ['ask-consil-fromtend-qwen-team', 'Ask consil fromtend']]) {
    await encender(fila); r = await pregunta();
    console.log('INFO 3 ' + nombre + ' → ' + r.slice(-260));
  }
  await ctx.close(); await b.close();
})().catch(e => { console.log('ERROR', e.message.split('\n')[0]); process.exit(1); });
