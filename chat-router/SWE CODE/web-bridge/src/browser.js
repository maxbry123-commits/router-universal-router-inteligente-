// browser.js — contexto Chromium persistente por sitio + rotacion de cuentas
import { chromium } from 'playwright';
import path from 'node:path';
import fs from 'node:fs';
import { SITES, login, pasarAgeGate, necesitaLogin } from './sites.js';
import { cuentaActual, clave, rotar } from './cuentas.js';

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
    args: ['--disable-blink-features=AutomationControlled'],
    viewport: { width: 1280, height: 900 },
    locale: 'es-ES',
    timezoneId: 'America/Bogota',
    userAgent: 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36',
  };
  if (PROXY) opts.proxy = { server: PROXY };
  const ctx = await chromium.launchPersistentContext(dir, opts);
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

async function asegurarSitio(site) {
  const cfg = SITES[site];
  if (!cfg) throw new Error(`sitio desconocido: ${site}`);
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
    const editor = await (async () => {
      for (const sel of cfg.input) {
        try { if (await page.locator(sel).first().isVisible({timeout:400})) return true; } catch {}
      }
      return false;
    })();
    if (expirada || !editor) {
      const f = fallo(site, 'SESSION_EXPIRED', 'CLAUDE_WEB_REQUIERE_SESION_AUTORIZADA');
      f.motivo = (await hayReto(page)) ? 'RETO_ANTIBOT' : 'SIN_SESION_EN_PERFIL';
      ultimoFallo.set(site, { code: f.code, motivo: f.motivo, ts: Date.now() });
      throw f;
    }
    entry.cuenta = { tipo:'sesion_web_autorizada', site };
    return entry;
  }
  if (!expirada) { ultimoFallo.delete(site); entry.cuenta = cuentaActual(); return entry; }

  // sesion caida: intenta login con cuenta actual, rota hasta agotar
  const total = cuentaActual().total;
  for (let i = 0; i < total; i++) {
    const c = cuentaActual();
    let ok=false;
    try { ok=await login(page, cfg, c.email, clave()); }
    catch (e) { if (e?.code === 'AGE_VERIFICATION_REQUIRED') throw e; }
    if (ok) { await pasarAgeGate(page, cfg); ultimoFallo.delete(site); entry.cuenta = c; return entry; }
    // Reto anti-bot (captcha/slider): headless no puede resolverlo; rotar cuentas
    // solo quema intentos. Fallar cerrado con causa distinguible.
    if (await hayReto(page)) {
      const r = fallo(site, 'SESSION_EXPIRED', 'WEB_RETO_ANTIBOT_REQUIERE_TITULAR');
      r.motivo = 'RETO_ANTIBOT'; ultimoFallo.set(site, { code: r.code, motivo: r.motivo, ts: Date.now() });
      throw r;
    }
    rotar(); // siguiente correo, misma clave
  }
  const e = fallo(site, 'SESSION_EXPIRED', 'SESSION_EXPIRED: todas las cuentas fallaron');
  e.motivo = total ? 'LOGIN_RECHAZADO_TODAS_CUENTAS' : 'SIN_CUENTAS_CONFIGURADAS';
  ultimoFallo.set(site, { code: e.code, motivo: e.motivo, ts: Date.now() });
  throw e;
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
    r[site] = { navegador:'ABIERTO', ...base, reto_antibot: await hayReto(p),
      auth_url: cfg.sesion_muerta(p.url()),
      login_visible:await visible([...(cfg.login_visible||[]),'input[type="password"]','form input[type="email"]']),
      editor_visible:await visible(cfg.input),
      modelo_selector_visible:await visible(cfg.model_selector),
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
