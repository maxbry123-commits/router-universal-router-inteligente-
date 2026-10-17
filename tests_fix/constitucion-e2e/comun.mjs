import { chromium } from 'playwright-core';
import fs from 'node:fs';
export const PORT = fs.readFileSync(new URL('./port.txt', import.meta.url), 'utf8').trim();
export const URL0 = 'https://riu-sim.vercel.app/';
export async function abrir() {
  const browser = await chromium.launch({ executablePath: process.env.CHROME || '/usr/bin/google-chrome', args: ['--no-sandbox'] });
  const ctx = await browser.newContext({ viewport: { width: 412, height: 915 }, deviceScaleFactor: 2.6, isMobile: true, hasTouch: true,
    userAgent: 'Mozilla/5.0 (Linux; Android 14; Pixel 8) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.0.0 Mobile Safari/537.36' });
  const externos = [];
  await ctx.route('**/*', async (r) => { const u = r.request().url();
    if (u.startsWith('https://riu-sim.vercel.app/')) {  // mismo origen *.vercel.app (como produccion) servido por el Router simulado local
      const q = r.request(); const res = await fetch('http://127.0.0.1:' + PORT + u.slice('https://riu-sim.vercel.app'.length), { method: q.method(), headers: { 'Content-Type': q.headers()['content-type'] || 'application/json' }, body: q.method() === 'GET' ? undefined : q.postDataBuffer() });
      return r.fulfill({ status: res.status, headers: { 'content-type': res.headers.get('content-type') || 'text/plain', 'cache-control': 'no-store' }, body: Buffer.from(await res.arrayBuffer()) }); }
    if (u.includes('LIVE_URL.json')) return r.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify({ LIVE_URL: 'https://comand-center-1-riu-router.hf.space' }) });
    externos.push(u); return r.abort(); });  // nada sale a produccion (hf.space) ni a internet
  const page = await ctx.newPage();
  const cdp = await ctx.newCDPSession(page);
  await cdp.send('Network.enable');
  await cdp.send('Network.emulateNetworkConditions', { offline: false, latency: 60, downloadThroughput: 9e6 / 8, uploadThroughput: 3e6 / 8 });  // 4G
  const errores = []; page.on('pageerror', (e) => errores.push(String(e))); page.on('console', (m) => { if (m.type() === 'error') errores.push('console: ' + m.text()); });
  return { browser, ctx, page, externos, errores };
}
