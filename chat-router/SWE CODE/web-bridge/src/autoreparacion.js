// SWEN · recuperación determinista + consulta especializada a OpenClaw.
// No evade autenticación, retos de identidad/edad, cuotas ni cambio de modelo.
// El agente consultor es read-only; nunca ejecuta un parche de sus sugerencias.
import fs from 'node:fs';
import path from 'node:path';
import crypto from 'node:crypto';

const BASE = process.env.BRIDGE_STATE_DIR || '/tmp/state';
const ARCHIVO = path.join(BASE, 'swen-gaps.json');
const ID = /^gap_[0-9a-f]{24}$/;
const MODELO = /^(?:web-(?:qwen38max|qwen37max|dsv4-flash|claude-sonnet)|swecode-consulta)$/;
const CLAVES = new Set([
  'SESSION_EXPIRED','AGE_VERIFICATION_REQUIRED','CF_CHALLENGE',
  'WEB_SITIO_NO_RESPONDE','SELECTOR_BROKEN','MODELO_SELECTOR_NO_VERIFICADO',
  'UPSTREAM_TIMEOUT','WEB_SIN_RESPUESTA','WEB_SALIDA_PARCIAL',
  'CLAUDE_AGENTE_NO_INSTALADO','CLAUDE_GATEWAY_NO_CONECTADO',
  'CLAUDE_GATEWAY_NO_DISPONIBLE','CLAUDE_GATEWAY_NO_CONFIGURADO',
  'CLAUDE_GATEWAY_NO_AUTORIZADO','CLAUDE_CUENTAS_AGOTADAS',
  'CUENTAS_FALTAN','NO_AUTORIZADO','BRIDGE_ERROR'
]);
const INTERVENCION = new Set([
  'SESSION_EXPIRED','AGE_VERIFICATION_REQUIRED','CF_CHALLENGE',
  'CLAUDE_GATEWAY_NO_AUTORIZADO','CLAUDE_CUENTAS_AGOTADAS',
  'CUENTAS_FALTAN','NO_AUTORIZADO'
]);
const RECUPERABLE = new Set(['WEB_SITIO_NO_RESPONDE']);
const MINUTOS = 5 * 60_000;
const MAX_CONSULTAS_DIARIAS = 8;
const agent = 'openclaw/swen-repair';

export function clasificarGap(code) {
  const codigo=String(code||'BRIDGE_ERROR').toUpperCase().slice(0,90);
  const seguro=CLAVES.has(codigo)?codigo:'BRIDGE_ERROR';
  const requiereUsuario=INTERVENCION.has(seguro);
  return {
    codigo:seguro,
    estado:requiereUsuario?'🚩 REQUIERE_OPERADOR':
      RECUPERABLE.has(seguro)?'RECUPERABLE':'🚧 DIAGNOSTICAR',
    reintentar:RECUPERABLE.has(seguro),
    accion:requiereUsuario?'Mantener checkpoint y solicitar acceso oficial/permiso o cuota válida; no eludir controles':
      seguro==='MODELO_SELECTOR_NO_VERIFICADO'?'Revisar selector de modelo y no atribuir la respuesta a otro modelo':
      seguro==='CLAUDE_AGENTE_NO_INSTALADO'?'Revisar registro y modelo del agente en OpenClaw; no cambiar a otro modelo':
      seguro==='CLAUDE_GATEWAY_NO_CONECTADO'?'Comprobar salud/configuración del Gateway existente y sus logs':
      seguro==='WEB_SITIO_NO_RESPONDE'?'Reintentar UNA vez el mismo modelo tras una falla de navegación previa al envío':
      'Conservar estado, investigar con herramientas y reportar solución verificable'
  };
}
function leer() {
  try {
    const s=JSON.parse(fs.readFileSync(ARCHIVO,'utf8'));
    return Array.isArray(s)?s.filter(x=>x&&ID.test(x.id)).slice(-150):[];
  }catch{return [];}
}
function guardar(entries) {
  try {
    fs.mkdirSync(BASE,{recursive:true,mode:0o700});
    const tmp=ARCHIVO+'.'+process.pid+'.'+crypto.randomBytes(4).toString('hex')+'.tmp';
    try{
      fs.writeFileSync(tmp,JSON.stringify(entries.slice(-150)),{mode:0o600,flag:'wx'});
      fs.renameSync(tmp,ARCHIVO); return true;
    }finally{try{fs.unlinkSync(tmp)}catch{}}
  }catch{return false}
}
export function registrarGap({modelo,code,convId=null}={}) {
  const clas=clasificarGap(code);
  const nombre=MODELO.test(String(modelo))?String(modelo):'swecode-consulta';
  const items=leer(),ahora=Date.now();
  const reciente=items.slice().reverse().find(x=>x.modelo===nombre&&x.codigo===clas.codigo&&
    ahora-x.creado<MINUTOS);
  if(reciente)return {...reciente,nuevo:false};
  const id='gap_'+crypto.randomBytes(12).toString('hex');
  // Nunca se escriben prompts, tokens, cuentas, URL ni salidas del modelo.
  const fila={id,modelo:nombre, ...clas,creado:ahora,
    // Hash corto para relacionar eventos, nunca recuperar el ID real de la sesión.
    sesion:convId?crypto.createHash('sha256').update(String(convId)).digest('hex').slice(0,12):null,
    intentos:0,investigado:false};
  items.push(fila);guardar(items);
  return {...fila,nuevo:true};
}
export function listarGaps({limite=25}={}){
  return leer().slice(-Math.max(1,Math.min(50,Number(limite)||25))).reverse();
}
export function gapPorId(id){
  return ID.test(String(id))?leer().find(x=>x.id===id)||null:null;
}
export async function investigarConOpenClaw(id,{fetchFn=fetch}={}){
  const fila=gapPorId(id);
  if(!fila)return {ok:false,code:'GAP_NO_ENCONTRADO'};
  if(fila.investigado)return {ok:true,code:'YA_INVESTIGADO',gap:fila};
  if(fila.estado.startsWith('🚩'))return {ok:false,code:'REQUIERE_OPERADOR',gap:fila};
  const items=leer(),ahora=Date.now();
  const n=items.filter(x=>x.investigado&&ahora-x.creado<86400000).length;
  if(n>=MAX_CONSULTAS_DIARIAS)return {ok:false,code:'LIMITE_DIAGNOSTICOS_DIARIOS'};
  if(process.env.OPENCLAW_ENABLE!=='1'||!process.env.OPENCLAW_GATEWAY_TOKEN)
    return {ok:false,code:'OPENCLAW_NO_DISPONIBLE',gap:fila};
  // Limitar referencias a datos controlados; sin URL externas ni mensajes de usuario.
  const texto=[
    'Eres SWEN REPAIR, agente técnico de diagnóstico (SOLO LECTURA).',
    'Investiga el GAP con tus herramientas de lectura y búsqueda web si están autorizadas.',
    'Nunca inicies sesión, resuelvas CAPTCHA/edad, cambies perfiles, credenciales o cuotas.',
    'No ejecutes shell/escrituras ni cambios a repositorio o servidor. No propongas evadir permisos.',
    'Responde con: 1) causa probable; 2) comprobación no destructiva;',
    '3) alternativa válida dentro de la arquitectura actual; 4) validación; 5) si requiere operador.',
    'No declares PASS sin una verificación real.',
    'GAP='+fila.codigo,'MODELO='+fila.modelo,
    'ESTADO='+fila.estado,'PISTA='+fila.accion
  ].join('\n');
  let respuesta;
  try {
    const r=await fetchFn('http://127.0.0.1:'+String(process.env.OPENCLAW_PORT||'18789')+'/openclaw/v1/chat/completions',{
      method:'POST',redirect:'error',signal:AbortSignal.timeout(70000),
      headers:{authorization:'Bearer '+process.env.OPENCLAW_GATEWAY_TOKEN,'content-type':'application/json'},
      body:JSON.stringify({model:agent,stream:false,user:'swen-repair-'+fila.id,
        messages:[{role:'user',content:texto}]})
    });
    if(!r.ok)return {ok:false,code:'OPENCLAW_DIAGNOSTICO_HTTP_'+r.status,gap:fila};
    const d=await r.json(), content=d?.choices?.[0]?.message?.content;
    if(typeof content!=='string'||!content.trim())return {ok:false,code:'OPENCLAW_SIN_DIAGNOSTICO'};
    respuesta=content.slice(0,3500);
  } catch {return {ok:false,code:'OPENCLAW_DIAGNOSTICO_NO_DISPONIBLE',gap:fila}}
  const actual=leer(),index=actual.findIndex(x=>x.id===id);
  if(index>=0){actual[index]={...actual[index],investigado:true,diagnostico:respuesta,investigado_en:Date.now()};guardar(actual)}
  return {ok:true,code:'DIAGNOSTICO_NO_ES_APROBACION',gap:gapPorId(id)};
}
