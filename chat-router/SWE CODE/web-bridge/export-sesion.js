#!/usr/bin/env node
// export-sesion.js — el TITULAR exporta storageState desde SU PC (sesión legítima).
// No corre en el Space. No elude captcha: inicia sesión a mano y guarda cookies.
//
// Uso:
//   node export-sesion.js qwen ./qwen.json
//   node export-sesion.js deepseek ./deepseek.json
//   node export-sesion.js claude ./claude.json
//
// Luego importa:
//   curl -X POST "$SPACE/web/v1/web/sesion/importar" \
//     -H "X-API-Key: $CLAVE" -H "content-type: application/json" \
//     -d "{\"site\":\"qwen\",\"storageState\":$(cat qwen.json)}"
//
// Tokens sueltos (alternativa):
//   Claude:   { "site":"claude", "sessionKey":"..." }
//   DeepSeek: { "site":"deepseek", "userToken":"..." }
//   Qwen:     { "site":"qwen", "token":"..." }

import { chromium } from 'playwright';
import fs from 'node:fs';
import path from 'node:path';

const SITIOS = {
  qwen: 'https://chat.qwen.ai/',
  deepseek: 'https://chat.deepseek.com/',
  claude: 'https://claude.ai/new',
};

const site = String(process.argv[2] || '').toLowerCase();
const out = process.argv[3] || `./${site || 'sesion'}.json`;
if (!SITIOS[site]) {
  console.error('Uso: node export-sesion.js <qwen|deepseek|claude> [salida.json]');
  process.exit(2);
}

const url = SITIOS[site];
console.log(`[export-sesion] Abriendo ${url}`);
console.log('[export-sesion] Inicia sesión y resuelve verificaciones oficiales. Cierra la ventana al terminar.');

const ctx = await chromium.launchPersistentContext(path.join(process.cwd(), `.export-profile-${site}`), {
  headless: false,
  viewport: { width: 1280, height: 900 },
});
const page = ctx.pages()[0] || await ctx.newPage();
await page.goto(url, { waitUntil: 'domcontentloaded' });

await new Promise((resolve) => {
  ctx.on('close', resolve);
  page.on('close', resolve);
});

const estado = await ctx.storageState().catch(async () => {
  // Si el usuario cerró todo, intentar desde un context efímero no aplica; fallar claro.
  throw new Error('contexto cerrado antes de storageState');
});
fs.writeFileSync(out, JSON.stringify(estado, null, 2));
console.log(`[export-sesion] Guardado ${out} (cookies=${estado.cookies?.length || 0}, origins=${estado.origins?.length || 0})`);
console.log('[export-sesion] Importa con POST /web/v1/web/sesion/importar (ver SESION_IMPORTAR.md).');
try { await ctx.close(); } catch {}
