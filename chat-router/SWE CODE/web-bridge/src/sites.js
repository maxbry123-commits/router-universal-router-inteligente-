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
    // Calibrado en vivo 2026-11 (es-ES): input[name=email] type=text; el pass solo aparece tras
    // "Iniciar sesión con contraseña"; submit = button[type=submit] "Iniciar sesión".
    // OJO: has-text("Continuar") casaba "Continuar con Google" (OAuth) -> solo submit / text-is.
    login_email: ['input[name="email"]', 'input[type="email"]', 'input[placeholder*="correo" i]', 'input[placeholder*="email" i]'],
    login_pass: ['input[name="password"]', 'input[type="password"]'],
    login_btn: ['button[type="submit"]', 'button:text-is("Iniciar sesión")', 'button:text-is("Log in")', 'button:text-is("Sign in")'],
    // CTA de auth o inputs del form. Evitar falsos positivos post-login.
    login_visible: ['input[name="email"]', 'input[name="password"]', 'input[type="password"]',
      'button:has-text("Iniciar sesión con contraseña")', 'button:has-text("Log in with a password")',
      'a[href*="/auth"]', 'button:has-text("Sign in")'],
    age_gate_continue: ['button:has-text("Continuar")', 'button:has-text("Continue")'],
    // qwen muestra "Login with verification code" por defecto:
    // hay que clicar "Log in with a password" ANTES de llenar el pass
    login_switch_pass: ['button:has-text("Iniciar sesión con contraseña")', 'button:has-text("Log in with a password")',
      'button:has-text("Log in with password")', 'button:has-text("Sign in with password")', 'button:has-text("密码登录")', 'a:has-text("password")'],
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
    // Calibrado comunidad 2025/2026 (.ds-sign-in-form): el identificador es input[type=text]
    // autocomplete=username con placeholder "Phone number / email address" (es-ES: "correo").
    login_email: ['.ds-sign-in-form__main input[autocomplete="username"]', 'input[autocomplete="username"]',
      'input[type="email"]', 'input[name="email"]', 'input[placeholder*="mail" i]', 'input[placeholder*="correo" i]',
      'input[placeholder*="phone" i]', 'input[placeholder*="teléfono" i]', '.ds-sign-in-form__main input[type="text"]'],
    login_pass: ['input[autocomplete="current-password"]', 'input[type="password"]', 'input[name="password"]'],
    login_btn: ['.ds-sign-in-form__main button.ds-basic-button--primary', 'div[role="button"]:has-text("Log in")', 'button:has-text("Log in")',
      'div[role="button"]:has-text("Iniciar sesión")', 'button:has-text("Iniciar sesión")', 'button:has-text("登录")', 'button[type="submit"]'],
    // DeepSeek abre por defecto "código SMS"; pasar a contraseña si existe la pestaña.
    login_switch_pass: [
      'div:text-is("Password")', 'div:text-is("Contraseña")', 'div:text-is("密码登录")',
      'button:has-text("Password")', 'button:has-text("Contraseña")',
      '[role="tab"]:has-text("Password")', '[role="tab"]:has-text("Contraseña")',
      '.ds-tab:has-text("Password")', '.ds-tab:has-text("Contraseña")',
      'div.ds-sign-in-form__tab:has-text("Password")', 'div.ds-sign-in-form__tab:has-text("Contraseña")',
    ],
    // DeepSeek puede mostrar la pantalla de inicio de sesión como modal en /
    // (sin cambiar a /sign_in): una URL / NO prueba cuenta autenticada.
    // Solo señales del FORM de auth (un enlace footer sign_in no debe forzar re-login).
    login_visible: ['.ds-sign-in-form__main', 'input[autocomplete="username"]',
      'input[autocomplete="current-password"]', 'input[type="password"]'],
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
// Evidencia criptográfica/local de sesión (comunidad): Qwen=localStorage.token JWT; DeepSeek=userToken.
async function evidenciaSesionWeb(page, cfg) {
  const u = String(cfg.url || cfg.login_url || '');
  try {
    if (/qwen\.ai/i.test(u)) {
      return await page.evaluate(() => {
        try {
          const t = localStorage.getItem('token') || localStorage.getItem('access_token') || '';
          return t.length > 20 && /^eyJ|^[A-Za-z0-9._-]{20,}$/.test(t);
        } catch { return false; }
      });
    }
    if (/deepseek/i.test(u)) {
      return await page.evaluate(() => {
        try {
          const t = localStorage.getItem('userToken') || localStorage.getItem('token') || '';
          return t.length > 10;
        } catch { return false; }
      });
    }
  } catch { return false; }
  return null; // sitio sin regla (p.ej. Claude): null = no decidir aquí
}

export async function necesitaLogin(page, cfg) {
  // Una URL "/" puede ser página pública o mostrar auth modal: NO es prueba
  // de acceso. Revisar indicadores reales DESPUÉS de la hidratación de la SPA.
  try { if (cfg.sesion_muerta(page.url())) return true; } catch {}
  await page.waitForTimeout(700).catch(() => {});
  const visible = async (sels, ms = 500) => {
    for (const sel of sels || []) {
      try {
        const el = page.locator(sel).first();
        if (await el.count() && await el.isVisible({ timeout: ms }).catch(() => false)) return true;
      } catch {}
    }
    return false;
  };
  // Qwen/DeepSeek: sin token real = guest aunque haya textarea (Qwen lo muestra pre-login).
  const evid = await evidenciaSesionWeb(page, cfg);
  if (evid === true) return false;
  if (evid === false) return true;
  const selLogin = [
    ...(cfg.login_visible || []),
    'input[type="password"]',
    'form input[type="email"]',
    'input[autocomplete="username"]',
    'input[autocomplete="current-password"]',
  ];
  if (await visible(selLogin, 500)) return true;
  if (await visible(cfg.input || [], 600)) return false;
  return true;
}

// Sanitiza texto de UI/API: sin correos, tokens ni claves.
export function sanitizarPista(t, max = 180) {
  return String(t || '')
    .replace(/[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}/gi, '[mail]')
    .replace(/\b[0-9a-f]{16,}\b/gi, '[hex]')
    .replace(/\b(?:password|passwd|pass|token|refresh_token|authorization)\b\s*[:=]\s*\S+/gi, '[redacted]')
    .replace(/\s+/g, ' ')
    .trim()
    .slice(0, max);
}

// Señales de OTP / código / magic-link / error tipico tras submit (sin PII).
export async function leerPistaLogin(page) {
  try {
    const raw = await page.evaluate(() => {
      const sels = [
        '[role="alert"]', '[class*="error" i]', '[class*="Error"]', '.ant-message', '.ant-notification',
        '[class*="toast" i]', '[class*="Toast"]', '[data-testid*="error" i]', '.ds-form-item-error',
        '[class*="message-error" i]', '[class*="helper-text" i]', '[class*="FormError"]'
      ];
      const bits = [];
      for (const s of sels) {
        for (const el of document.querySelectorAll(s)) {
          const t = String(el.innerText || el.textContent || '').trim();
          if (t && t.length < 240) bits.push(t);
        }
      }
      const body = String(document.body?.innerText || '').slice(0, 2500);
      return { bits: bits.slice(0, 6), body };
    });
    const blob = [...(raw.bits || []), raw.body || ''].join(' | ');
    const lower = blob.toLowerCase();
    let motivo = null;
    if (/verifica(tion|ción)?\s*code|código\s*(de\s*)?(verific|sms|otp)|one[- ]time|magic\s*link|te\s+enviamos\s+(un\s+)?c[oó]digo|enter\s+(the\s+)?code|input.*otp|otp/i.test(blob))
      motivo = 'OTP_REQUERIDO';
    else if (/incorrect|inv[aá]lid|wrong\s*password|contrase[nñ]a\s*(incorrecta|inv[aá]lida)|email or password|correo.*contrase|user\s*not\s*found|no\s*encontr|does not exist|cuenta.*no\s*exist/i.test(blob))
      motivo = 'CREDENCIAL_RECHAZADA';
    else if (/captcha|too\s*many|rate\s*limit|suspicious|blocked|acceso\s*denegado|try\s*again\s*later/i.test(blob))
      motivo = 'RETO_O_LIMITE';
    const pista = sanitizarPista((raw.bits && raw.bits[0]) || blob.match(/(incorrect[^.|]{0,80}|inv[aá]lid[^.|]{0,80}|código[^.|]{0,80}|verification[^.|]{0,80}|contrase[nñ]a[^.|]{0,80})/i)?.[0] || '');
    return { motivo, pista: pista || null };
  } catch {
    return { motivo: null, pista: null };
  }
}

async function rellenarHumano(page, lista, valor) {
  for (const sel of lista || []) {
    try {
      const loc = page.locator(sel).first();
      if (!(await loc.isVisible({ timeout: 1500 }).catch(() => false))) continue;
      await loc.click({ timeout: 3000 }).catch(() => {});
      await loc.fill('');
      // React controlado: fill a veces no dispara onChange; pressSequentially sí.
      if (typeof loc.pressSequentially === 'function') {
        await loc.pressSequentially(String(valor), { delay: 25 }).catch(async () => { await loc.fill(String(valor)); });
      } else {
        await loc.fill(String(valor));
      }
      return true;
    } catch { /* siguiente */ }
  }
  return false;
}

// Qwen: el front hashea SHA-256 hex antes del POST /api/v2/auths/signin (comunidad qwengate/qwen2API).
async function loginQwenApi(page, email, pass) {
  const crypto = await import('node:crypto');
  const hash = crypto.createHash('sha256').update(String(pass)).digest('hex');
  const r = await page.evaluate(async ({ email, hash }) => {
    try {
      const resp = await fetch('/api/v2/auths/signin', {
        method: 'POST',
        headers: {
          accept: 'application/json, text/plain, */*',
          'content-type': 'application/json',
          source: 'web',
          timezone: Intl.DateTimeFormat().resolvedOptions().timeZone,
          'x-request-id': (crypto.randomUUID && crypto.randomUUID()) || String(Date.now()),
        },
        credentials: 'include',
        body: JSON.stringify({ email, password: hash }),
      });
      let body = '';
      try { body = await resp.text(); } catch { /* ignore */ }
      return { status: resp.status, ok: resp.ok, body: String(body).slice(0, 240) };
    } catch (e) {
      return { status: 0, ok: false, body: String(e && e.message || e).slice(0, 120) };
    }
  }, { email, hash });
  return r;
}

async function sesionVivaTrasLogin(page, cfg) {
  // Tras submit: solo vivo si ya no hace falta login (login UI / auth URL vencen a token viejo).
  return !(await necesitaLogin(page, cfg));
}

// login: {ok, motivo?, pista?} — nunca loguea email/clave. Formulario + (qwen) API SHA-256 de respaldo.
export async function login(page, cfg, email, pass) {
  await page.goto(cfg.login_url, { waitUntil: 'domcontentloaded' });
  await page.waitForTimeout(1500);
  await pasarAgeGate(page, cfg);
  await page.locator([...(cfg.login_email || []), ...(cfg.login_switch_pass || [])].join(', ')).first()
    .waitFor({ state: 'visible', timeout: 15000 }).catch(() => {});
  if (cfg.login_switch_pass) {
    for (let intento = 0; intento < 2; intento++) {
      let cambiado = false;
      for (const sel of cfg.login_switch_pass) {
        try {
          const loc = page.locator(sel).first();
          if (await loc.isVisible({ timeout: 800 })) {
            await loc.click();
            await page.waitForTimeout(1000);
            cambiado = true;
            break;
          }
        } catch { /* siguiente */ }
      }
      // Confirmar que el campo password quedó visible (DeepSeek SMS-first).
      const passVisible = await page.locator((cfg.login_pass || ['input[type="password"]']).join(', ')).first()
        .isVisible({ timeout: 1500 }).catch(() => false);
      if (passVisible) break;
      if (!cambiado) await page.waitForTimeout(800);
    }
  }
  if (!await rellenarHumano(page, cfg.login_email, email))
    throw Object.assign(new Error('LOGIN_FORM_NO_ENCONTRADO'), { code: 'LOGIN_FORM_NO_ENCONTRADO', campo: 'identificador' });
  if (!await rellenarHumano(page, cfg.login_pass, pass))
    throw Object.assign(new Error('LOGIN_FORM_NO_ENCONTRADO'), { code: 'LOGIN_FORM_NO_ENCONTRADO', campo: 'clave' });
  let pulsado = false;
  for (const sel of cfg.login_btn) {
    try {
      const loc = page.locator(sel).first();
      if (await loc.isVisible({ timeout: 800 })) { await loc.click({ timeout: 5000 }); pulsado = true; break; }
    } catch { /* siguiente */ }
  }
  if (!pulsado) await page.keyboard.press('Enter').catch(() => {});
  await page.waitForLoadState('networkidle', { timeout: 30000 }).catch(() => {});
  await page.waitForTimeout(1800);
  if (await sesionVivaTrasLogin(page, cfg)) return { ok: true };

  // Qwen: si el form no dejó sesión, intentar API con SHA-256 (mismo contrato que el front).
  const esQwen = /qwen\.ai/i.test(String(cfg.url || cfg.login_url || ''));
  if (esQwen) {
    const api = await loginQwenApi(page, email, pass);
    if (api.ok) {
      await page.goto(cfg.url, { waitUntil: 'domcontentloaded', timeout: 45000 }).catch(() => {});
      await page.waitForTimeout(1500);
      if (await sesionVivaTrasLogin(page, cfg)) return { ok: true, via: 'api_sha256' };
    }
    const pistaApi = sanitizarPista(api.body || `http_${api.status}`);
    const ui = await leerPistaLogin(page);
    return {
      ok: false,
      motivo: ui.motivo || (api.status === 401 || api.status === 403 ? 'CREDENCIAL_RECHAZADA' : 'LOGIN_RECHAZADO'),
      pista: ui.pista || pistaApi || null,
      api_status: api.status,
    };
  }

  const ui = await leerPistaLogin(page);
  return { ok: false, motivo: ui.motivo || 'LOGIN_RECHAZADO', pista: ui.pista || null };
}
