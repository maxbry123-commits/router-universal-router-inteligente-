import { CONTROL_LABELS } from "./config.js";

export const LANGUAGES = ["es", "en", "fr", "pt"];

export const STRINGS = {
  es: {
    tools: "Herramientas", selectors: "Selectores", controls: "Controles", chatMenu: "Menú del chat", documents: "Subir documentos", documentsActionId: "Subir documentos", plugins: "Plugins del Router", fichas: "Fichas del Router", components: "Componentes UI",
    componentsDesc: "Los 22 componentes Rare UI portados de la skill; interacción real local, sin datos falsos.",
    iconLibrary: "Biblioteca de iconos V12", iconLibraryDesc: "54 prototipos en revisión; filtra, previsualiza y copia SVG localmente. Copiar no asigna una acción al backend.", iconCopied: "SVG de {name} copiado.", iconCopyFailed: "El navegador no permitió copiar el SVG.",
    typography: "Tipografía", typo_title: "Título", typo_subtitle: "Subtítulo", typo_body: "Texto", typo_input: "Entrada", typo_placeholder: "Placeholder", typo_output: "Salida", typo_button: "Botón", typo_meta: "Meta",
    typoColor: "Color", typoCustomColor: "Color personalizado", typoFont: "Fuente", typoSize: "Tamaño (10–48)", typoWeight: "Peso (300–900)", typoTracking: "Interletraje (−1 a 4)", typoLineHeight: "Interlineado (1–2.3)", typoItalic: "Cursiva", typoUnderline: "Subrayado", typoUppercase: "Mayúsculas", typoAlign: "Alineación",
    typoApply: "Aplicar al chat", typoReset: "Restablecer clase", typoExport: "Exportar CSS", typoSaved: "Tipografía guardada y aplicada.", typoContrast: "Contraste sobre el módulo: {ratio} (mínimo 4.5)", typoMobileNote: "Vista móvil del texto seleccionado.", typoDesc: "Editor de 8 clases de texto con muestra editable, persistencia y exportación CSS (parte 2, en revisión).",
    catAll: "Todos", catGeneral: "General", catFiles: "Archivos", catAi: "AI", catConnect: "Conexión", catMedia: "Multimedia", catStatus: "Estado",
    apply: "Aplicar", cancel: "Cancelar", modelSearch: "Buscar modelo", noResults: "Sin resultados", themeGris: "Gris V07", themeLittle: "Little", themeMatte: "Matte", themeBlanco: "Blanco", themeCrystal: "Crystal", themeOrange: "Orange", themeBlue: "Blue", themeCanonical: "Paleta base", themeReference: "Paleta de referencia · no aprobada",
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
    modelsFormat: "Cada modelo necesita id | nombre.", missingNames: "Completa id y nombre en los modelos y opciones.", settingsSaved: "Configuración guardada localmente. Los comandos remotos requieren un bridge real.", settingsTemporary: "Configuración activa solo en esta pestaña: el navegador bloqueó el almacenamiento local.", configExport: "Exportar configuración", configImport: "Importar configuración", configReset: "Restablecer configuración", configResetConfirm: "¿Restablecer la configuración del chat? Esta acción sustituirá tus nombres y comandos guardados.", configImportConfirm: "¿Importar y sustituir la configuración actual?", configImported: "Configuración importada.", configExported: "Archivo de configuración creado.", configResetDone: "Configuración restablecida.", configInvalid: "Archivo de configuración inválido.",
    configure: "Configurar", back: "Volver al chat", save: "Guardar configuración", close: "Nuevo chat", export: "Exportar chat",
    models: "Elegir modelo", modes: "Razonamiento", functions: "+ 12 funciones", attach: "Adjuntar", voice: "Voz", watchdog: "Watchdog", send: "Enviar ↗", skills: "Habilidades", connectors: "Conectores",
  },
  en: {
    tools: "Tools", selectors: "Selectors", controls: "Controls", chatMenu: "Chat menu", documents: "Upload documents", documentsActionId: "Upload documents", plugins: "Router plugins", fichas: "Router fichas", components: "UI components",
    componentsDesc: "The 22 Rare UI components ported from the skill; real local interaction, no fake data.",
    iconLibrary: "V12 icon library", iconLibraryDesc: "54 prototypes under review; filter, preview and copy SVG locally. Copying does not assign a backend action.", iconCopied: "SVG for {name} copied.", iconCopyFailed: "The browser could not copy the SVG.",
    typography: "Typography", typo_title: "Title", typo_subtitle: "Subtitle", typo_body: "Body", typo_input: "Input", typo_placeholder: "Placeholder", typo_output: "Output", typo_button: "Button", typo_meta: "Meta",
    typoColor: "Color", typoCustomColor: "Custom color", typoFont: "Font", typoSize: "Size (10–48)", typoWeight: "Weight (300–900)", typoTracking: "Letter spacing (−1 to 4)", typoLineHeight: "Line height (1–2.3)", typoItalic: "Italic", typoUnderline: "Underline", typoUppercase: "Uppercase", typoAlign: "Alignment",
    typoApply: "Apply to chat", typoReset: "Reset class", typoExport: "Export CSS", typoSaved: "Typography saved and applied.", typoContrast: "Contrast on module: {ratio} (minimum 4.5)", typoMobileNote: "Mobile view of the selected text.", typoDesc: "8-class text editor with editable sample, persistence and CSS export (part 2, under review).",
    catAll: "All", catGeneral: "General", catFiles: "Files", catAi: "AI", catConnect: "Connect", catMedia: "Media", catStatus: "Status",
    apply: "Apply", cancel: "Cancel", modelSearch: "Search models", noResults: "No results", themeGris: "Gray V07", themeLittle: "Little", themeMatte: "Matte", themeBlanco: "Light", themeCrystal: "Crystal", themeOrange: "Orange", themeBlue: "Blue", themeCanonical: "Base palette", themeReference: "Reference palette · not approved",
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
    modelsFormat: "Each model needs id | name.", missingNames: "Complete id and name for models and options.", settingsSaved: "Settings saved locally. Remote commands require a real bridge.", settingsTemporary: "Settings are active in this tab only: the browser blocked local storage.", configExport: "Export settings", configImport: "Import settings", configReset: "Reset settings", configResetConfirm: "Reset chat settings? This will replace your saved names and commands.", configImportConfirm: "Import and replace current settings?", configImported: "Settings imported.", configExported: "Settings file created.", configResetDone: "Settings reset.", configInvalid: "Invalid settings file.",
    configure: "Settings", back: "Back to chat", save: "Save settings", close: "New chat", export: "Export chat",
    models: "Choose model", modes: "Reasoning", functions: "+ 12 functions", attach: "Attach", voice: "Voice", watchdog: "Watchdog", send: "Send ↗", skills: "Skills", connectors: "Connectors",
  },
  fr: {
    tools: "Outils", selectors: "Sélecteurs", controls: "Commandes", chatMenu: "Menu du chat", documents: "Téléverser des documents", documentsActionId: "Téléverser des documents", plugins: "Plugins du Router", fichas: "Fiches du Router", components: "Composants UI",
    componentsDesc: "Les 22 composants Rare UI portés de la skill ; interaction locale réelle, sans données fausses.",
    iconLibrary: "Bibliothèque d’icônes V12", iconLibraryDesc: "54 prototypes en révision ; filtrer, prévisualiser et copier un SVG local. La copie n’assigne pas d’action backend.", iconCopied: "SVG de {name} copié.", iconCopyFailed: "Le navigateur n’a pas permis de copier le SVG.",
    typography: "Typographie", typo_title: "Titre", typo_subtitle: "Sous-titre", typo_body: "Texte", typo_input: "Saisie", typo_placeholder: "Placeholder", typo_output: "Sortie", typo_button: "Bouton", typo_meta: "Méta",
    typoColor: "Couleur", typoCustomColor: "Couleur personnalisée", typoFont: "Police", typoSize: "Taille (10–48)", typoWeight: "Graisse (300–900)", typoTracking: "Interlettrage (−1 à 4)", typoLineHeight: "Interligne (1–2.3)", typoItalic: "Italique", typoUnderline: "Souligné", typoUppercase: "Majuscules", typoAlign: "Alignement",
    typoApply: "Appliquer au chat", typoReset: "Réinitialiser la classe", typoExport: "Exporter le CSS", typoSaved: "Typographie enregistrée et appliquée.", typoContrast: "Contraste sur le module : {ratio} (minimum 4.5)", typoMobileNote: "Vue mobile du texte sélectionné.", typoDesc: "Éditeur de 8 classes de texte avec échantillon, persistance et export CSS (partie 2, en révision).",
    catAll: "Tous", catGeneral: "Général", catFiles: "Fichiers", catAi: "IA", catConnect: "Connexion", catMedia: "Média", catStatus: "Statut",
    apply: "Appliquer", cancel: "Annuler", modelSearch: "Rechercher un modèle", noResults: "Aucun résultat", themeGris: "Gris V07", themeLittle: "Little", themeMatte: "Matte", themeBlanco: "Clair", themeCrystal: "Crystal", themeOrange: "Orange", themeBlue: "Blue", themeCanonical: "Palette de base", themeReference: "Palette de référence · non approuvée",
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
    modelsFormat: "Chaque modèle nécessite id | nom.", missingNames: "Renseignez id et nom pour les modèles et options.", settingsSaved: "Paramètres enregistrés localement. Les commandes distantes nécessitent un bridge réel.", settingsTemporary: "Paramètres actifs uniquement dans cet onglet : le navigateur a bloqué le stockage local.", configExport: "Exporter les paramètres", configImport: "Importer les paramètres", configReset: "Réinitialiser les paramètres", configResetConfirm: "Réinitialiser les paramètres du chat ? Vos noms et commandes enregistrés seront remplacés.", configImportConfirm: "Importer et remplacer les paramètres actuels ?", configImported: "Paramètres importés.", configExported: "Fichier des paramètres créé.", configResetDone: "Paramètres réinitialisés.", configInvalid: "Fichier de paramètres invalide.",
    configure: "Configurer", back: "Retour au chat", save: "Enregistrer", close: "Nouveau chat", export: "Exporter le chat",
    models: "Choisir un modèle", modes: "Raisonnement", functions: "+ 12 fonctions", attach: "Joindre", voice: "Voix", watchdog: "Watchdog", send: "Envoyer ↗", skills: "Compétences", connectors: "Connecteurs",
  },
  pt: {
    tools: "Ferramentas", selectors: "Seletores", controls: "Controles", chatMenu: "Menu do chat", documents: "Enviar documentos", documentsActionId: "Enviar documentos", plugins: "Plugins do Router", fichas: "Fichas do Router", components: "Componentes UI",
    componentsDesc: "Os 22 componentes Rare UI portados da skill; interação local real, sem dados falsos.",
    iconLibrary: "Biblioteca de ícones V12", iconLibraryDesc: "54 protótipos em revisão; filtre, visualize e copie SVG localmente. Copiar não atribui uma ação backend.", iconCopied: "SVG de {name} copiado.", iconCopyFailed: "O navegador não permitiu copiar o SVG.",
    typography: "Tipografia", typo_title: "Título", typo_subtitle: "Subtítulo", typo_body: "Texto", typo_input: "Entrada", typo_placeholder: "Placeholder", typo_output: "Saída", typo_button: "Botão", typo_meta: "Meta",
    typoColor: "Cor", typoCustomColor: "Cor personalizada", typoFont: "Fonte", typoSize: "Tamanho (10–48)", typoWeight: "Peso (300–900)", typoTracking: "Espaçamento (−1 a 4)", typoLineHeight: "Entrelinha (1–2.3)", typoItalic: "Itálico", typoUnderline: "Sublinhado", typoUppercase: "Maiúsculas", typoAlign: "Alinhamento",
    typoApply: "Aplicar ao chat", typoReset: "Redefinir classe", typoExport: "Exportar CSS", typoSaved: "Tipografia salva e aplicada.", typoContrast: "Contraste no módulo: {ratio} (mínimo 4.5)", typoMobileNote: "Vista móvel do texto selecionado.", typoDesc: "Editor de 8 classes de texto com amostra editável, persistência e exportação CSS (parte 2, em revisão).",
    catAll: "Todos", catGeneral: "Geral", catFiles: "Arquivos", catAi: "IA", catConnect: "Conexão", catMedia: "Mídia", catStatus: "Estado",
    apply: "Aplicar", cancel: "Cancelar", modelSearch: "Buscar modelos", noResults: "Sem resultados", themeGris: "Cinza V07", themeLittle: "Little", themeMatte: "Matte", themeBlanco: "Claro", themeCrystal: "Crystal", themeOrange: "Orange", themeBlue: "Blue", themeCanonical: "Paleta base", themeReference: "Paleta de referência · não aprovada",
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
    modelsFormat: "Cada modelo precisa de id | nome.", missingNames: "Preencha id e nome nos modelos e opções.", settingsSaved: "Configurações salvas localmente. Comandos remotos exigem uma ponte real.", settingsTemporary: "Configurações ativas apenas nesta aba: o navegador bloqueou o armazenamento local.", configExport: "Exportar configurações", configImport: "Importar configurações", configReset: "Redefinir configurações", configResetConfirm: "Redefinir configurações do chat? Seus nomes e comandos salvos serão substituídos.", configImportConfirm: "Importar e substituir as configurações atuais?", configImported: "Configurações importadas.", configExported: "Arquivo de configurações criado.", configResetDone: "Configurações redefinidas.", configInvalid: "Arquivo de configurações inválido.",
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
