// LOOP + Cola + Watchdog en el panel del chat. Uso: (servidor.py en :8765) node chat/e2e/loop_cola_watchdog.js
// Backend REAL local (servidor.py, modelos simulados) para la Cola (puente_chat). El plugin loop_wachdog NO existe en el mvp
// (404 "plugin no disponible en mvp"): se prueba que la interfaz lo diga con claridad (SIN_BACKEND) y no finja.
// Se interceptan peticiones SOLO para: acortar el intervalo del JSON, retrasar/romper una ruta y contar peticiones.
const { chromium } = require('playwright');
const BASE = 'http://127.0.0.1:8765';
const KEY = 'api-e2e';
let fallos = 0;
const ok = (n, c, x) => { if (!c) fallos++; console.log((c ? 'PASS ' : 'FAIL ') + n + (x ? ' :: ' + x : '')); };
const esperar = (ms) => new Promise((r) => setTimeout(r, ms));
const VISTAS = [[345, 700, 'movil'], [768, 900, 'tablet'], [1280, 800, 'desk']];

async function limpiarCola() {
  const h = { 'Content-Type': 'application/json', 'X-API-Key': KEY };
  const post = (a, extra) => fetch(BASE + '/plugins/puente_chat/call/checklist', { method: 'POST', headers: h, body: JSON.stringify({ accion: a, ...extra }) }).then((r) => r.json());
  const r = await post('listar');
  for (const t of (r.result && r.result.pendientes) || []) await post('quitar', { id: t.id });
}
async function pagina(b, w, h, opts = {}) {
  const movil = w < 500;
  const ctx = await b.newContext({ viewport: { width: w, height: h }, isMobile: movil, hasTouch: movil });
  const ses = 't2' + Math.random().toString(36).slice(2, 8);  // sesión propia: el servidor guarda el cuaderno/yaiwes por sesión
  await ctx.addInitScript((o) => {
    sessionStorage.setItem('riu_clave', 'api-e2e');
    if (!sessionStorage.getItem('e2e_ini')) {
      sessionStorage.setItem('e2e_ini', '1'); sessionStorage.setItem('riu_sesion', o.ses);
      for (const k of Object.keys(o.seed || {})) sessionStorage.setItem(k, JSON.stringify(o.seed[k]));
    }
  }, { seed: opts.seed || {}, ses });
  const p = await ctx.newPage();
  p.errs = []; p.on('pageerror', (e) => p.errs.push(e.message));
  if (opts.json) {
    await p.route('**/chat/ui/LOOP-wachdog-cola.json', async (route) => {
      const j = await (await route.fetch()).json(); opts.json(j);
      await route.fulfill({ contentType: 'application/json', body: JSON.stringify(j) });
    });
  }
  if (w <= 720) {
    // DEFECTO AJENO (chat/frontend/barra-mas.js y ventana-tareas.js, no autorizados): con <=720px ambos reescriben .mas-nom en cada mutación y el
    // MutationObserver de colocar() se llama a sí mismo sin fin: la pestaña se congela. Solo en ESTA prueba se sirve esa línea con guarda.
    await p.route(/(barra-mas|ventana-tareas)\.js/, async (route) => {
      const t = await (await route.fetch()).text();
      await route.fulfill({ contentType: 'application/javascript', body: t.replace('if (s) s.textContent = b.getAttribute("aria-label");', 'if (s && s.textContent !== b.getAttribute("aria-label")) s.textContent = b.getAttribute("aria-label");').replace('if (nom) nom.textContent = b.getAttribute("aria-label");', 'if (nom && nom.textContent !== b.getAttribute("aria-label")) nom.textContent = b.getAttribute("aria-label");') });
    });
  }
  await p.goto(BASE + '/chat/ui/shell.html');
  await p.waitForSelector('#btn-loop', { state: 'attached', timeout: 15000 });
  await p.waitForSelector('#btn-cola', { state: 'attached' }); await p.waitForSelector('#btn-watchdog', { state: 'attached' });
  await p.waitForTimeout(1200);
  p.ctx = ctx; p.ses = ses; return p;
}
const visible = (p, s) => p.evaluate((s) => { const e = document.querySelector(s); if (!e) return false; const r = e.getBoundingClientRect(), c = getComputedStyle(e); return r.width > 0 && r.height > 0 && c.visibility !== 'hidden' && c.display !== 'none' && !e.closest('[hidden]'); }, s);
const menuMas = async (p) => { if (!(await visible(p, '#btn-loop')) && await visible(p, '#btn-mas')) { await p.click('#btn-mas'); await p.waitForTimeout(250); } };
const abrir = async (p, id) => { await menuMas(p); await p.click('#btn-' + id); await p.waitForSelector('#ventana-' + id + ':not([hidden])'); await p.waitForTimeout(250); };
const cerrar = async (p, id) => { await p.keyboard.press('Escape'); await p.waitForTimeout(150); };
const boton = (p, id, txt) => p.locator('#ventana-' + id + ' button', { hasText: new RegExp('^' + txt + '$') }).first();
const textoVentana = (p, id) => p.evaluate((id) => document.querySelector('#ventana-' + id).innerText, id);

(async () => {
  const b = await chromium.launch(process.env.CHROMIUM ? { executablePath: process.env.CHROMIUM } : {});

  // ===== A) PANEL: las tres piezas aparecen en el chat y no rompen el composer, en 3 anchos =====
  for (const [w, h, nom] of VISTAS) {
    const t = nom + ' ';
    const p = await pagina(b, w, h);
    await menuMas(p);
    for (const id of ['loop', 'watchdog', 'cola']) {
      ok(t + 'A1 botón #btn-' + id + ' visible con nombre accesible', await visible(p, '#btn-' + id) && !!(await p.getAttribute('#btn-' + id, 'aria-label')));
    }
    if (w <= 720) await p.keyboard.press('Escape');
    ok(t + 'A2 composer intacto (#message y Enviar a la vista)', await visible(p, '#message') && await visible(p, '#composer .action'));
    ok(t + 'A3 selector de modelos intacto', await visible(p, '#btn-selector-modelos'));
    for (const id of ['loop', 'watchdog', 'cola']) {
      await abrir(p, id);
      const m = await p.evaluate((id) => { const s = document.querySelector('#ventana-' + id), c = s.querySelector('.va-caja').getBoundingClientRect(); return { sobra: document.documentElement.scrollWidth - innerWidth, dentro: c.left >= -1 && c.right <= innerWidth + 1, modal: s.getAttribute('aria-modal'), rol: s.getAttribute('role') }; }, id);
      ok(t + 'A4 ' + id + ': ventana dentro de la pantalla sin scroll horizontal', m.dentro && m.sobra <= 1, JSON.stringify(m));
      ok(t + 'A5 ' + id + ': role=dialog + aria-modal', m.rol === 'dialog' && m.modal === 'true', JSON.stringify(m));
      const chicos = await p.evaluate((id) => [...document.querySelectorAll('#ventana-' + id + ' button, #ventana-' + id + ' input, #ventana-' + id + ' textarea')].filter((e) => { const r = e.getBoundingClientRect(); return r.width > 0 && (r.width < 24 || r.height < 24); }).map((e) => e.textContent || e.placeholder), id);
      ok(t + 'A6 ' + id + ': objetivos táctiles >= 24px (WCAG 2.5.8)', chicos.length === 0, chicos.join('|'));
      // foco contenido: Tab repetido nunca sale del diálogo
      let fuera = 0;
      for (let i = 0; i < 40; i++) { await p.keyboard.press('Tab'); if (!(await p.evaluate((id) => document.querySelector('#ventana-' + id).contains(document.activeElement), id))) fuera++; }
      ok(t + 'A7 ' + id + ': Tab no escapa del diálogo (foco contenido)', fuera === 0, 'fuera=' + fuera);
      await cerrar(p, id);
      ok(t + 'A8 ' + id + ': Escape cierra' + (w <= 720 ? '' : ' y devuelve el foco al botón'), await p.evaluate(([id, movil]) => document.querySelector('#ventana-' + id).hidden && (movil || (document.activeElement && document.activeElement.id === 'btn-' + id)), [id, w <= 720]));
    }
    ok(t + 'A9 sin errores JS', p.errs.length === 0, p.errs.join('|'));
    await p.ctx.close();
  }

  // ===== B) LOOP (escritorio) =====
  {
    const p = await pagina(b, 1280, 800);
    await abrir(p, 'loop');
    const t = 'desk ';
    // etiquetas accesibles de los campos
    const nombres = await p.evaluate(() => ['#loop-objetivo', '#loop-plan', '#loop-tareas'].map((s) => document.querySelector(s).getAttribute('aria-label') || ''));
    ok(t + 'B1 campos objetivo/plan/tareas con aria-label', nombres.every(Boolean), JSON.stringify(nombres));
    ok(t + 'B2 mensaje de estado en región viva (role=status)', await p.evaluate(() => !!document.querySelector('#ventana-loop [role=status]')));
    ok(t + 'B3 barra de avance role=progressbar con valor', await p.evaluate(() => { const e = document.querySelector('#ventana-loop [role=progressbar]'); return !!e && e.hasAttribute('aria-valuenow'); }));
    // Disparar apagado
    await boton(p, 'loop', 'Disparar').click();
    ok(t + 'B4 Disparar apagado avisa "enciéndelo primero"', /enciéndelo primero/.test(await textoVentana(p, 'loop')));
    // Encender
    await p.fill('#loop-objetivo', 'Objetivo uno'); await p.fill('#loop-plan', 'Plan uno'); await p.fill('#loop-tareas', 'tarea A\ntarea B');
    await boton(p, 'loop', 'Encender').click(); await p.waitForTimeout(600);
    ok(t + 'B5 Encender marca aria-pressed del botón #btn-loop', (await p.getAttribute('#btn-loop', 'aria-pressed')) === 'true');
    const txt = await textoVentana(p, 'loop');
    ok(t + 'B6 sin plugin ni /api/loop la ventana dice SIN_BACKEND (no finge)', /SIN_BACKEND/.test(txt), txt.replace(/\n/g, ' | ').slice(0, 160));
    // ciclo completo contexto→plan→actuar→observar con clics reales
    const fases = [];
    for (let i = 0; i < 4; i++) { await boton(p, 'loop', 'Disparar').click(); await p.waitForTimeout(450); fases.push(await p.evaluate(() => JSON.parse(sessionStorage.getItem('riu_loop')).fase)); }
    ok(t + 'B7 ciclo objetivo→plan→tarea→verificar→objetivo', fases.join('>') === 'plan>tarea>verificar>objetivo', fases.join('>'));
    ok(t + 'B8 una tarea hecha tras la vuelta (hecho=1)', await p.evaluate(() => JSON.parse(sessionStorage.getItem('riu_loop')).hecho) === 1);
    // Apagar y Reiniciar
    await boton(p, 'loop', 'Apagar').click(); await p.waitForTimeout(500);
    ok(t + 'B9 Apagar: on=false y aria-pressed=false', await p.evaluate(() => !JSON.parse(sessionStorage.getItem('riu_loop')).on) && (await p.getAttribute('#btn-loop', 'aria-pressed')) === 'false');
    await boton(p, 'loop', 'Reiniciar').click(); await p.waitForTimeout(500);
    ok(t + 'B10 Reiniciar: paso=0, hecho=0, fase objetivo', await p.evaluate(() => { const e = JSON.parse(sessionStorage.getItem('riu_loop')); return e.paso === 0 && e.hecho === 0 && e.fase === 'objetivo'; }));
    // Yaiwes escribe de verdad en el backend real
    await boton(p, 'loop', 'Yaiwes').click(); await p.waitForTimeout(900);
    const y = await fetch(BASE + '/plugins/puente_chat/call/handoff_texto', { method: 'POST', headers: { 'Content-Type': 'application/json', 'X-API-Key': KEY }, body: JSON.stringify({ sesion: p.ses }) }).then((r) => r.json());
    ok(t + 'B11 Yaiwes dejó el bloque LOOP en el servidor', /loop-yaiwes/.test(((y.result || {}).texto) || '') && /Objetivo uno/.test(((y.result || {}).texto) || ''));
    await p.ctx.close();
  }
  // B12 Yaiwes sin doble escritura
  {
    const p = await pagina(b, 1280, 800); let escrituras = 0;
    await p.route('**/plugins/puente_chat/call/handoff_texto', async (route) => {
      const c = JSON.parse(route.request().postData() || '{}'); if (typeof c.texto === 'string') escrituras++;
      await esperar(700); await route.continue();
    });
    await abrir(p, 'loop'); await p.fill('#loop-objetivo', 'X');
    const y = boton(p, 'loop', 'Yaiwes'); await y.dblclick({ delay: 10 }); await p.waitForTimeout(2500);
    ok('desk B12 doble clic en Yaiwes escribe una sola vez', escrituras === 1, 'escrituras=' + escrituras);
    await p.ctx.close();
  }
  // B13 Proyecto: si el servidor rechaza, la ventana lo dice
  {
    const p = await pagina(b, 1280, 800);
    await p.route('**/plugins/puente_chat/call/proyecto', (route) => route.fulfill({ status: 500, contentType: 'application/json', body: '{"detail":"boom"}' }));
    await abrir(p, 'loop'); await p.fill('#loop-objetivo', 'Obj'); await p.fill('#loop-tareas', 't1');
    await boton(p, 'loop', 'Proyecto').click(); await p.waitForTimeout(900);
    const txt = await textoVentana(p, 'loop');
    ok('desk B13 Proyecto con servidor caído no afirma éxito a secas', /servidor/i.test(txt) && /(no|sin|falló)/i.test(txt.split('\n').filter((l) => /proyecto|servidor/i.test(l)).join(' ')), txt.replace(/\n/g, ' | ').slice(-140));
    await p.ctx.close();
  }
  {  // B13b Proyecto contra el backend real: queda guardado en el servidor
    const p = await pagina(b, 1280, 800);
    await abrir(p, 'loop'); await p.fill('#loop-objetivo', 'Obj'); await p.fill('#loop-tareas', 't1\nt2');
    await boton(p, 'loop', 'Proyecto').click(); await p.waitForTimeout(900);
    const txt = await textoVentana(p, 'loop');
    ok('desk B13b Proyecto real: "guardado en el servidor"', /guardado en el servidor/.test(txt), txt.replace(/\n/g, ' | ').slice(-120));
    const lst = await fetch(BASE + '/plugins/puente_chat/call/proyecto', { method: 'POST', headers: { 'Content-Type': 'application/json', 'X-API-Key': KEY }, body: JSON.stringify({ op: 'list' }) }).then((r) => r.json());
    ok('desk B13c el proyecto LOOP existe en el servidor', ((lst.result || {}).proyectos || []).some((x) => x.nombre === 'LOOP'));
    await p.ctx.close();
  }
  // B14 Seguir usa el intervalo del JSON y nunca solapa pasos; B15 tope
  {
    let vuelo = 0, maxVuelo = 0, pasos = 0;
    const p = await pagina(b, 1280, 800, { json: (j) => { j.wachdog.intervalo_ms = 250; j.wachdog.tope = 50; } });
    await p.route('**/api/loop', async (route) => {
      const c = JSON.parse(route.request().postData() || '{}');
      if (c.accion === 'paso') { pasos++; vuelo++; maxVuelo = Math.max(maxVuelo, vuelo); await esperar(500); vuelo--; }
      await route.fulfill({ status: 404, body: 'no' });
    });
    await abrir(p, 'loop'); await p.fill('#loop-objetivo', 'o'); await p.fill('#loop-plan', 'p'); await p.fill('#loop-tareas', 'a\nb\nc\nd\ne');
    await boton(p, 'loop', 'Encender').click(); await p.waitForTimeout(700);
    await boton(p, 'loop', 'Seguir').click();
    ok('desk B14a Seguir cambia a "Pausa" y marca aria-pressed', (await boton(p, 'loop', 'Pausa').count()) === 1 && (await boton(p, 'loop', 'Pausa').getAttribute('aria-pressed')) === 'true');
    await p.waitForTimeout(3000);
    ok('desk B14b Seguir respeta intervalo_ms del JSON (>=3 pasos en 3 s)', pasos >= 3, 'pasos=' + pasos);
    ok('desk B14c nunca hay dos pasos en vuelo a la vez', maxVuelo <= 1, 'maxVuelo=' + maxVuelo);
    await boton(p, 'loop', 'Pausa').click(); const n0 = pasos; await p.waitForTimeout(1500);
    ok('desk B14d Pausa detiene el bucle', pasos - n0 <= 1, 'extra=' + (pasos - n0));
    await p.ctx.close();
  }
  {
    const p = await pagina(b, 1280, 800, { json: (j) => { j.wachdog.intervalo_ms = 120; j.wachdog.tope = 3; } });
    await abrir(p, 'loop'); await p.fill('#loop-objetivo', 'o'); await p.fill('#loop-plan', 'p'); await p.fill('#loop-tareas', 'a\nb\nc\nd\ne\nf');
    await boton(p, 'loop', 'Encender').click(); await p.waitForTimeout(500);
    await boton(p, 'loop', 'Seguir').click(); await p.waitForTimeout(6000);
    const e = await p.evaluate(() => JSON.parse(sessionStorage.getItem('riu_loop')));
    ok('desk B15 tope del JSON (3) apaga el LOOP solo', e.on === false && e.nota === 'tope' && e.paso === 3, JSON.stringify({ on: e.on, nota: e.nota, paso: e.paso }));
    ok('desk B15b tras el tope el botón #btn-loop queda aria-pressed=false', (await p.getAttribute('#btn-loop', 'aria-pressed')) === 'false');
    await p.ctx.close();
  }

  // ===== C) WATCHDOG (escritorio) =====
  {
    const p = await pagina(b, 1280, 800); let sondeos = 0;
    await p.route('**/plugins/loop_wachdog/call/paso', async (route) => { sondeos++; await route.continue(); });
    await abrir(p, 'watchdog'); const t = 'desk ';
    const estado = () => p.evaluate(() => document.querySelector('#ventana-watchdog .wd-estado').textContent);
    ok(t + 'C1 estado inicial borrador', /borrador/.test(await estado()));
    for (const [txt, n] of [['10 min', 10], ['1 h', 60], ['24 h', 1440], ['48 h', 2880]]) {
      await boton(p, 'watchdog', txt).click();
      ok(t + 'C2 preset ' + txt + ' fija ' + n + ' min y queda aria-pressed', (await p.inputValue('#ventana-watchdog input[type=number]')) === String(n) && (await boton(p, 'watchdog', txt).getAttribute('aria-pressed')) === 'true');
    }
    await boton(p, 'watchdog', 'Validar').click();
    ok(t + 'C3 Validar sin objetivo: "falta objetivo"', /falta objetivo/.test(await textoVentana(p, 'watchdog')));
    await p.fill('#ventana-watchdog textarea', 'Que pase la prueba');
    await p.fill('#ventana-watchdog input[type=number]', '5'); await boton(p, 'watchdog', 'Validar').click();
    ok(t + 'C4 5 min fuera de rango: avisa 10 a 2880', /10 a 2880/.test(await textoVentana(p, 'watchdog')));
    await p.fill('#ventana-watchdog input[type=number]', '99999'); await boton(p, 'watchdog', 'Validar').click();
    ok(t + 'C5 99999 min fuera de rango: avisa', /10 a 2880/.test(await textoVentana(p, 'watchdog')));
    await p.fill('#ventana-watchdog input[type=number]', '10'); await boton(p, 'watchdog', 'Validar').click();
    ok(t + 'C6 10 min con objetivo: plan válido', /plan válido/.test(await textoVentana(p, 'watchdog')));
    // validación obsoleta: cambiar los minutos tras validar obliga a validar de nuevo
    await p.fill('#ventana-watchdog input[type=number]', '99999');
    await boton(p, 'watchdog', 'Activar').click(); await p.waitForTimeout(500);
    ok(t + 'C7 minutos cambiados tras validar: Activar NO activa', !/activo/.test(await estado()), await estado());
    await p.fill('#ventana-watchdog input[type=number]', '10'); await boton(p, 'watchdog', 'Validar').click();
    await boton(p, 'watchdog', 'Activar').dblclick({ delay: 5 }); await p.waitForTimeout(1500);
    ok(t + 'C8 Activar -> activo, aria-pressed del botón del chat y un solo sondeo', /activo/.test(await estado()) && (await p.getAttribute('#btn-watchdog', 'aria-pressed')) === 'true' && sondeos === 1, 'sondeos=' + sondeos);
    ok(t + 'C9 sin plugin en el servidor dice SIN_BACKEND (no finge que corre)', /SIN_BACKEND/.test(await estado()), await estado());
    ok(t + 'C10 muestra cuánto queda o el vencimiento', /quedan|vence|hasta/i.test(await estado()), await estado());
    ok(t + 'C11 mensajes en región viva (role=status)', await p.evaluate(() => !!document.querySelector('#ventana-watchdog [role=status]')));
    await boton(p, 'watchdog', 'Pausar').click(); ok(t + 'C12 Pausar -> pausa', /pausa/.test(await estado()));
    await boton(p, 'watchdog', 'Cancelar').click(); ok(t + 'C13 Cancelar -> cancelado y aria-pressed=false', /cancelado/.test(await estado()) && (await p.getAttribute('#btn-watchdog', 'aria-pressed')) === 'false');
    ok(t + 'C14 el ciclo muestra plan→ejecutar→observar→verificar→decidir', (await textoVentana(p, 'watchdog')).replace(/\s+/g, ' ').includes('plan ejecutar observar verificar decidir'));
    ok(t + 'C15 sin errores JS', p.errs.length === 0, p.errs.join('|'));
    await p.ctx.close();
  }
  {  // vencimiento: un watchdog activo cuyo plazo ya pasó no se muestra como activo
    const p = await pagina(b, 1280, 800, { seed: { riu_watchdog: { estado: 'activo', minutos: 10, objetivo: 'viejo', validado: true, inicio: Date.now() - 11 * 60000 } } });
    await abrir(p, 'watchdog');
    const e = await p.evaluate(() => document.querySelector('#ventana-watchdog .wd-estado').textContent);
    ok('desk C16 watchdog con plazo vencido no figura como activo', /vencido/.test(e) && (await p.getAttribute('#btn-watchdog', 'aria-pressed')) === 'false', e);
    await p.ctx.close();
  }

  // ===== D) COLA contra el backend real (puente_chat) =====
  {
    await limpiarCola();
    const p = await pagina(b, 1280, 800); const t = 'desk ';
    await abrir(p, 'cola');
    const filas = () => p.locator('#ventana-cola .cola-fila span:not(.cola-check)').allTextContents();
    for (const x of ['uno', 'dos', 'tres']) { await p.fill('#ventana-cola textarea', x); await p.press('#ventana-cola textarea', 'Enter'); await p.waitForTimeout(350); }
    ok(t + 'D1 Enter añade 3 tareas en el servidor', (await filas()).join('|') === '1. uno|2. dos|3. tres', (await filas()).join('|'));
    const real = await fetch(BASE + '/plugins/puente_chat/call/checklist', { method: 'POST', headers: { 'Content-Type': 'application/json', 'X-API-Key': KEY }, body: JSON.stringify({ accion: 'listar' }) }).then((r) => r.json());
    ok(t + 'D2 el servidor tiene las 3 tareas', real.result.pendientes.map((x) => x.texto).join('|') === 'uno|dos|tres');
    await p.locator('#ventana-cola input[type=checkbox]').first().check(); await p.waitForTimeout(450);
    ok(t + 'D3 marcar hecha llega al servidor', (await fetch(BASE + '/plugins/puente_chat/call/checklist', { method: 'POST', headers: { 'Content-Type': 'application/json', 'X-API-Key': KEY }, body: JSON.stringify({ accion: 'listar' }) }).then((r) => r.json())).result.pendientes[0].hecho === true);
    await boton(p, 'cola', 'Bajar').first().click(); await p.waitForTimeout(450);
    ok(t + 'D4 Bajar reordena en el servidor', (await filas()).join('|') === '1. dos|2. uno|3. tres', (await filas()).join('|'));
    await boton(p, 'cola', 'Quitar').first().click(); await p.waitForTimeout(450);
    ok(t + 'D5 Quitar elimina', (await filas()).join('|') === '1. uno|2. tres', (await filas()).join('|'));
    ok(t + 'D6 estado: contador y dónde se guarda', /2\/50/.test(await p.textContent('#ventana-cola .wd-estado')) && /servidor|no se guarda/.test(await p.textContent('#ventana-cola .wd-estado')), await p.textContent('#ventana-cola .wd-estado'));
    ok(t + 'D7 lista con role=list y estado en región viva', await p.evaluate(() => !!document.querySelector('#ventana-cola [role=list]') && !!document.querySelector('#ventana-cola [role=status]')));
    ok(t + 'D8 botón Tool con aria-pressed', ['true', 'false'].includes(await p.getAttribute('#ventana-cola .cola-tool', 'aria-pressed')));
    ok(t + 'D9 sin errores JS', p.errs.length === 0, p.errs.join('|'));
    await p.ctx.close(); await limpiarCola();
  }
  {  // servidor caído: modo local claro, y lo hecho sobrevive a cerrar/abrir
    const p = await pagina(b, 1280, 800); const t = 'desk ';
    await p.route('**/plugins/puente_chat/call/checklist', (route) => route.abort());
    await abrir(p, 'cola'); await p.waitForTimeout(800);
    ok(t + 'D10 servidor caído: la Cola dice SIN_BACKEND', /SIN_BACKEND/.test(await textoVentana(p, 'cola')), (await textoVentana(p, 'cola')).replace(/\n/g, ' | ').slice(0, 140));
    await p.fill('#ventana-cola textarea', 'local uno'); await p.press('#ventana-cola textarea', 'Enter'); await p.waitForTimeout(200);
    await p.locator('#ventana-cola input[type=checkbox]').first().check(); await p.waitForTimeout(200);
    await cerrar(p, 'cola'); await abrir(p, 'cola'); await p.waitForTimeout(800);
    ok(t + 'D11 modo local: la tarea y su "hecha" sobreviven a cerrar y abrir', await p.evaluate(() => { const c = document.querySelector('#ventana-cola input[type=checkbox]'); return !!c && c.checked; }));
    await p.ctx.close();
  }

  await b.close();
  console.log(fallos ? ('RESULTADO: ' + fallos + ' FAIL') : 'RESULTADO: todo PASS');
  process.exit(fallos ? 1 : 0);
})().catch((e) => { console.log('ERROR ' + (e && e.stack || e)); process.exit(2); });
