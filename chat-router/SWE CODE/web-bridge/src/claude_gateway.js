// Claude Sonnet via the EXISTING OpenClaw Gateway (not browser automation).
// OpenClaw owns authenticated Anthropic profile rotation, cooldown and retry.
// Strictly pin Sonnet; never silently fallback to another model. No credentials stored here.
const MODEL = 'anthropic/claude-sonnet-5-5';
const AGENT = 'openclaw/swen-council';
const ID = /^[A-Za-z0-9_-]{1,80}$/;
const clean = v => String(v || '').slice(0,2500);
const issue = (code, http=503) => Object.assign(new Error(code),{code,http});
function cfg(){
  const token=String(process.env.OPENCLAW_GATEWAY_TOKEN||'').trim();
  const base=String(process.env.RIU_OPENCLAW_URL||'http://127.0.0.1:18789').trim().replace(/\/+$/,'');
  let url;
  try{
    const x=new URL(base);
    if(x.username||x.password||!((x.protocol==='https:' && x.hostname)
      ||(x.protocol==='http:' && ['localhost','127.0.0.1','::1'].includes(x.hostname))))return null;
    url=base;
  }catch{return null;}
  return token?{url,token}:null;
}
function classify(http){
  if(http===401||http===403)return issue('CLAUDE_CUENTA_NO_AUTORIZADA',http);
  if(http===402||http===429)return issue('CLAUDE_CUENTAS_AGOTADAS',http);
  if(http===404)return issue('CLAUDE_AGENTE_NO_INSTALADO',http);
  if(http===408||http>=500)return issue('CLAUDE_GATEWAY_TEMPORAL',http);
  return issue('CLAUDE_GATEWAY_HTTP_'+http,http);
}
// Metadata, NOT a claim of credentials or quota. Safe to expose without email.
export async function estadoClaude({fetchFn=fetch}={}){
  const c=cfg();
  if(!c)return {ok:false,disponible:false,modelo:MODEL,reason:'CLAUDE_GATEWAY_NO_CONFIGURADO',thinking:'max'};
  try {
    const ctl=AbortSignal.timeout(6500);
    const r=await fetchFn(c.url+'/v1/models',{method:'GET',
      headers:{authorization:'Bearer '+c.token},signal:ctl,redirect:'error'});
    if(!r.ok)return {ok:false,disponible:false,modelo:MODEL,
      reason:r.status===401||r.status===403?'CLAUDE_GATEWAY_NO_AUTORIZADO':'CLAUDE_GATEWAY_NO_DISPONIBLE',thinking:'max'};
    const x=await r.json(), agentes=Array.isArray(x.data)?x.data.map(t=>t.id):[];
    const instalado=agentes.includes(AGENT);
    return {ok:instalado,disponible:instalado,modelo:MODEL,
      reason:instalado?'PENDIENTE_PROBAR_INFERENCIA':'CLAUDE_AGENTE_NO_INSTALADO',
      thinking:'max',agente:AGENT,rotacion:'perfiles Anthropic de OpenClaw'};
  }catch{return {ok:false,disponible:false,modelo:MODEL,reason:'CLAUDE_GATEWAY_NO_CONECTADO',thinking:'max'}}
}
// Ordinary user+text; caller-provided task text is data, no tool authority.
// The dedicated OpenClaw agent has a minimal tool profile.
export async function consultarClaude(texto,{convId='',fetchFn=fetch,timeoutMs=180000}={}){
  const c=cfg();
  if(!c)throw issue('CLAUDE_GATEWAY_NO_CONFIGURADO');
  const key=ID.test(String(convId))?String(convId):'consulta';
  const ctl=AbortSignal.timeout(Math.max(20000,Math.min(timeoutMs,180000)));
  let r;
  try{
    r=await fetchFn(c.url+'/v1/chat/completions',{method:'POST',signal:ctl,redirect:'error',
      headers:{authorization:'Bearer '+c.token,'content-type':'application/json',
        'x-openclaw-model':MODEL},
      body:JSON.stringify({model:AGENT,user:'swen-sonnet-'+key,stream:false,
        messages:[{role:'user',content:'/think:max\n'+String(texto).slice(0,100000)}]})});
  }catch(e){throw issue(e?.name==='TimeoutError'||e?.name==='AbortError'?
    'CLAUDE_GATEWAY_TIMEOUT':'CLAUDE_GATEWAY_NO_CONECTADO')}
  if(!r.ok)throw classify(r.status);
  const raw=await r.text();
  if(raw.length>500000)throw issue('CLAUDE_RESPUESTA_GRANDE',502);
  let x;
  try{x=JSON.parse(raw)}catch{throw issue('CLAUDE_RESPUESTA_INVALIDA',502)}
  if(x.error)throw issue('CLAUDE_GATEWAY_ERROR',502);
  const m=x?.choices?.[0]?.message;
  if(!m||!String(m.content||'').trim())throw issue('CLAUDE_RESPUESTA_VACIA',502);
  if((x.modelo_usado||x.model)&&String(x.modelo_usado||x.model).includes('opus'))
    throw issue('CLAUDE_MODELO_NO_PERMITIDO',502);
  return {texto:clean(m.content).length===String(m.content).length ? String(m.content):String(m.content).slice(0,100000),
    modelo:MODEL,thinking:'max',origen:'openclaw',perfil:'gestionado_por_gateway'};
}
export function esCuotaClaude(code){
  return ['CLAUDE_CUENTAS_AGOTADAS','CLAUDE_CUENTA_NO_AUTORIZADA'].includes(String(code||''));
}
export const CLAUDE_MODEL = MODEL;
