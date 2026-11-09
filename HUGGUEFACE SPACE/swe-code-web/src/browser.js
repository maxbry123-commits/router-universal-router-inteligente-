// browser.js — contexto Chromium persistente por sitio + rotacion de cuentas
// AVISO: importa ./cuentas.js, que NO esta copiado (decision del owner). Sin ese modulo no arranca.
import { chromium } from 'playwright';
import path from 'node:path';
import fs from 'node:fs';
import { SITES, login, sesionMuerta } from './sites.js';
import { cuentaActual, clave, rotar } from './cuentas.js';

const STATE = process.env.BRIDGE_STATE_DIR || './state';
const PROXY = process.env.BRIDGE_PROXY || null; // http://user:pass@host:port (residencial opcional)

const contextos = new Map(); // site -> {ctx, page, cuenta}

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
export async function asegurar(site) {
  const cfg = SITES[site];
  if (!cfg) throw new Error(`sitio desconocido: ${site}`);
  let entry = contextos.get(site);
  if (!entry) {
    entry = await lanzar(site);
    contextos.set(site, entry);
  }
  const { page } = entry;
  if (page.isClosed()) { contextos.delete(site); return asegurar(site); }

  await page.goto(cfg.url, { waitUntil: 'domcontentloaded', timeout: 45000 }).catch(() => {});
  if (!sesionMuerta(page, cfg)) { entry.cuenta = cuentaActual(); return entry; }

  // sesion caida: intenta login con cuenta actual, rota hasta agotar
  const total = cuentaActual().total;
  for (let i = 0; i < total; i++) {
    const c = cuentaActual();
    const ok = await login(page, cfg, c.email, clave()).catch(() => false);
    if (ok) { entry.cuenta = c; return entry; }
    rotar(); // siguiente correo, misma clave
  }
  const e = new Error('SESSION_EXPIRED: todas las cuentas fallaron');
  e.code = 'SESSION_EXPIRED';
  throw e;
}

export function estadoCuentas() {
  const out = {};
  for (const [site, e] of contextos) out[site] = e.cuenta || null;
  return out;
}

export async function cerrarTodo() {
  for (const [, e] of contextos) await e.ctx.close().catch(() => {});
  contextos.clear();
}
