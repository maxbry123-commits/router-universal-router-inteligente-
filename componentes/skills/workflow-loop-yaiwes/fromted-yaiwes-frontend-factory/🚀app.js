/* FROMTED × YAIWES v0.2: local UI functionality + explicit remote fail-closed integration. */
(() => {
  'use strict';
  const KEY = 'yaiwes.visual.review.v02';
  const makeId = () => (window.crypto && typeof window.crypto.randomUUID==='function') ? window.makeId() : `${Date.now().toString(36)}-${Math.random().toString(36).slice(2)}`;
  const MODES = ['fast','think','balanced'];
  const THEMES = {
    little: {label:'Little',category:'CANÓNICO · PRINCIPAL',bg:'#1C1B1A',card:'#2A2927',accent:'#C65D3B',swatch:'#F5F4F0'},
    matte: {label:'Negro mate',category:'CANÓNICO',bg:'#0a0a0d',card:'#202025',accent:'#2563eb',swatch:'#e4e4e7'},
    crystal: {label:'Cristal holográfico',category:'EN REVISIÓN',bg:'#0c1421',card:'rgba(135,190,210,.36)',accent:'#b8f5fa',swatch:'#e6f4ff'},
    orange: {label:'Naranja / negro',category:'EN REVISIÓN',bg:'#100e0d',card:'#26211d',accent:'#ef823c',swatch:'#f5e9df'},
    blue: {label:'Azul profundo',category:'EN REVISIÓN',bg:'#0a1424',card:'#192c45',accent:'#66b7ff',swatch:'#e1edfa'},
    blanco: {label:'Blanco',category:'CANÓNICO',bg:'#f4f4f5',card:'#ffffff',accent:'#2563eb',swatch:'#3f3f46'},
    gris: {label:'Gris neutro',category:'NUEVO · EN REVISIÓN',bg:'#969ba2',card:'#d6d9de',accent:'#303740',swatch:'#252932'}
  };
  const LABELS = {
    es:{workspace:'ESPACIO DE TRABAJO',product:'FROMTED PRODUCT',chat:'Chat',files:'Archivos',wall:'Crazy Wall',settings:'Configuración',design_lock:'PERFIL VISUAL',theme_lock_hint:'Tokens conservados · vistas en revisión',customize:'Personalizar apariencia',not_connected:'Sin backend',connected:'Puente disponible',hello:'Un espacio para crear.',tagline:'Diseño modular FROMTED × YAIWES. Cada función se prueba antes de aprobar el perfil visual.',chat_intro:'Tu conversación, tus herramientas y tus modelos en un solo lugar.',conversation:'CONVERSACIÓN',new_chat:'Nuevo chat',mode:'Modo',fast:'Rápido',think:'Pensar',balanced:'Equilibrado',fast_desc:'Respuestas directas',think_desc:'Mayor profundidad',balanced_desc:'Velocidad y detalle',model:'Modelo',empty_chat:'Escribe para comenzar',no_invent:'Sin motor conectado: nunca se inventarán respuestas.',type_message:'Escribe aquí tu mensaje…',document:'Documento',website:'Web',image:'Imagen',send:'Enviar',attach:'Adjuntar',offline_note:'Sin backend: el envío se bloquea. El borrador y las herramientas siguen funcionando.',gallery:'Tus archivos locales',file_intro:'Añade archivos reales desde tu dispositivo. Se guardan localmente los de hasta 1 MB.',add_files:'Añadir archivos',search_files:'Buscar archivos…',local:'Local',pinned:'Anclados',empty_files:'Todavía no has agregado archivos.',empty_search:'No hay archivos que coincidan.',all_local:'Todos',pin:'Anclar',download:'Descargar',file_session:'Solo esta sesión',file_saved:'Conservado localmente',wall_intro:'Raíces editables del ejemplo YAIWES. Los estados son locales; no representan comprobaciones de GitHub.',workflow:'FLUJO DE TRABAJO',edit:'Abrir ficha',roots:'Raíces registradas',add_root:'Añadir raíz',progress:'En curso',enabled:'Encendido',warning:'Advertencia',pending:'Pendiente',save:'Guardar',cancel:'Cancelar',close:'Cerrar',note:'Bitácora / nota',name:'Nombre',apply:'Aplicar',choose_mode:'Cómo quieres que trabaje el modelo conectado',choose_visual:'Selecciona una apariencia. Little es el diseño principal.',themes:'TEMAS DISPONIBLES',appearance:'Apariencia de la interfaz',theme_intro:'7 estilos · 3 canónicos + 4 propuestas (incluido gris neutro).',status_legend:'CÓDIGO DE ESTADOS',status_help:'Estos indicadores semánticos funcionan en los siete temas.',preferences:'PREFERENCIAS',motion:'Animaciones',motion_desc:'Transiciones discretas',hints:'Ayudas de contexto',hints_desc:'Mostrar información de referencia',language:'Idioma',export:'Exportar',import:'Importar',reset:'Reiniciar estado',reset_confirm:'¿Borrar datos locales?',reset_explain:'Se eliminarán los archivos guardados, notas y opciones de este navegador.',test:'PRUEBA FUNCIONAL',action_log:'Última acción',verified:'Verificación',local_only:'Local · no simula backend',design_review:'EN REVISIÓN',storage:'Persistencia local',message_blocked:'No enviado: falta un bridge funcional.',invalid_file:'Archivo no válido.',saved:'Guardado en este navegador',updated:'Actualizado',file_added:'Archivo añadido',sent_ok:'Enviado mediante bridge',import_ok:'Estado importado',no_messages:'No hay mensajes enviados.',choose_file:'Selecciona un archivo',delete:'Eliminar',attached:'Adjunto',how_works:'REFERENCIA → SKILL → CÓDIGO → NAVEGADOR → TEST → PASS',meta_label:'Diseño principal',no_bridge:'No hay bridge conectado',no_notes:'Sin notas todavía',root_name:'Ruta o nombre',file_persist_note:'Los archivos mayores de 1 MB solo permanecen disponibles mientras esta pestaña esté abierta.',remote_label:'Motor externo',local_actions:'Herramientas locales'},
    en:{workspace:'WORKSPACE',product:'FROMTED PRODUCT',chat:'Chat',files:'Files',wall:'Crazy Wall',settings:'Settings',design_lock:'VISUAL PROFILE',theme_lock_hint:'Original tokens · under review',customize:'Customize appearance',not_connected:'No backend',connected:'Bridge available',hello:'A space to create.',tagline:'Modular FROMTED × YAIWES design. Every feature is tested before approval.',chat_intro:'Your conversation, tools, and models together.',conversation:'CONVERSATION',new_chat:'New chat',mode:'Mode',fast:'Fast',think:'Think',balanced:'Balanced',fast_desc:'Direct answers',think_desc:'Deeper reasoning',balanced_desc:'Speed and detail',model:'Model',empty_chat:'Type to begin',no_invent:'No connected engine: replies will never be invented.',type_message:'Write your message…',document:'Document',website:'Web',image:'Image',send:'Send',attach:'Attach',offline_note:'No backend: sending is blocked. Drafts and tools work.',gallery:'Local files',file_intro:'Add real files from your device. Files under 1 MB are stored locally.',add_files:'Add files',search_files:'Search files…',local:'Local',pinned:'Pinned',empty_files:'No files added yet.',empty_search:'No matching files.',all_local:'All',pin:'Pin',download:'Download',file_session:'This session only',file_saved:'Saved locally',wall_intro:'Editable YAIWES sample roots. Local statuses are not verified GitHub states.',workflow:'WORKFLOW',edit:'Open item',roots:'Registered roots',add_root:'Add root',progress:'In progress',enabled:'Enabled',warning:'Warning',pending:'Pending',save:'Save',cancel:'Cancel',close:'Close',note:'Log / note',name:'Name',apply:'Apply',choose_mode:'Choose how the connected model should work',choose_visual:'Choose a look. Little is the primary design.',themes:'AVAILABLE THEMES',appearance:'Interface appearance',theme_intro:'7 styles · 3 canonical + 4 proposals (including neutral gray).',status_legend:'STATE COLORS',status_help:'These semantic indicators work across all seven themes.',preferences:'PREFERENCES',motion:'Animations',motion_desc:'Subtle transitions',hints:'Context hints',hints_desc:'Show reference information',language:'Language',export:'Export',import:'Import',reset:'Reset state',reset_confirm:'Delete local data?',reset_explain:'This browser’s files, notes and options will be deleted.',test:'FUNCTIONAL TEST',action_log:'Last action',verified:'Verification',local_only:'Local · no backend simulation',design_review:'UNDER REVIEW',storage:'Local persistence',message_blocked:'Not sent: no functional bridge.',invalid_file:'Invalid file.',saved:'Saved in this browser',updated:'Updated',file_added:'File added',sent_ok:'Sent through bridge',import_ok:'State imported',no_messages:'No messages sent yet.',choose_file:'Choose file',delete:'Delete',attached:'Attached',how_works:'REFERENCE → SKILL → CODE → BROWSER → TEST → PASS',meta_label:'Primary design',no_bridge:'No bridge connected',no_notes:'No notes yet',root_name:'Path or name',file_persist_note:'Files above 1 MB only remain available while this tab is open.',remote_label:'External engine',local_actions:'Local tools'},
    fr:{workspace:'ESPACE DE TRAVAIL',product:'PRODUIT FROMTED',chat:'Chat',files:'Fichiers',wall:'Crazy Wall',settings:'Paramètres',design_lock:'PROFIL VISUEL',theme_lock_hint:'Tokens originaux · en révision',customize:'Personnaliser',not_connected:'Backend absent',connected:'Bridge disponible',hello:'Un espace pour créer.',tagline:'Design modulaire FROMTED × YAIWES, testé avant approbation.',chat_intro:'Vos conversations et outils au même endroit.',conversation:'CONVERSATION',new_chat:'Nouveau chat',mode:'Mode',fast:'Rapide',think:'Réfléchir',balanced:'Équilibré',fast_desc:'Réponses directes',think_desc:'Analyse approfondie',balanced_desc:'Vitesse et détails',model:'Modèle',empty_chat:'Commencez à écrire',no_invent:'Aucun moteur connecté : aucune réponse inventée.',type_message:'Votre message…',document:'Document',website:'Web',image:'Image',send:'Envoyer',attach:'Joindre',offline_note:'Pas de backend : envoi bloqué. Brouillons et outils actifs.',gallery:'Fichiers locaux',file_intro:'Ajoutez de vrais fichiers. Jusqu’à 1 Mo stockés localement.',add_files:'Ajouter',search_files:'Rechercher…',local:'Local',pinned:'Épinglés',empty_files:'Aucun fichier ajouté.',empty_search:'Aucun résultat.',all_local:'Tous',pin:'Épingler',download:'Télécharger',file_session:'Session uniquement',file_saved:'Sauvegardé localement',wall_intro:'Racines YAIWES éditables. Statuts locaux, non vérifiés sur GitHub.',workflow:'PROCESSUS',edit:'Ouvrir',roots:'Racines',add_root:'Ajouter une racine',progress:'En cours',enabled:'Activé',warning:'Avertissement',pending:'En attente',save:'Enregistrer',cancel:'Annuler',close:'Fermer',note:'Journal / note',name:'Nom',apply:'Appliquer',choose_mode:'Choisir le mode du modèle connecté',choose_visual:'Choisissez un style. Little est le design principal.',themes:'THÈMES',appearance:'Apparence',theme_intro:'7 styles · 3 canoniques + 4 propositions.',status_legend:'COULEURS D’ÉTAT',status_help:'Les états sont disponibles sur les sept thèmes.',preferences:'PRÉFÉRENCES',motion:'Animations',motion_desc:'Transitions discrètes',hints:'Aide contextuelle',hints_desc:'Afficher les références',language:'Langue',export:'Exporter',import:'Importer',reset:'Réinitialiser',reset_confirm:'Effacer les données locales ?',reset_explain:'Tous les fichiers, notes et réglages de ce navigateur seront supprimés.',test:'TEST FONCTIONNEL',action_log:'Dernière action',verified:'Vérification',local_only:'Local · backend non simulé',design_review:'EN RÉVISION',storage:'Stockage local',message_blocked:'Non envoyé : bridge indisponible.',invalid_file:'Fichier invalide.',saved:'Sauvegardé localement',updated:'Mis à jour',file_added:'Fichier ajouté',sent_ok:'Envoyé via bridge',import_ok:'État importé',no_messages:'Aucun message envoyé.',choose_file:'Choisir un fichier',delete:'Supprimer',attached:'Pièce jointe',how_works:'RÉFÉRENCE → SKILL → CODE → NAVIGATEUR → TEST → PASS',meta_label:'Design principal',no_bridge:'Bridge indisponible',no_notes:'Aucune note',root_name:'Chemin ou nom',file_persist_note:'Au-delà de 1 Mo, fichiers disponibles durant cette session seulement.',remote_label:'Moteur distant',local_actions:'Outils locaux'},
    pt:{workspace:'ÁREA DE TRABALHO',product:'PRODUTO FROMTED',chat:'Chat',files:'Arquivos',wall:'Crazy Wall',settings:'Configurações',design_lock:'PERFIL VISUAL',theme_lock_hint:'Tokens originais · em revisão',customize:'Personalizar aparência',not_connected:'Sem backend',connected:'Bridge disponível',hello:'Um espaço para criar.',tagline:'Design modular FROMTED × YAIWES, testado antes da aprovação.',chat_intro:'Suas conversas, ferramentas e modelos em um lugar.',conversation:'CONVERSA',new_chat:'Novo chat',mode:'Modo',fast:'Rápido',think:'Pensar',balanced:'Equilibrado',fast_desc:'Respostas diretas',think_desc:'Mais profundidade',balanced_desc:'Velocidade e detalhe',model:'Modelo',empty_chat:'Escreva para começar',no_invent:'Sem motor conectado: nenhuma resposta será inventada.',type_message:'Escreva sua mensagem…',document:'Documento',website:'Web',image:'Imagem',send:'Enviar',attach:'Anexar',offline_note:'Sem backend: envio bloqueado. Rascunhos e ferramentas continuam ativos.',gallery:'Arquivos locais',file_intro:'Adicione arquivos reais. Arquivos até 1 MB são salvos localmente.',add_files:'Adicionar arquivos',search_files:'Pesquisar arquivos…',local:'Local',pinned:'Fixados',empty_files:'Nenhum arquivo adicionado.',empty_search:'Nenhum arquivo encontrado.',all_local:'Todos',pin:'Fixar',download:'Baixar',file_session:'Somente nesta sessão',file_saved:'Salvo localmente',wall_intro:'Raízes YAIWES editáveis. Estados locais não são dados confirmados do GitHub.',workflow:'FLUXO DE TRABALHO',edit:'Abrir',roots:'Raízes',add_root:'Adicionar raiz',progress:'Em andamento',enabled:'Ativado',warning:'Aviso',pending:'Pendente',save:'Salvar',cancel:'Cancelar',close:'Fechar',note:'Registro / nota',name:'Nome',apply:'Aplicar',choose_mode:'Escolha como o modelo conectado deve trabalhar',choose_visual:'Escolha o visual. Little é o principal.',themes:'TEMAS',appearance:'Aparência',theme_intro:'7 estilos · 3 canônicos + 4 propostas.',status_legend:'CORES DE STATUS',status_help:'Estados semânticos nos sete temas.',preferences:'PREFERÊNCIAS',motion:'Animações',motion_desc:'Transições discretas',hints:'Dicas de contexto',hints_desc:'Mostrar referências',language:'Idioma',export:'Exportar',import:'Importar',reset:'Redefinir estado',reset_confirm:'Apagar dados locais?',reset_explain:'Arquivos, notas e opções deste navegador serão apagados.',test:'TESTE FUNCIONAL',action_log:'Última ação',verified:'Verificação',local_only:'Local · sem simulação do backend',design_review:'EM REVISÃO',storage:'Armazenamento local',message_blocked:'Não enviado: bridge indisponível.',invalid_file:'Arquivo inválido.',saved:'Salvo neste navegador',updated:'Atualizado',file_added:'Arquivo adicionado',sent_ok:'Enviado pelo bridge',import_ok:'Estado importado',no_messages:'Nenhuma mensagem enviada.',choose_file:'Escolher arquivo',delete:'Excluir',attached:'Anexo',how_works:'REFERÊNCIA → SKILL → CÓDIGO → NAVEGADOR → TESTE → PASS',meta_label:'Visual principal',no_bridge:'Bridge indisponível',no_notes:'Sem notas',root_name:'Caminho ou nome',file_persist_note:'Arquivos acima de 1 MB permanecem apenas durante esta sessão.',remote_label:'Motor externo',local_actions:'Ferramentas locais'}
  };
  const ic = name => `<svg class="icon" aria-hidden="true"><use href="#i-${name}"/></svg>`;
  const esc = value => String(value ?? '').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  const baseRoots = [
    {id:'r1',name:'Desplegar/',description:'Entrada de lotes y entrega',status:'pending',note:''},
    {id:'r2',name:'PIPELINE/',description:'Planes y checkpoints',status:'pending',note:''},
    {id:'r3',name:'Método de trabajo/',description:'Leyes y reglas',status:'pending',note:''},
    {id:'r4',name:'Refactoria/',description:'Preservación y paridad',status:'pending',note:''},
    {id:'r5',name:'Yaiwes wordflow/',description:'Agente y kernel',status:'pending',note:''},
    {id:'r6',name:'Wordflow Code/',description:'Runner y evidencia',status:'pending',note:''}
  ];
  const defaults = () => ({version:2,theme:'little',locale:'es',page:'chat',mode:'fast',model:'MiniMax M3',settings:{motion:true,hints:true},draft:'',tools:{document:false,website:false,image:false},messages:[],files:[],attachments:[],filter:'local',search:'',roots:structuredClone(baseRoots),selectedRoot:'r1'});
  let state = defaults(), modeDraft='fast', sheetKind=null, uploadPurpose='files', toastTimer=null, sending=false;
  const volatileUrls = new Map();
  const $ = sel => document.querySelector(sel);
  const t = key => (LABELS[state.locale] || LABELS.es)[key] || LABELS.es[key] || key;
  const knownStatus = new Set(['progress','enabled','warning','pending']);
  const knownPages = ['chat','files','wall','settings'];
  const knownModels = ['MiniMax M3','Grok','Claude','GPT','DeepSeek','Qwen'];
  const bridgeReady = () => !!(window.YAIWES_PLUGIN_BRIDGE && typeof window.YAIWES_PLUGIN_BRIDGE.execute === 'function');
  function bus(action,payload={},remote=false){return window.YAIWESActionBus.execute(action,payload,{remote});}
  function persist(){
    try {
      const saved = {...state,files:state.files.filter(f=>!f.volatile)};
      localStorage.setItem(KEY,JSON.stringify(saved));
    } catch(err){console.warn('Local state could not be persisted:',err);}
  }
  function validImport(obj){
    if(!obj || typeof obj!=='object' || obj.version!==2 || !Object.hasOwn(THEMES,obj.theme)) throw Error('version/theme invalid');
    if(!['es','en','fr','pt'].includes(obj.locale) || !Array.isArray(obj.roots) || obj.roots.length>100 || !Array.isArray(obj.files) || obj.files.length>120) throw Error('shape invalid');
    if(!obj.roots.every(x => x && typeof x.id==='string' && typeof x.name==='string' && x.name.length<200 && knownStatus.has(x.status))) throw Error('roots invalid');
    if(!obj.files.every(f=>f && typeof f.name==='string' && typeof f.data==='string' && f.data.startsWith('data:') && f.data.length<1500000)) throw Error('file invalid');
    const d=defaults();
    return {...d,...obj,page:knownPages.includes(obj.page)?obj.page:'chat',mode:MODES.includes(obj.mode)?obj.mode:'fast',model:knownModels.includes(obj.model)?obj.model:'MiniMax M3',messages:Array.isArray(obj.messages)?obj.messages.slice(-200).filter(x=>x && typeof x.text==='string' && typeof x.role==='string'):[],draft:typeof obj.draft==='string'?obj.draft.slice(0,20000):'',tools:{...d.tools,...obj.tools},settings:{...d.settings,...obj.settings},attachments:Array.isArray(obj.attachments)?obj.attachments:[],files:obj.files.filter(f=>!f.volatile)};
  }
  try{const raw=localStorage.getItem(KEY);if(raw)state=validImport(JSON.parse(raw));}catch(err){console.warn('State was invalid; safe defaults loaded.',err);state=defaults();}
  function local(action,payload={}) {bus(action,payload).catch(()=>{});}
  function statusBadge(status){return `<span class="tag-status ${esc(status)}"><span class="signal"></span>${esc(t(status))}</span>`;}
  function nav(){
    const navs=[['chat','message'],['files','folder'],['wall','grid'],['settings','settings']];
    const markup = navs.map(([id,icon])=>`<button type="button" class="nav-button ${state.page===id?'active':''}" data-nav="${id}" aria-current="${state.page===id?'page':'false'}">${ic(icon)}<span>${esc(t(id))}</span></button>`).join('');
    $('#sideNav').innerHTML=markup;
    $('#bottomNav').innerHTML=markup;
  }
  function drawInspector(){
    const last=window.__YAIWES_LAST_ACTION__||'—';
    $('#inspector').innerHTML=`<div><div class="eyebrow">${esc(t('design_lock'))}</div><h3>${esc(THEMES[state.theme].label)}</h3><p>${esc(THEMES[state.theme].category)}</p><div class="micro-row"><span>${esc(t('meta_label'))}</span><strong>Little</strong></div><div class="micro-row"><span>${esc(t('model'))}</span><strong>${esc(state.model)}</strong></div><div class="micro-row"><span>${esc(t('mode'))}</span><strong>${esc(t(state.mode))}</strong></div><div class="micro-row"><span>${esc(t('remote_label'))}</span><span class="code-chip">${bridgeReady()?'BRIDGE OK':'FAIL-CLOSED'}</span></div><div class="inspect-divider"></div><div class="eyebrow">${esc(t('status_legend'))}</div><p style="margin-top:9px">${esc(t('status_help'))}</p><div class="status-key"><span class="signal progress"></span>${esc(t('progress'))}</div><div class="status-key"><span class="signal enabled"></span>${esc(t('enabled'))}</div><div class="status-key"><span class="signal warning"></span>${esc(t('warning'))}</div><div class="inspect-divider"></div><div class="eyebrow">${esc(t('action_log'))}</div><div class="inspect-log" id="actionLog">${esc(last)}</div><div class="inspect-divider"></div><p>${ic('shield')} ${esc(t('how_works'))}</p></div>`;
  }
  function footer(){return `<div class="footer-line">FROMTED × YAIWES · v0.2.0 · ${esc(t('design_review'))}</div>`;}
  function intro(kicker,title,desc,actions=''){return `<section class="page-intro"><div class="header-line"><span class="mini-kicker">${esc(kicker)}</span>${actions}</div><h1 class="page-title">${esc(title)}</h1><p class="lead">${esc(desc)}</p></section>`;}
  function chatPage(){
    const bubbles = state.messages.length ? state.messages.map(m=>`<article class="chat-bubble ${m.role==='user'?'user':''}"><div class="bubble-meta">${m.role==='user'?'TÚ':esc(state.model)} · ${esc(m.time||'')}</div><p>${esc(m.text)}</p></article>`).join('') : `<div class="empty-message">${ic('message')}<strong>${esc(t('empty_chat'))}</strong><span>${esc(t('no_invent'))}</span></div>`;
    return `${intro('YAIWES / '+t('chat'),t('hello'),t('tagline'),'<span class="pill soft">'+ic('spark')+' '+esc(t('meta_label'))+': Little</span>')}
      <div class="chat-main"><section class="chat-hero"><span class="hero-overline">◈ FROMTED / CHAT</span><h2>${esc(t('chat_intro'))}</h2><p>${esc(t('how_works'))}</p></section>
      <div class="header-tools"><span class="section-label" style="margin:0">${esc(t('conversation'))}</span><button type="button" class="btn btn-ghost" data-action="chat.close">${ic('plus')}${esc(t('new_chat'))}</button></div>
      <div class="chat-messages" id="chatMessages">${bubbles}</div>
      <div class="surface-card" style="padding:12px 15px"><div class="header-line"><label class="select-wrap"><span class="field-label" style="margin:0">${esc(t('model'))}</span><select class="input-control" id="modelSelect" style="max-width:160px">${knownModels.map(x=>`<option value="${esc(x)}" ${state.model===x?'selected':''}>${esc(x)}</option>`).join('')}</select></label><button type="button" class="btn btn-secondary" data-action="mode.open">${ic('spark')}${esc(t(state.mode))}${ic('down')}</button></div></div>
      <form class="composer" id="chatForm"><label for="composeText" class="field-label">${esc(t('chat'))} / ${esc(t('type_message'))}</label><textarea id="composeText" maxlength="20000" placeholder="${esc(t('type_message'))}" autocomplete="off">${esc(state.draft)}</textarea>
      ${state.attachments.length?`<div class="attachments">${state.attachments.map(id=>{const f=state.files.find(x=>x.id===id);return f?`<span class="attachment-chip">${ic('file')}${esc(f.name)}<button type="button" data-remove-attach="${esc(id)}" aria-label="${esc(t('delete'))} ${esc(f.name)}">×</button></span>`:''}).join('')}</div>`:''}
      <div class="compose-bottom"><div class="compose-tools"><button type="button" data-action="chat.attach" class="tool-btn" title="${esc(t('attach'))}">${ic('attach')}<span>${esc(t('attach'))}</span></button>${[['document','doc'],['website','globe'],['image','photo']].map(([k,ico])=>`<button type="button" data-tool="${k}" class="tool-btn ${state.tools[k]?'on':''}" aria-pressed="${state.tools[k]}" title="${esc(t(k))}">${ic(ico)}<span>${esc(t(k))}</span></button>`).join('')}</div><button type="submit" class="btn btn-primary send-btn" id="sendButton" ${sending?'disabled':''}>${ic('send')}<span>${esc(t('send'))}</span></button></div></form>
      <div class="chat-notice">${ic('shield')}<span>${esc(bridgeReady()?t('connected'):t('offline_note'))}</span></div></div>${footer()}`;
  }
  function filesPage(){
    const entries = state.files.filter(f=>state.filter==='local'||f.pinned).filter(f=>f.name.toLowerCase().includes(state.search.toLowerCase()));
    const rows = entries.map(f=>`<div class="file-row" data-file-id="${esc(f.id)}"><div class="file-icon">${ic('file')}</div><div class="file-data"><div class="name">${esc(f.name)}</div><div class="sub">${esc(formatBytes(f.size))} · ${esc(f.volatile?t('file_session'):t('file_saved'))}</div></div><div class="file-actions"><button title="${esc(t('pin'))}" aria-label="${esc(t('pin'))} ${esc(f.name)}" data-pin="${esc(f.id)}" class="${f.pinned?'on':''}">${ic('pin')}</button><button class="download-text" title="${esc(t('download'))}" aria-label="${esc(t('download'))} ${esc(f.name)}" data-download="${esc(f.id)}">${ic('download')}<span>${esc(t('download'))}</span></button><button title="${esc(t('delete'))}" aria-label="${esc(t('delete'))} ${esc(f.name)}" data-delete="${esc(f.id)}">${ic('trash')}</button></div></div>`).join('');
    return `${intro('YAIWES / '+t('files'),t('gallery'),t('file_intro'),`<button type="button" class="btn btn-primary" data-action="files.add">${ic('plus')}${esc(t('add_files'))}</button>`)}<div class="file-toolbar"><div class="search-wrap">${ic('search')}<input type="search" id="fileSearch" class="search-input" placeholder="${esc(t('search_files'))}" value="${esc(state.search)}" autocomplete="off"></div><span class="pill">${state.files.length} ${esc(t('files'))}</span></div><div class="segmented" role="tablist"><button role="tab" type="button" class="tab-button ${state.filter==='local'?'active':''}" data-filter="local" aria-selected="${state.filter==='local'}">${esc(t('local'))}</button><button role="tab" type="button" class="tab-button ${state.filter==='pinned'?'active':''}" data-filter="pinned" aria-selected="${state.filter==='pinned'}">${esc(t('pinned'))} · ${state.files.filter(x=>x.pinned).length}</button></div><div style="margin-top:17px" id="fileRows">${rows||`<div class="empty-state">${ic('folder')}<p>${esc(state.files.length?t('empty_search'):t('empty_files'))}</p><button type="button" class="btn btn-secondary" data-action="files.add">${esc(t('add_files'))}</button></div>`}</div><p class="muted-note">${esc(t('file_persist_note'))}</p>${footer()}`;
  }
  function wallPage(){
    const cards=state.roots.map((r,i)=>`<button type="button" class="root-card" data-root="${esc(r.id)}" aria-label="${esc(t('edit'))}: ${esc(r.name)}"><div class="root-bottom"><span class="root-index">ROOT · ${String(i+1).padStart(2,'0')}</span>${statusBadge(r.status)}</div><h3>${ic('folder')} ${esc(r.name)}</h3><small>${esc(r.description||r.note||'—')}</small><div class="root-bottom"><span class="muted-note">${esc(t('edit'))}</span>${ic('chevron')}</div></button>`).join('');
    return `${intro('YAIWES / '+t('wall'),t('workflow'),t('wall_intro'),`<button type="button" class="btn btn-primary" data-action="wall.root.add">${ic('plus')}${esc(t('add_root'))}</button>`)}<div class="section-label">${esc(t('how_works'))}</div><div class="flow-track" aria-label="Flujo de trabajo">${['INPUT','MISIÓN','KERNEL','WORDFLOW','EVIDENCIA','OUT'].map((x,i)=>`${i?'<i>→</i>':''}<span>${x}</span>`).join('')}</div><div class="header-line" style="margin:9px 0 13px"><h2 class="section-label" style="margin:0">${esc(t('roots'))}</h2><span class="pill">${state.roots.length} ROOTS</span></div><div class="wall-grid" id="wallGrid">${cards||`<div class="empty-state">${esc(t('roots'))}: 0</div>`}</div>${footer()}`;
  }
  function settingsPage(){
    const grid=Object.entries(THEMES).map(([id,meta])=>`<button type="button" class="theme-option ${state.theme===id?'selected':''}" data-theme="${id}" aria-pressed="${state.theme===id}"><div class="theme-swatch" style="background:${meta.bg}"><span style="background:${meta.card}"></span><span style="background:${meta.accent};width:21px"></span><span style="background:${meta.swatch};width:13px"></span></div><div class="theme-meta"><strong>${esc(meta.label)}</strong>${state.theme===id?ic('check'):''}</div><small>${esc(meta.category)}</small></button>`).join('');
    return `${intro('YAIWES / '+t('settings'),t('appearance'),t('choose_visual'),'<span class="pill soft">'+ic('shield')+' DESIGN LOCK</span>')}<div class="section-label">${esc(t('themes'))}</div><div class="themes-grid" id="themeGrid">${grid}</div><p class="muted-note">${esc(t('theme_intro'))}</p><div class="section-label">${esc(t('status_legend'))}</div><div class="surface-card"><p class="card-desc" style="margin:0 0 13px">${esc(t('status_help'))}</p><div class="tiny-row">${statusBadge('progress')}${statusBadge('enabled')}${statusBadge('warning')}</div></div><div class="section-label">${esc(t('preferences'))}</div><div class="surface-card"><div class="setting-row"><div><strong>${esc(t('language'))}</strong><small>es · en · fr · pt</small></div><select id="localeSelect" class="input-control" aria-label="${esc(t('language'))}">${[['es','Español'],['en','English'],['fr','Français'],['pt','Português']].map(([k,label])=>`<option value="${k}" ${state.locale===k?'selected':''}>${label}</option>`).join('')}</select></div>${[['motion','motion_desc'],['hints','hints_desc']].map(([id,desc])=>`<div class="setting-row"><div><strong>${esc(t(id))}</strong><small>${esc(t(desc))}</small></div><button type="button" class="switch" role="switch" data-setting="${id}" aria-label="${esc(t(id))}" aria-checked="${state.settings[id]}"></button></div>`).join('')}</div><div class="section-label">${esc(t('storage'))}</div><div class="tiny-row"><button type="button" class="btn btn-secondary" data-action="state.export">${ic('download')}${esc(t('export'))} JSON</button><button type="button" class="btn btn-secondary" data-action="state.import">${ic('folder')}${esc(t('import'))}</button><button type="button" class="btn btn-ghost" data-action="state.reset">${ic('trash')}${esc(t('reset'))}</button></div>${footer()}`;
  }
  function refresh(){
    document.documentElement.dataset.theme=state.theme;
    document.documentElement.dataset.motion=state.settings.motion?'on':'off';
    document.documentElement.lang=state.locale;
    document.querySelector('meta[name="theme-color"]').content=THEMES[state.theme].bg;
    $('#sidebarThemeName').textContent=THEMES[state.theme].label+(state.theme==='little'?' · Principal':'');
    $('#pageLocation').textContent=t(state.page);
    $('[data-i18n="not_connected"]').textContent=bridgeReady()?t('connected'):t('not_connected');
    $('#topBridgeStatus .signal').className='signal '+(bridgeReady()?'active':'neutral');
    document.querySelectorAll('[data-i18n]').forEach(el=>{if(el.dataset.i18n!=='not_connected')el.textContent=t(el.dataset.i18n);});
    nav();
    $('#mainContent').innerHTML=state.page==='chat'?chatPage():state.page==='files'?filesPage():state.page==='wall'?wallPage():settingsPage();
    drawInspector();
  }
  function go(page){if(!knownPages.includes(page))return;state.page=page;local('ui.navigate',{page});persist();refresh();}
  function theme(id){if(!Object.hasOwn(THEMES,id))return;state.theme=id;local('theme.select',{theme:id});persist();refresh();toast(THEMES[id].label+' · '+t('updated'),'success');}
  function toast(text,type='success'){
    const node=document.createElement('div');node.className='toast '+type;node.textContent=text;$('#toastArea').append(node);
    while($('#toastArea').children.length>3)$('#toastArea').firstChild.remove();
    setTimeout(()=>node.remove(),4000);
  }
  function formatBytes(bytes){if(bytes<1024)return bytes+' B';if(bytes<1024**2)return (bytes/1024).toFixed(1)+' KB';return (bytes/1024**2).toFixed(1)+' MB';}
  function filePicker(purpose='files') {uploadPurpose=purpose;$('#filePicker').value='';$('#filePicker').click();}
  function fileAsDataURL(file) {return new Promise((resolve,reject)=>{const r=new FileReader();r.onload=()=>resolve(r.result);r.onerror=()=>reject(Error('read failed'));r.readAsDataURL(file);});}
  async function addFiles(fileList){
    let count=0;
    for(const file of [...fileList].slice(0,20)){
      if(!file || !file.name)continue;
      const id='f-'+makeId();
      let data='',volatile=false;
      try{if(file.size<=1024*1024)data=await fileAsDataURL(file);else {volatile=true;volatileUrls.set(id,URL.createObjectURL(file));}}
      catch(err){toast(t('invalid_file')+' '+file.name,'error');continue;}
      state.files.unshift({id,name:file.name,mime:file.type||'application/octet-stream',size:file.size,data,volatile,pinned:false});
      if(uploadPurpose==='attach')state.attachments.push(id);
      local('files.add',{id,name:file.name,size:file.size,volatile});count++;
    }
    if(count){persist();refresh();toast(`${count} · ${t('file_added')}`,'success');}
  }
  function getFile(id){return state.files.find(f=>f.id===id);}
  function download(file){
    let href=file.volatile?volatileUrls.get(file.id):file.data;
    if(!href || !(href.startsWith('blob:')||href.startsWith('data:'))) {toast(t('invalid_file'),'error');return;}
    const a=document.createElement('a');a.href=href;a.download=file.name;document.body.append(a);a.click();a.remove();local('files.download',{id:file.id,name:file.name});
  }
  function triggerDownload(data,filename,type='application/json'){
    const url=URL.createObjectURL(new Blob([data],{type}));const a=document.createElement('a');a.href=url;a.download=filename;document.body.append(a);a.click();a.remove();setTimeout(()=>URL.revokeObjectURL(url),1000);
  }
  function exportState(){
    const output={...state,files:state.files.filter(f=>!f.volatile)};
    triggerDownload(JSON.stringify(output,null,2),'YAIWES-PERFIL-ESTADO-v02.json');local('state.export',{count:output.roots.length});toast(t('export')+' JSON','success');
  }
  function exportChat(){triggerDownload(JSON.stringify({model:state.model,mode:state.mode,messages:state.messages},null,2),'YAIWES-CHAT.json');local('chat.export',{messages:state.messages.length});toast(t('export')+' Chat JSON','success');}
  async function send(){
    if(sending)return;
    const text=state.draft.trim();if(!text){$('#composeText')?.focus();return;}
    const attachments=state.attachments.map(getFile).filter(Boolean);
    if(attachments.some(f=>f.volatile)){toast(t('file_session')+': bridge de archivos grande no implementado','error');return;}
    sending=true;const btn=$('#sendButton');if(btn)btn.disabled=true;
    const payload={message:text,model:state.model,mode:state.mode,tools:{...state.tools},attachments:attachments.map(({name,mime,size,data})=>({name,mime,size,dataUrl:data}))};
    const result=await bus('chat.send',payload,true);
    sending=false;
    if(!result.ok){refresh();toast(t('message_blocked')+' ['+result.code+']','error');return;}
    state.messages.push({id:'m'+makeId(),role:'user',text,time:new Date().toLocaleTimeString(state.locale,{hour:'2-digit',minute:'2-digit'})});
    const remote=result.result;
    const reply=typeof remote.reply==='string'?remote.reply:typeof remote.message==='string'?remote.message:null;
    if(reply)state.messages.push({id:'m'+makeId(),role:'assistant',text:reply,time:new Date().toLocaleTimeString(state.locale,{hour:'2-digit',minute:'2-digit'})});
    state.draft='';state.attachments=[];persist();refresh();toast(t('sent_ok'),'success');
    $('#chatMessages')?.scrollTo(0,999999);
  }
  function openSheet(kind,rootId=null){
    sheetKind=kind;const dlg=$('#sheet');
    const header=(title,sub)=>`<div class="sheet-header"><div><span class="eyebrow">FROMTED / YAIWES</span><h2 id="sheetTitle">${esc(title)}</h2><p>${esc(sub)}</p></div><button type="button" class="sheet-close" data-close aria-label="${esc(t('close'))}">${ic('x')}</button></div>`;
    let content='';
    if(kind==='mode'){
      modeDraft=state.mode;
      content=`${header(t('mode'),t('choose_mode'))}${MODES.map((m,i)=>`<button type="button" class="mode-option ${modeDraft===m?'selected':''}" data-mode="${m}" aria-pressed="${modeDraft===m}">${ic(['clock','spark','grid'][i])}<span style="flex:1"><strong>${esc(t(m))}</strong><small>${esc(t(m+'_desc'))}</small></span>${modeDraft===m?`<span class="check">${ic('check')}</span>`:''}</button>`).join('')}<div class="sheet-footer"><button type="button" class="btn btn-secondary" data-close>${esc(t('cancel'))}</button><button type="button" class="btn btn-primary" data-confirm-mode>${esc(t('apply'))}</button></div>`;
    } else if(kind==='root'){
      const r=state.roots.find(x=>x.id===rootId);if(!r)return;
      content=`${header(r.name,t('local_only'))}<div class="section-label">${esc(t('status_legend'))}</div><div class="status-selector">${['pending','progress','enabled','warning'].map(x=>`<button type="button" class="status-button ${r.status===x?'selected':''}" data-status="${x}"><span class="signal ${x}"></span>${esc(t(x))}</button>`).join('')}</div><div class="section-label">${esc(t('note'))}</div><textarea class="textarea-control" id="rootNote" placeholder="${esc(t('no_notes'))}">${esc(r.note)}</textarea><div class="sheet-footer"><button type="button" class="btn btn-secondary" data-close>${esc(t('cancel'))}</button><button type="button" class="btn btn-primary" data-save-root="${esc(r.id)}">${esc(t('save'))}</button></div>`;
    } else if(kind==='new-root'){
      content=`${header(t('add_root'),t('local_only'))}<label class="field-label" for="rootName">${esc(t('root_name'))}</label><input class="input-control" id="rootName" maxlength="150" autocomplete="off" placeholder="nuevo-proyecto/"><label class="field-label" for="rootDesc" style="margin-top:14px">${esc(t('note'))}</label><textarea class="textarea-control" id="rootDesc"></textarea><div class="sheet-footer"><button type="button" class="btn btn-secondary" data-close>${esc(t('cancel'))}</button><button type="button" class="btn btn-primary" data-add-root>${esc(t('save'))}</button></div>`;
    } else if(kind==='reset'){
      content=`${header(t('reset_confirm'),t('reset_explain'))}<div class="sheet-footer"><button type="button" class="btn btn-secondary" data-close>${esc(t('cancel'))}</button><button type="button" class="btn btn-primary" data-reset-confirm>${esc(t('reset'))}</button></div>`;
    }
    $('#sheetInner').innerHTML=`<div class="sheet-wrap">${content}</div>`;
    dlg.showModal();
  }
  function closeSheet(){const dlg=$('#sheet');if(dlg.open)dlg.close();sheetKind=null;}
  function notifyAction(event){
    window.__YAIWES_LAST_ACTION__=event.detail.actionId;
    const el=$('#actionLog');if(el)el.textContent=event.detail.actionId;
  }
  window.addEventListener('yaiwes:ui-action',notifyAction);
  document.addEventListener('click',async e=>{
    const button=e.target.closest('button');if(!button)return;
    const {nav:page,theme:id,action,tool,filter,pin,download:downloadId,delete:deleteId,root,setting,mode,status,removeAttach}=button.dataset;
    if(page){go(page);return;}
    if(id){theme(id);return;}
    if(action){
      if(action==='mode.open'){openSheet('mode');return;}
      if(action==='chat.export'){exportChat();return;}
      if(action==='chat.close'){state.messages=[];state.attachments=[];state.draft='';persist();refresh();local('chat.close',{});toast(t('new_chat'),'success');return;}
      if(action==='chat.attach'){local('chat.attach',{});filePicker('attach');return;}
      if(action==='files.add'){filePicker('files');return;}
      if(action==='wall.root.add'){openSheet('new-root');return;}
      if(action==='state.export'){exportState();return;}
      if(action==='state.import'){$('#restorePicker').value='';$('#restorePicker').click();return;}
      if(action==='state.reset'){openSheet('reset');return;}
    }
    if(tool){state.tools[tool]=!state.tools[tool];local('tool.'+tool+'.toggle',{enabled:state.tools[tool]});persist();refresh();return;}
    if(filter){state.filter=filter;persist();refresh();return;}
    if(pin){const f=getFile(pin);if(f){f.pinned=!f.pinned;local('files.pin',{id:pin,pinned:f.pinned});persist();refresh();}return;}
    if(downloadId){const f=getFile(downloadId);if(f)download(f);return;}
    if(deleteId){const f=getFile(deleteId);if(f){if(f.volatile&&volatileUrls.has(f.id)){URL.revokeObjectURL(volatileUrls.get(f.id));volatileUrls.delete(f.id);}state.files=state.files.filter(x=>x.id!==f.id);state.attachments=state.attachments.filter(x=>x!==f.id);persist();refresh();toast(t('delete'),'success');}return;}
    if(root){state.selectedRoot=root;persist();openSheet('root',root);return;}
    if(setting){state.settings[setting]=!state.settings[setting];local('ui.settings',{key:setting,value:state.settings[setting]});persist();refresh();return;}
    if(removeAttach){state.attachments=state.attachments.filter(x=>x!==removeAttach);persist();refresh();return;}
    if(mode){modeDraft=mode;document.querySelectorAll('[data-mode]').forEach(x=>{x.classList.toggle('selected',x.dataset.mode===mode);x.setAttribute('aria-pressed',String(x.dataset.mode===mode));const prior=x.querySelector('.check');if(prior)prior.remove();if(x.dataset.mode===mode)x.insertAdjacentHTML('beforeend',`<span class="check">${ic('check')}</span>`);});return;}
    if(status&&sheetKind==='root'){document.querySelectorAll('[data-status]').forEach(x=>x.classList.toggle('selected',x.dataset.status===status));button.dataset.selected=status;return;}
    if(button.hasAttribute('data-close')){closeSheet();return;}
    if(button.hasAttribute('data-confirm-mode')){state.mode=modeDraft;local('mode.select',{mode:modeDraft});local('mode.thinking.toggle',{enabled:modeDraft==='think'});closeSheet();persist();refresh();toast(t('mode')+': '+t(state.mode),'success');return;}
    if(button.hasAttribute('data-save-root')){
      const r=state.roots.find(x=>x.id===button.dataset.saveRoot);if(r){const selected=$('#sheet .status-button.selected');if(selected)r.status=selected.dataset.status;r.note=$('#rootNote').value.slice(0,5000);local('wall.status.set',{id:r.id,status:r.status});local('wall.note.set',{id:r.id,note:r.note});persist();closeSheet();refresh();toast(t('saved'),'success');}return;
    }
    if(button.hasAttribute('data-add-root')){
      const name=$('#rootName').value.trim().slice(0,150);if(!name){$('#rootName').focus();return;}
      state.roots.push({id:'r-'+makeId(),name,description:$('#rootDesc').value.trim().slice(0,300),status:'pending',note:''});local('wall.root.add',{name});persist();closeSheet();refresh();toast(t('saved'),'success');return;
    }
    if(button.hasAttribute('data-reset-confirm')){volatileUrls.forEach(u=>URL.revokeObjectURL(u));volatileUrls.clear();state=defaults();local('state.reset',{});persist();closeSheet();refresh();toast(t('reset'),'success');return;}
  });
  $('#sheet').addEventListener('click',e=>{if(e.target===$('#sheet'))closeSheet();});
  document.addEventListener('input',e=>{
    if(e.target.id==='composeText'){state.draft=e.target.value;persist();}
    if(e.target.id==='fileSearch'){state.search=e.target.value;local('files.search',{query:state.search});persist();const entries=state.files.filter(f=>(state.filter==='local'||f.pinned)&&f.name.toLowerCase().includes(state.search.toLowerCase()));/* Keep input focus while updating list. */
      const list=$('#fileRows');if(list){const old=document.activeElement;const pos=e.target.selectionStart;const html=filesPage();const temp=document.createElement('div');temp.innerHTML=html;list.innerHTML=temp.querySelector('#fileRows').innerHTML;}}
  });
  document.addEventListener('change',e=>{
    if(e.target.id==='modelSelect'){state.model=e.target.value;local('model.select',{model:state.model});persist();drawInspector();return;}
    if(e.target.id==='localeSelect'){state.locale=e.target.value;local('locale.select',{locale:state.locale});persist();refresh();return;}
  });
  document.addEventListener('submit',e=>{if(e.target.id==='chatForm'){e.preventDefault();send();}});
  $('#filePicker').addEventListener('change',e=>{addFiles(e.target.files);});
  $('#restorePicker').addEventListener('change',async e=>{const f=e.target.files?.[0];if(!f)return;try{if(f.size>3*1024*1024)throw Error('too large');const parsed=validImport(JSON.parse(await f.text()));volatileUrls.forEach(u=>URL.revokeObjectURL(u));volatileUrls.clear();state=parsed;local('state.import',{version:2});persist();refresh();toast(t('import_ok'),'success');}catch(err){toast(t('invalid_file')+' '+err.message,'error');}});
  document.addEventListener('keydown',e=>{if((e.ctrlKey||e.metaKey)&&e.key.toLowerCase()==='k'){e.preventDefault();go('files');$('#fileSearch')?.focus();}if((e.ctrlKey||e.metaKey)&&e.key==='Enter'&&state.page==='chat'){e.preventDefault();send();}});
  refresh();
  window.YAIWES_UI_DEBUG = Object.freeze({getState:()=>structuredClone(state),themes:()=>Object.keys(THEMES),version:'0.2.0'});
})();
