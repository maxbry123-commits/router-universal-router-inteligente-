// Pantalla real del teléfono del Director: 412x690 de área visible (Chrome móvil con barras), IA+Agentes ON, 5 anclados, chat con mensajes.
const { chromium } = require('playwright');
const modo = process.argv[2] || '';
(async()=>{const b=await chromium.launch((process.env.CHROMIUM?{executablePath:process.env.CHROMIUM}:{}));
const ctx=await b.newContext({viewport:{width:+(process.env.W||412),height:+(process.env.H||690)},deviceScaleFactor:2,isMobile:true,hasTouch:true});
await ctx.addInitScript(()=>sessionStorage.setItem('riu_clave','api-e2e'));const p=await ctx.newPage();p.on('pageerror',e=>console.log('ERR',e.message));
await p.goto('http://127.0.0.1:8765/chat/ui/shell.html');await p.waitForSelector('#btn-prompt', { state: 'attached' });await p.waitForTimeout(1800);
for(const s of ['#btn-tools','#btn-agentes']){if(!/ON/.test(await p.textContent(s))){await p.$eval(s, e => e.click());await p.waitForTimeout(500)}}
for(let i=0;i<3;i++){await p.fill('#message','Que modelo eres '+i);await p.$eval('#composer .action',e=>e.click());await p.waitForTimeout(1800)}
await p.evaluate(()=>{const a=document.querySelector('#anclados');if(a)a.innerHTML='<div>INPUT-BLOCK-VERBATIM-FICHAS-MODELOS-2026-10-04.md</div><div>grok_1789211630170.jpg</div><div>+3 más ⚓</div>'});
await p.fill('#message','Ok');
if(modo==='grande'){await p.click('.riu-ampliar');await p.waitForTimeout(300)}
const m=await p.evaluate(()=>{const r=s=>{const e=document.querySelector(s);if(!e)return null;const b=e.getBoundingClientRect();return [Math.round(b.top),Math.round(b.height)]};return {hist:r('.chat-history'),composer:r('#composer'),mensaje:r('#message'),herr:r('.cb-sel-herr'),enviar:r('#composer .action'),btnTools:r('#btn-tools'),vh:innerHeight,solapa:(()=>{const h=document.querySelector('.chat-history').getBoundingClientRect(),c=document.querySelector('#composer').getBoundingClientRect();return Math.round(h.bottom-c.top)})()}});
console.log(JSON.stringify(m));await p.screenshot({path:'phone'+modo+'.png'});await b.close()})()
