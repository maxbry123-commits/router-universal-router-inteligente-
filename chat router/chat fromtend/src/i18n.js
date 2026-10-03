import { CONTROL_LABELS } from "./config.js";

export const LANGUAGES = ["es", "en", "fr", "pt"];

export const STRINGS = {
  es: {
    chatAria: "Chat", controlsAria: "Modelos y modos", selectorsAria: "Selectores configurables", togglesAria: "Ocho controles configurables", messagesAria: "Mensajes",
    defaultDescription: "Elige un modelo y configura las acciones para conectar tu backend.", slotMode: "Nivel {number}", slotSelector: "Selector {number}", slotToggle: "Control {number}", slotAction: "Función {number}",
    emptyTitle: "¿Qué vamos a construir hoy?", placeholder: "Escribe un mensaje…", messageAria: "Mensaje", fileInput: "Elegir archivos", closeWindow: "Cerrar",
    stopRecording: "Detener {name}", on: "encendido", off: "apagado", toggleConfirmed: "{name}: {state} confirmado.", backendConfirmed: "{name}: confirmado por el backend.",
    selectedRemote: "{name} confirmado", selectedLocal: "{name} elegido localmente; el backend se comprobará al enviar.",
    modelRequired: "Selecciona un modelo antes de enviar.", backendSending: "Enviando al backend…", backendReceived: "Respuesta recibida del backend.",
    modelsEmpty: "No hay modelos configurados. Añádelos en Configuración o conecta el catálogo del backend.", modelsRefresh: "Actualizar desde backend", modelsUpdated: "Catálogo actualizado desde el backend.",
    selectorEmpty: "Configura las opciones de esta ventana en Configuración.", backendLoading: "Consultando el backend…", resourcesEmpty: "El backend no devolvió elementos.",
    fileLocal: "local", fileUploaded: "subido", uploadConfirmed: "{name}: subida confirmada.", uploadLocal: "{name}: {error}; sigue solo en esta pestaña.",
    voiceUnavailable: "VOICE_UNAVAILABLE: el navegador no permite grabar.", recording: "Grabando audio localmente…", audioConfirmed: "Audio confirmado por el backend.",
    watchdogConfirmed: "Watchdog: confirmado por el backend.", exportStarted: "Exportación iniciada en este navegador.",
    settingsAria: "Configuración del chat", settingsTitle: "Configuración", settingsIntro: "Edita nombres, descripciones y actionId. Nunca pegues claves, contraseñas ni código ejecutable: el bridge seguro implementa los comandos.",
    chatTitle: "Título del chat", chatDescription: "Descripción del chat", theme: "Tema", language: "Idioma", backendConnections: "Conexiones de backend",
    modelsActionId: "Cargar catálogo de modelos", modelActionId: "Seleccionar modelo", sendActionId: "Enviar mensaje", attachActionId: "Subir adjunto", voiceActionId: "Enviar voz", watchdogActionId: "Watchdog", skillsActionId: "Listar habilidades", connectorsActionId: "Listar conectores",
    namesAndDescriptions: "Nombres y descripciones de botones", name: "Nombre", description: "Descripción", actionId: "Comando de acción (actionId)", modelsHeading: "Modelos",
    modelsInfo: "Un modelo por línea: id | nombre. Si tienes catálogo remoto, configura también su comando.", modelsField: "Modelos (id | nombre)",
    selectorGroup: "5 selectores · una ventana por selector", optionsField: "Opciones: id | nombre | actionId (una por línea)", modesGroup: "8 niveles de razonamiento", togglesGroup: "8 controles de encendido", actionsGroup: "12 funciones del menú +",
    modelsFormat: "Cada modelo necesita id | nombre.", missingNames: "Completa id y nombre en los modelos y opciones.", settingsSaved: "Configuración guardada localmente. Los comandos remotos requieren un bridge real.", settingsTemporary: "Configuración activa solo en esta pestaña: el navegador bloqueó el almacenamiento local.",
    configure: "Configurar", back: "Volver al chat", save: "Guardar configuración", close: "Nuevo chat", export: "Exportar chat",
    models: "Elegir modelo", modes: "Razonamiento", functions: "+ 12 funciones", attach: "Adjuntar", voice: "Voz", watchdog: "Watchdog", send: "Enviar ↗", skills: "Habilidades", connectors: "Conectores",
  },
  en: {
    chatAria: "Chat", controlsAria: "Models and modes", selectorsAria: "Configurable selectors", togglesAria: "Eight configurable controls", messagesAria: "Messages",
    defaultDescription: "Choose a model and configure actions to connect your backend.", slotMode: "Level {number}", slotSelector: "Selector {number}", slotToggle: "Control {number}", slotAction: "Function {number}",
    emptyTitle: "What shall we build today?", placeholder: "Write a message…", messageAria: "Message", fileInput: "Choose files", closeWindow: "Close",
    stopRecording: "Stop {name}", on: "on", off: "off", toggleConfirmed: "{name}: {state} confirmed.", backendConfirmed: "{name}: confirmed by the backend.",
    selectedRemote: "{name} confirmed", selectedLocal: "{name} selected locally; the backend will be checked when sending.",
    modelRequired: "Select a model before sending.", backendSending: "Sending to backend…", backendReceived: "Reply received from backend.",
    modelsEmpty: "No models configured. Add them in Settings or connect the backend catalog.", modelsRefresh: "Refresh from backend", modelsUpdated: "Catalog updated from backend.",
    selectorEmpty: "Configure this window's options in Settings.", backendLoading: "Contacting backend…", resourcesEmpty: "The backend returned no items.",
    fileLocal: "local", fileUploaded: "uploaded", uploadConfirmed: "{name}: upload confirmed.", uploadLocal: "{name}: {error}; remains in this tab only.",
    voiceUnavailable: "VOICE_UNAVAILABLE: this browser cannot record.", recording: "Recording audio locally…", audioConfirmed: "Audio confirmed by backend.",
    watchdogConfirmed: "Watchdog: confirmed by backend.", exportStarted: "Export started in this browser.",
    settingsAria: "Chat settings", settingsTitle: "Settings", settingsIntro: "Edit names, descriptions and actionId values. Never paste keys, passwords or executable code: the secure bridge implements the commands.",
    chatTitle: "Chat title", chatDescription: "Chat description", theme: "Theme", language: "Language", backendConnections: "Backend connections",
    modelsActionId: "Load model catalog", modelActionId: "Select model", sendActionId: "Send message", attachActionId: "Upload attachment", voiceActionId: "Send voice", watchdogActionId: "Watchdog", skillsActionId: "List skills", connectorsActionId: "List connectors",
    namesAndDescriptions: "Button names and descriptions", name: "Name", description: "Description", actionId: "Action command (actionId)", modelsHeading: "Models",
    modelsInfo: "One model per line: id | name. If you have a remote catalog, configure its command too.", modelsField: "Models (id | name)",
    selectorGroup: "5 selectors · one window per selector", optionsField: "Options: id | name | actionId (one per line)", modesGroup: "8 reasoning levels", togglesGroup: "8 power controls", actionsGroup: "12 functions in the + menu",
    modelsFormat: "Each model needs id | name.", missingNames: "Complete id and name for models and options.", settingsSaved: "Settings saved locally. Remote commands require a real bridge.", settingsTemporary: "Settings are active in this tab only: the browser blocked local storage.",
    configure: "Settings", back: "Back to chat", save: "Save settings", close: "New chat", export: "Export chat",
    models: "Choose model", modes: "Reasoning", functions: "+ 12 functions", attach: "Attach", voice: "Voice", watchdog: "Watchdog", send: "Send ↗", skills: "Skills", connectors: "Connectors",
  },
  fr: {
    chatAria: "Chat", controlsAria: "Modèles et modes", selectorsAria: "Sélecteurs configurables", togglesAria: "Huit commandes configurables", messagesAria: "Messages",
    defaultDescription: "Choisissez un modèle et configurez les actions pour connecter votre backend.", slotMode: "Niveau {number}", slotSelector: "Sélecteur {number}", slotToggle: "Commande {number}", slotAction: "Fonction {number}",
    emptyTitle: "Qu'allons-nous construire aujourd'hui ?", placeholder: "Écrivez un message…", messageAria: "Message", fileInput: "Choisir des fichiers", closeWindow: "Fermer",
    stopRecording: "Arrêter {name}", on: "activé", off: "désactivé", toggleConfirmed: "{name} : état {state} confirmé.", backendConfirmed: "{name} : confirmé par le backend.",
    selectedRemote: "{name} confirmé", selectedLocal: "{name} sélectionné localement ; le backend sera vérifié lors de l'envoi.",
    modelRequired: "Sélectionnez un modèle avant l'envoi.", backendSending: "Envoi au backend…", backendReceived: "Réponse reçue du backend.",
    modelsEmpty: "Aucun modèle configuré. Ajoutez-en dans les réglages ou connectez le catalogue du backend.", modelsRefresh: "Actualiser depuis le backend", modelsUpdated: "Catalogue mis à jour depuis le backend.",
    selectorEmpty: "Configurez les options de cette fenêtre dans les réglages.", backendLoading: "Consultation du backend…", resourcesEmpty: "Le backend n'a renvoyé aucun élément.",
    fileLocal: "local", fileUploaded: "téléversé", uploadConfirmed: "{name} : téléversement confirmé.", uploadLocal: "{name} : {error} ; reste uniquement dans cet onglet.",
    voiceUnavailable: "VOICE_UNAVAILABLE : ce navigateur ne peut pas enregistrer.", recording: "Enregistrement audio local…", audioConfirmed: "Audio confirmé par le backend.",
    watchdogConfirmed: "Watchdog : confirmé par le backend.", exportStarted: "Exportation lancée dans ce navigateur.",
    settingsAria: "Paramètres du chat", settingsTitle: "Paramètres", settingsIntro: "Modifiez les noms, descriptions et actionId. Ne collez jamais de clés, mots de passe ou code exécutable : le bridge sécurisé implémente les commandes.",
    chatTitle: "Titre du chat", chatDescription: "Description du chat", theme: "Thème", language: "Langue", backendConnections: "Connexions backend",
    modelsActionId: "Charger le catalogue des modèles", modelActionId: "Sélectionner un modèle", sendActionId: "Envoyer un message", attachActionId: "Téléverser une pièce jointe", voiceActionId: "Envoyer la voix", watchdogActionId: "Watchdog", skillsActionId: "Lister les compétences", connectorsActionId: "Lister les connecteurs",
    namesAndDescriptions: "Noms et descriptions des boutons", name: "Nom", description: "Description", actionId: "Commande d'action (actionId)", modelsHeading: "Modèles",
    modelsInfo: "Un modèle par ligne : id | nom. Si vous avez un catalogue distant, configurez aussi sa commande.", modelsField: "Modèles (id | nom)",
    selectorGroup: "5 sélecteurs · une fenêtre par sélecteur", optionsField: "Options : id | nom | actionId (une par ligne)", modesGroup: "8 niveaux de raisonnement", togglesGroup: "8 commandes d'activation", actionsGroup: "12 fonctions du menu +",
    modelsFormat: "Chaque modèle nécessite id | nom.", missingNames: "Renseignez id et nom pour les modèles et options.", settingsSaved: "Paramètres enregistrés localement. Les commandes distantes nécessitent un bridge réel.", settingsTemporary: "Paramètres actifs uniquement dans cet onglet : le navigateur a bloqué le stockage local.",
    configure: "Configurer", back: "Retour au chat", save: "Enregistrer", close: "Nouveau chat", export: "Exporter le chat",
    models: "Choisir un modèle", modes: "Raisonnement", functions: "+ 12 fonctions", attach: "Joindre", voice: "Voix", watchdog: "Watchdog", send: "Envoyer ↗", skills: "Compétences", connectors: "Connecteurs",
  },
  pt: {
    chatAria: "Chat", controlsAria: "Modelos e modos", selectorsAria: "Seletores configuráveis", togglesAria: "Oito controles configuráveis", messagesAria: "Mensagens",
    defaultDescription: "Escolha um modelo e configure as ações para conectar seu backend.", slotMode: "Nível {number}", slotSelector: "Seletor {number}", slotToggle: "Controle {number}", slotAction: "Função {number}",
    emptyTitle: "O que vamos construir hoje?", placeholder: "Escreva uma mensagem…", messageAria: "Mensagem", fileInput: "Escolher arquivos", closeWindow: "Fechar",
    stopRecording: "Parar {name}", on: "ligado", off: "desligado", toggleConfirmed: "{name}: {state} confirmado.", backendConfirmed: "{name}: confirmado pelo backend.",
    selectedRemote: "{name} confirmado", selectedLocal: "{name} selecionado localmente; o backend será verificado ao enviar.",
    modelRequired: "Selecione um modelo antes de enviar.", backendSending: "Enviando ao backend…", backendReceived: "Resposta recebida do backend.",
    modelsEmpty: "Nenhum modelo configurado. Adicione em Configurações ou conecte o catálogo do backend.", modelsRefresh: "Atualizar pelo backend", modelsUpdated: "Catálogo atualizado pelo backend.",
    selectorEmpty: "Configure as opções desta janela em Configurações.", backendLoading: "Consultando o backend…", resourcesEmpty: "O backend não retornou itens.",
    fileLocal: "local", fileUploaded: "enviado", uploadConfirmed: "{name}: envio confirmado.", uploadLocal: "{name}: {error}; permanece somente nesta aba.",
    voiceUnavailable: "VOICE_UNAVAILABLE: este navegador não permite gravar.", recording: "Gravando áudio localmente…", audioConfirmed: "Áudio confirmado pelo backend.",
    watchdogConfirmed: "Watchdog: confirmado pelo backend.", exportStarted: "Exportação iniciada neste navegador.",
    settingsAria: "Configurações do chat", settingsTitle: "Configurações", settingsIntro: "Edite nomes, descrições e actionId. Nunca cole chaves, senhas ou código executável: a ponte segura implementa os comandos.",
    chatTitle: "Título do chat", chatDescription: "Descrição do chat", theme: "Tema", language: "Idioma", backendConnections: "Conexões do backend",
    modelsActionId: "Carregar catálogo de modelos", modelActionId: "Selecionar modelo", sendActionId: "Enviar mensagem", attachActionId: "Enviar anexo", voiceActionId: "Enviar voz", watchdogActionId: "Watchdog", skillsActionId: "Listar habilidades", connectorsActionId: "Listar conectores",
    namesAndDescriptions: "Nomes e descrições dos botões", name: "Nome", description: "Descrição", actionId: "Comando de ação (actionId)", modelsHeading: "Modelos",
    modelsInfo: "Um modelo por linha: id | nome. Se tiver um catálogo remoto, configure também seu comando.", modelsField: "Modelos (id | nome)",
    selectorGroup: "5 seletores · uma janela por seletor", optionsField: "Opções: id | nome | actionId (uma por linha)", modesGroup: "8 níveis de raciocínio", togglesGroup: "8 controles de ativação", actionsGroup: "12 funções do menu +",
    modelsFormat: "Cada modelo precisa de id | nome.", missingNames: "Preencha id e nome nos modelos e opções.", settingsSaved: "Configurações salvas localmente. Comandos remotos exigem uma ponte real.", settingsTemporary: "Configurações ativas apenas nesta aba: o navegador bloqueou o armazenamento local.",
    configure: "Configurar", back: "Voltar ao chat", save: "Salvar configurações", close: "Novo chat", export: "Exportar chat",
    models: "Escolher modelo", modes: "Raciocínio", functions: "+ 12 funções", attach: "Anexar", voice: "Voz", watchdog: "Watchdog", send: "Enviar ↗", skills: "Habilidades", connectors: "Conectores",
  },
};

export function t(context, key, vars = {}) {
  const locale = context.config.locale;
  const template = STRINGS[locale]?.[key] ?? STRINGS.es[key];
  if (template === undefined) throw new Error(`TRANSLATION_MISSING:${key}`);
  return template.replace(/\{(\w+)\}/g, (_, name) => String(vars[name] ?? ""));
}

export function controlLabel(context, key) {
  const configured = context.config.labels[key];
  return configured === CONTROL_LABELS[key] ? t(context, key) : configured;
}

export function slotLabel(context, slot) {
  const [prefix, number] = slot.id.split("-");
  const original = { mode: "Nivel", selector: "Selector", toggle: "Control", action: "Función" }[prefix];
  return original && slot.label === `${original} ${number}`
    ? t(context, `slot${prefix[0].toUpperCase()}${prefix.slice(1)}`, { number }) : slot.label;
}

export function chatDescription(context) {
  return context.config.description === STRINGS.es.defaultDescription
    ? t(context, "defaultDescription") : context.config.description;
}
