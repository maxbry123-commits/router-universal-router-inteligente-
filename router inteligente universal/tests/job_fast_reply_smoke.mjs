// Humo real del boton ⚡ Rapida: el chat REAL (panel-chat.js + api.js sin cambios) en un navegador minimo, hablando con el Router real del job.
// Uso: ROUTER_URL=http://127.0.0.1:8000 RIU_ROUTER_API_KEY=... node job_fast_reply_smoke.mjs <carpeta del frontend con package.json type=module>
import fs from 'node:fs';
const fetchReal = globalThis.fetch;
const { DOC, ERRORES } = await import('./minidom.mjs');
const FE = process.argv[2] || '/tmp/fe', ROUTER = (process.env.ROUTER_URL || 'http://127.0.0.1:8000').replace(/\/$/, ''), KEY = process.env.RIU_ROUTER_API_KEY || '';
process.on('unhandledRejection', (e) => ERRORES.push('RECHAZO: ' + (e && e.message)));
const esperar = (ms) => new Promise((r) => setTimeout(r, ms));
const peticiones = [];
const HOST = /^https:\/\/[a-f0-9]{24}--8000\.hf\.jobs/;
globalThis.fetch = async (url, opts = {}) => {
  let u = String(url); const remoto = HOST.test(u); if (remoto) u = u.replace(HOST, ROUTER);
  peticiones.push({ metodo: opts.method || 'GET', ruta: u.replace(ROUTER, '').slice(0, 90), router_local: remoto, fast_reply: typeof opts.body === 'string' ? (opts.body.match(/"fast_reply":\s*(true|false)/) || [])[1] : undefined });
  return fetchReal(u, opts);
};
sessionStorage.setItem('riu_clave', KEY);
await import(FE + '/config.js');
const shell = fs.readFileSync(FE + '/shell.html', 'utf8').replace(/^[\s\S]*?<body[^>]*>/i, '').replace(/<script[\s\S]*?<\/script>/gi, '').replace(/<\/body>[\s\S]*$/i, '');
DOC.body.innerHTML = shell;
const panel = DOC.querySelector('#panel'); panel.innerHTML = fs.readFileSync(FE + '/panel-chat.html', 'utf8');
const apiMod = await import(FE + '/api.js'), mod = await import(FE + '/panel-chat.js');
await mod.mount(panel, { api: apiMod.api, tell: () => {} }); await esperar(400);
const q = (s) => panel.querySelector(s), btn = q('#btn-fast-reply'), R = {};
R.boton = btn ? btn.textContent : 'NO EXISTE';
btn.click(); await esperar(50); R.tras_clic = btn.textContent + ' | aria-pressed=' + btn.getAttribute('aria-pressed');
window.RIU_SELECTORES = { activo: 'ask-consil-code-qwen-team', selectores: [] };
const enviar = async (txt, marca, limiteS) => {
  const t0 = Date.now(); q('#message').value = txt; q('#composer').requestSubmit();
  while (Date.now() - t0 < limiteS * 1000 && !panel.textContent.includes(marca)) await esperar(1000);
  return { llego_aviso: panel.textContent.includes(marca), segundos: Math.round((Date.now() - t0) / 1000) };
};
R.rapida = await enviar('¿Qué es un DAG? Responde en una frase.', '⚡ respuesta rápida', 240);
const txt = panel.textContent; const i = txt.indexOf('⚡ respuesta rápida'); R.aviso = i >= 0 ? txt.slice(i, i + 40) : null; R.respuesta = i >= 0 ? txt.slice(Math.max(0, i - 160), i).replace(/\s+/g, ' ') : txt.slice(-220);
R.pesada = await enviar('Corrige este código: def f(x): return x +', 'Respuesta rápida omitida', 420);
R.peticiones_con_fast_reply = peticiones.filter((p) => p.fast_reply !== undefined).map((p) => p.ruta + ' fast_reply=' + p.fast_reply);
R.rutas_vistas = [...new Set(peticiones.map((p) => p.metodo + ' ' + p.ruta.split('?')[0]))].slice(0, 12);
R.errores_de_eventos = ERRORES.length; R.errores = ERRORES.slice(0, 3);
console.log('SMOKE ' + JSON.stringify(R));
console.log('SMOKE_RESUMEN ' + (R.rapida.llego_aviso && R.pesada.llego_aviso && ERRORES.length === 0 && R.peticiones_con_fast_reply.some((x) => x.endsWith('true')) ? 'PASS' : 'FALLA'));
process.exit(0);
