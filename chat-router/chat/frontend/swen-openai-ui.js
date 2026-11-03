// UI exclusiva de SWE CODE free: OpenAI API separada de ChatGPT.
// Facturable sólo con click explícito y opt-in del backend. Sin modelo local.
import { api } from './api.js';
const BASE='/plugins/deepseek_harness/modelos/v1/openai';
const style=document.createElement('style');
style.textContent='.swen-extras[hidden]{display:none!important}.swen-openai-salida{border:1px solid #484848;border-radius:10px;padding:10px;white-space:pre-wrap;overflow-wrap:anywhere}.swen-openai-salida img{max-width:100%;height:auto;border-radius:9px}.swen-openai-salida a{color:#83b7ff}';
document.head.append(style);
const pausa=ms=>new Promise(resolve=>setTimeout(resolve,ms));
const host=()=>document.querySelector('.swen-extras:not([hidden])');
function estado(h,m){const e=h?.querySelector('.swe-openai-estado');if(e)e.textContent=String(m||'');}
function tarjeta(h,titulo){
  const s=document.createElement('section');s.className='swen-openai-salida';
  const t=document.createElement('strong');t.textContent=titulo;s.append(t);h.append(s);return s;
}
function linea(h,contenido){
  const p=document.createElement('p');p.textContent=contenido;h.append(p);return p;
}
async function investigar(h,boton,id){
  if(!id){
    const prompt=String(document.querySelector('#message')?.value||'').trim();
    if(!prompt){estado(h,'Escribe la pregunta en el input.');return;}
    if(!window.confirm('Iniciar UNA investigacion via API OpenAI de pago, independiente de ChatGPT?'))return;
    const x=await api(BASE+'/research',{method:'POST',body:{prompt}});
    id=x.id;
    localStorage.setItem('riu_swen_investigacion_id',id);
  }
  if(!/^[0-9a-f]{32}$/.test(id))throw Error('ID_INVALIDO');
  const panel=tarjeta(h,'@ Investigacion profunda - '+id);
  const info=linea(panel,'Consultando estado...');
  for(let i=0;i<40;i++){
    if(i)await pausa(8000);
    const x=await api(BASE+'/research/'+id);
    info.textContent='Estado: '+String(x.estado||'desconocido')+'. ID: '+id;
    if(x.estado==='completed'){
      const p=document.createElement('pre');
      p.style.cssText='white-space:pre-wrap;overflow-wrap:anywhere';
      p.textContent=String(x.texto||'Sin informe visible');
      panel.append(p);
      for(const c of (Array.isArray(x.citas)?x.citas:[]).slice(0,30)){
        if(typeof c.url!=='string'||!c.url.startsWith('https://'))continue;
        const a=document.createElement('a');
        a.href=c.url;a.target='_blank';a.rel='noopener noreferrer';
        a.textContent=c.titulo||c.url;
        panel.append(a,document.createElement('br'));
      }
      estado(h,'Investigacion terminada.');return;
    }
    if(['failed','cancelled','incomplete'].includes(x.estado)){
      estado(h,'La investigacion no se completo: '+x.estado);return;
    }
  }
  estado(h,'Sigue en curso. Puedes consultar de nuevo con el mismo ID.');
}
async function mostrarImagen(h,id){
  if(!/^[0-9a-f]{32}$/.test(String(id||'')))throw Error('IMAGEN_ID_INVALIDO');
  const v=await api(BASE+'/image/'+id+'/data');
  if(!v.base64||v.mime!=='image/png')throw Error('IMAGEN_SIN_DATOS');
  const url='data:image/png;base64,'+v.base64;
  const panel=tarjeta(h,'Imagen OpenAI '+id.slice(0,12));
  const im=document.createElement('img');im.src=url;im.alt='Imagen generada con OpenAI';
  const a=document.createElement('a');a.href=url;a.download=v.nombre||'openai.png';
  a.textContent='Descargar PNG';panel.append(im,a);
  estado(h,'Imagen disponible para descargar PNG.');
}
async function generarImagen(h){
  const prompt=String(document.querySelector('#message')?.value||'').trim();
  if(!prompt){estado(h,'Escribe la descripcion de la imagen en el input.');return;}
  if(!window.confirm('Crear UNA imagen con API OpenAI (facturacion distinta de ChatGPT)?'))return;
  const x=await api(BASE+'/image',{method:'POST',body:{prompt}});
  if(!/^[0-9a-f]{32}$/.test(String(x.id||'')))throw Error('IMAGEN_ID_INVALIDO');
  localStorage.setItem('riu_swen_ultima_imagen_id',x.id);
  const input=h.querySelector('[data-swen-image-id]');if(input)input.value=x.id;
  return mostrarImagen(h,x.id);
}
document.addEventListener('click',async e=>{
  const b=e.target.closest?.('[data-swen-accion],[data-swen-investigacion-cargar],[data-swen-imagen-cargar]');
  if(!b||b.disabled)return;
  const h=host();if(!h)return;
  b.disabled=true;
  try{
    if(b.dataset.swenAccion==='research')await investigar(h,b,'');
    else if(b.dataset.swenAccion==='image')await generarImagen(h);
    else if(b.dataset.swenInvestigacionCargar){
      const id=String(h.querySelector('[data-swen-research-id]')?.value||'').trim();
      if(id)await investigar(h,b,id);
      else estado(h,'Escribe el ID guardado de la investigacion.');
    } else if(b.dataset.swenImagenCargar){
      const id=String(h.querySelector('[data-swen-image-id]')?.value||'').trim();
      if(id)await mostrarImagen(h,id);
      else estado(h,'Escribe el ID guardado de la imagen.');
    }
  }catch(error){estado(h,'GAP OpenAI: '+String(error?.message||error).slice(0,180));}
  finally{b.disabled=false;}
});
document.addEventListener('click',e=>{
  if(!e.target.closest?.('#sel-swen'))return;
  setTimeout(async()=>{
    const h=host();if(!h)return;
    try{
      const x=await api(BASE+'/estado');
      estado(h,x.habilitada?'OpenAI API habilitada (coste por uso).':
        'OpenAI API sin habilitar. Configura OPENAI_API_KEY y RIU_OPENAI_ACCIONES_ON=1 en el backend.');
    }catch(error){estado(h,'No se pudo verificar OpenAI API.');}
  },250);
});