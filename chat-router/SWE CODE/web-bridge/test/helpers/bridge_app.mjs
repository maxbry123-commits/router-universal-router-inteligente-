// helper de pruebas de integracion (no es un test): copia web-bridge a un temporal, express real o stub, playwright falso y motor.js falso.
import { spawn, spawnSync } from 'node:child_process';
import fs from 'node:fs';
import http from 'node:http';
import net from 'node:net';
import os from 'node:os';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { envConAcceso } from './acceso.mjs';

const ORIGEN = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..', '..');
export const TMP = fs.mkdtempSync(path.join(os.tmpdir(), 'bridge-ret-'));
const APP = path.join(TMP, 'app');
export const servidores = [], mocks = [];

const MOTOR_FALSO = `
export async function consultarWeb(modelo) { return 'WEB[' + modelo + ']'; }
export async function salud() { return {}; }
`;
const EXPRESS_STUB = `
import http from 'node:http';
function express() {
  const rutas = [], mws = [];
  const app = async (req, res) => {
    const u = new URL(req.url, 'http://x');
    req.query = Object.fromEntries(u.searchParams); req.path = u.pathname; req.params = {};
    res.status = (c) => { res.statusCode = c; return res; };
    res.json = (o) => { if (!res.getHeader('content-type')) res.setHeader('content-type', 'application/json'); res.end(JSON.stringify(o)); return res; };
    for (const mw of mws) await new Promise((ok) => mw(req, res, ok));
    if (res.writableEnded) return;
    for (const r of rutas) {
      if (r.metodo !== req.method) continue;
      const ks = []; const re = new RegExp('^' + r.ruta.replace(/:([a-zA-Z_]+)/g, (_, k) => { ks.push(k); return '([^/]+)'; }) + '$');
      const m = re.exec(u.pathname); if (!m) continue;
      ks.forEach((k, i) => req.params[k] = decodeURIComponent(m[i + 1]));
      return r.fn(req, res);
    }
    res.statusCode = 404; res.end('not found');
  };
  app.use = (fn) => mws.push(fn);
  app.set = () => app;
  for (const m of ['get', 'post', 'delete']) app[m] = (ruta, fn) => rutas.push({ metodo: m.toUpperCase(), ruta, fn });
  app.listen = (port, cb) => { const s = http.createServer(app).listen(port, cb); return s; };
  return app;
}
express.json = () => (req, res, next) => {
  if (req.method !== 'POST') return next();
  let d = ''; req.on('data', (c) => d += c);
  req.on('end', () => { try { req.body = d ? JSON.parse(d) : {}; next(); } catch { res.statusCode = 400; res.end('bad json'); } });
};
export default express;
`;

export function prepararApp() {
  fs.mkdirSync(APP, { recursive: true });
  fs.cpSync(path.join(ORIGEN, 'src'), path.join(APP, 'src'), { recursive: true });
  fs.writeFileSync(path.join(APP, 'package.json'), JSON.stringify({ name: 'bridge-test', private: true, type: 'module', dependencies: { express: '^4.19.2' } }));
  fs.writeFileSync(path.join(APP, 'src', 'motor.js'), MOTOR_FALSO);
  fs.writeFileSync(path.join(APP, 'preload.mjs'), `const r = await import('./src/respaldo.js');\nif (process.env.TEST_GROQ_URL) r.BASES.groq = process.env.TEST_GROQ_URL;\n`);
  let real = false;
  if (!process.env.TEST_STUB_EXPRESS) {
    const r = spawnSync('npm', ['install', 'express', '--no-audit', '--no-fund', '--no-package-lock', '--loglevel=error'], { cwd: APP, timeout: 120000, encoding: 'utf8' });
    real = r.status === 0 && fs.existsSync(path.join(APP, 'node_modules', 'express', 'package.json'));
  }
  if (!real) {
    const d = path.join(APP, 'node_modules', 'express');
    fs.mkdirSync(d, { recursive: true });
    fs.writeFileSync(path.join(d, 'package.json'), JSON.stringify({ name: 'express', type: 'module', main: 'index.js', exports: './index.js' }));
    fs.writeFileSync(path.join(d, 'index.js'), EXPRESS_STUB);
  }
  const pw = path.join(APP, 'node_modules', 'playwright');
  fs.mkdirSync(pw, { recursive: true });
  fs.writeFileSync(path.join(pw, 'package.json'), JSON.stringify({ name: 'playwright', type: 'module', main: 'index.js', exports: './index.js' }));
  fs.writeFileSync(path.join(pw, 'index.js'), `export const chromium = {};\n`);
  return real;
}

const puertoLibre = () => new Promise((ok) => { const s = net.createServer().listen(0, '127.0.0.1', () => { const p = s.address().port; s.close(() => ok(p)); }); });

export async function arrancar(nombre, envExtra = {}) {
  const port = await puertoLibre();
  const state = envExtra.BRIDGE_STATE_DIR || path.join(TMP, `state-${nombre}`);
  fs.mkdirSync(state, { recursive: true });
  const env = { PATH: process.env.PATH, HOME: TMP, TMPDIR: TMP, BRIDGE_PORT: String(port), BRIDGE_STATE_DIR: state, BRIDGE_AUTOACTUALIZAR: '0', ...envConAcceso(envExtra) };
  const p = spawn(process.execPath, ['--import', './preload.mjs', 'src/server.js'], { cwd: APP, env, stdio: ['ignore', 'pipe', 'pipe'] });
  let log = '';
  p.stdout.on('data', (c) => log += c); p.stderr.on('data', (c) => log += c);
  await new Promise((ok, ko) => {
    const t = setTimeout(() => ko(new Error(`server ${nombre} no arranco:\n${log}`)), 15000);
    const iv = setInterval(() => { if (/escuchando/.test(log)) { clearTimeout(t); clearInterval(iv); ok(); } }, 50);
    p.on('exit', (c) => { clearTimeout(t); clearInterval(iv); ko(new Error(`server ${nombre} salio (${c}):\n${log}`)); });
  });
  const srv = { nombre, port, state, proc: p, base: `http://127.0.0.1:${port}`, log: () => log, matar: async () => { p.kill('SIGKILL'); await new Promise((ok) => p.once('exit', ok)); } };
  servidores.push(srv);
  return srv;
}

export function limpiar() {
  for (const s of servidores) s.proc.kill('SIGKILL');
  for (const m of mocks) { m.closeAllConnections?.(); m.close(); }
  fs.rmSync(TMP, { recursive: true, force: true });
}
export const registrarMock = (s) => mocks.push(s);
