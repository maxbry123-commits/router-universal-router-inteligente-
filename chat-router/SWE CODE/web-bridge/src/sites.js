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
    login_btn: ['button:has-text("Continue")', 'button:has-text("Continuar")', 'button[type="submit"]'],
    login_visible: ['button:has-text("Iniciar sesión")', 'a:has-text("Iniciar sesión")', 'button:has-text("Log in")', 'a:has-text("Log in")', 'button:has-text("Sign in")'],
    age_gate_continue: ['button:has-text("Continuar")', 'button:has-text("Continue")'],
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
    // DeepSeek puede mostrar la pantalla de inicio de sesión como modal en /
    // (sin cambiar a /sign_in): una URL / NO prueba cuenta autenticada.
    login_visible: ['a[href*="sign_in"]', 'button:has-text("Log in")',
      'a:has-text("Log in")', 'button:has-text("Sign in")',
      'a:has-text("Sign in")', 'button:has-text("登录")'],
    model_selector: [],
    // No hay selector conocido de V4 Flash; únicamente comprobar un indicador REAL.
    // Sin evidencia del modelo, fallar cerrado (no declarar DeepSeek V4 Flash).
    model_indicador: ['button:has-text("V4 Flash")', '[data-testid*="model" i]',
      'button[aria-label*="model" i]', '[role="combobox"]'],
    nuevo_chat: ['[class*="new" i][class*="chat" i]', 'button:has-text("New chat")', 'div[role="button"]:has-text("New")'],
    sesion_muerta: (url) => /sign_in|login/i.test(url),
    sse_match: /chat|completion|session/i,
  },
  claude: {
    nombre: 'Claude Sonnet · chat web',
    url: 'https://claude.ai/new',
    login_url: 'https://claude.ai/login',
    // Claude usa sesiones autorizadas del navegador; no Anthropic API ni Claude CLI.
    // La autenticación (email, SSO, desafíos) corresponde al titular.
    manual_login: true,
    input: ['div.ProseMirror[contenteditable="true"]', '[contenteditable="true"][data-placeholder]',
      '[role="textbox"][contenteditable="true"]'],
    enviar: ['button[aria-label="Send Message"]', 'button[aria-label="Send message"]',
      'button[data-testid="send-button"]', 'button[type="submit"]'],
    // Priorizar mensajes del asistente: no leer el último mensaje del usuario.
    respuesta: ['.font-claude-response', '[data-testid="assistant-message"]', '[data-is-streaming]'],
    stop_gen: ['button[aria-label*="Stop response" i]', 'button[aria-label*="Stop generating" i]'],
    login_visible: ['a[href*="/login"]', 'button:has-text("Log in")',
      'a:has-text("Log in")', 'button:has-text("Sign in")'],
    model_selector: ['button[data-testid*="model" i]', 'button[aria-label*="model" i]',
      'button:has-text("Sonnet")'],
    model_indicador: ['button:has-text("Sonnet")', '[data-testid*="model" i]'],
    nuevo_chat: ['a[href="/new"]', 'button[aria-label*="New chat" i]'],
    sesion_muerta: (url) => /claude\.ai\/(?:login|auth|signup|verify)/i.test(url),
    sse_match: /completion|conversation|stream/i,
  },
};

// modelos web logicos: sitio + regex para elegir el modelo en el picker de la web
export const MODELOS_WEB = {
  'dsv4-flash':  { site: 'deepseek', etiqueta: 'DeepSeek V4 Flash', modelo_regex: /v4.*flash|flash/i },
  'qwen37max':   { site: 'qwen',     etiqueta: 'Qwen 3.7 Max',      modelo_regex: /3\.7.*max|qwen3\.7-max/i },
  'qwen38max':   { site: 'qwen',     etiqueta: 'Qwen 3.8 Max',      modelo_regex: /3\.8.*max|qwen3\.8-max/i },
  'claude-sonnet': { site: 'claude', etiqueta: 'Claude Sonnet (web)', modelo_regex: /sonnet/i },
};

const VIS_MS = 8500; // 4 candidatos * 8.5s; evitar agotar el deadline WEB por input ausente

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
export async function leerRespuesta(page, cfg, { timeoutMs = 145000, previo = '' } = {}) {
  const sel = cfg.respuesta.join(',');
  const t0 = Date.now();
  let ultimo = '', estable = 0, recibido = '';
  while (Date.now() - t0 < timeoutMs) {
    await page.waitForTimeout(1300);
    const txt = await page.evaluate((sel) => {
      const els = [...document.querySelectorAll(sel)];
      return els.length ? String(els[els.length - 1].innerText || '') : '';
    }, sel);
    if (!txt || txt === previo) continue; // no devolver el mensaje ANTERIOR como si fuera la respuesta
    recibido = txt;
    const generando = await (async () => {
      for (const stop of cfg.stop_gen || []) {
        try { const boton = page.locator(stop).first(); if (await boton.isVisible({timeout:400})) return true; }
        catch { /* DOM cambió */ }
      }
      return false;
    })();
    if (txt === ultimo && !generando) { if (++estable >= 3) return txt; }
    else { estable = 0; ultimo = txt; }
  }
  if (recibido) throw Object.assign(new Error('SALIDA_PARCIAL_NO_CONFIRMADA'), {
    code:'WEB_SALIDA_PARCIAL', texto_parcial:recibido.slice(0,20000) });
  throw Object.assign(new Error('NO_SE_RECIBIO_SALIDA_DEL_CHAT_WEB'), {code:'WEB_SIN_RESPUESTA'});
}

export function sesionMuerta(page, cfg) {
  return cfg.sesion_muerta(page.url());
}

// Verificar el modelo por texto visible (no confiar en el ID del request).
// Si un sitio cambia el DOM, el error es MODELO_SELECTOR_NO_VERIFICADO,
// nunca se sustituye por un modelo local o la API del proveedor.
export async function elegirModelo(page, cfg, modelo_regex) {
  if (!(modelo_regex instanceof RegExp)) return false;
  const indicadores = [...(cfg.model_indicador || []), ...(cfg.model_selector || [])];
  const visibleConModelo = async () => {
    for (const sel of indicadores) {
      try {
        const loc = page.locator(sel).first();
        if (!await loc.isVisible({ timeout: 350 })) continue;
        const label = (await loc.innerText().catch(() => '')) ||
          (await loc.getAttribute?.('aria-label').catch(() => '')) || '';
        if (modelo_regex.test(String(label))) return true;
      } catch { /* otro selector */ }
    }
    return false;
  };
  if (await visibleConModelo()) return true;
  for (const sel of cfg.model_selector || []) {
    try {
      const control = page.locator(sel).first();
      if (!await control.isVisible({ timeout: 500 })) continue;
      await control.click();
      await page.waitForTimeout(350);
      // page.$$ devuelve lista; page.$ devolvía un solo handle o null.
      const opciones = await page.$$(
        '[role="option"], [role="menuitemradio"], [role="menuitem"], ' +
        '[data-testid*="model-option" i], [role="listbox"] button, [role="menu"] button'
      );
      for (const op of opciones) {
        const t = String(await op.innerText().catch(() => '')).trim();
        if (!modelo_regex.test(t) || !await op.isVisible().catch(() => false)) continue;
        await op.click();
        await page.waitForTimeout(450);
        if (await visibleConModelo()) return true; // comprobar POST selección
      }
      await page.keyboard.press('Escape').catch(() => {});
    } catch { /* probar otro control */ }
  }
  return false;
}


// Cualquier control de edad/identidad se resuelve exclusivamente mediante los
// mecanismos oficiales y legítimos de la plataforma por su titular.
// No inventar un año de nacimiento ni completar la verificación automáticamente.
export async function pasarAgeGate(page, cfg) {
  try {
    const modal = page.getByText(/Confirma tu edad|Confirm your age|naciste|year were you born/i).first();
    if (await modal.isVisible().catch(() => false)) {
      throw Object.assign(new Error('AGE_VERIFICATION_REQUIRED'), { code:'AGE_VERIFICATION_REQUIRED' });
    }
  } catch (e) {
    if (e.code === 'AGE_VERIFICATION_REQUIRED') throw e;
  }
  return false;
}

// login necesario: URL de auth O boton "Iniciar sesión"/"Log in" visible (URL puede seguir en /)
export async function necesitaLogin(page, cfg) {
  // Una URL "/" puede ser página pública o mostrar auth modal: NO es prueba
  // de acceso. Revisar indicadores reales DESPUÉS de la hidratación de la SPA.
  try { if (cfg.sesion_muerta(page.url())) return true; } catch {}
  const selLogin = [
    ...(cfg.login_visible || []),
    'input[type="password"]',
    'form input[type="email"]'
  ];
  for (const sel of selLogin) {
    try {
      const el = page.locator(sel).first();
      if (await el.count() && await el.isVisible({ timeout: 400 }).catch(() => false))
        return true;
    } catch {}
  }
  return false;
}

export async function login(page, cfg, email, pass) {
  await page.goto(cfg.login_url, { waitUntil: 'domcontentloaded' });
  await page.waitForTimeout(1500);
  await pasarAgeGate(page, cfg);
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
  await page.waitForTimeout(1000);
  // Antes daba LOGIN_OK por URL incluso si el formulario seguía en pantalla.
  return !(await necesitaLogin(page, cfg));
}
