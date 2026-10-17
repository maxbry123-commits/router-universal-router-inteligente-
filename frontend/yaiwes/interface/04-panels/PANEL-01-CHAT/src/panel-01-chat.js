(() => {
  'use strict';
  const STORAGE_KEY = 'yaiwes.panel01.chat.v2';
  const $ = (id) => document.getElementById(id);
  const uid = () => (globalThis.crypto?.randomUUID?.() || `${Date.now()}-${Math.random().toString(16).slice(2)}`);
  const now = () => new Date().toLocaleTimeString('es-CO',{hour:'2-digit',minute:'2-digit'});
  const defaultState = () => ({
    version:2,
    chats:[{id:uid(),title:'Proyecto UI YAIWES',messages:[],updatedAt:Date.now()}],
    activeChatId:null,
    mode:'Expert',
    enabledTools:['research'],
    attachments:[],
    events:[],
    run:{status:'READY',timer:null,token:null},
    recording:false
  });

  const EMPTY_STATE = $('emptyState');
  const S = loadState();
  if (!S.activeChatId || !S.chats.some(c => c.id === S.activeChatId)) S.activeChatId = S.chats[0].id;
  S.attachments = [];
  S.run = {status:'READY',timer:null,token:null};
  let mediaRecorder = null;
  let recordedChunks = [];

  function loadState(){
    try{
      const raw = localStorage.getItem(STORAGE_KEY);
      if (!raw) return defaultState();
      const parsed = JSON.parse(raw);
      if (!Array.isArray(parsed.chats) || !parsed.chats.length) return defaultState();
      return {...defaultState(),...parsed,attachments:[],events:Array.isArray(parsed.events)?parsed.events.slice(0,12):[]};
    }catch{return defaultState()}
  }

  function persist(){
    const safe = {...S,attachments:[],run:{status:S.run.status,timer:null,token:null},events:S.events.slice(0,12)};
    try{localStorage.setItem(STORAGE_KEY,JSON.stringify(safe))}catch{}
  }

  function activeChat(){ return S.chats.find(c => c.id === S.activeChatId) || S.chats[0]; }

  function log(action,result='ok'){
    S.events.unshift({action,result,time:now()});
    S.events = S.events.slice(0,12);
    persist();
    renderEvents();
  }

  function emitAction(actionId,payload={}){
    const event = {type:'YAIWES_UI_ACTION',panelId:'PANEL-01',windowId:'CHAT-01',actionId,payload,at:new Date().toISOString()};
    window.dispatchEvent(new CustomEvent('yaiwes:ui-action',{detail:event}));
    const bridge = window.YAIWES_BRIDGE;
    if (bridge && typeof bridge.dispatch === 'function') {
      try { return Promise.resolve(bridge.dispatch(actionId,payload)); }
      catch (error) { return Promise.resolve({ok:false,reason:error?.message || 'bridge_error'}); }
    }
    return Promise.resolve({ok:false,reason:'bridge_not_connected'});
  }

  function setRunState(status){
    S.run.status = status;
    const normalized = status.toLowerCase();
    $('runState').textContent = status;
    $('runState').dataset.state = normalized.includes('run') || normalized.includes('queue') ? 'running' : normalized.includes('block') ? 'blocked' : normalized.includes('cancel') ? 'cancelled' : 'idle';
    $('inspectState').textContent = status;
    $('stopBtn').hidden = !['QUEUED','RUNNING'].includes(status);
  }

  function escapeHtml(text){
    const div=document.createElement('div'); div.textContent=String(text ?? ''); return div.innerHTML;
  }

  function renderChats(){
    const list = $('chatList');
    list.innerHTML = '';
    for (const chat of S.chats){
      const btn = document.createElement('button');
      btn.type='button'; btn.className=`chat-item${chat.id===S.activeChatId?' active':''}`; btn.dataset.chatId=chat.id;
      const last=chat.messages.at(-1)?.text || 'Sin mensajes';
      btn.innerHTML=`<span class="chat-avatar" aria-hidden="true">${escapeHtml((chat.title||'C').trim().charAt(0).toUpperCase())}</span><span class="chat-copy"><b>${escapeHtml(chat.title)}</b><small>${escapeHtml(last)}</small></span>${chat.id===S.activeChatId?'<span class="unread-dot" aria-hidden="true"></span>':''}`;
      btn.addEventListener('click',()=>{S.activeChatId=chat.id;persist();closeRail();renderAll();log('chat.select',chat.title)});
      list.append(btn);
    }
  }

  function renderMessages(){
    const thread=$('messages'); thread.replaceChildren(); const chat=activeChat();
    if(!chat.messages.length){
      EMPTY_STATE.hidden=false;
      thread.append(EMPTY_STATE);
      return;
    }
    for(const m of chat.messages){
      const article=document.createElement('article');
      article.className=`message ${m.role}${m.blocked?' blocked':''}`;
      const head=document.createElement('div'); head.className='message-head';
      head.innerHTML=`<b>${m.role==='user'?'Tú':'YAIWES'}</b><span>${escapeHtml(m.time||'')}</span><span>${escapeHtml(m.state||'')}</span>`;
      const body=document.createElement('div'); body.className='message-body'; body.textContent=m.text || '';
      article.append(head,body);
      if(m.attachments?.length){
        const row=document.createElement('div'); row.className='attachment-row';
        for(const a of m.attachments){
          const chip=document.createElement('div'); chip.className='attachment-chip';
          chip.innerHTML=`<span class="kind">${a.type?.startsWith('image/')?'IMG':a.type?.startsWith('audio/')?'AUD':'FILE'}</span><span><b>${escapeHtml(a.name)}</b><small>${escapeHtml(a.size)}</small></span>`;
          row.append(chip);
        }
        article.append(row);
      }
      thread.append(article);
    }
    requestAnimationFrame(()=>{thread.scrollTop=thread.scrollHeight});
  }

  function renderAttachments(){
    const host=$('attachmentPreview'); host.innerHTML='';
    S.attachments.forEach((a,index)=>{
      const item=document.createElement('div'); item.className='preview';
      if(a.preview){const img=document.createElement('img');img.src=a.preview;img.alt='';item.append(img)}
      const label=document.createElement('span');label.textContent=a.name;item.append(label);
      const remove=document.createElement('button');remove.type='button';remove.setAttribute('aria-label',`Quitar ${a.name}`);remove.textContent='×';
      remove.addEventListener('click',()=>{if(a.preview?.startsWith('blob:'))URL.revokeObjectURL(a.preview);S.attachments.splice(index,1);renderAttachments();syncSendState();log('attachment.remove',a.name)});
      item.append(remove);host.append(item);
    });
  }

  function renderEvents(){
    $('eventLog').innerHTML=S.events.map(e=>`<div class="event"><b>${escapeHtml(e.action)}</b><span>${escapeHtml(e.result)}</span><time>${escapeHtml(e.time)}</time></div>`).join('');
  }

  function renderMode(){
    $('modelLabel').textContent=S.mode;$('modeLabel').textContent=S.mode;$('inspectMode').textContent=S.mode;
    document.querySelectorAll('[data-mode]').forEach(btn=>btn.setAttribute('aria-checked',String(btn.dataset.mode===S.mode)));
  }

  function renderTools(){
    document.querySelectorAll('[data-tool]').forEach(btn=>btn.setAttribute('aria-pressed',String(S.enabledTools.includes(btn.dataset.tool))));
  }

  function renderAll(){ renderChats();renderMessages();renderAttachments();renderEvents();renderMode();renderTools();syncSendState(); }

  function autoGrow(){
    const t=$('composer');t.style.height='auto';t.style.height=Math.min(t.scrollHeight,140)+'px';syncSendState();
  }
  function syncSendState(){ $('sendBtn').disabled=!$('composer').value.trim()&&!S.attachments.length; }

  function openRail(){ $('rail').classList.add('open');$('railOpen').setAttribute('aria-expanded','true'); if(innerWidth<=720){$('scrim').hidden=false} }
  function closeRail(){ $('rail').classList.remove('open');$('railOpen').setAttribute('aria-expanded','false');$('scrim').hidden=true; }

  function closeMenus(){
    $('modelMenu').hidden=true;$('actionMenu').hidden=true;$('modelTrigger').setAttribute('aria-expanded','false');$('modeTrigger').setAttribute('aria-expanded','false');$('moreTrigger').setAttribute('aria-expanded','false');
  }
  function toggleModelMenu(anchor){
    const willOpen=$('modelMenu').hidden; closeMenus(); if(willOpen){$('modelMenu').hidden=false;$(anchor).setAttribute('aria-expanded','true');$('modelMenu').querySelector('[aria-checked="true"]')?.focus();}
  }
  function toggleActionMenu(){ const willOpen=$('actionMenu').hidden; closeMenus(); if(willOpen){$('actionMenu').hidden=false;$('moreTrigger').setAttribute('aria-expanded','true');$('actionMenu').querySelector('button')?.focus();} }

  function addFiles(fileList){
    const files=[...fileList];
    for(const f of files){
      const item={name:f.name,size:formatBytes(f.size),type:f.type||'application/octet-stream'};
      if(f.type.startsWith('image/')) item.preview=URL.createObjectURL(f);
      S.attachments.push(item);
    }
    renderAttachments();syncSendState();log('attachment.add',`${files.length} archivo(s)`);
  }
  function formatBytes(bytes){if(bytes<1024)return `${bytes} B`;if(bytes<1048576)return `${(bytes/1024).toFixed(1)} KB`;return `${(bytes/1048576).toFixed(1)} MB`}

  async function startAudio(){
    if(mediaRecorder?.state==='recording'){mediaRecorder.stop();return}
    if(!navigator.mediaDevices?.getUserMedia || !window.MediaRecorder){log('audio.record','unsupported');return}
    try{
      const stream=await navigator.mediaDevices.getUserMedia({audio:true}); recordedChunks=[]; mediaRecorder=new MediaRecorder(stream);
      mediaRecorder.ondataavailable=(e)=>{if(e.data.size)recordedChunks.push(e.data)};
      mediaRecorder.onstop=()=>{
        const blob=new Blob(recordedChunks,{type:mediaRecorder.mimeType||'audio/webm'});
        S.attachments.push({name:`audio-${Date.now()}.webm`,size:formatBytes(blob.size),type:blob.type||'audio/webm'});
        stream.getTracks().forEach(t=>t.stop());S.recording=false;renderAttachments();syncAudioButtons();syncSendState();log('audio.record','ready');
      };
      mediaRecorder.start();S.recording=true;syncAudioButtons();log('audio.record','recording');
    }catch{S.recording=false;syncAudioButtons();log('audio.record','permission_denied')}
  }
  function syncAudioButtons(){
    $('audioBtn').classList.toggle('recording',S.recording);$('audioBtn').textContent=S.recording?'■':'⌁';$('audioBtn').setAttribute('aria-label',S.recording?'Detener grabación':'Grabar audio');
    $('audioTile').classList.toggle('active',S.recording);
  }

  async function send(){
    const text=$('composer').value.trim(); if(!text&&!S.attachments.length)return;
    if(['QUEUED','RUNNING'].includes(S.run.status))return;
    const chat=activeChat();
    const attachments=S.attachments.map(({name,size,type})=>({name,size,type}));
    chat.messages.push({id:uid(),role:'user',text:text||'[Adjuntos]',attachments,time:now(),state:'QUEUED'});chat.updatedAt=Date.now();
    $('composer').value='';S.attachments.forEach(a=>{if(a.preview?.startsWith('blob:'))URL.revokeObjectURL(a.preview)});S.attachments=[];autoGrow();renderAll();setRunState('QUEUED');log('send_message','queued');
    const token=uid();S.run.token=token;
    const resultPromise=emitAction('send_message',{conversationId:chat.id,text,attachments,mode:S.mode,tools:S.enabledTools});
    setRunState('RUNNING');
    const timeout=new Promise(resolve=>{S.run.timer=setTimeout(()=>resolve({ok:false,reason:'bridge_not_connected'}),700)});
    const result=await Promise.race([resultPromise,timeout]);
    if(S.run.token!==token)return;
    clearTimeout(S.run.timer);S.run.timer=null;
    if(result?.ok){setRunState('READY');log('bridge.dispatch','accepted');return}
    chat.messages.push({id:uid(),role:'system',text:'La interfaz registró la acción, pero el bridge backend no está conectado. No se generó una respuesta artificial.',time:now(),state:'BRIDGE_REQUIRED',blocked:true});
    chat.updatedAt=Date.now();setRunState('BRIDGE_REQUIRED');persist();renderAll();log('bridge.dispatch',result?.reason||'not_connected');
    setTimeout(()=>{if(S.run.status==='BRIDGE_REQUIRED')setRunState('READY')},900);
  }

  function cancelRun(){
    if(!['QUEUED','RUNNING'].includes(S.run.status))return;
    if(S.run.timer)clearTimeout(S.run.timer);S.run.timer=null;S.run.token=uid();setRunState('CANCELLED');emitAction('cancel_run',{conversationId:activeChat().id});log('cancel_run','local_cancelled');setTimeout(()=>setRunState('READY'),700);
  }

  function newChat(){
    const chat={id:uid(),title:'Nuevo chat',messages:[],updatedAt:Date.now()};S.chats.unshift(chat);S.activeChatId=chat.id;persist();renderAll();closeRail();$('composer').focus();log('chat.create','ok');
  }
  function renameChat(){
    closeMenus();const chat=activeChat();const name=prompt('Nombre del chat',chat.title);if(name?.trim()){chat.title=name.trim().slice(0,80);chat.updatedAt=Date.now();persist();renderAll();log('chat.rename',chat.title)}
  }
  function exportChat(){
    closeMenus();const data=JSON.stringify(activeChat(),null,2);const url=URL.createObjectURL(new Blob([data],{type:'application/json'}));const a=document.createElement('a');a.href=url;a.download=`yaiwes-${activeChat().title.replace(/[^a-z0-9-_]+/gi,'-').toLowerCase()||'chat'}.json`;document.body.append(a);a.click();a.remove();setTimeout(()=>URL.revokeObjectURL(url),0);log('export_conversation','json');
  }
  function askClear(){closeMenus();$('confirmText').textContent='Se eliminarán los mensajes de esta conversación. El chat se conservará.';$('confirmDialog').showModal();}
  function clearMessages(){const chat=activeChat();chat.messages=[];chat.updatedAt=Date.now();persist();$('confirmDialog').close();renderAll();log('chat.clear','ok')}

  function selectMode(mode){S.mode=mode;persist();renderMode();closeMenus();log('mode.select',mode);$('composer').focus()}
  function toggleTool(name){
    const i=S.enabledTools.indexOf(name);if(i>=0)S.enabledTools.splice(i,1);else S.enabledTools.push(name);persist();renderTools();log('tool.toggle',`${name}:${S.enabledTools.includes(name)?'on':'off'}`);
  }

  $('railOpen').addEventListener('click',openRail);$('railClose').addEventListener('click',closeRail);$('scrim').addEventListener('click',()=>{closeRail();closeMenus()});
  $('newChat').addEventListener('click',newChat);$('modelTrigger').addEventListener('click',()=>toggleModelMenu('modelTrigger'));$('modeTrigger').addEventListener('click',()=>toggleModelMenu('modeTrigger'));$('moreTrigger').addEventListener('click',toggleActionMenu);
  document.querySelectorAll('[data-mode]').forEach(btn=>btn.addEventListener('click',()=>selectMode(btn.dataset.mode)));
  document.querySelectorAll('[data-tool]').forEach(btn=>btn.addEventListener('click',()=>toggleTool(btn.dataset.tool)));
  $('addTrigger').addEventListener('click',()=>{$('toolsDialog').showModal();log('tools.open','ok')});$('toolsClose').addEventListener('click',()=>$('toolsDialog').close());
  $('fileBtn').addEventListener('click',()=>{$('toolsDialog').close();$('fileInput').click()});$('imageBtn').addEventListener('click',()=>{$('toolsDialog').close();$('imageInput').click()});$('cameraBtn').addEventListener('click',()=>{$('toolsDialog').close();$('cameraInput').click()});$('audioTile').addEventListener('click',()=>{$('toolsDialog').close();startAudio()});
  $('fileInput').addEventListener('change',e=>{addFiles(e.target.files);e.target.value=''});$('imageInput').addEventListener('change',e=>{addFiles(e.target.files);e.target.value=''});$('cameraInput').addEventListener('change',e=>{addFiles(e.target.files);e.target.value=''});
  $('audioBtn').addEventListener('click',startAudio);$('sendBtn').addEventListener('click',send);$('stopBtn').addEventListener('click',cancelRun);
  $('renameBtn').addEventListener('click',renameChat);$('exportBtn').addEventListener('click',exportChat);$('clearBtn').addEventListener('click',askClear);$('confirmCancel').addEventListener('click',()=>$('confirmDialog').close());$('confirmOk').addEventListener('click',clearMessages);
  $('composer').addEventListener('input',autoGrow);$('composer').addEventListener('keydown',e=>{if(e.key==='Enter'&&!e.shiftKey){e.preventDefault();send()}});
  document.addEventListener('pointerdown',e=>{if(!e.target.closest('.menu')&&!e.target.closest('#modelTrigger')&&!e.target.closest('#modeTrigger')&&!e.target.closest('#moreTrigger'))closeMenus()});
  document.addEventListener('keydown',e=>{if(e.key==='Escape'){closeMenus();closeRail()}if(e.key==='ArrowDown'&&!$('modelMenu').hidden){e.preventDefault();const items=[...$('modelMenu').querySelectorAll('button')];const i=items.indexOf(document.activeElement);items[(i+1+items.length)%items.length].focus()}if(e.key==='ArrowUp'&&!$('modelMenu').hidden){e.preventDefault();const items=[...$('modelMenu').querySelectorAll('button')];const i=items.indexOf(document.activeElement);items[(i-1+items.length)%items.length].focus()}});
  window.addEventListener('resize',()=>{if(innerWidth>720)closeRail()});

  window.__YAIWES_PANEL01__={state:S,send,newChat,selectMode,toggleTool,emitAction};
  renderAll();setRunState('READY');syncAudioButtons();autoGrow();log('panel.init','ready');
})();
