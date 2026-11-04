// browser.js — contexto Chromium persistente por sitio + rotacion de cuentas
// Vías 16+17: mutex/cola por sitio + listeners close/disconnect; 1 página maestra Map/sitio.
// Vía 14: verificación API de perfil (401=expirada) vía sites.verificarSesionApi.
// Vías 20+7: import storageState | cookie-JSON | Cookie header | Netscape + tokens.
// Vías 4+15: perfil bajo /data (BRIDGE_STATE_DIR); storageState atómico tmp+rename.
// Vías 5+13: ESPERANDO_LOGIN una vez; pool.json; rotar solo ok; sin WEB_PASS por defecto.
import { chromium } from 'playwright';
import path from 'node:path';
import fs from 'node:fs';
import { SITES, login, pasarAgeGate, necesitaLogin, leerPistaLogin, verificarSesionApi } from './sites.js';
import { cuentaActual, clave, rotar, reiniciarIndice, marcarFallo, cuentasOk, validarYGuardarPool } from './cuentas.js';

const STATE = process.env.BRIDGE_STATE_DIR || './state';
const PROXY = process.env.BRIDGE_PROXY || null; // http://user:pass@host:port (residencial opcional)
const SESIONES_DIR = path.join(STATE, 'sesiones');
// NO WEB_PASS login churn: solo si BRIDGE_ALLOW_WEB_PASS=1 se intenta password.
const ALLOW_WEB_PASS = process.env.BRIDGE_ALLOW_WEB_PASS === '1';

const contextos = new Map(); // site -> {ctx, page, cuenta}
// Último motivo de fallo de sesión por sitio (sin datos personales) para @swen/diag.
const ultimoFallo = new Map(); // site -> {code, ts, motivo?}
// Desafíos anti-bot: no se resuelven ni eluden; se informa al titular.
// Selectores ESTRECHOS: [class*="captcha"] disparaba falsos en UI de login (Google/Apple).
const RETO = ['iframe[src*="recaptcha" i]', 'iframe[src*="hcaptcha" i]', 'iframe[src*="turnstile" i]',
  'iframe[src*="captcha-delivery" i]', '#nc_1_wrapper', '.g-recaptcha', '[data-sitekey]'];
async function hayReto(page) {
  for (const s of RETO) { try { if (await page.locator(s).first().isVisible({ timeout: 300 })) return true; } catch {} }
  return false;
}
function fallo(site, code, msg) {
  ultimoFallo.set(site, { code, ts: Date.now() });
  return Object.assign(new Error(msg || code), { code, site });
}
const paginas = new Map();   // convId -> {page, site, master?}
const cola = [];             // espera de slot de tab
const MAX_TABS = parseInt(process.env.BRIDGE_MAX_TABS || '4', 10);
// Una página maestra por sitio (vía 16): serializa uso; no create/close por request.
const masterLocks = new Map(); // site -> Promise chain
const masterBusy = new Map();  // site -> convId | null

function escribirAtomico(destino, contenido) {
  fs.mkdirSync(path.dirname(destino), { recursive: true });
  const tmp = destino + '.tmp.' + process.pid + '.' + Date.now();
  fs.writeFileSync(tmp, contenido, { mode: 0o600 });
  fs.renameSync(tmp, destino);
}

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
  const entry = { ctx, page };
  // Vía 17: si Chromium cierra el contexto, que nadie reutilice la entrada muerta.
  ctx.on('close', () => { if (contextos.get(site) === entry) contextos.delete(site); });
  page.on('close', () => {
    if (contextos.get(site) === entry) {
      // Página maestra cerrada: invalidar entrada (relanzará en el próximo asegurar).
      contextos.delete(site);
    }
  });
  page.on('crash', () => { if (contextos.get(site) === entry) contextos.delete(site); });
  return entry;
}

// asegura sesion viva en el sitio; si cayo -> login con cuenta actual,
// si el login falla -> rota al siguiente correo y reintenta
// un solo asegurar por sitio a la vez: dos modelos del mismo sitio en paralelo (concilio) no lanzan dos Chromium sobre el mismo perfil
const candados = new Map();
function conCandado(site, fn) {
  const corrida = (candados.get(site) || Promise.resolve()).catch(() => {}).then(fn);
  candados.set(site, corrida.catch(() => {}));
  return corrida;
}
export function asegurar(site) { return conCandado(site, () => asegurarSitioSeguro(site)); }

// Carrera "Target page, context or browser has been closed": descartar contexto muerto y repetir.
const CERRADO_RE = /has been closed|Target (page|closed)|context or browser|Browser closed|browserContext\.newPage|Execution context was destroyed/i;
export const esCierre = (e) => !e?.terminal && CERRADO_RE.test(String(e?.message || e || ''));
async function asegurarSitioSeguro(site, intentos = 3) {
  for (let n = 0; ; n++) {
    try { return await asegurarSitio(site); }
    catch (e) {
      if (!esCierre(e) || n + 1 >= intentos) throw e;
      const viejo = contextos.get(site);
      contextos.delete(site);
      if (viejo) await viejo.ctx.close().catch(() => {});
      await new Promise(r => setTimeout(r, 750 * (n + 1)));
    }
  }
}

// Fallos de sesión que SOLO el titular resuelve: no se reintentan en bucle
// (evita bloquear cuentas y escalar retos anti-bot). Se enfría N ms y se
// responde al instante con el mismo motivo; importarSesion() lo limpia.
const TERMINALES = new Set(['RETO_ANTIBOT', 'LOGIN_RECHAZADO_TODAS_CUENTAS', 'SIN_SESION_EN_PERFIL',
  'SIN_CUENTAS_CONFIGURADAS', 'LOGIN_FORM_NO_ENCONTRADO', 'OTP_REQUERIDO', 'CREDENCIAL_RECHAZADA',
  'ESPERANDO_LOGIN', 'SSO_REQUIERE_IMPORT']);
const ENFRIAR_MS = parseInt(process.env.BRIDGE_SESION_ENFRIAR_MS || '600000', 10);
const LOGIN_MAX = Math.max(1, parseInt(process.env.BRIDGE_LOGIN_MAX || '10', 10));
export function limpiarEnfriamiento(site) { ultimoFallo.delete(site); }

function pedirImportUnaVez(site, page, motivoBase = 'ESPERANDO_LOGIN') {
  const reto = false; // no await aquí — caller pasa hayReto si quiere
  const motivo = motivoBase;
  const f = fallo(site, 'SESSION_EXPIRED', 'WEB_REQUIERE_SESION_IMPORTADA');
  f.motivo = motivo; f.terminal = true; f.importar = true;
  ultimoFallo.set(site, { code: f.code, motivo: f.motivo, ts: Date.now() });
  return f;
}

async function editorVisible(page, cfg) {
  for (const sel of cfg.input || []) {
    try { if (await page.locator(sel).first().isVisible({ timeout: 400 })) return true; } catch {}
  }
  return false;
}

async function asegurarSitio(site) {
  const cfg = SITES[site];
  if (!cfg) throw new Error(`sitio desconocido: ${site}`);
  const previo = ultimoFallo.get(site);
  if (previo && TERMINALES.has(previo.motivo) && Date.now() - previo.ts < ENFRIAR_MS) {
    throw Object.assign(new Error('SESSION_EXPIRED: ' + previo.motivo + ' (enfriando; requiere titular)'), {
      code: 'SESSION_EXPIRED', site, motivo: previo.motivo, terminal: true, importar: true,
      reintentar_en_s: Math.ceil((ENFRIAR_MS - (Date.now() - previo.ts)) / 1000) });
  }
  let entry = contextos.get(site);
  if (!entry) {
    entry = await lanzar(site);
    contextos.set(site, entry);
  }
  const { page } = entry;
  if (page.isClosed()) { contextos.delete(site); await entry.ctx.close().catch(() => {}); return asegurarSitio(site); }

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

  // Hidratar storageState persistido bajo /data/state/sesiones/<site>.json (vía 4+15) si hace falta.
  let expirada = await necesitaLogin(page, cfg);
  if (expirada && !entry._hidratoDisco) {
    entry._hidratoDisco = true;
    const okDisco = await hidratarSesionDisco(site);
    if (okDisco) {
      try { await page.goto(cfg.url, { waitUntil: 'domcontentloaded', timeout: 45000 }); } catch {}
      await pasarAgeGate(page, cfg);
      expirada = await necesitaLogin(page, cfg);
    }
  }

  // Claude / sitios import-only / sin WEB_PASS: nunca quemar password.
  const importOnly = !!cfg.manual_login || !!cfg.auth_import || !ALLOW_WEB_PASS;
  if (importOnly) {
    let editor = await editorVisible(page, cfg);
    if ((expirada || !editor) && !entry._hidratoEnv) {
      entry._hidratoEnv = true;
      const okH = await hidratarSesionEnv(site);
      if (okH) {
        try { await page.goto(cfg.url, { waitUntil: 'domcontentloaded', timeout: 45000 }); } catch {}
        await pasarAgeGate(page, cfg);
        expirada = await necesitaLogin(page, cfg);
        editor = await editorVisible(page, cfg);
        if (!expirada && editor) {
          // Vía 14: confirmar con API de perfil antes de declarar vivo.
          const api = await verificarSesionApi(page, cfg).catch(() => ({ ok: true, skipped: true }));
          if (api && api.ok === false && (api.status === 401 || api.status === 403)) {
            const f = pedirImportUnaVez(site, page, 'ESPERANDO_LOGIN');
            f.motivo = 'SIN_SESION_EN_PERFIL';
            ultimoFallo.set(site, { code: f.code, motivo: f.motivo, ts: Date.now() });
            throw f;
          }
          ultimoFallo.delete(site);
          entry.cuenta = { tipo: 'sesion_web_autorizada', site, via: 'storage_env' };
          await persistirStorageStateAtomico(site, entry).catch(() => {});
          return entry;
        }
      }
    }
    if (expirada || !editor) {
      const f = fallo(site, 'SESSION_EXPIRED', 'WEB_REQUIERE_SESION_IMPORTADA');
      f.motivo = (await hayReto(page)) ? 'RETO_ANTIBOT' : 'ESPERANDO_LOGIN';
      f.terminal = true; f.importar = true;
      ultimoFallo.set(site, { code: f.code, motivo: f.motivo, ts: Date.now() });
      throw f;
    }
    // Vía 14 antes de dar por buena la sesión.
    const api = await verificarSesionApi(page, cfg).catch(() => ({ ok: true, skipped: true }));
    if (api && api.ok === false && (api.status === 401 || api.status === 403)) {
      const f = fallo(site, 'SESSION_EXPIRED', 'WEB_SESION_API_401');
      f.motivo = 'ESPERANDO_LOGIN'; f.terminal = true; f.importar = true;
      ultimoFallo.set(site, { code: f.code, motivo: f.motivo, ts: Date.now() });
      throw f;
    }
    ultimoFallo.delete(site);
    entry.cuenta = { tipo: 'sesion_web_autorizada', site };
    await persistirStorageStateAtomico(site, entry).catch(() => {});
    return entry;
  }

  if (!expirada) {
    const api = await verificarSesionApi(page, cfg).catch(() => ({ ok: true, skipped: true }));
    if (api && api.ok === false && (api.status === 401 || api.status === 403)) {
      // Sesión DOM ok pero API 401 → forzar re-login path abajo.
    } else {
      ultimoFallo.delete(site);
      try { const c0 = cuentaActual(); entry.cuenta = { index: c0.index, total: c0.total }; }
      catch { entry.cuenta = { tipo: 'sesion_web_autorizada', site }; }
      return entry;
    }
  }

  // Password path (solo BRIDGE_ALLOW_WEB_PASS=1): intenta login, rota solo índices ok.
  const total = (() => { try { return cuentaActual().total; } catch { return 0; } })();
  const intentos = Math.min(total, LOGIN_MAX);
  let ultimaPista = null, ultimoMotivoUi = null;
  for (let i = 0; i < intentos; i++) {
    let c;
    try { c = cuentaActual(); } catch {
      const r = fallo(site, 'SESSION_EXPIRED', 'WEB_SIN_CUENTAS'); r.motivo = 'SIN_CUENTAS_CONFIGURADAS';
      r.terminal = true; r.importar = true;
      ultimoFallo.set(site, { code: r.code, motivo: r.motivo, ts: Date.now() }); throw r;
    }
    // Vía 13: saltar índices marcados fallidos.
    if (!cuentasOk(c.index)) { rotar(); continue; }
    let res = { ok: false };
    try { res = await login(page, cfg, c.email, clave()); if (res === true) res = { ok: true }; if (res === false) res = { ok: false }; }
    catch (e) {
      if (e?.code === 'AGE_VERIFICATION_REQUIRED') throw e;
      if (e?.code === 'LOGIN_FORM_NO_ENCONTRADO') {
        const r = fallo(site, 'SESSION_EXPIRED', 'WEB_LOGIN_FORM_NO_ENCONTRADO');
        r.motivo = (await hayReto(page)) ? 'RETO_ANTIBOT' : 'LOGIN_FORM_NO_ENCONTRADO';
        r.campo = e.campo; r.terminal = true; ultimoFallo.set(site, { code: r.code, motivo: r.motivo, campo: e.campo, ts: Date.now() }); throw r;
      }
      res = { ok: false, motivo: e?.code || 'LOGIN_ERROR', pista: String(e?.message || '').slice(0, 120) };
    }
    if (res?.ok) {
      await pasarAgeGate(page, cfg); ultimoFallo.delete(site);
      entry.cuenta = { index: c.index, total: c.total };
      await persistirStorageStateAtomico(site, entry).catch(() => {});
      return entry;
    }
    ultimaPista = res?.pista || ultimaPista;
    ultimoMotivoUi = res?.motivo || ultimoMotivoUi;
    marcarFallo(c.index, res?.motivo || 'LOGIN_RECHAZADO');
    if (res?.motivo === 'OTP_REQUERIDO' || await paginaPideOtp(page)) {
      const r = fallo(site, 'SESSION_EXPIRED', 'WEB_OTP_REQUIERE_TITULAR');
      r.motivo = 'OTP_REQUERIDO'; r.terminal = true; r.pista = ultimaPista;
      ultimoFallo.set(site, { code: r.code, motivo: r.motivo, pista: ultimaPista, intentos: i + 1, ts: Date.now() });
      throw r;
    }
    const retoDom = await hayReto(page);
    const pistaLoginSso = /google|apple|reg[ií]strate|sign\s*up|iniciar\s*sesi[oó]n|sso|oauth/i.test(String(ultimaPista || ''));
    // Si parece SSO: parar password y pedir import (vía 5+13).
    if (pistaLoginSso || res?.motivo === 'SSO_REQUIERE_IMPORT') {
      const r = fallo(site, 'SESSION_EXPIRED', 'WEB_SSO_REQUIERE_IMPORT');
      r.motivo = 'SSO_REQUIERE_IMPORT'; r.terminal = true; r.importar = true; r.pista = ultimaPista;
      ultimoFallo.set(site, { code: r.code, motivo: r.motivo, pista: ultimaPista, ts: Date.now() });
      throw r;
    }
    if ((retoDom && !pistaLoginSso) || res?.motivo === 'RETO_O_LIMITE') {
      const r = fallo(site, 'SESSION_EXPIRED', 'WEB_RETO_ANTIBOT_REQUIERE_TITULAR');
      r.motivo = 'RETO_ANTIBOT'; r.terminal = true; r.pista = ultimaPista;
      ultimoFallo.set(site, { code: r.code, motivo: r.motivo, pista: ultimaPista, ts: Date.now() });
      throw r;
    }
    rotar(); // siguiente correo ok
  }
  const e = fallo(site, 'SESSION_EXPIRED', 'SESSION_EXPIRED: todas las cuentas fallaron');
  e.motivo = total ? (ultimoMotivoUi === 'CREDENCIAL_RECHAZADA' ? 'CREDENCIAL_RECHAZADA' : 'LOGIN_RECHAZADO_TODAS_CUENTAS') : 'SIN_CUENTAS_CONFIGURADAS';
  e.terminal = true; e.intentos = intentos; e.pista = ultimaPista; e.importar = true;
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

// Vía 16: reutilizar la página maestra del sitio (Map) bajo cola/mutex; no create/close por request.
export async function nuevaPagina(site, convId) {
  const viejo = paginas.get(convId);
  if (viejo && !viejo.page.isClosed()) return viejo.page;
  const entry = await asegurar(site);
  const page = entry.page;
  if (page.isClosed()) {
    contextos.delete(site);
    await entry.ctx.close().catch(() => {});
    return nuevaPagina(site, convId);
  }
  await esperarSlot(site);
  // Serializar uso de la maestra por sitio (cola).
  const prev = masterLocks.get(site) || Promise.resolve();
  let release;
  const gate = new Promise(r => { release = r; });
  masterLocks.set(site, prev.then(() => gate).catch(() => gate));
  await prev.catch(() => {});
  masterBusy.set(site, convId);
  const cfg = SITES[site];
  try {
    if (!cfg.sesion_muerta(page.url())) {
      // Ya en sitio; abrir chat nuevo si hace falta.
    } else {
      await page.goto(cfg.url, { waitUntil: 'domcontentloaded', timeout: 45000 }).catch(() => {});
    }
    await pasarAgeGate(page, cfg);
    for (const sel of cfg.nuevo_chat || []) {
      const el = await page.$(sel);
      if (el) { await el.click().catch(() => {}); await page.waitForTimeout(700); break; }
    }
  } catch (e) {
    release();
    masterBusy.set(site, null);
    if (esCierre(e)) {
      contextos.delete(site);
      throw Object.assign(new Error('WEB_SITIO_NO_RESPONDE'), { code: 'WEB_SITIO_NO_RESPONDE', cause: e });
    }
    throw e;
  }
  const slot = { page, site, master: true, _release: release };
  paginas.set(convId, slot);
  // No destruir la maestra al "cerrar" el slot de conv.
  return page;
}

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

export async function diagnosticoAcceso() {
  const r = {};
  for (const [site, cfg] of Object.entries(SITES)) {
    const e = contextos.get(site);
    const perfil = path.join(STATE, 'perfiles', site);
    const sesionFile = path.join(SESIONES_DIR, `${site}.json`);
    const base = { perfil_absoluto: path.isAbsolute(STATE), perfil_existe: fs.existsSync(perfil),
      sesion_import_existe: fs.existsSync(sesionFile),
      auth_mode: (cfg.manual_login || cfg.auth_import || !ALLOW_WEB_PASS) ? 'import' : 'password',
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
    const api = await verificarSesionApi(p, cfg).catch(() => ({ ok: null, error: 'api_skip' }));
    r[site] = { navegador:'ABIERTO', ...base, reto_antibot: await hayReto(p),
      auth_url: cfg.sesion_muerta(p.url()),
      login_visible:await visible([...(cfg.login_visible||[]),'input[type="password"]','form input[type="email"]']),
      editor_visible:await visible(cfg.input),
      modelo_selector_visible:await visible(cfg.model_selector),
      sesion_api: api && typeof api === 'object' ? { ok: api.ok, status: api.status ?? null, motivo: api.motivo || null } : null,
      pista_ui: pistaUi.pista || null, motivo_ui: pistaUi.motivo || null,
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
  return { tabs: porSite, en_cola: cola.length, max_tabs: MAX_TABS, master_busy: Object.fromEntries([...masterBusy]) };
}

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
  if (!e) return;
  paginas.delete(convId);
  const w = cola.shift(); if (w) w();
  if (e._release) { try { e._release(); } catch {} }
  if (masterBusy.get(e.site) === convId) masterBusy.set(e.site, null);
  // Nunca cerrar la página maestra: solo liberar el slot de conversación.
  if (!e.master) await e.page.close().catch(() => {});
}

export async function cerrarTodo() {
  for (const [, e] of contextos) await e.ctx.close().catch(() => {});
  contextos.clear();
  paginas.clear();
  masterBusy.clear();
}

export async function repararSesion(site = null) {
  const sitios = site ? [site] : Object.keys(SITES);
  const out = {};
  try { reiniciarIndice(); } catch { /* sin pool aún */ }
  for (const s of sitios) {
    limpiarEnfriamiento(s);
    out[s] = await conCandado(s, async () => {
      const rec = await reiniciarSitioInactivo(s).catch(e => ({ ok: false, code: e?.code || 'RECICLO_FALLO' }));
      try {
        await hidratarSesionEnv(s);
        await hidratarSesionDisco(s);
        await asegurarSitioSeguro(s);
        return { ok: true, reciclado: rec, estado: 'vivo' };
      } catch (e) {
        return { ok: false, reciclado: rec, estado: 'caido', code: e?.code || 'SESSION_EXPIRED',
          motivo: e?.motivo || (esCierre(e) ? 'CONTEXTO_CERRADO' : null), pista: e?.pista || ultimoFallo.get(s)?.pista || null,
          reintentar_en_s: e?.reintentar_en_s, importar: !!e?.importar };
      }
    });
  }
  return out;
}

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

async function hidratarSesionDisco(site) {
  const ruta = path.join(SESIONES_DIR, `${site}.json`);
  if (!fs.existsSync(ruta)) return false;
  try {
    const estado = JSON.parse(fs.readFileSync(ruta, 'utf8'));
    const r = await inyectarStorageState(site, estado);
    return !!r.ok;
  } catch { return false; }
}

async function persistirStorageStateAtomico(site, entry) {
  if (!entry?.ctx) return false;
  try {
    const estado = await entry.ctx.storageState();
    const dest = path.join(SESIONES_DIR, `${site}.json`);
    escribirAtomico(dest, JSON.stringify(estado));
    return true;
  } catch { return false; }
}

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
  // Tokens explícitos (Claude sessionKey / DeepSeek userToken / Qwen token).
  const tokens = estado._tokens || {};
  if (tokens.sessionKey || tokens.userToken || tokens.token) {
    try {
      const origin = new URL(cfg.url).origin;
      await entry.page.goto(origin, { waitUntil: 'domcontentloaded', timeout: 45000 }).catch(() => {});
      await entry.page.evaluate((t) => {
        if (t.sessionKey) {
          try { localStorage.setItem('sessionKey', t.sessionKey); } catch {}
          try { document.cookie = `sessionKey=${encodeURIComponent(t.sessionKey)}; path=/; Secure; SameSite=Lax`; } catch {}
        }
        if (t.userToken) {
          try { localStorage.setItem('userToken', t.userToken); } catch {}
          try { localStorage.setItem('token', t.userToken); } catch {}
        }
        if (t.token) {
          try { localStorage.setItem('token', t.token); } catch {}
          try { localStorage.setItem('access_token', t.token); } catch {}
        }
      }, tokens);
    } catch { /* token opcional */ }
  }
  ultimoFallo.delete(site);
  return { ok: true, code: 'STORAGE_INYECTADO', cookies: cookies.length, origenes: origenes.length };
}

// Normaliza storageState | cookie-JSON | Cookie header | Netscape | tokens sueltos.
export function normalizarEstadoImport(site, body = {}) {
  const cfg = SITES[site];
  if (!cfg) return { ok: false, code: 'SITIO_INVALIDO' };
  const host = new URL(cfg.url).hostname;
  const baseDomain = host.split('.').slice(-2).join('.');
  const origin = new URL(cfg.url).origin;
  const tokens = {};
  if (body.sessionKey) tokens.sessionKey = String(body.sessionKey);
  if (body.userToken) tokens.userToken = String(body.userToken);
  if (body.token) tokens.token = String(body.token);
  if (body.qwenToken) tokens.token = String(body.qwenToken);
  if (body.deepseekToken) tokens.userToken = String(body.deepseekToken);
  if (body.claudeSessionKey) tokens.sessionKey = String(body.claudeSessionKey);

  let estado = body.storageState || body.estado || null;
  if (typeof estado === 'string') {
    try { estado = JSON.parse(estado); } catch { return { ok: false, code: 'STORAGE_STATE_JSON_INVALIDO' }; }
  }

  // Cookie header: "a=1; b=2"
  const cookieHeader = body.cookie || body.Cookie || body.cookie_header || null;
  // cookies array JSON
  let cookiesIn = body.cookies || (estado && estado.cookies) || null;
  // Netscape cookies.txt
  const netscape = body.netscape || body.cookies_txt || null;

  if (!estado && cookieHeader && typeof cookieHeader === 'string') {
    const cookies = [];
    for (const part of cookieHeader.split(';')) {
      const i = part.indexOf('=');
      if (i < 1) continue;
      const name = part.slice(0, i).trim();
      const value = part.slice(i + 1).trim();
      if (!name) continue;
      cookies.push({ name, value, domain: '.' + baseDomain, path: '/', secure: true, httpOnly: false, sameSite: 'Lax' });
    }
    estado = { cookies, origins: [] };
  } else if (!estado && Array.isArray(cookiesIn)) {
    estado = { cookies: cookiesIn, origins: body.origins || [] };
  } else if (!estado && typeof netscape === 'string') {
    const cookies = [];
    for (const line of netscape.split(/\r?\n/)) {
      const t = line.trim();
      if (!t || t.startsWith('#')) continue;
      const cols = t.split(/\t/);
      if (cols.length < 7) continue;
      const [domain, , pathC, secure, expires, name, value] = cols;
      if (!String(domain || '').replace(/^\./, '').endsWith(baseDomain)) continue;
      const o = { name, value, domain, path: pathC || '/', secure: String(secure).toUpperCase() === 'TRUE', httpOnly: false, sameSite: 'Lax' };
      const exp = parseInt(expires, 10);
      if (exp > 0) o.expires = exp;
      cookies.push(o);
    }
    estado = { cookies, origins: [] };
  }

  // Tokens sueltos → cookies/localStorage sintéticos.
  if ((!estado || !estado.cookies?.length) && Object.keys(tokens).length) {
    const cookies = [];
    const localStorage = [];
    if (tokens.sessionKey) {
      cookies.push({ name: 'sessionKey', value: tokens.sessionKey, domain: '.claude.ai', path: '/', secure: true, httpOnly: false, sameSite: 'Lax' });
      localStorage.push({ name: 'sessionKey', value: tokens.sessionKey });
    }
    if (tokens.userToken) {
      cookies.push({ name: 'userToken', value: tokens.userToken, domain: '.deepseek.com', path: '/', secure: true, httpOnly: false, sameSite: 'Lax' });
      localStorage.push({ name: 'userToken', value: tokens.userToken }, { name: 'token', value: tokens.userToken });
    }
    if (tokens.token) {
      cookies.push({ name: 'token', value: tokens.token, domain: '.' + baseDomain, path: '/', secure: true, httpOnly: false, sameSite: 'Lax' });
      localStorage.push({ name: 'token', value: tokens.token }, { name: 'access_token', value: tokens.token });
    }
    estado = { cookies, origins: localStorage.length ? [{ origin, localStorage }] : [] };
  }

  if (!estado || !Array.isArray(estado.cookies)) return { ok: false, code: 'FORMATO_IMPORT_NO_SOPORTADO' };

  // Fusionar tokens en origins.
  if (Object.keys(tokens).length) {
    estado._tokens = { ...(estado._tokens || {}), ...tokens };
    const ls = [];
    if (tokens.sessionKey) ls.push({ name: 'sessionKey', value: tokens.sessionKey });
    if (tokens.userToken) ls.push({ name: 'userToken', value: tokens.userToken }, { name: 'token', value: tokens.userToken });
    if (tokens.token) ls.push({ name: 'token', value: tokens.token }, { name: 'access_token', value: tokens.token });
    const origins = Array.isArray(estado.origins) ? [...estado.origins] : [];
    const idx = origins.findIndex(o => o && o.origin === origin);
    if (idx >= 0) origins[idx] = { origin, localStorage: [...(origins[idx].localStorage || []), ...ls] };
    else origins.push({ origin, localStorage: ls });
    estado.origins = origins;
  }
  return { ok: true, estado };
}

function expiraDeEstado(estado) {
  try {
    const exps = (estado.cookies || []).map(c => c.expires).filter(n => typeof n === 'number' && n > 0);
    if (!exps.length) return null;
    const min = Math.min(...exps);
    if (min > 1e12) return new Date(min).toISOString(); // ms
    return new Date(min * 1000).toISOString(); // sec
  } catch { return null; }
}

export async function importarSesion(site, bodyOrEstado) {
  const body = (bodyOrEstado && typeof bodyOrEstado === 'object' && (bodyOrEstado.storageState || bodyOrEstado.cookies || bodyOrEstado.cookie || bodyOrEstado.netscape || bodyOrEstado.sessionKey || bodyOrEstado.userToken || bodyOrEstado.token))
    ? bodyOrEstado
    : { storageState: bodyOrEstado };
  const norm = normalizarEstadoImport(site, body);
  if (!norm.ok) return { ok: false, sitio: site, ...norm };
  const estado = norm.estado;
  const inj = await inyectarStorageState(site, estado);
  if (!inj.ok) return { ok: false, sitio: site, expira: null, ...inj };
  // Persistir atómico bajo /data (vía 4+15) ANTES de validar, para sobrevivir reinicios.
  try {
    const dest = path.join(SESIONES_DIR, `${site}.json`);
    escribirAtomico(dest, JSON.stringify(estado));
  } catch { /* disco opcional en local */ }
  try {
    const entry = await asegurar(site);
    // Vía 14: validar con profile API.
    const api = await verificarSesionApi(entry.page, SITES[site]).catch(() => ({ ok: true, skipped: true }));
    if (api && api.ok === false && (api.status === 401 || api.status === 403)) {
      return { ok: false, sitio: site, expira: expiraDeEstado(estado), code: 'SESION_IMPORTADA_PERO_NO_VALIDA',
        motivo: 'SESSION_EXPIRED', api_status: api.status };
    }
    await persistirStorageStateAtomico(site, entry).catch(() => {});
    return { ok: true, sitio: site, expira: expiraDeEstado(estado) || api?.expira || null,
      code: 'SESION_IMPORTADA_Y_VERIFICADA', cookies: inj.cookies, origenes: inj.origenes };
  } catch (e) {
    return { ok: false, sitio: site, expira: expiraDeEstado(estado), code: 'SESION_IMPORTADA_PERO_NO_VALIDA',
      motivo: e?.motivo || e?.code || 'DESCONOCIDO', cookies: inj.cookies };
  }
}

// Export interno (diagnóstico): estado del pool validado.
export function refrescarPool(mails, pass) {
  return validarYGuardarPool(mails, pass);
}
