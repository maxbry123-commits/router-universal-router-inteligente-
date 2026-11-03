// OpenAI @Investigación profunda / imágenes para SWEN y OpenClaw.
// SOLO vía API propia con autorización del operador en el entorno:
// OPENAI_API_KEY + RIU_OPENAI_ACCIONES_ON=1. La suscripción ChatGPT no es la API.
// Respuestas asíncronas con checkpoint del bridge; consultar NO genera otra inferencia.
// Imagen almacena bytes en BRIDGE_STATE_DIR y se descarga desde endpoint autenticado.
import fs from 'node:fs';
import path from 'node:path';
import crypto from 'node:crypto';
import { estadoDir } from './bloques.js';

const BASE='https://api.openai.com/v1/';
const ID=/^[0-9a-f]{32}$/;
const CLAVE=()=>String(process.env.OPENAI_API_KEY||'').trim();
const ACTIVADO=()=>Boolean(CLAVE() && process.env.RIU_OPENAI_ACCIONES_ON==='1');
const DIR=()=>path.join(estadoDir(),'openai_api');
const JSONLIM=120000;
const MAX_IMAGEN_BYTES=8*1024*1024;
const ERROR=(code,status=400)=>Object.assign(new Error(code),{codigo:code,http:status});
function guardarJson(id,contenido){
  const base=DIR();fs.mkdirSync(base,{recursive:true,mode:0o700});
  const target=path.join(base,id+'.json');
  const tmp=target+'.'+process.pid+'.'+crypto.randomBytes(4).toString('hex')+'.tmp';
  try{fs.writeFileSync(tmp,JSON.stringify(contenido),{encoding:'utf8',mode:0o600,flag:'wx'});fs.renameSync(tmp,target);}
  finally{try{fs.unlinkSync(tmp);}catch{}}
}
function leer(id,propietario){
  if(!ID.test(id)||!propietario)return null;
  try{const o=JSON.parse(fs.readFileSync(path.join(DIR(),id+'.json'),'utf8'));
    return o.propietario===propietario?o:null;}catch{return null}
}
function guardarBytes(id,buffer){
  fs.mkdirSync(DIR(),{recursive:true,mode:0o700});
  const ruta=path.join(DIR(),id+'.png'),tmp=ruta+'.'+process.pid+'.tmp';
  try{fs.writeFileSync(tmp,buffer,{mode:0o600,flag:'wx'});fs.renameSync(tmp,ruta);}
  finally{try{fs.unlinkSync(tmp);}catch{}}
}
async function llamar(uri,{metodo='GET',body,ms=90000}={}){
  if(!ACTIVADO())throw ERROR('OPENAI_API_NO_CONFIGURADA',503);
  const ac=new AbortController(),timer=setTimeout(()=>ac.abort(),ms);
  try{
    const r=await fetch(BASE+uri,{method:metodo,headers:{
      'Authorization':'Bearer '+CLAVE(),'Content-Type':'application/json'
    },...(body?{body:JSON.stringify(body)}:{}),signal:ac.signal,redirect:'error'});
    if(!r.ok)throw ERROR('OPENAI_HTTP_'+r.status,r.status===429?429:502);
    const t=await r.text();
    if(t.length>14*1024*1024)throw ERROR('OPENAI_RESPUESTA_GRANDE',502);
    let j;try{j=JSON.parse(t)}catch{throw ERROR('OPENAI_RESPUESTA_INVALIDA',502)}
    return j;
  }catch(e){if(e?.name==='AbortError')throw ERROR('OPENAI_TIMEOUT',504);throw e}
  finally{clearTimeout(timer)}
}
function salidaResearch(j){
  const chunks=[],citas=[];
  for(const v of Array.isArray(j.output)?j.output:[]){
    if(v?.type!=='message'||!Array.isArray(v.content))continue;
    for(const c of v.content){
      if(c.type==='output_text'&&typeof c.text==='string')chunks.push(c.text);
      for(const a of Array.isArray(c.annotations)?c.annotations:[]){
        if(a?.type==='url_citation'&&typeof a.url==='string'&&/^https:\/\//.test(a.url))
          citas.push({titulo:String(a.title||'').slice(0,150),url:a.url.slice(0,1800)});
      }
    }
  }
  return {texto:chunks.join('\n\n').slice(0,JSONLIM),citas:citas.slice(0,70)};
}
const responderError=(res,e)=>{
  const code=typeof e.codigo==='string'?e.codigo:'OPENAI_FALLO';
  return res.status(e.http||502).json({ok:false,error:{code}});
};
export function montarAccionesOpenAI(app,propietarioDe){
  app.get('/v1/openai/estado',(_req,res)=>res.json({ok:true,
    configurada:!!CLAVE(),habilitada:ACTIVADO(),
    requiere:'OPENAI_API_KEY y RIU_OPENAI_ACCIONES_ON=1',facturacion:'API OpenAI separada de ChatGPT',
    modelos:{imagen:'gpt-image-2.5-flare',investigacion:'gpt-5.6-sol'}}));
  app.post('/v1/openai/research',async(req,res)=>{
    const prompt=req.body?.prompt;
    if(typeof prompt!=='string'||!prompt.trim()||prompt.length>12000)
      return res.status(400).json({ok:false,error:{code:'PROMPT_INVALIDO'}});
    if(!ACTIVADO())return responderError(res,ERROR('OPENAI_API_NO_CONFIGURADA',503));
    const owner=propietarioDe(req);
    if(!owner)return responderError(res,ERROR('NO_AUTORIZADO',401));
    try{
      // Crear UNA solicitud de investigación; consultas posteriores son GET, no otra llamada de inferencia.
      const r=await llamar('responses',{metodo:'POST',ms:90000,
        body:{model:'gpt-5.6-sol',background:true,input:prompt.trim(),
          tools:[{type:'web_search'}]}});
      if(!/^resp_[a-zA-Z0-9_-]{8,160}$/.test(String(r.id||'')))throw ERROR('OPENAI_RESEARCH_ID_INVALIDO',502);
      const id=crypto.randomBytes(16).toString('hex');
      const tarea={id,propietario:owner,remote_id:r.id,tipo:'investigacion',prompt:prompt.trim().slice(0,1000),
        status:r.status||'queued',fecha:new Date().toISOString(),resultado:null};
      if(r.status==='completed')tarea.resultado=salidaResearch(r);
      guardarJson(id,tarea);
      return res.json({ok:true,id,estado:tarea.status,...(tarea.resultado||{})});
    }catch(e){return responderError(res,e)}
  });
  app.get('/v1/openai/research/:id',async(req,res)=>{
    const t=leer(req.params.id,propietarioDe(req));
    if(!t||t.tipo!=='investigacion')return res.status(404).json({ok:false,error:{code:'INVESTIGACION_NO_ENCONTRADA'}});
    if(['completed','failed','cancelled','incomplete'].includes(t.status))
      return res.json({ok:true,id:t.id,estado:t.status,...(t.resultado||{})});
    if(!ACTIVADO())return responderError(res,ERROR('OPENAI_API_NO_CONFIGURADA',503));
    try{
      const r=await llamar('responses/'+encodeURIComponent(t.remote_id),{ms:30000});
      t.status=r.status||t.status;
      if(t.status==='completed')t.resultado=salidaResearch(r);
      guardarJson(t.id,t);
      return res.json({ok:true,id:t.id,estado:t.status,...(t.resultado||{})});
    }catch(e){return responderError(res,e)}
  });
  app.post('/v1/openai/image',async(req,res)=>{
    const prompt=req.body?.prompt;
    if(typeof prompt!=='string'||!prompt.trim()||prompt.length>8000)
      return res.status(400).json({ok:false,error:{code:'PROMPT_INVALIDO'}});
    if(!ACTIVADO())return responderError(res,ERROR('OPENAI_API_NO_CONFIGURADA',503));
    const owner=propietarioDe(req);
    if(!owner)return responderError(res,ERROR('NO_AUTORIZADO',401));
    try{
      const r=await llamar('images/generations',{metodo:'POST',ms:160000,
        body:{model:'gpt-image-2.5-flare',prompt:prompt.trim(),size:'1024x1024',quality:'medium',n:1}});
      const b64=r.data?.[0]?.b64_json;
      if(typeof b64!=='string'||b64.length>MAX_IMAGEN_BYTES*1.4||!/^[-A-Za-z0-9+/=]+$/.test(b64))
        throw ERROR('OPENAI_IMAGEN_INVALIDA',502);
      const img=Buffer.from(b64,'base64');
      if(img.length>MAX_IMAGEN_BYTES||img.length<100||!img.subarray(0,8).equals(Buffer.from([137,80,78,71,13,10,26,10])))
        throw ERROR('OPENAI_IMAGEN_INVALIDA',502);
      const id=crypto.randomBytes(16).toString('hex');
      guardarBytes(id,img);
      guardarJson(id,{id,propietario:owner,tipo:'imagen',mime:'image/png',bytes:img.length,
        prompt:prompt.trim().slice(0,2000),fecha:new Date().toISOString()});
      return res.json({ok:true,id,mime:'image/png',bytes:img.length,descarga:'/v1/openai/image/'+id});
    }catch(e){return responderError(res,e)}
  });
  app.get('/v1/openai/image/:id/data',(req,res)=>{
    const t=leer(req.params.id,propietarioDe(req));
    if(!t||t.tipo!=='imagen')return res.status(404).json({ok:false,error:{code:'IMAGEN_NO_ENCONTRADA'}});
    try{
      const bytes=fs.readFileSync(path.join(DIR(),t.id+'.png'));
      if(bytes.length>MAX_IMAGEN_BYTES)throw ERROR('IMAGEN_INVALIDA',500);
      return res.json({ok:true,id:t.id,mime:'image/png',nombre:'openai-'+t.id.slice(0,10)+'.png',
        base64:bytes.toString('base64')});
    }catch(e){return responderError(res,e)}
  });
  app.get('/v1/openai/image/:id',(req,res)=>{
    const t=leer(req.params.id,propietarioDe(req));
    if(!t||t.tipo!=='imagen')return res.status(404).json({ok:false,error:{code:'IMAGEN_NO_ENCONTRADA'}});
    try{
      const bytes=fs.readFileSync(path.join(DIR(),t.id+'.png'));
      if(bytes.length>MAX_IMAGEN_BYTES)throw ERROR('IMAGEN_INVALIDA',500);
      res.setHeader('content-type','image/png');
      res.setHeader('content-disposition','attachment; filename="openai-'+t.id.slice(0,10)+'.png"');
      res.setHeader('cache-control','private, no-store');
      return res.send(bytes);
    }catch(e){return responderError(res,e)}
  });
}