// Vista A · Proyecto / Inicio. Nunca crea proyectos, ejecutores ni estados falsos.
(() => {
 'use strict';
 const el=id=>document.getElementById(id);
 const home=el('lp-home'),work=el('loop-workspace'),banner=el('loop-safety-banner');
 const tabHome=el('lp-tab-home'),tabWork=el('lp-tab-work'),go=el('go-run');
 if(!home||!work||!banner||!tabHome||!tabWork||!go)return;
 let verified=null;
 const output=el('lp-runtime');
 function message(t){output.textContent=String(t).slice(0,250);output.classList.remove('is-verified');}
 function switchView(name,focus){
   const start=name==='home';
   home.hidden=!start;work.hidden=start;banner.hidden=start;
   tabHome.classList.toggle('is-current',start);
   tabWork.classList.toggle('is-current',!start);
   tabHome.setAttribute('aria-selected',String(start));
   tabWork.setAttribute('aria-selected',String(!start));
   if(focus){const node=el(focus);if(node){node.scrollIntoView({block:'nearest',behavior:'smooth'});node.focus({preventScroll:true});}}
 }
 function isVerified(){
   return !!verified && !go.disabled &&
     verified.project_id===el('project-id')?.value.trim() &&
     verified.loop_id===el('loop-id')?.value.trim();
 }
 function repaint(){
   const ok=isVerified(),p=el('project-id')?.value.trim(),l=el('loop-id')?.value.trim();
   el('lp-project-name').textContent=ok?'Proyecto '+p:'Sin proyecto vinculado';
   el('lp-project-loop').textContent=ok?'LOOP '+l+' · backend confirmado':'Vincula project_id y loop_id reales';
   const state=el('lp-state');state.textContent=ok?'● Vinculado':'◌ Sin verificar';state.classList.toggle('is-verified',ok);
   el('lp-start').disabled=!ok;el('lp-checkpoint').disabled=!ok;
   if(ok){output.textContent='LOOP verificado por el backend. Los controles ejecutan acciones reales.';output.classList.add('is-verified');}
   else{output.textContent='Sin proyecto verificado: no se enviará ninguna orden al motor.';output.classList.remove('is-verified');}
 }
 async function anchor(kind){
   const a=window.YAIWES_PANEL;
   if(!a?.openAnchor){message('Puente de anclaje no disponible');return;}
   try{await a.openAnchor(kind);}
   catch(e){message('Anclaje no disponible: '+String(e.message||e));}
 }
 tabHome.addEventListener('click',()=>switchView('home'));
 tabWork.addEventListener('click',()=>switchView('work'));
 el('lp-config-project').addEventListener('click',()=>switchView('work','project-id'));
 el('lp-setup').addEventListener('click',()=>switchView('work','project-id'));
 el('lp-verify').addEventListener('click',()=>switchView('work','project-id'));
 el('lp-open-anchor').addEventListener('click',()=>anchor('general'));
 el('lp-open-handoff').addEventListener('click',()=>anchor('handoff'));
 el('lp-open-files').addEventListener('click',()=>anchor('files'));
 el('lp-open-notes').addEventListener('click',()=>anchor('notes'));
 el('lp-constitution').addEventListener('click',()=>anchor('constitution'));
 el('lp-context').addEventListener('click',()=>anchor('general'));
 el('lp-plan').addEventListener('click',()=>switchView('work','categories'));
 el('lp-pending').addEventListener('click',()=>switchView('work','show-filter'));
 el('lp-start').addEventListener('click',()=>{
   if(!isVerified()){message('Verifica el proyecto y el LOOP antes de iniciar');repaint();return;}
   go.click(); // reutiliza el único handler con validación backend
 });
 el('lp-checkpoint').addEventListener('click',()=>{
   if(!isVerified()){message('Checkpoint no disponible sin backend confirmado');return;}
   switchView('work');
   el('load-checkpoint')?.click();
   el('events')?.scrollIntoView({block:'nearest',behavior:'smooth'});
 });
 window.addEventListener('yaiwes:loop-verified',e=>{
   const v=e.detail;
   if(!v||!v.project_id||!v.loop_id)return;
   verified={project_id:v.project_id,loop_id:v.loop_id};
   repaint();
 });
 window.addEventListener('yaiwes:loop-unverified',()=>{verified=null;repaint();});
 for(const name of ['project-id','loop-id'])el(name)?.addEventListener('input',repaint);
 new MutationObserver(repaint).observe(go,{attributes:true,attributeFilter:['disabled']});
 switchView('home');repaint();
})();
