// Espejo del chat en producción: abre el chat REAL en un navegador (móvil 345×700), entra con la clave, pulsa cada botón y prueba cada modelo.
// Corre en GitHub Actions (.github/workflows/espejo-chat.yml) o en local. Salida: capturas + reporte.json + reporte.md en OUT.
// Seguridad: la clave llega por la variable RIU_QA_KEY (secreto del repo) y nunca se imprime ni se guarda. No pulsa botones destructivos
// (apagar/reiniciar el Router, borrar, limpiar, cancelar). Los interruptores IA / Agentes / System prompt se pulsan DOS veces: quedan como estaban.
const { chromium } = require('playwright');
const fs = require('fs'), path = require('path');
const BASE = process.env.BASE || 'https://riu-jev-bridge.vercel.app/';
const KEY = process.env.RIU_QA_KEY || '';
const OUT = process.env.OUT || 'espejo-salida';
const CON_MODELOS = process.env.CON_MODELOS !== '0';
const NO_PULSAR = /power|servidor|reinici|apag|borrar|eliminar|limpiar|cancelar|cerrar sesi/i;
const DOBLE = /btn-tools|btn-agentes|btn-prompt|IA (ON|OFF)|Agentes (ON|OFF)|System prompt (ON|OFF)/i;
fs.mkdirSync(OUT, { recursive: true });
const rep = { base: BASE, con_clave: !!KEY, inicio: new Date().toISOString(), cabecera: '', consola: [], red_fallos: [], botones: [], modelos: [], resumen: {} };
const limpia = (s) => String(s || '').replace(KEY && KEY.length > 3 ? KEY : /$^/, '[clave]');
const foto = async (p, n) => { const f = path.join(OUT, n + '.png'); try { await p.screenshot({ path: f }); } catch (e) {} return n + '.png'; };
(async () => {
  const b = await chromium.launch();
  const ctx = await b.newContext({ viewport: { width: 345, height: 700 }, isMobile: true, hasTouch: true, deviceScaleFactor: 2 });
  if (KEY) await ctx.addInitScript((k) => { try { sessionStorage.setItem('riu_clave', k); } catch (e) {} }, KEY);
  const p = await ctx.newPage();
  p.on('pageerror', (e) => rep.consola.push(limpia('pageerror: ' + e.message)));
  p.on('console', (m) => { if (m.type() === 'error') rep.consola.push(limpia('console: ' + m.text()).slice(0, 200)); });
  p.on('response', (r) => { if (r.status() >= 400) rep.red_fallos.push(r.status() + ' ' + r.request().method() + ' ' + limpia(r.url()).replace(/[?&](key|clave)=[^&]*/g, '').slice(0, 140)); });
  const abrir = async () => { await p.goto(BASE, { waitUntil: 'domcontentloaded', timeout: 60000 }); await p.waitForSelector('#message', { state: 'attached', timeout: 45000 }).catch(() => {}); await p.waitForTimeout(3500); };
  await abrir();
  rep.cabecera = limpia(await p.evaluate(() => (document.body.innerText.match(/Router disponible|Sin conexi[oó]n|Acceso requerido|Error de Router|Router/i) || [''])[0]));
  rep.version = await p.evaluate(() => fetch('/chat/ui/version.json', { cache: 'no-store' }).then(r => r.json()).then(j => j.commit).catch(() => ''));
  await foto(p, '00-inicio');
  rep.hay_clave_pedida = await p.evaluate(() => /Clave de acceso/i.test(document.body.innerText));
  // inventario de botones visibles
  const lista = await p.evaluate(() => [...document.querySelectorAll('button, [role=button]')].map((e, i) => { const r = e.getBoundingClientRect(), c = getComputedStyle(e); if (!(r.width > 0 && r.height > 0 && c.display !== 'none' && c.visibility !== 'hidden') || e.closest('[hidden]')) return null; return { i, id: e.id || '', nombre: (e.getAttribute('aria-label') || e.title || e.textContent || '').replace(/\s+/g, ' ').trim().slice(0, 40), ancho: Math.round(r.width), alto: Math.round(r.height) }; }).filter(Boolean));
  rep.resumen.botones_visibles = lista.length;
  let n = 0;
  for (const bt of lista) {
    const etiqueta = bt.id || bt.nombre || ('boton-' + bt.i);
    if (NO_PULSAR.test(bt.id + ' ' + bt.nombre)) { rep.botones.push({ ...bt, resultado: 'NO SE PULSA (puede apagar, reiniciar o borrar)' }); continue; }
    const veces = DOBLE.test(bt.id + ' ' + bt.nombre) ? 2 : 1;
    try {
      await abrir();
      const antes = await p.evaluate((i) => { const e = document.querySelectorAll('button, [role=button]')[i]; return e ? { t: (e.textContent || '').trim(), p: e.getAttribute('aria-pressed'), hojas: [...document.querySelectorAll('.sheet:not([hidden])')].length } : null; }, bt.i);
      if (!antes) { rep.botones.push({ ...bt, resultado: 'no encontrado tras recargar' }); continue; }
      let despues = antes;
      for (let k = 0; k < veces; k++) {
        await p.evaluate((i) => document.querySelectorAll('button, [role=button]')[i].scrollIntoView({ block: 'center' }), bt.i);
        await p.locator('button, [role=button]').nth(bt.i).click({ timeout: 8000 });
        await p.waitForTimeout(900);
        despues = await p.evaluate((i) => { const e = document.querySelectorAll('button, [role=button]')[i]; return { t: e ? (e.textContent || '').trim() : '(desapareció)', p: e ? e.getAttribute('aria-pressed') : null, hojas: [...document.querySelectorAll('.sheet:not([hidden])')].length }; }, bt.i);
        if (k === 0) await foto(p, String(++n).padStart(2, '0') + '-' + etiqueta.replace(/[^a-z0-9]+/gi, '_').slice(0, 24));
      }
      const efecto = (despues.hojas > antes.hojas ? 'abre ventana' : despues.t !== antes.t || despues.p !== antes.p ? 'cambia estado' : 'sin cambio visible');
      rep.botones.push({ ...bt, resultado: veces === 2 ? 'pulsado 2 veces (queda como estaba): ' + efecto : efecto });
    } catch (e) { rep.botones.push({ ...bt, resultado: 'ERROR al pulsar: ' + limpia(e.message).split('\n')[0].slice(0, 120) }); }
  }
  // modelos reales: encender cada selector, preguntar y leer quién responde
  if (CON_MODELOS && KEY) {
    for (const [fila, nombre, elegir] of [['team-qwen', 'Team qwen glm-5.3', 'glm-5.3'], ['groq', 'Groq', ''], ['nvidia-groq-team', 'NVIDIA', ''], ['team-5-mvp', 'Team 5 MVP', '']]) {
      const r = { selector: nombre, estado: '' };
      try {
        await abrir();
        await p.evaluate(() => window.RIU_SELECTORES && window.RIU_SELECTORES.apagar && window.RIU_SELECTORES.apagar()); await p.waitForTimeout(300);
        await p.click('#btn-selector-modelos', { timeout: 6000 }).catch(() => {}); await p.waitForTimeout(500);
        if (elegir) { await p.locator('#sel-nuevo').click({ timeout: 6000 }); await p.waitForTimeout(1500); r.modelos_en_lista = await p.locator('#sh-modelos-lista button').count(); await p.evaluate((n) => { const x = [...document.querySelectorAll('#sh-modelos-lista button')].find(e => e.textContent.includes(n)); if (x) x.click(); }, elegir); await p.waitForTimeout(500); await p.click('#btn-selector-modelos', { timeout: 6000 }).catch(() => {}); await p.waitForTimeout(400); }
        if (fila === 'groq') { await p.locator('#sel-groq').click({ timeout: 6000 }).catch(() => {}); await p.waitForTimeout(1500); r.hoja_groq = limpia(await p.evaluate(() => (document.querySelector('#sh-groq-lista') || {}).innerText || '')).slice(0, 160); await foto(p, 'groq-hoja'); await p.evaluate(() => { const x = document.querySelector('#sh-groq-lista button'); if (x) x.click(); }); await p.waitForTimeout(500); await p.click('#btn-selector-modelos', { timeout: 6000 }).catch(() => {}); await p.waitForTimeout(400); }
        const on = p.locator('.sel-fila[data-selector="' + fila + '"] .sel-on');
        if (!(await on.evaluate(e => e.classList.contains('on')).catch(() => false))) await on.click({ timeout: 6000 }).catch(() => {});
        await p.waitForTimeout(500); r.indicador = limpia((await p.textContent('#btn-selector-modelos').catch(() => '')) || '').trim();
        await p.keyboard.press('Escape'); await p.waitForTimeout(300);
        const n0 = await p.locator('.chat-history .message:not(.user):not(.pending)').count();
        await p.fill('#message', 'Responde en una sola línea: ¿qué modelo eres?'); await p.$eval('#composer .action', e => e.click());
        await p.waitForFunction((n) => document.querySelectorAll('.chat-history .message:not(.user):not(.pending)').length > n && !document.querySelector('.chat-history .message.pending'), n0, { timeout: 70000 }).catch(() => {});
        r.respuesta = limpia(await p.evaluate(() => [...document.querySelectorAll('.chat-history .message:not(.user):not(.pending)')].slice(-3).map(x => x.innerText.replace(/\s+/g, ' ').trim()).join(' | '))).slice(0, 400);
        r.estado = /Modelo solicitado|Soy |soy /.test(r.respuesta) ? 'respondió' : 'sin respuesta de modelo';
        await foto(p, 'modelo-' + fila);
      } catch (e) { r.estado = 'ERROR: ' + limpia(e.message).split('\n')[0].slice(0, 120); }
      rep.modelos.push(r);
    }
  }
  const sinCambio = rep.botones.filter(x => /sin cambio/.test(x.resultado)).length, errores = rep.botones.filter(x => /ERROR|no encontrado/.test(x.resultado)).length;
  rep.resumen = { ...rep.resumen, pulsados: rep.botones.filter(x => !/NO SE PULSA/.test(x.resultado)).length, sin_cambio_visible: sinCambio, con_error: errores, errores_consola: rep.consola.length, fallos_de_red: rep.red_fallos.length, fin: new Date().toISOString() };
  fs.writeFileSync(path.join(OUT, 'reporte.json'), JSON.stringify(rep, null, 1));
  const md = ['# Espejo del chat — ' + rep.base, '', 'Commit servido: `' + (rep.version || '?') + '` · Cabecera: **' + rep.cabecera + '** · clave aplicada: ' + (rep.con_clave ? 'sí' : 'NO'), '', 'Resumen: ' + JSON.stringify(rep.resumen), '', '## Botones (345×700)', '| id | nombre | tamaño | resultado |', '|---|---|---|---|', ...rep.botones.map(x => `| ${x.id} | ${x.nombre} | ${x.ancho}×${x.alto} | ${x.resultado} |`), '', '## Modelos', ...rep.modelos.map(m => `- **${m.selector}** → ${m.estado}${m.modelos_en_lista != null ? ' (lista: ' + m.modelos_en_lista + ' modelos)' : ''} · indicador: ${m.indicador || '-'} · ${m.respuesta || m.hoja_groq || ''}`), '', '## Errores de consola', ...rep.consola.slice(0, 20).map(x => '- ' + x), '', '## Fallos de red (4xx/5xx)', ...rep.red_fallos.slice(0, 30).map(x => '- ' + x)];
  fs.writeFileSync(path.join(OUT, 'reporte.md'), md.join('\n'));
  console.log(md.slice(0, 6).join('\n')); await b.close();
})().catch((e) => { console.log('ERROR', limpia(e.message).split('\n')[0]); process.exit(1); });
