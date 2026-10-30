// sites.js — adaptadores por sitio web de chat
// Escribe el prompt y recoge la salida. Estrategia de lectura:
//   1) intercepta el stream SSE propio de la web (respuesta "cableada", token a token)
//   2) fallback: MutationObserver sobre el ultimo mensaje del asistente
// Selectores viven aqui agrupados: si la web cambia el DOM, se arregla en este archivo.
//
// TODO(calibrar-en-vivo): los selectores marcados @@ son candidatos genericos;
// grockbot/Devin los fija contra la pagina real en el primer despliegue.

export const SITES = {
  qwen: {
    nombre: 'Qwen web',
    url: 'https://chat.qwen.ai/',
    login_url: 'https://chat.qwen.ai/auth',
    input: ['@@textarea', 'textarea'],
    enviar: ['@@button[aria-label="Send"]', 'button[type="submit"]'],
    respuesta: ['@@.markdown', '.markdown-body', '[class*="message"]'],
    stop_gen: ['@@button[aria-label="Stop"]'],
    login_email: ['@@input[type="email"]', 'input[name="email"]'],
    login_pass: ['@@input[type="password"]'],
    login_btn: ['@@button[type="submit"]'],
    // detecta muro de login / sesion caida
    sesion_muerta: (url) => /auth|login|signin/i.test(url),
    sse_match: /chat|completion|conversation/i,
  },
  deepseek: {
    nombre: 'DeepSeek web',
    url: 'https://chat.deepseek.com/',
    login_url: 'https://chat.deepseek.com/sign_in',
    input: ['@@textarea', 'textarea'],
    enviar: ['@@div[role="button"]', 'button[type="submit"]'],
    respuesta: ['@@.ds-markdown', '.markdown', '[class*="message"]'],
    stop_gen: ['@@button[class*="stop"]'],
    login_email: ['@@input[type="email"]', 'input[name="email"]'],
    login_pass: ['@@input[type="password"]'],
    login_btn: ['@@button[type="submit"]'],
    sesion_muerta: (url) => /sign_in|login/i.test(url),
    sse_match: /chat|completion|session/i,
  },
};

// modelos web logica: nombre logico -> sitio (+ etiqueta para el prompt al modelo)
export const MODELOS_WEB = {
  'dsv4-flash':  { site: 'deepseek', etiqueta: 'DeepSeek V4 Flash' },
  'qwen37max':   { site: 'qwen',     etiqueta: 'Qwen 3.7 Max' },
  'qwen38max':   { site: 'qwen',     etiqueta: 'Qwen 3.8 Max' },
};

export async function escribe(page, cfg, texto) {
  for (const sel of cfg.input) {
    const el = await page.$(sel.replace(/^@@/, ''));
    if (el) {
      await el.click();
      await el.fill(texto);
      return true;
    }
  }
  return false;
}

export async function enviar(page, cfg) {
  for (const sel of cfg.enviar) {
    const el = await page.$(sel.replace(/^@@/, ''));
    if (el) { await el.click(); return true; }
  }
  await page.keyboard.press('Enter'); // fallback comun
  return true;
}

// espera a que termine de generar: no mas boton stop + texto estable 2 polls
export async function leerRespuesta(page, cfg, { timeoutMs = 180000 } = {}) {
  const sel = cfg.respuesta.map(s => s.replace(/^@@/, '')).join(',');
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

export async function login(page, cfg, email, pass) {
  await page.goto(cfg.login_url, { waitUntil: 'domcontentloaded' });
  for (const sel of cfg.login_email) {
    const el = await page.$(sel.replace(/^@@/, ''));
    if (el) { await el.fill(email); break; }
  }
  for (const sel of cfg.login_pass) {
    const el = await page.$(sel.replace(/^@@/, ''));
    if (el) { await el.fill(pass); break; }
  }
  for (const sel of cfg.login_btn) {
    const el = await page.$(sel.replace(/^@@/, ''));
    if (el) { await el.click(); break; }
  }
  await page.waitForLoadState('networkidle', { timeout: 30000 }).catch(() => {});
  return !sesionMuerta(page, cfg);
}
