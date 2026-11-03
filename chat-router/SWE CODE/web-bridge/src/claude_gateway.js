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
    // Control UI basePath es sólo para la interfaz gráfica.
    // /openclaw/v1/models devuelve HTML; la API real está en /v1/models.
    url=x.origin+(x.pathname==='/' ? '' :
      (x.pathname.endsWith('/') ? x.pathname.slice(0,-1) : x.pathname));
  }catch{return null;}
  return token?{url,token}:null;
}
function classify(http){
  // 401/403 suelen corresponder al token del propio Gateway, NO a cuota de Anthropic.
  if(http===401||http===403)return issue('CLAUDE_GATEWAY_NO_AUTORIZADO',http);
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
      headers:{authorization:'Bearer '+c.token,accept:'application/json, text/html;q=0'},
      signal:ctl,redirect:'error'});
    if(!r.ok)return {ok:false,disponible:false,modelo:MODEL,
      reason:r.status===401||r.status===403?'CLAUDE_GATEWAY_NO_AUTORIZADO':
        r.status===404?'CLAUDE_GATEWAY_MODELOS_NO_HABILITADOS':
        'CLAUDE_GATEWAY_NO_DISPONIBLE',http:r.status,thinking:'max'};
    const x=await r.json(), agentes=Array.isArray(x.data)?x.data.map(t=>t.id):[];
    const instalado=agentes.includes(AGENT);
    return {ok:instalado,disponible:instalado,modelo:MODEL,
      reason:instalado?'PENDIENTE_PROBAR_INFERENCIA':'CLAUDE_AGENTE_NO_INSTALADO',
      thinking:'max',agente:AGENT,rotacion:'perfiles Anthropic de OpenClaw'};
  }catch{return {ok:false,disponible:false,modelo:MODEL,reason:'CLAUDE_GATEWAY_NO_CONECTADO',thinking:'max'}}
}
// Ordinary user+text; caller-provided task text is data, no tool authority.
// The dedicated OpenClaw agent has a minimal tool profile.
export async function consultarClaude(texto,{convId='',fetchFn=fetch,timeoutMs=300000}={}){
  const c=cfg();
  if(!c)throw issue('CLAUDE_GATEWAY_NO_CONFIGURADO');
  const key=ID.test(String(convId))?String(convId):'consulta';
  const ctl=AbortSignal.timeout(Math.max(20000,Math.min(timeoutMs,300000)));
  let r;
  try{
    r=await fetchFn(c.url+'/v1/chat/completions',{method:'POST',signal:ctl,redirect:'error',
      headers:{authorization:'Bearer '+c.token,'content-type':'application/json',
        'x-openclaw-model':MODEL},
      body:JSON.stringify({model:AGENT,user:'swen-sonnet-'+key,stream:false,
        messages:[{role:'user',content:'/think:max\n'+String(texto).slice(0,100000)}]})});
  }catch(e){throw issue(e?.name==='TimeoutError'||e?.name==='AbortError'?
    'CLAUDE_GATEWAY_TIMEOUT':'CLAUDE_GATEWAY_NO_CONECTADO')}
  if(!r.ok){
    // 401 puede venir del proveedor Anthropic (missing-provider-auth) AUN
    // cuando el token del Gateway es válido. No atribuirlo falsamente a la API.
    if(r.status===401){
      const raw=String(await r.text().catch(()=>'')).slice(0,8000);
      let er={};try{er=JSON.parse(raw)?.error||{}}catch{}
      const code=String(er?.code||'').toLowerCase();
      const tipo=String(er?.type||'').toLowerCase();
      if(code==='missing-provider-auth' ||
         (tipo==='authentication_error' && code.includes('provider')))
        throw issue('CLAUDE_PROVEEDOR_SIN_CREDENCIALES',401);
      throw issue('CLAUDE_GATEWAY_NO_AUTORIZADO',401);
    }
    // Categorizar HTTP 400 sin propagar el cuerpo: puede contener detalles de
    // perfiles/credenciales. Sólo códigos prefijados conocidos.
    if(r.status===400){
      const raw=String(await r.text().catch(()=>'')).slice(0,9000);
      let body={};try{body=JSON.parse(raw)}catch{}
      const error=body?.error||{};
      const msg=String(error?.message||'').toLowerCase();
      const code=String(error?.code||'').toLowerCase();
      const joined=code+' '+msg;
      if(/model.*(?:not allowed|allowlist|not in|unknown|unavailable|invalid)|model_not_allowed/.test(joined))
        throw issue('CLAUDE_MODELO_NO_AUTORIZADO_GATEWAY',400);
      if(/agent.*(?:unknown|not found|not allowed|invalid)|unknown.agent/.test(joined))
        throw issue('CLAUDE_AGENTE_NO_INSTALADO',400);
      if(/(?:auth|credential|profile|login|token).*(?:missing|unavailable|required|invalid)/.test(joined))
        throw issue('CLAUDE_CREDENCIALES_NO_DISPONIBLES',400);
      if(/thinking|effort/.test(joined))
        throw issue('CLAUDE_RAZONAMIENTO_NO_ADMITIDO',400);
      if(/session|user/.test(joined))
        throw issue('CLAUDE_SESION_INVALIDA',400);
      throw issue('CLAUDE_PETICION_NO_ACEPTADA',400);
    }
    // OpenClaw puede devolver 500 para "all auth profiles in cooldown".
    // Sólo se inspecciona para clasificar, nunca se muestra ni registra el cuerpo
    // que puede contener datos de una cuenta.
    if(r.status===500||r.status===503){
      const errorBody=String(await r.text().catch(()=>'')).slice(0,8000);
      if(/no available auth profile|all (?:auth )?profiles|all profiles.*(?:cooldown|unusable)|(?:billing|insufficient.?credit|quota).*(?:exhaust|limit|exceed)|(?:auth|provider).*(?:quota|cooldown)/i.test(errorBody))
        throw issue('CLAUDE_CUENTAS_AGOTADAS',429);
    }
    throw classify(r.status);
  }
  const raw=await r.text();
  if(raw.length>500000)throw issue('CLAUDE_RESPUESTA_GRANDE',502);
  let x;
  try{x=JSON.parse(raw)}catch{throw issue('CLAUDE_RESPUESTA_INVALIDA',502)}
  if(x.error)throw issue('CLAUDE_GATEWAY_ERROR',502);
  const m=x?.choices?.[0]?.message;
  if(!m||!String(m.content||'').trim())throw issue('CLAUDE_RESPUESTA_VACIA',502);
  if((x.modelo_usado||x.model)&&String(x.modelo_usado||x.model).includes('opus'))
    throw issue('CLAUDE_MODELO_NO_PERMITIDO',502);
  return {texto:String(m.content).slice(0,100000),
    modelo:MODEL,thinking:'max',origen:'openclaw',perfil:'gestionado_por_gateway'};
}
export function esCuotaClaude(code){
  return ['CLAUDE_CUENTAS_AGOTADAS'].includes(String(code||''));
}
export const CLAUDE_MODEL = MODEL;
