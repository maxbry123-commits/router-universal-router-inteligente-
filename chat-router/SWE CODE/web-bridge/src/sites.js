// sites.js — adaptadores por sitio web de chat
// Escribe el prompt y recoge la salida. Estrategia de lectura:
//   1) intercepta el stream SSE propio de la web (respuesta "cableada", token a token)
//   2) fallback: ultimo bloque de respuesta del asistente estable en el DOM
// Selectores viven aqui agrupados: si la web cambia el DOM, se arregla en este archivo.
//
// Calibrado contra DOM real (chat.qwen.ai): textarea visible pre-login,
// login = email + "Log in with a password" -> password; modelo via aria-label Select Model.

export const SITES = {
  qwen: {
    nombre: 'Qwen web',
    url: 'https://chat.qwen.ai/',
    login_url: 'https://chat.qwen.ai/auth',
    input: ['textarea[placeholder]', 'textarea', 'div[contenteditable="true"]', '[role="textbox"]'],
    enviar: ['button[aria-label*="end" i]', 'button[type="submit"]'],
    respuesta: ['.markdown-body', '[class*="markdown"]', '[class*="message"]', '[class*="prose"]'],
    stop_gen: ['button[aria-label*="top" i]'],
    login_email: ['input[name="email"]', 'input[type="email"]'],
    login_pass: ['input[type="password"]', 'input[name="password"]'],
    login_btn: ['button:has-text("Continue")', 'button[type="submit"]'],
    // qwen muestra "Login with verification code" por defecto:
    // hay que clicar "Log in with a password" ANTES de llenar el pass
    login_switch_pass: ['button:has-text("Log in with a password")', 'a:has-text("password")'],
    model_selector: ['div[aria-label="Select Model"]'],
    nuevo_chat: ['div[aria-label="New Chat"]', 'button[aria-label*="New" i]'],
    model_option_text: /qwen3\.8|3\.8.?max/i,   // se sobrescribe por modelo logico
    sesion_muerta: (url) => /\/auth|login|signin/i.test(url),
    sse_match: /chat|completion|conversation/i,
  },
  deepseek: {
    nombre: 'DeepSeek web',
    url: 'https://chat.deepseek.com/',
    login_url: 'https://chat.deepseek.com/sign_in',
    input: ['textarea[placeholder]', 'textarea', '#chat-input', 'div[contenteditable="true"]'],
    enviar: ['button[aria-label*="end" i]', 'div[role="button"]', 'button[type="submit"]'],
    respuesta: ['.ds-markdown', '.markdown-body', '[class*="markdown"]', '[class*="message"]'],
    stop_gen: ['button[class*="stop" i]'],
    login_email: ['input[type="email"]', 'input[name="email"]', 'input[placeholder*="mail" i]'],
    login_pass: ['input[type="password"]', 'input[name="password"]'],
    login_btn: ['div[role="button"]:has-text("Log in")', 'button:has-text("Log in")', 'button[type="submit"]'],
    model_selector: [],
    nuevo_chat: ['[class*="new" i][class*="chat" i]', 'button:has-text("New chat")', 'div[role="button"]:has-text("New")'],
    sesion_muerta: (url) => /sign_in|login/i.test(url),
    sse_match: /chat|completion|session/i,
  },
};

// modelos web logicos: sitio + regex para elegir el modelo en el picker de la web
export const MODELOS_WEB = {
  'dsv4-flash':  { site: 'deepseek', etiqueta: 'DeepSeek V4 Flash', modelo_regex: /v4.*flash|flash/i },
  'qwen37max':   { site: 'qwen',     etiqueta: 'Qwen 3.7 Max',      modelo_regex: /3\.7.*max|qwen3\.7-max/i },
  'qwen38max':   { site: 'qwen',     etiqueta: 'Qwen 3.8 Max',      modelo_regex: /3\.8.*max|qwen3\.8-max/i },
};

const VIS_MS = 20000;

// espera visible + rellena; sin espera la SPA del Space tardaba -> INPUT_NO_ENCONTRADO falso
export async function escribe(page, cfg, texto) {
  for (const sel of cfg.input) {
    try {
      const el = await page.waitForSelector(sel, { state: 'visible', timeout: VIS_MS });
      if (el) {
        await el.click();
        await el.fill(texto);
        return true;
      }
    } catch { /* siguiente candidato */ }
  }
  return false;
}

export async function enviar(page, cfg) {
  for (const sel of cfg.enviar) {
    const el = await page.$(sel);
    if (el && await el.isVisible().catch(() => true)) { await el.click(); return true; }
  }
  await page.keyboard.press('Enter'); // fallback comun (qwen acepta Enter)
  return true;
}

// espera a que termine de generar: texto del ultimo bloque estable 2 polls
export async function leerRespuesta(page, cfg, { timeoutMs = 180000 } = {}) {
  const sel = cfg.respuesta.join(',');
  const t0 = Date.now();
  let ultimo = '', estable = 0;
  while (Date.now() - t0 < timeoutMs) {
    await page.waitForTimeout(1200);
    const txt = await page.evaluate((sel) => {
      const els = [...document.querySelectorAll(sel)];
      return els.length ? els[els.length - 1].innerText : '';
    }, sel);
    if (txt && txt === ultimo) { if (++estable >= 2) return txt; }
    else { estable = 0; ultimo = txt; }
  }
  return ultimo || null;
}

export function sesionMuerta(page, cfg) {
  return cfg.sesion_muerta(page.url());
}

// elige el modelo en el picker de la web (qwen: aria-label="Select Model")
// si no hay selector o no matchea, sigue con el modelo que este activo
export async function elegirModelo(page, cfg, modelo_regex) {
  if (!cfg.model_selector?.length || !modelo_regex) return false;
  for (const sel of cfg.model_selector) {
    const el = await page.$(sel);
    if (!el) continue;
    await el.click();
    await page.waitForTimeout(800);
    const opciones = await page.$$('[role="option"], [class*="option"], [class*="item"], li, button');
    for (const op of opciones) {
      const t = (await op.innerText().catch(() => '')).trim();
      if (modelo_regex.test(t)) { await op.click(); await page.waitForTimeout(500); return true; }
    }
    await page.keyboard.press('Escape');
    return false;
  }
  return false;
}


// AGE_GATE qwen: modal "Confirma tu edad" — Antonio orden año 2000
export async function pasarAgeGate(page, year = '2000') {
  const modal = page.locator('text=/Confirma tu edad|Confirm your age|naciste|year were you born/i').first();
  try {
    await modal.waitFor({ state: 'visible', timeout: 5000 });
  } catch {
    return false;
  }
  // año: combobox / select / listbox
  const combo = page.locator('button:has-text("2000"), [role="combobox"], select, [class*="select"]').first();
  try {
    if (await combo.count()) {
      await combo.click({ timeout: 2000 }).catch(() => {});
      const opt = page.locator(`[role="option"]:has-text("${year}"), option[value="${year}"], text="${year}"`).first();
      if (await opt.count()) await opt.click({ timeout: 2000 }).catch(() => {});
    }
  } catch {}
  // Continuar
  for (const sel of [
    'button:has-text("Continuar")',
    'button:has-text("Continue")',
    'button:has-text("Confirm")',
  ]) {
    const el = await page.$(sel);
    if (el) { await el.click(); await page.waitForTimeout(800); return true; }
  }
  return false;
}

export async function login(page, cfg, email, pass) {
  await page.goto(cfg.login_url, { waitUntil: 'domcontentloaded' });
  await page.waitForTimeout(1500);
  // qwen: por defecto pide codigo -> cambiar a password primero
  if (cfg.login_switch_pass) {
    for (const sel of cfg.login_switch_pass) {
      const el = await page.$(sel);
      if (el) { await el.click(); await page.waitForTimeout(800); break; }
    }
  }
  for (const sel of cfg.login_email) {
    const el = await page.$(sel);
    if (el) { await el.fill(email); break; }
  }
  for (const sel of cfg.login_pass) {
    const el = await page.$(sel);
    if (el) { await el.fill(pass); break; }
  }
  for (const sel of cfg.login_btn) {
    const el = await page.$(sel);
    if (el) { await el.click(); break; }
  }
  await page.waitForLoadState('networkidle', { timeout: 30000 }).catch(() => {});
  return !sesionMuerta(page, cfg);
}
