#!/usr/bin/env python3
"""patch_2f_chat.py — MINIMAX 2F: el chat con agentes ON/OFF, formato NCT/APEX,
artefactos y cuadros.

Ventanas nuevas en `chat-router/chat/index.html`:
  4 · AGENTES     -> interruptor ON/OFF por agente + estado de las 3 raices
  5 · INPUT (📌)  -> parse del bloque 📌 (clasificador + F1/F2) + render F3/F4
  6 · ARTEFACTOS  -> crear/leer md, py, html y otros
  7 · CUADROS     -> cuadros de estado (agentes, modos, raices, memoria)
Ademas: botonera NCT/APEX (9 botones + HANDOFF) al final del chat.

Fail-closed: cada ancla debe aparecer UNA vez; si no, el script no escribe.
"""
from __future__ import annotations

import sys
from pathlib import Path

CHAT = Path(__file__).resolve().parent.parent / "chat-router" / "chat" / "index.html"

OLD_NAV = '''        <button type="button" class="nav-btn" data-view="motores"><span class="n">3</span>Motores</button>
'''

NEW_NAV = '''        <button type="button" class="nav-btn" data-view="motores"><span class="n">3</span>Motores</button>
        <button type="button" class="nav-btn" data-view="agentes"><span class="n">4</span>Agentes</button>
        <button type="button" class="nav-btn" data-view="input"><span class="n">5</span>Input</button>
        <button type="button" class="nav-btn" data-view="artefactos"><span class="n">6</span>Artefactos</button>
        <button type="button" class="nav-btn" data-view="cuadros"><span class="n">7</span>Cuadros</button>
'''

OLD_SECTIONS_END = '''    </section>
  </main>
'''

NEW_SECTIONS = '''    </section>

    <!-- VENTANA 4 · AGENTES (interruptor ON/OFF + raices con auto-pull) -->
    <section class="view" id="v-agentes">
      <div class="card">
        <h2>Agentes</h2>
        <p>Registro central con interruptor real: un agente apagado no enruta (el proxy responde 409).</p>
        <div class="list" id="agent-list"></div>
        <div class="row" style="margin-top:10px">
          <button type="button" class="btn" id="agent-refresh-btn">Actualizar</button>
          <span class="badge" id="agent-badge">sin consultar</span>
        </div>
        <div class="note"><b>ON/OFF.</b> El estado se guarda en <code>state/agents/&lt;agente&gt;/state.json</code> del servidor, no en el navegador. Cada agente tiene su historial (<code>history.jsonl</code>) y su memoria (<code>memory.json</code>).</div>
      </div>
      <div class="card">
        <h2>Raices del workspace</h2>
        <p>Las 3 raices reales (<code>ruflo</code>, <code>rowboat</code>, <code>donors</code>) con su estado de integridad y su auto-pull.</p>
        <div class="list" id="root-list"></div>
        <div class="row" style="margin-top:10px">
          <button type="button" class="btn" id="root-pull-btn">Auto-pull (informe)</button>
          <span class="badge" id="root-badge">sin consultar</span>
        </div>
        <div class="note"><b>Auto-pull.</b> El boton pide un INFORME (nunca escribe). Para aplicar de verdad hace falta <code>apply:true</code> en <code>/v1/roots/pull</code>.</div>
      </div>
    </section>

    <!-- VENTANA 5 · INPUT (bloque 📌 + formatos NCT/APEX) -->
    <section class="view" id="v-input">
      <div class="card">
        <h2>Input 📌 · NCT/APEX</h2>
        <p>Pega el bloque 📌 literal (F1 corto o F2 largo). El sistema lo clasifica y devuelve los campos y el plan.</p>
        <textarea class="area" id="nct-input" placeholder="🟢 F1 — INPUT CORTO&#10;&#10;**Objetivo:** ..."></textarea>
        <div class="row" style="margin-top:10px">
          <button type="button" class="btn primary" id="nct-parse-btn">Analizar input</button>
          <button type="button" class="btn" id="nct-f3-btn">Render F3</button>
          <button type="button" class="btn" id="nct-f4-btn">Render F4</button>
          <span class="badge" id="nct-badge">idle</span>
        </div>
        <div class="msg" id="nct-preview" style="margin-top:10px"></div>
      </div>
      <div class="card">
        <h2>Salida normalizada</h2>
        <p>El handoff JSON y la bitacora son internos: aqui solo se ve F3 o F4.</p>
        <div class="msg" id="nct-out"></div>
      </div>
    </section>

    <!-- VENTANA 6 · ARTEFACTOS -->
    <section class="view" id="v-artefactos">
      <div class="card">
        <h2>Crear artefacto</h2>
        <div class="row">
          <input class="key-input" id="art-name" type="text" placeholder="nombre (ej. informe.md)">
          <select class="model-selector" id="art-kind">
            <option value="md">md</option><option value="py">py</option><option value="html">html</option>
            <option value="json">json</option><option value="txt">txt</option><option value="csv">csv</option>
            <option value="yaml">yaml</option><option value="sh">sh</option>
          </select>
        </div>
        <textarea class="area" id="art-content" placeholder="contenido del artefacto" style="margin-top:10px"></textarea>
        <div class="row" style="margin-top:10px">
          <button type="button" class="btn primary" id="art-create-btn">Crear</button>
          <button type="button" class="btn" id="art-refresh-btn">Listar</button>
          <span class="badge" id="art-badge">idle</span>
        </div>
      </div>
      <div class="card">
        <h2>Artefactos</h2>
        <div class="list" id="art-list"></div>
        <div class="msg" id="art-view" style="margin-top:10px"></div>
      </div>
    </section>

    <!-- VENTANA 7 · CUADROS -->
    <section class="view" id="v-cuadros">
      <div class="card">
        <h2>Cuadros</h2>
        <p>Cada cuadro consulta su endpoint real: nada se inventa.</p>
        <div class="row" style="margin-top:10px">
          <button type="button" class="btn" id="cuadros-btn">Actualizar cuadros</button>
          <span class="badge" id="cuadros-badge">sin consultar</span>
        </div>
      </div>
      <div class="card"><h2>Agentes</h2><div class="list" id="cuadro-agentes"></div></div>
      <div class="card"><h2>Modos</h2><div class="list" id="cuadro-modos"></div></div>
      <div class="card"><h2>Raices</h2><div class="list" id="cuadro-raices"></div></div>
      <div class="card"><h2>Memoria por agente</h2><div class="list" id="cuadro-memoria"></div></div>
    </section>
  </main>
'''

OLD_TITLES = """var TITLES={chat:'Chat',paneles:'Paneles',motores:'Motores'};
var SUBS={chat:'Selector de motores + API Key',paneles:'Una ventana por panel',motores:'Estado real de cada Space'};"""

NEW_TITLES = """var TITLES={chat:'Chat',paneles:'Paneles',motores:'Motores',agentes:'Agentes',input:'Input',artefactos:'Artefactos',cuadros:'Cuadros'};
var SUBS={chat:'Selector de motores + API Key',paneles:'Una ventana por panel',motores:'Estado real de cada Space',agentes:'ON/OFF + raices',input:'Bloque 📌 + F1/F2/F3/F4',artefactos:'Crear md, py, html y otros',cuadros:'Estado real por cuadro'};"""

OLD_SEND_ROW = '''        <div class="row" style="margin-top:10px">
          <button type="button" class="btn primary" id="send-btn">Enviar</button>
          <button type="button" class="btn ghost" id="clear-btn">Limpiar</button>
          <span class="badge" id="conn">idle</span>
        </div>
'''

NEW_SEND_ROW = '''        <div class="row" style="margin-top:10px">
          <button type="button" class="btn primary" id="send-btn">Enviar</button>
          <button type="button" class="btn ghost" id="clear-btn">Limpiar</button>
          <span class="badge" id="conn">idle</span>
        </div>
        <div class="row" id="botonera" style="margin-top:10px"></div>
'''

OLD_START = """  paintMessages();paintPaneles();paintMotores();render();
});
})();"""

NEW_START = """  paintMessages();paintPaneles();paintMotores();paintBotonera();paintAgentes();render();
});
})();"""

NEW_JS = r'''
/* ==========================================================================
   MINIMAX 2F · AGENTES (ON/OFF), INPUT 📌 (NCT/APEX), ARTEFACTOS, CUADROS
   ========================================================================== */
var AGENTS=[];           // registro vivo
var BOTONERA_DEF=[
  {id:'audit_xray',label:'🔍 AUDIT X-RAY',approval:false},
  {id:'input_shark',label:'🦈 INPUT SHARK',approval:false},
  {id:'mapa_mental',label:'🧠 MAPA MENTAL',approval:false},
  {id:'analisis',label:'📊 ANALISIS',approval:false},
  {id:'propuesta',label:'💡 PROPUESTA',approval:false},
  {id:'refactorizar',label:'🛠️ REFACTORIZAR',approval:true},
  {id:'modo_agentico',label:'🤖 MODO AGENTICO',approval:true},
  {id:'validar',label:'✅ VALIDAR',approval:false},
  {id:'recovery',label:'♻️ RECOVERY',approval:false},
  {id:'handoff',label:'🔒 HANDOFF',approval:false}
];
var ACTIVE_BTN=[];

function api(path){
  /* Mismo origen: el proxy sirve el chat y las rutas. Con ?api= se puede
     apuntar a otro host. Sin destino NO se llama a la red (anti-ruido). */
  var base=(new URLSearchParams(location.search).get('api')||'').replace(/\/$/,'');
  if(!base && location.protocol==='file:')return '';
  return base+path;
}
function apiJSON(path,opts){
  var u=api(path);
  if(!u)return Promise.reject(new Error('sin destino'));
  var h=Object.assign({'Content-Type':'application/json'},opts&&opts.headers||{});
  if(S.key)h['x-api-key']=S.key;
  return fetch(u,Object.assign({},opts,{headers:h})).then(function(r){
    return r.json().catch(function(){return{};}).then(function(j){
      if(!r.ok){var e=new Error((j&&(j.detail||j.error))||('HTTP '+r.status));e.status=r.status;throw e;}
      return j;
    });
  });
}
function badge(id,text,cls){var b=el(id);if(!b)return;b.textContent=text;b.className='badge '+(cls||'warning');}
function bubbleHTML(text){
  return '<div class="msg-row"><span class="who">sistema</span><div class="bubble"></div></div>';
}

/* ---------- BOTONERA ---------- */
function paintBotonera(){
  var box=el('botonera');if(!box)return;
  box.innerHTML=BOTONERA_DEF.map(function(b){
    var on=ACTIVE_BTN.indexOf(b.id)>=0;
    return '<button type="button" class="btn '+(on?'primary':'ghost')+'" data-btn="'+b.id+'" aria-pressed="'+(on?'true':'false')+'">'+b.label+'</button>';
  }).join('');
  box.querySelectorAll('[data-btn]').forEach(function(btn){
    btn.onclick=function(){boton(btn.getAttribute('data-btn'));};
  });
}
function boton(id){
  var def=null;for(var i=0;i<BOTONERA_DEF.length;i++){if(BOTONERA_DEF[i].id===id)def=BOTONERA_DEF[i];}
  if(!def)return;
  if(def.approval){
    if(!window.confirm('Esta accion ('+def.label+') pide autorizacion del Director. Continuar?'))return;
  }
  var idx=ACTIVE_BTN.indexOf(id);
  if(idx>=0)ACTIVE_BTN.splice(idx,1);else ACTIVE_BTN.push(id);
  paintBotonera();
  if(id==='handoff'){nctRecovery();return;}
  var last='';
  for(var i=S.messages.length-1;i>=0;i--){if(S.messages[i].who==='user'){last=S.messages[i].text;break;}}
  if(!last){toast('No hay mensaje que integrar');return;}
  var intent={'audit_xray':'🔍 AUDIT X-RAY: audita la respuesta anterior, sus fuentes y su codigo.',
              'input_shark':'🦈 INPUT SHARK: investiga y contrasta 20 fuentes y deja las 8 relevantes con evidencia.',
              'mapa_mental':'🧠 MAPA MENTAL: devuelve el mapa de 10 vistas del sistema.',
              'analisis':'📊 ANALISIS: profundiza el razonamiento tecnico de la respuesta anterior.',
              'propuesta':'💡 PROPUESTA: genera mejoras y recomendaciones priorizadas.',
              'refactorizar':'🛠️ REFACTORIZAR: prepara el refactor autorizado de lo anterior.',
              'modo_agentico':'🤖 MODO AGENTICO: ejecuta con agentes y herramientas.',
              'validar':'✅ VALIDAR: ejecuta las verificaciones y pruebas de lo anterior.'}[id]||'';
  sendMessage(intent);
}

/* ---------- AGENTES: ON/OFF ---------- */
function paintAgentes(){
  var box=el('agent-list');if(!box)return;
  box.innerHTML='<div class="list-row"><div class="name">consultando<span><small>…</small></span></div><span class="status wait">···</span></div>';
  apiJSON('/v1/agents').then(function(d){
    AGENTS=Object.keys(d.agents||{}).map(function(n){
      var a=d.agents[n]||{};
      return {name:n,enabled:!!a.enabled,role:a.role||'',type:a.type||'',tools:a.tools||[],
              history:a.history_count||0,memory:a.memory_keys||[],root:a.root||'',path:a.chat_path||'',
              implemented:!!a.implemented};
    });
    box.innerHTML=AGENTS.map(function(a){
      return '<div class="list-row" data-agent="'+a.name+'">'+
        '<div class="name">'+a.name+'<small>'+a.role+'</small></div>'+
        '<span class="status '+(a.enabled?'ok':'fail')+'">'+(a.enabled?'ON':'OFF')+'</span>'+
        '<button type="button" class="btn '+(a.enabled?'ghost':'primary')+'" data-toggle="'+a.name+'">'+(a.enabled?'Apagar':'Encender')+'</button>'+
        '</div>';
    }).join('');
    box.querySelectorAll('[data-toggle]').forEach(function(b){
      b.onclick=function(){toggleAgent(b.getAttribute('data-toggle'));};
    });
    badge('agent-badge',AGENTS.length+' agentes · '+(d.ok?'registro vivo':'reserva'),'success');
    paintRootList();
  }).catch(function(e){
    box.innerHTML='<div class="list-row"><div class="name">SIN CONEXION<small>'+String(e.message||e)+'</small></div><span class="status fail">OFFLINE</span></div>';
    badge('agent-badge','sin conexion','danger');
  });
}
function toggleAgent(name){
  var a=null;for(var i=0;i<AGENTS.length;i++){if(AGENTS[i].name===name)a=AGENTS[i];}
  if(!a)return;
  apiJSON('/v1/agents/'+encodeURIComponent(name)+'/state',{method:'POST',body:JSON.stringify({enabled:!a.enabled,reason:'chat'})})
    .then(function(){paintAgentes();toast(name+' -> '+(a.enabled?'OFF':'ON'));})
    .catch(function(e){badge('agent-badge',String(e.message||e),'danger');});
}

/* ---------- RAICES + AUTO-PULL ---------- */
function paintRootList(){
  var box=el('root-list');if(!box)return;
  apiJSON('/v1/roots').then(function(d){
    var rows=Object.keys(d.roots||{}).map(function(n){
      var r=d.roots[n]||{};
      var state=r.exists?'ok':'fail';
      var meta=(r.files?r.files+' ficheros':'—')+(r.bytes?' · '+Math.round(r.bytes/1024)+' KB':'')+(r.manifest_sha256?' · sha '+r.manifest_sha256.slice(0,8):'');
      return '<div class="list-row"><div class="name">'+n+'<small>'+meta+'</small></div><span class="status '+state+'">'+(r.exists?'RAIZ':'AUSENTE')+'</span></div>';
    });
    box.innerHTML=rows.join('')||'<div class="list-row"><div class="name">sin raices</div></div>';
    badge('root-badge',Object.keys(d.roots||{}).length+' raices','success');
  }).catch(function(e){badge('root-badge',String(e.message||e),'danger');});
}
function rootPull(){
  badge('root-badge','consultando...','warning');
  apiJSON('/v1/roots/pull',{method:'POST',body:JSON.stringify({apply:false})}).then(function(d){
    var txt=(d.stdout||'').trim().split('\n').slice(0,6).join(' · ');
    badge('root-badge',d.ok?'informe OK':'informe con avisos',d.ok?'success':'danger');
    var box=el('root-list');
    if(box)box.innerHTML='<div class="list-row"><div class="name">INFORME AUTO-PULL<small>'+txt.replace(/</g,'&lt;')+'</small></div></div>';
  }).catch(function(e){badge('root-badge',String(e.message||e),'danger');});
}

/* ---------- NCT/APEX: parse del bloque 📌 + render F3/F4 ---------- */
function showBox(id,text){
  var box=el(id);if(!box)return;
  box.innerHTML=bubbleHTML(String(text==null?'':text));
  var b=box.querySelector('.bubble');if(b)b.textContent=String(text==null?'':text);
}
function nctParse(){
  var text=el('nct-input')?el('nct-input').value:'';
  if(!text){badge('nct-badge','input vacio','danger');return;}
  badge('nct-badge','analizando...','warning');
  apiJSON('/v1/nct/parse',{method:'POST',body:JSON.stringify({text:text})}).then(function(d){
    var p=d.parsed||{},c=d.classification||{};
    badge('nct-badge',c.kind+' · '+(c.format_in||'?')+'→'+(c.format_out||'?'),'success');
    showBox('nct-preview',d.preview||'');
  }).catch(function(e){badge('nct-badge',String(e.message||e),'danger');});
}
function nctRender(fmt){
  var text=el('nct-input')?el('nct-input').value:'';
  var data={objetivo:text.slice(0,200)||'—',texto:text.slice(0,800),estado:'EXECUTING',progreso:'—',
            tiempo:'—',pendientes:0,confirma_input:false,instrucciones:true,motores_activos:true,
            grupos:[{name:'Chat',done:null,total:null,piezas:[]}],analisis:'Entrada entregada al clasificador.',
            arquitectura:'NCT/APEX · F1/F2 → F3/F4',evidencias:['parse local del bloque 📌'],
            plan:['Analizar input','Aprobar plan','Ejecutar','Validar']};
  apiJSON('/v1/nct/render',{method:'POST',body:JSON.stringify({data:data,format:fmt})}).then(function(d){
    showBox('nct-out',d.markdown||'');
    badge('nct-badge','render '+fmt,'success');
  }).catch(function(e){badge('nct-badge',String(e.message||e),'danger');});
}
function nctRecovery(){
  apiJSON('/v1/nct/recovery').then(function(d){
    showBox('nct-out','RECOVERY STATE\n'+JSON.stringify(d,null,2));
    badge('nct-badge','recovery','success');
  }).catch(function(e){badge('nct-badge',String(e.message||e),'danger');});
}

/* ---------- ARTEFACTOS ---------- */
function paintArtifacts(){
  var box=el('art-list');if(!box)return;
  apiJSON('/v1/artifacts').then(function(d){
    box.innerHTML=(d.artifacts||[]).map(function(a){
      return '<div class="list-row"><div class="name">'+a.name+'<small>'+a.bytes+' B · sha '+String(a.sha256).slice(0,12)+'</small></div>'+
        '<button type="button" class="btn" data-art="'+a.name+'">Ver</button></div>';
    }).join('')||'<div class="list-row"><div class="name">sin artefactos</div></div>';
    box.querySelectorAll('[data-art]').forEach(function(b){
      b.onclick=function(){apiJSON('/v1/artifacts/'+encodeURIComponent(b.getAttribute('data-art'))).then(function(x){showBox('art-view',x.content||'');});};
    });
    badge('art-badge',(d.artifacts||[]).length+' artefactos','success');
  }).catch(function(e){badge('art-badge',String(e.message||e),'danger');});
}
function createArtifact(){
  var name=el('art-name')?el('art-name').value:'';
  var kind=el('art-kind')?el('art-kind').value:'md';
  var content=el('art-content')?el('art-content').value:'';
  if(!name){badge('art-badge','falta nombre','danger');return;}
  apiJSON('/v1/artifacts',{method:'POST',body:JSON.stringify({name:name,kind:kind,content:content})}).then(function(d){
    badge('art-badge','creado '+d.name,'success');
    if(el('art-content'))el('art-content').value='';
    paintArtifacts();
  }).catch(function(e){badge('art-badge',String(e.message||e),'danger');});
}

/* ---------- CUADROS ---------- */
function paintCuadros(){
  badge('cuadros-badge','consultando...','warning');
  var pAgents=apiJSON('/v1/agents').then(function(d){
    var list=Object.keys(d.agents||{}).map(function(n){
      var a=d.agents[n]||{};
      return '<div class="list-row"><div class="name">'+n+'<small>'+(a.role||'')+'</small></div><span class="status '+(a.enabled?'ok':'fail')+'">'+(a.enabled?'ON':'OFF')+' · '+(a.history_count||0)+' turnos</span></div>';
    });
    el('cuadro-agentes').innerHTML=list.join('')||'<div class="list-row"><div class="name">sin datos</div></div>';
  }).catch(function(){el('cuadro-agentes').innerHTML='<div class="list-row"><div class="name">SIN CONEXION</div></div>';});
  var pModes=apiJSON('/v1/modes').then(function(d){
    var codigo=(d.code_modes||[]).join(', ')||'—';
    var servicio=(d.service_modes||[]).join(', ')||'—';
    el('cuadro-modos').innerHTML='<div class="list-row"><div class="name">codigo ('+(d.code_modes||[]).length+')<small>'+codigo+'</small></div><span class="status ok">OK</span></div>'+
      '<div class="list-row"><div class="name">servicio ('+(d.service_modes||[]).length+')<small>'+servicio+'</small></div><span class="status ok">OK</span></div>';
  }).catch(function(){el('cuadro-modos').innerHTML='<div class="list-row"><div class="name">SIN CONEXION</div></div>';});
  var pRoots=apiJSON('/v1/roots').then(function(d){
    el('cuadro-raices').innerHTML=Object.keys(d.roots||{}).map(function(n){
      var r=d.roots[n]||{};
      return '<div class="list-row"><div class="name">'+n+'<small>'+(r.path||'')+' · '+(r.files||0)+' ficheros</small></div><span class="status '+(r.exists?'ok':'fail')+'">'+(r.exists?'OK':'FALTA')+'</span></div>';
    }).join('')||'<div class="list-row"><div class="name">sin datos</div></div>';
  }).catch(function(){el('cuadro-raices').innerHTML='<div class="list-row"><div class="name">SIN CONEXION</div></div>';});
  var pMem=apiJSON('/v1/agents').then(function(d){
    var names=Object.keys(d.agents||{});
    if(!names.length){el('cuadro-memoria').innerHTML='<div class="list-row"><div class="name">sin datos</div></div>';return;}
    Promise.all(names.map(function(n){
      return apiJSON('/v1/agents/'+encodeURIComponent(n)+'/memory').then(function(m){
        return '<div class="list-row"><div class="name">'+n+'<small>'+((m.keys||[]).join(', ')||'sin claves')+'</small></div><span class="status ok">'+(m.keys||[]).length+'</span></div>';
      }).catch(function(){return '<div class="list-row"><div class="name">'+n+'<small>sin lectura</small></div><span class="status fail">ERR</span></div>';});
    })).then(function(rows){el('cuadro-memoria').innerHTML=rows.join('');});
  }).catch(function(){el('cuadro-memoria').innerHTML='<div class="list-row"><div class="name">SIN CONEXION</div></div>';});
  Promise.all([pAgents,pModes,pRoots,pMem]).then(function(){badge('cuadros-badge','cuadros al dia','success');});
}
'''

REPLACEMENTS = [
    (OLD_NAV, NEW_NAV, "nav 4 ventanas"),
    (OLD_SECTIONS_END, NEW_SECTIONS, "secciones AGENTES/INPUT/ARTEFACTOS/CUADROS"),
    (OLD_TITLES, NEW_TITLES, "titulos de ventanas"),
    (OLD_SEND_ROW, NEW_SEND_ROW, "botonera en el chat"),
    (OLD_START, NEW_START, "arranque con botonera y agentes"),
]


def main() -> int:
    if not CHAT.is_file():
        print(f"FALLO: no existe {CHAT}")
        return 2
    src = CHAT.read_text(encoding="utf-8")
    original = src
    for old, new, label in REPLACEMENTS:
        count = src.count(old)
        if count != 1:
            print(f"FALLO: ancla '{label}' aparece {count} veces (se esperaba 1)")
            return 2
        src = src.replace(old, new, 1)
        print(f"OK: {label}")

    if "MINIMAX 2F · AGENTES (ON/OFF)" in src:
        print("OK: JS ya presente (idempotente)")
    else:
        marker = "})();\n</script>"
        if src.count(marker) != 1:
            print("FALLO: no se encuentra el cierre del script principal")
            return 2
        src = src.replace(marker, NEW_JS.strip() + "\n" + marker, 1)
        print("OK: JS de agentes/NCT/artefactos/cuadros anadido")

    # Botones: enganchar los nuevos eventos al final del IIFE principal.
    hook_anchor = "el('probe-btn').onclick=probe;"
    hook_new = """el('probe-btn').onclick=probe;
el('agent-refresh-btn').onclick=paintAgentes;
el('root-pull-btn').onclick=rootPull;
el('nct-parse-btn').onclick=nctParse;
el('nct-f3-btn').onclick=function(){nctRender('F3');};
el('nct-f4-btn').onclick=function(){nctRender('F4');};
el('art-create-btn').onclick=createArtifact;
el('art-refresh-btn').onclick=paintArtifacts;
el('cuadros-btn').onclick=paintCuadros;"""
    if src.count(hook_anchor) != 1:
        print("FALLO: no se encuentra el ancla de los botones")
        return 2
    src = src.replace(hook_anchor, hook_new, 1)
    print("OK: eventos de los botones nuevos")

    # Al abrir la ventana de cuadros/agentes se pintan.
    render_anchor = "  if(S.view==='motores')probe();"
    render_new = """  if(S.view==='motores')probe();
  if(S.view==='agentes'){paintAgentes();}
  if(S.view==='artefactos'){paintArtifacts();}
  if(S.view==='cuadros'){paintCuadros();}"""
    if src.count(render_anchor) != 1:
        print("FALLO: no se encuentra el ancla de render()")
        return 2
    src = src.replace(render_anchor, render_new, 1)
    print("OK: render() refresca las ventanas nuevas")

    if src == original:
        print("FALLO: el fichero no cambio")
        return 2
    CHAT.write_text(src, encoding="utf-8")
    print(f"OK: chat actualizado ({len(original)} -> {len(src)} bytes)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
