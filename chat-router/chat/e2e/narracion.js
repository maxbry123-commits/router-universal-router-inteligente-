// ¿Durante la espera el chat muestra lo que hace el modelo (burbuja «Pensando…/Enviando…») y el cubo de pensamiento y el botón Detener?
const { chromium } = require('playwright');
(async()=>{const b=await chromium.launch((process.env.CHROMIUM?{executablePath:process.env.CHROMIUM}:{}));
const ctx=await b.newContext({viewport:{width:345,height:700},isMobile:true,hasTouch:true});
await ctx.addInitScript(()=>sessionStorage.setItem('riu_clave','api-e2e'));const p=await ctx.newPage();
await p.route(/chat_async|chat\/send|call\/resultado/, async r => { await new Promise(x => setTimeout(x, 1500)); r.continue(); });  // red lenta: 1,5 s por llamada
await p.goto('http://127.0.0.1:8765/chat/ui/shell.html');await p.waitForSelector('#message',{state:'attached'});await p.waitForTimeout(2500);
await p.fill('#message','hola');await p.$eval('#composer .action',e=>e.click());
const vistos=new Set();let cubo='nunca',detener='nunca',pend='';
for(let i=0;i<60;i++){await p.waitForTimeout(100);const s=await p.evaluate(()=>{const v=e=>{if(!e)return false;const r=e.getBoundingClientRect(),c=getComputedStyle(e);return r.width>0&&r.height>0&&c.visibility!=='hidden'&&c.display!=='none'&&!e.closest('[hidden]')};const pe=[...document.querySelectorAll('.chat-history .pending')].map(x=>x.textContent.trim().slice(0,60));return{pend:pe,cubo:v(document.querySelector('.p3d')),det:v(document.querySelector('#btn-detener'))}});s.pend.forEach(t=>vistos.add(t));if(s.cubo)cubo='visible';if(s.det)detener='visible'}
console.log(JSON.stringify({textosDeEspera:[...vistos],cuboPensamiento:cubo,botonDetener:detener}));await b.close()})()
