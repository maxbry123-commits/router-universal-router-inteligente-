// E2E Android simulado (412 px, 4G): Enviar -> respuesta visible, con la Constitucion ON/OFF, system prompt aparte y grafo por el Harness.
import { abrir, URL0 } from './comun.mjs';
import fs from 'node:fs';
const fmt = (ms) => Math.floor(ms / 1000) + ' s ' + String(ms % 1000).padStart(3, '0') + ' ms';
const { browser, page, externos, errores } = await abrir();
await page.goto(URL0, { waitUntil: 'load' }); await page.waitForTimeout(1200);
const res = []; const ok = (n, c, extra) => { res.push({ prueba: n, ok: !!c, ...(extra || {}) }); console.log((c ? 'PASS ' : 'FAIL ') + n + (extra ? ' ' + JSON.stringify(extra) : '')); };
const cerrarHojas = () => page.evaluate(() => document.querySelectorAll('.sheet').forEach((s) => { s.hidden = true; }));
const panel = async (abrirlo) => { const ab = await page.evaluate(() => !document.querySelector('#movil-panel').hidden); if (ab !== abrirlo) await page.click('#movil-toggle'); };
async function elegir(sel) {
  await cerrarHojas(); await panel(false);
  await page.evaluate(() => { const S = window.RIU_SELECTORES; if (S && S.activo && S.apagar) S.apagar(); });  // un selector a la vez (como el botón de encendido)
  if (sel.modelo) {
    await page.locator('#' + sel.pill).scrollIntoViewIfNeeded(); await page.click('#' + sel.pill);
    const b = page.locator('#sh-modelos button.mod-fila').filter({ has: page.locator('b', { hasText: new RegExp('^' + sel.modelo.replace(/\./g, '\\.') + '$') }) }).first();
    if ((await b.getAttribute('aria-pressed')) === 'true') { await cerrarHojas(); await page.evaluate((id) => window.RIU_SELECTORES.encender(id), sel.id); }  // ya elegido: otro clic lo desmarcaria
    else { await b.click(); await page.waitForTimeout(200); await cerrarHojas(); }
  } else await page.evaluate((id) => window.RIU_SELECTORES.encender(id), sel.id);
  return page.evaluate(() => window.RIU_SELECTORES.activo);
}
async function constitucion(texto, on) {
  await panel(true); await page.click('#pill-constitucion');
  const ta = page.locator("#ventana-constitucion textarea[aria-label='Mi constitución']"); if (texto != null) await ta.fill(texto);
  const t = page.locator('#ventana-constitucion button.toggle').first(); const ya = (await t.textContent()).includes('ON'); if (ya !== on) await t.click();
  const fin = (await page.locator('#ventana-constitucion button.toggle').first().textContent()); await cerrarHojas(); await panel(false); return fin;
}
async function enviar(msg) {
  const n0 = await page.locator('.item').count();
  await page.locator('textarea').filter({ hasNot: page.locator('[aria-label]') }).last();
  const box = page.getByPlaceholder('Escribe una orden o /ayuda'); await box.fill(msg);
  const t0 = Date.now(); await page.getByRole('button', { name: /Enviar/ }).click();
  await page.waitForFunction((n) => { const its = [...document.querySelectorAll('.item')].slice(n); return its.some((e) => /simulado|Corregida/.test(e.textContent) && !e.classList.contains('pending')); }, n0, { timeout: 60000 });
  const ms = Date.now() - t0; await page.waitForTimeout(250);
  const nuevos = await page.evaluate((n) => [...document.querySelectorAll('.item')].slice(n).map((e) => ({ c: e.className, t: e.textContent.trim() })), n0);
  const resp = nuevos.filter((x) => /simulado|Corregida/.test(x.t)).pop();
  return { ms, tiempo: fmt(ms), reply: resp ? resp.t.replace(/[⧉👍👎✅\s]+$/u, '') : '', meta: nuevos.filter((x) => x.c.includes('sentinela')).map((x) => x.t) };
}
const SELS = [{ nombre: 'Team qwen 3.8 Max', pill: 'sel-nuevo', modelo: 'Qwen 3.8 Max', id: 'team-qwen' }, { nombre: 'Team qwen 3.8 Flash', pill: 'sel-nuevo', modelo: 'Qwen 3.8 Flash', id: 'team-qwen' },
  { nombre: 'Team 5 MVP Max', pill: 'sel-mvp', modelo: 'Qwen 3.8 Max', id: 'team-5-mvp' }, { nombre: 'Team 5 MVP Flash', pill: 'sel-mvp', modelo: 'Qwen 3.8 Flash', id: 'team-5-mvp' },
  { nombre: 'Ask consil code', id: 'ask-consil-code-qwen-team' }, { nombre: 'Ask consil frontend', id: 'ask-consil-fromtend-qwen-team' }];
// 1) Constitucion ON: «termina con SENTINELA7» en los 6 selectores
ok('Constitución ON (botón)', (await constitucion('termina con SENTINELA7', true)).includes('ON'));
for (const s of SELS) {
  const act = await elegir(s); const r = await enviar('Di hola');
  ok('ON · ' + s.nombre + ' termina con SENTINELA7', act === s.id && r.reply.endsWith('SENTINELA7') && r.meta.some((m) => m.includes('pasó')), { activo: act, tiempo: r.tiempo, reply: r.reply.slice(-60), meta: r.meta });
}
await page.screenshot({ path: 'e2e-on.png' });
// 2) OFF: no viaja ni se valida
ok('Constitución OFF (botón)', (await constitucion(null, false)).includes('OFF'));
for (const s of SELS) {
  await elegir(s); const r = await enviar('Di hola');
  ok('OFF · ' + s.nombre + ' sin SENTINELA7', !r.reply.includes('SENTINELA7') && !r.meta.length, { tiempo: r.tiempo, reply: r.reply.slice(-60) });
}
await page.screenshot({ path: 'e2e-off.png' });
// 3) System prompt: ventana aparte, viaja con la Constitucion OFF y no se valida
await panel(true); await page.click('#pill-system-prompt');
const vsp = page.locator('#ventana-system-prompt');
ok('Ventana System prompt aparte (no dentro de Constitución)', await vsp.isVisible() && !(await page.locator('#ventana-constitucion [data-sent=sp-texto]').count()));
await vsp.getByLabel('Nombre del system prompt').fill('vale'); await vsp.getByLabel('Texto del system prompt').fill('Empieza con VALE');
await vsp.getByRole('button', { name: 'Guardar' }).click(); await page.waitForTimeout(200);
await page.screenshot({ path: 'e2e-system-prompt.png' });
ok('Pill system prompt marcada', await page.locator('#pill-system-prompt.on').count() === 1);
await cerrarHojas(); await panel(false);
await elegir(SELS[1]); let r = await enviar('Di hola');
ok('System prompt viaja (Constitución OFF) y no se valida', r.reply.startsWith('VALE.') && r.meta.some((m) => m.includes('System prompt: vale')) && !r.meta.some((m) => m.includes('Constitución')), { tiempo: r.tiempo, reply: r.reply, meta: r.meta });
// 4) Grafo por el Harness: Anclar al grafo ahora
await constitucion(null, true);
await panel(true); await page.click('#pill-constitucion');
const vc = page.locator('#ventana-constitucion');
await vc.getByRole('button', { name: 'Anclar al grafo ahora' }).click();
await page.waitForFunction(() => /Grafo SQLite: SAVED/.test(document.querySelector('#ventana-constitucion [data-sent=grafo-estado]').textContent), null, { timeout: 20000 });
const est = await vc.locator('[data-sent=grafo-estado]').textContent();
await vc.getByRole('button', { name: 'Consultar el grafo' }).click(); await page.waitForTimeout(800);
const pre = await vc.locator('[data-sent=grafo-res]').textContent();
await page.screenshot({ path: 'e2e-grafo.png' });
const log = fs.readFileSync('sim.log', 'utf8').trim().split('\n').map((l) => JSON.parse(l));
const sent = log.filter((x) => x.tipo === 'http' && /sentinela_/.test(x.ruta)).map((x) => x.origen + ' ' + x.ruta);
const directo = sent.filter((x) => x.startsWith('navegador') && x.includes('/fichas_qwen/'));
ok('Grafo anclado por el Harness (componente→puente_chat→HTTP→fichas_qwen)', /Grafo SQLite: SAVED/.test(est) && !directo.length && sent.some((x) => x === 'navegador /plugins/puente_chat/call/sentinela_anclar') && sent.some((x) => x === 'harness /plugins/fichas_qwen/call/sentinela_anclar'), { estado: est, rutas: [...new Set(sent)] });
ok('Consulta del grafo devuelve lo anclado', /Grafo SQLite: [1-9]/.test(pre), { res: pre.slice(0, 160) });
// 5) OFF -> lo que llego al modelo
const mods = log.filter((x) => x.tipo === 'modelo');
ok('Nada sale a producción ni a internet', !externos.some((u) => /hf\.space\/plugins/.test(u)), { externos: [...new Set(externos)].slice(0, 5) });
fs.writeFileSync('e2e-resultado.json', JSON.stringify({ res, errores: errores.slice(0, 20), modelo_llamadas: mods.length }, null, 1));
console.log('TOTAL', res.filter((x) => x.ok).length + '/' + res.length);
await browser.close();
