// inventario de controles del chat (id, nombre accesible, visible/oculto/en ventana) en una pantalla de teléfono; salida JSON
const { chromium } = require('playwright');
(async()=>{const b=await chromium.launch((process.env.CHROMIUM?{executablePath:process.env.CHROMIUM}:{}));
const ctx=await b.newContext({viewport:{width:345,height:700},isMobile:true,hasTouch:true});
await ctx.addInitScript(()=>sessionStorage.setItem('riu_clave','api-e2e'));const p=await ctx.newPage();
await p.goto('http://127.0.0.1:8765/chat/ui/shell.html');await p.waitForSelector('#message',{state:'attached'});await p.waitForTimeout(3000);
const inv=await p.evaluate(()=>{const o={};document.querySelectorAll('button, select, textarea, input, [role=button]').forEach(e=>{const n=(e.id||e.getAttribute('aria-label')||e.title||e.textContent||'').trim().replace(/\s+/g,' ').slice(0,40);if(!n)return;const r=e.getBoundingClientRect();const hid=e.closest('[hidden]')||r.width===0||getComputedStyle(e).display==='none';const enSheet=!!e.closest('.sheet,.cb-hoja');const mv=!!e.closest('#movil-panel');o[n]=(hid?(enSheet?'ventana':mv?'panel superior':'oculto'):'visible')});return o});
console.log(JSON.stringify(inv));await b.close()})()
