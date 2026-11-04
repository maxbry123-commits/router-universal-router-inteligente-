// browser.js — contexto Chromium persistente por sitio + rotacion de cuentas
import { chromium } from 'playwright';
import path from 'node:path';
import fs from 'node:fs';
import { SITES, login, pasarAgeGate, necesitaLogin, leerPistaLogin } from './sites.js';
import { cuentaActual, clave, rotar, reiniciarIndice } from './cuentas.js';

const STATE = process.env.BRIDGE_STATE_DIR || './state';
const PROXY = process.env.BRIDGE_PROXY || null; // http://user:pass@host:port (residencial opcional)

const contextos = new Map(); // site -> {ctx, page, cuenta}
// Último motivo de fallo de sesión por sitio (sin datos personales) para @swen/diag.
const ultimoFallo = new Map(); // site -> {code, ts}
// Desafíos anti-bot: no se resuelven ni eluden; se informa al titular.
const RETO = ['iframe[src*="captcha" i]', 'iframe[src*="recaptcha" i]', 'iframe[src*="hcaptcha" i]',
  '[id*="captcha" i]', '[class*="captcha" i]', '#nc_1_wrapper', '[id*="nocaptcha" i]', 'iframe[src*="turnstile" i]'];
async function hayReto(page) {
  for (const s of RETO) { try { if (await page.locator(s).first().isVisible({ timeout: 300 })) return true; } catch {} }
  return false;
}
function fallo(site, code, msg) {
  ultimoFallo.set(site, { code, ts: Date.now() });
  return Object.assign(new Error(msg || code), { code, site });
}
const paginas = new Map();   // convId -> {page, site}
const cola = [];             // espera de slot de tab
const MAX_TABS = parseInt(process.env.BRIDGE_MAX_TABS || '4', 10);

async function lanzar(site) {
  const dir = path.join(STATE, 'perfiles', site);
  fs.mkdirSync(dir, { recursive: true });
  const opts = {
    headless: true,
    args: ['--disable-blink-features=AutomationControlled', '--no-first-run', '--no-default-browser-check'],
    ignoreDefaultArgs: ['--enable-automation'],
    viewport: { width: 1280, height: 900 },
    locale: 'es-ES',
    timezoneId: 'America/Bogota',
    // UA estable sin HeadlessChrome (comunidad DeepSeek/CloudFront).
    userAgent: 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
  };
  if (PROXY) opts.proxy = { server: PROXY };
  const ctx = await chromium.launchPersistentContext(dir, opts);
  // Enmascarar navigator.webdriver en cada documento (stealth minimo, sin plugins externos).
  await ctx.addInitScript(() => {
    try { Object.defineProperty(navigator, 'webdriver', { get: () => undefined }); } catch {}
  }).catch(() => {});
  const page = ctx.pages()[0] || await ctx.newPage();
  return { ctx, page };
}

// asegura sesion viva en el sitio; si cayo -> login con cuenta actual,
// si el login falla -> rota al siguiente correo y reintenta
// un solo asegurar por sitio a la vez: dos modelos del mismo sitio en paralelo (concilio) no lanzan dos Chromium sobre el mismo perfil
const candados = new Map();
export function asegurar(site) {
  const corrida = (candados.get(site) || Promise.resolve()).catch(() => {}).then(() => asegurarSitio(site));
  candados.set(site, corrida.catch(() => {}));
  return corrida;
}

// Fallos de sesión que SOLO el titular resuelve: no se reintentan en bucle
// (evita bloquear cuentas y escalar retos anti-bot). Se enfría N ms y se
// responde al instante con el mismo motivo; importarSesion() lo limpia.
const TERMINALES = new Set(['RETO_ANTIBOT', 'LOGIN_RECHAZADO_TODAS_CUENTAS', 'SIN_SESION_EN_PERFIL', 'SIN_CUENTAS_CONFIGURADAS', 'LOGIN_FORM_NO_ENCONTRADO', 'OTP_REQUERIDO', 'CREDENCIAL_RECHAZADA']);
const ENFRIAR_MS = parseInt(process.env.BRIDGE_SESION_ENFRIAR_MS || '600000', 10);
const LOGIN_MAX = Math.max(1, parseInt(process.env.BRIDGE_LOGIN_MAX || '10', 10));
export function limpiarEnfriamiento(site) { ultimoFallo.delete(site); }

async function asegurarSitio(site) {
  const cfg = SITES[site];
  if (!cfg) throw new Error(`sitio desconocido: ${site}`);
  const previo = ultimoFallo.get(site);
  if (previo && TERMINALES.has(previo.motivo) && Date.now() - previo.ts < ENFRIAR_MS) {
    throw Object.assign(new Error('SESSION_EXPIRED: ' + previo.motivo + ' (enfriando; requiere titular)'), {
      code: 'SESSION_EXPIRED', site, motivo: previo.motivo, terminal: true,
      reintentar_en_s: Math.ceil((ENFRIAR_MS - (Date.now() - previo.ts)) / 1000) });
  }
  let entry = contextos.get(site);
  if (!entry) {
    entry = await lanzar(site);
    contextos.set(site, entry);
  }
  const { page } = entry;
  if (page.isClosed()) { contextos.delete(site); return asegurarSitio(site); }

  try { await page.goto(cfg.url, { waitUntil:'domcontentloaded', timeout:45000 }); }
  catch {
    // Auto-reparación NO destructiva: un solo reciclado del contexto (mismo perfil) y reintento.
    if (!entry._reciclado) {
      contextos.delete(site);
      await entry.ctx.close().catch(() => {});
      const nuevo = await lanzar(site); nuevo._reciclado = true; contextos.set(site, nuevo);
      return asegurarSitio(site);
    }
    throw fallo(site, 'WEB_SITIO_NO_RESPONDE');
  }
  entry._reciclado = false;
  await pasarAgeGate(page, cfg); // Verificación oficial requerida; no saltarla.
  const expirada = await necesitaLogin(page, cfg);
  if (cfg.manual_login) {
    // Claude: no reutilizar el email/clave global de Qwen y DeepSeek.
    // Una cuenta autenticada se conserva en Chromium persistente.
    // Opcional: WEB_SESION_CLAUDE / CLAUDE_STORAGE_STATE = storageState.json del titular.
    let editor = await (async () => {
      for (const sel of cfg.input) {
        try { if (await page.locator(sel).first().isVisible({timeout:400})) return true; } catch {}
      }
      return false;
    })();
    if ((expirada || !editor) && !entry._hidratoEnv) {
      entry._hidratoEnv = true;
      const okH = await hidratarSesionEnv(site);
      if (okH) {
        try { await page.goto(cfg.url, { waitUntil: 'domcontentloaded', timeout: 45000 }); } catch {}
        await pasarAgeGate(page, cfg);
        const exp2 = await necesitaLogin(page, cfg);
        editor = false;
        for (const sel of cfg.input) {
          try { if (await page.locator(sel).first().isVisible({ timeout: 400 })) { editor = true; break; } } catch {}
        }
        if (!exp2 && editor) {
          ultimoFallo.delete(site);
          entry.cuenta = { tipo: 'sesion_web_autorizada', site, via: 'storage_env' };
          return entry;
        }
      }
    }
    if (expirada || !editor) {
      const f = fallo(site, 'SESSION_EXPIRED', 'CLAUDE_WEB_REQUIERE_SESION_AUTORIZADA');
      f.motivo = (await hayReto(page)) ? 'RETO_ANTIBOT' : 'SIN_SESION_EN_PERFIL'; f.terminal = true;
      ultimoFallo.set(site, { code: f.code, motivo: f.motivo, ts: Date.now() });
      throw f;
    }
    entry.cuenta = { tipo:'sesion_web_autorizada', site };
    return entry;
  }
  if (!expirada) { ultimoFallo.delete(site); const c0 = cuentaActual(); entry.cuenta = { index: c0.index, total: c0.total }; return entry; }

  // sesion caida: intenta login con cuenta actual, rota hasta agotar
  const total = cuentaActual().total;
  const intentos = Math.min(total, LOGIN_MAX);  // tope N: no quemar las 10 cuentas en cada llamada
  let ultimaPista = null, ultimoMotivoUi = null;
  for (let i = 0; i < intentos; i++) {
    const c = cuentaActual();
    let res = { ok: false };
    try { res = await login(page, cfg, c.email, clave()); if (res === true) res = { ok: true }; if (res === false) res = { ok: false }; }
    catch (e) {
      if (e?.code === 'AGE_VERIFICATION_REQUIRED') throw e;
      if (e?.code === 'LOGIN_FORM_NO_ENCONTRADO') {  // selectores desactualizados: rotar cuentas no ayuda
        const r = fallo(site, 'SESSION_EXPIRED', 'WEB_LOGIN_FORM_NO_ENCONTRADO'); r.motivo = (await hayReto(page)) ? 'RETO_ANTIBOT' : 'LOGIN_FORM_NO_ENCONTRADO';
        r.campo = e.campo; r.terminal = true; ultimoFallo.set(site, { code: r.code, motivo: r.motivo, campo: e.campo, ts: Date.now() }); throw r;
      }
      res = { ok: false, motivo: e?.code || 'LOGIN_ERROR', pista: String(e?.message || '').slice(0, 120) };
    }
    if (res?.ok) { await pasarAgeGate(page, cfg); ultimoFallo.delete(site); entry.cuenta = { index: c.index, total: c.total }; return entry; }
    ultimaPista = res?.pista || ultimaPista;
    ultimoMotivoUi = res?.motivo || ultimoMotivoUi;
    // OTP / magic-link: rotar no ayuda (mismo factor humano). Fallar cerrado ya.
    if (res?.motivo === 'OTP_REQUERIDO' || await paginaPideOtp(page)) {
      const r = fallo(site, 'SESSION_EXPIRED', 'WEB_OTP_REQUIERE_TITULAR');
      r.motivo = 'OTP_REQUERIDO'; r.terminal = true; r.pista = ultimaPista;
      ultimoFallo.set(site, { code: r.code, motivo: r.motivo, pista: ultimaPista, intentos: i + 1, ts: Date.now() });
      throw r;
    }
    // Reto anti-bot (captcha/slider): headless no puede resolverlo; rotar cuentas
    // solo quema intentos. Fallar cerrado con causa distinguible.
    if (await hayReto(page) || res?.motivo === 'RETO_O_LIMITE') {
      const r = fallo(site, 'SESSION_EXPIRED', 'WEB_RETO_ANTIBOT_REQUIERE_TITULAR');
      r.motivo = 'RETO_ANTIBOT'; r.terminal = true; r.pista = ultimaPista;
      ultimoFallo.set(site, { code: r.code, motivo: r.motivo, pista: ultimaPista, ts: Date.now() });
      throw r;
    }
    rotar(); // siguiente correo, misma clave
  }
  const e = fallo(site, 'SESSION_EXPIRED', 'SESSION_EXPIRED: todas las cuentas fallaron');
  e.motivo = total ? (ultimoMotivoUi === 'CREDENCIAL_RECHAZADA' ? 'CREDENCIAL_RECHAZADA' : 'LOGIN_RECHAZADO_TODAS_CUENTAS') : 'SIN_CUENTAS_CONFIGURADAS';
  e.terminal = true; e.intentos = intentos; e.pista = ultimaPista;
  ultimoFallo.set(site, { code: e.code, motivo: e.motivo, pista: ultimaPista, intentos, ts: Date.now() });
  throw e;
}

async function paginaPideOtp(page) {
  try {
    const p = await leerPistaLogin(page);
    return p.motivo === 'OTP_REQUERIDO';
  } catch { return false; }
}

async function esperarSlot(site) {
  const vivos = [...paginas.values()].filter(p => p.site === site && !p.page.isClosed()).length;
  if (vivos < MAX_TABS) return;
  await new Promise(r => cola.push(r));
}

// cada conversacion = su propio tab + chat nuevo en la web
export async function nuevaPagina(site, convId) {
  const viejo = paginas.get(convId);
  if (viejo && !viejo.page.isClosed()) return viejo.page;
  const { ctx, page: master } = await asegurar(site);
  const cfg = SITES[site];
  await esperarSlot(site);
  const page = await ctx.newPage();
  try { await page.goto(cfg.url, { waitUntil:'domcontentloaded', timeout:45000 }); }
  catch {
    await page.close().catch(() => {});
    throw Object.assign(new Error('WEB_SITIO_NO_RESPONDE'),{code:'WEB_SITIO_NO_RESPONDE'});
  }
  await pasarAgeGate(page, cfg); // Verificación oficial requerida; no saltarla.
  // "New Chat" para que el hilo no se mezcle con el anterior
  for (const sel of cfg.nuevo_chat || []) {
    const el = await page.$(sel);
    if (el) { await el.click().catch(() => {}); await page.waitForTimeout(700); break; }
  }
  const entry = { page, site };
  paginas.set(convId, entry);
  page.on('close', () => { paginas.delete(convId); const w = cola.shift(); if (w) w(); });
  return page;
}

// Recuperación NO destructiva del contexto de un sitio cuando falla la
// navegación ANTES de enviar el prompt. Si hay algún chat activo, no reiniciar.
// Se conserva el perfil persistido; los checkpoints y demás sitios no se tocan.
export async function reiniciarSitioInactivo(site) {
  if (!SITES[site]) return {ok:false,code:'SITIO_INVALIDO'};
  if ([...paginas.values()].some(x=>x.site===site&&!x.page.isClosed()))
    return {ok:false,code:'CHATS_EN_CURSO'};
  const entry=contextos.get(site);
  if (!entry) return {ok:true,code:'SIN_CONTEXTO_ACTIVO'};
  contextos.delete(site);
  try { await entry.ctx.close(); return {ok:true,code:'CONTEXTO_RECICLADO'}; }
  catch { return {ok:false,code:'CIERRE_NAVEGADOR_FALLO'}; }
}

// Diagnóstico seguro del navegador ya abierto, sin texto, URL, DOM, cookies,
 // claves, capturas ni identidades. No ejecuta login ni navega por la web.
export async function diagnosticoAcceso() {
  const r = {};
  for (const [site, cfg] of Object.entries(SITES)) {
    const e = contextos.get(site);
    const perfil = path.join(STATE, 'perfiles', site);
    const base = { perfil_absoluto: path.isAbsolute(STATE), perfil_existe: fs.existsSync(perfil),
      ultimo_fallo: ultimoFallo.get(site) || null };
    if (!e || e.page.isClosed()) { r[site] = { navegador:'SIN_INICIAR', ...base }; continue; }
    const p = e.page;
    const visible = async (selectores) => {
      for (const s of selectores || []) {
        try { if (await p.locator(s).first().isVisible({ timeout:250 })) return true; }
        catch { /* selectores no presentes */ }
      }
      return false;
    };
    const pistaUi = await leerPistaLogin(p).catch(() => ({ motivo: null, pista: null }));
    r[site] = { navegador:'ABIERTO', ...base, reto_antibot: await hayReto(p),
      auth_url: cfg.sesion_muerta(p.url()),
      login_visible:await visible([...(cfg.login_visible||[]),'input[type="password"]','form input[type="email"]']),
      editor_visible:await visible(cfg.input),
      modelo_selector_visible:await visible(cfg.model_selector),
      pista_ui: pistaUi.pista || null, motivo_ui: pistaUi.motivo || null,
      // Es indicador, NO prueba criptográfica de una cuenta autenticada.
      nota:'Los indicadores no demuestran una respuesta de inferencia.' };
  }
  return r;
}

export function estadoCuentas() {
  const out = {};
  for (const [site, e] of contextos) out[site] = e.cuenta || null;
  return out;
}

export function estadoTabs() {
  const porSite = {};
  for (const [convId, e] of paginas) {
    if (e.page.isClosed()) continue;
    (porSite[e.site] ||= []).push(convId);
  }
  return { tabs: porSite, en_cola: cola.length, max_tabs: MAX_TABS };
}


// Diagnóstico: url + title + screenshot PNG base64 de un tab (o lista sin shot).
export async function snapshotTab(convId = null, { shot = true } = {}) {
  const list = [];
  for (const [id, e] of paginas) {
    if (e.page.isClosed()) continue;
    if (convId && id !== convId) continue;
    const url = e.page.url();
    const title = await e.page.title().catch(() => '');
    const item = { conv_id: id, site: e.site, url, title };
    if (shot) {
      const buf = await e.page.screenshot({ fullPage: false, type: 'png' }).catch(() => null);
      item.screenshot_png_base64 = buf ? buf.toString('base64') : null;
    }
    list.push(item);
  }
  if (convId && !list.length) return { ok: false, error: 'TAB_NOT_FOUND', conv_id: convId };
  return { ok: true, tabs: list };
}

export async function cerrarPagina(convId) {
  const e = paginas.get(convId);
  if (e) { await e.page.close().catch(() => {}); paginas.delete(convId); }
}

export async function cerrarTodo() {
  for (const [, e] of contextos) await e.ctx.close().catch(() => {});
  contextos.clear();
  paginas.clear();
}

// Auto-reparación OpenClaw: limpia enfriamiento terminal, recicla contexto inactivo
// y reintenta asegurar(). Usado por POST /refresh_session ante SESSION_EXPIRED.
export async function repararSesion(site = null) {
  const sitios = site ? [site] : Object.keys(SITES);
  const out = {};
  // Al reparar: volver al correo 0 para no quedarse en un índice ya quemado (pool actual=3..).
  try { reiniciarIndice(); } catch { /* sin pool aún */ }
  for (const s of sitios) {
    limpiarEnfriamiento(s);
    const rec = await reiniciarSitioInactivo(s).catch(e => ({ ok: false, code: e?.code || 'RECICLO_FALLO' }));
    try {
      // Intento de hidratar sesión desde archivo del titular (sin secretos en logs).
      await hidratarSesionEnv(s);
      await asegurar(s);
      out[s] = { ok: true, reciclado: rec, estado: 'vivo' };
    } catch (e) {
      out[s] = { ok: false, reciclado: rec, estado: 'caido', code: e?.code || 'SESSION_EXPIRED',
        motivo: e?.motivo || null, pista: e?.pista || ultimoFallo.get(s)?.pista || null,
        reintentar_en_s: e?.reintentar_en_s };
    }
  }
  return out;
}

// WEB_SESION_<SITE>=ruta.json (storageState Playwright del titular). Claude/Qwen/DeepSeek.
// verificar=false cuando se llama DENTRO de asegurarSitio (evita deadlock del candado).
async function hidratarSesionEnv(site, { verificar = false } = {}) {
  const key = `WEB_SESION_${String(site || '').toUpperCase()}`;
  const ruta = process.env[key] || (site === 'claude' ? process.env.CLAUDE_STORAGE_STATE : null);
  if (!ruta || !fs.existsSync(ruta)) return false;
  try {
    const estado = JSON.parse(fs.readFileSync(ruta, 'utf8'));
    const r = await inyectarStorageState(site, estado);
    if (!r.ok) return false;
    if (verificar) {
      try { await asegurar(site); return true; } catch { return false; }
    }
    return true;
  } catch { return false; }
}

// Solo cookies/localStorage — sin asegurar() (seguro desde asegurarSitio / repararSesion).
async function inyectarStorageState(site, estado) {
  const cfg = SITES[site];
  if (!cfg) return { ok: false, code: 'SITIO_INVALIDO' };
  if (!estado || !Array.isArray(estado.cookies) || !estado.cookies.length)
    return { ok: false, code: 'STORAGE_STATE_INVALIDO' };
  const host = new URL(cfg.url).hostname.split('.').slice(-2).join('.');
  const cookies = estado.cookies.filter(c => c && c.name && typeof c.value === 'string' &&
    String(c.domain || '').replace(/^\./, '').endsWith(host)).map(c => {
      const o = { name: c.name, value: c.value, domain: c.domain, path: c.path || '/',
        httpOnly: !!c.httpOnly, secure: c.secure !== false, sameSite: ['Strict', 'Lax', 'None'].includes(c.sameSite) ? c.sameSite : 'Lax' };
      if (typeof c.expires === 'number' && c.expires > 0) o.expires = c.expires;
      return o;
    });
  if (!cookies.length) return { ok: false, code: 'SIN_COOKIES_DEL_SITIO', dominio: host };
  let entry = contextos.get(site);
  if (!entry || entry.page.isClosed()) { entry = await lanzar(site); contextos.set(site, entry); }
  await entry.ctx.addCookies(cookies);
  const origenes = (estado.origins || []).filter(o => o && String(o.origin || '').includes(host));
  for (const o of origenes) {
    try {
      await entry.page.goto(o.origin, { waitUntil: 'domcontentloaded', timeout: 45000 });
      await entry.page.evaluate(items => { for (const i of items || []) localStorage.setItem(i.name, i.value); }, o.localStorage || []);
    } catch { /* origen opcional */ }
  }
  ultimoFallo.delete(site);
  return { ok: true, code: 'STORAGE_INYECTADO', cookies: cookies.length, origenes: origenes.length };
}

// Importación de sesión autorizada (Playwright storageState) exportada por el
// TITULAR desde su propio navegador tras iniciar sesión y resolver cualquier
// verificación oficial. No elude captcha: solo reutiliza una sesión legítima.
// Se inyecta en el perfil persistente existente (mismo contexto/arquitectura).
// Nunca se registran cookies ni valores en logs/respuestas.
export async function importarSesion(site, estado) {
  const inj = await inyectarStorageState(site, estado);
  if (!inj.ok) return inj;
  try {
    await asegurar(site);
    return { ok: true, code: 'SESION_IMPORTADA_Y_VERIFICADA', cookies: inj.cookies, origenes: inj.origenes };
  } catch (e) {
    return { ok: false, code: 'SESION_IMPORTADA_PERO_NO_VALIDA', motivo: e?.motivo || e?.code || 'DESCONOCIDO', cookies: inj.cookies };
  }
}
