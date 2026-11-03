// browser.js — contexto Chromium persistente por sitio + rotacion de cuentas
import { chromium } from 'playwright';
import path from 'node:path';
import fs from 'node:fs';
import { SITES, login, pasarAgeGate, necesitaLogin } from './sites.js';
import { cuentaActual, clave, rotar } from './cuentas.js';

const STATE = process.env.BRIDGE_STATE_DIR || './state';
const PROXY = process.env.BRIDGE_PROXY || null; // http://user:pass@host:port (residencial opcional)

const contextos = new Map(); // site -> {ctx, page, cuenta}
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

  await page.goto(cfg.url, { waitUntil: 'domcontentloaded', timeout: 45000 }).catch(() => {});
  await pasarAgeGate(page, cfg); // Verificación oficial requerida; no saltarla.
  if (!(await necesitaLogin(page, cfg))) { entry.cuenta = cuentaActual(); return entry; }

  // sesion caida: intenta login con cuenta actual, rota hasta agotar
  const total = cuentaActual().total;
  for (let i = 0; i < total; i++) {
    const c = cuentaActual();
    let ok=false;
    try { ok=await login(page, cfg, c.email, clave()); }
    catch (e) { if (e?.code === 'AGE_VERIFICATION_REQUIRED') throw e; }
    if (ok) { await pasarAgeGate(page, cfg); entry.cuenta = c; return entry; }
    rotar(); // siguiente correo, misma clave
  }
  const e = new Error('SESSION_EXPIRED: todas las cuentas fallaron');
  e.code = 'SESSION_EXPIRED';
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
  await page.goto(cfg.url, { waitUntil: 'domcontentloaded', timeout: 45000 }).catch(() => {});
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
