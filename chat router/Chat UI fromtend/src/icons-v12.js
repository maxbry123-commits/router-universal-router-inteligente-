// Biblioteca V12 portada desde YAIWES-ICONOS-PRO-V12.html (54 entradas, categorías y usos originales).
export const V12_COLORS = [
  {
    "id": "white",
    "name": "Blanco iluminado",
    "hex": "#F8F8F8"
  },
  {
    "id": "blue",
    "name": "Azul eléctrico",
    "hex": "#0647F4"
  },
  {
    "id": "green",
    "name": "Verde intenso",
    "hex": "#0FD56A"
  },
  {
    "id": "red",
    "name": "Rojo vivo",
    "hex": "#FF4A5F"
  },
  {
    "id": "orange",
    "name": "Naranja vivo",
    "hex": "#FF7A1C"
  },
  {
    "id": "gray",
    "name": "Gris claro",
    "hex": "#DADADA"
  }
];

const PATHS =  {
search:'<circle cx="11" cy="11" r="6"></circle><path d="M20 20l-4.2-4.2"></path>',
settings:'<circle cx="12" cy="12" r="3"></circle><path d="M12 2v3M12 19v3M4.9 4.9l2.1 2.1M17 17l2.1 2.1M2 12h3M19 12h3M4.9 19.1L7 17M17 7l2.1-2.1"></path>',
home:'<path d="M4 11.5L12 4l8 7.5"></path><path d="M6.5 10.5V20h11V10.5"></path>',
menu:'<path d="M4 7h16M4 12h16M4 17h16"></path>',
grid:'<rect x="4" y="4" width="6" height="6" rx="1.5"></rect><rect x="14" y="4" width="6" height="6" rx="1.5"></rect><rect x="4" y="14" width="6" height="6" rx="1.5"></rect><rect x="14" y="14" width="6" height="6" rx="1.5"></rect>',
star:'<path d="M12 3.6l2.6 5.3 5.8.8-4.2 4.1 1 5.8L12 16.8 6.8 19.6l1-5.8-4.2-4.1 5.8-.8z"></path>',
heart:'<path d="M12 20s-7-4.7-7-10a4 4 0 0 1 7-2 4 4 0 0 1 7 2c0 5.3-7 10-7 10z"></path>',
pin:'<path d="M15 4l5 5-3 1-3 6-2-2-6 3-1-1 3-6-2-2z"></path>',
folder:'<path d="M3 8.5h6l2 2h10v7.5A2 2 0 0 1 19 20H5a2 2 0 0 1-2-2z"></path>',
file:'<path d="M7 3h7l5 5v13H7z"></path><path d="M14 3v5h5"></path>',
upload:'<path d="M12 17V5"></path><path d="M7.5 9.5L12 5l4.5 4.5"></path><path d="M5 20h14"></path>',
download:'<path d="M12 5v12"></path><path d="M7.5 12.5L12 17l4.5-4.5"></path><path d="M5 20h14"></path>',
copy:'<rect x="9" y="9" width="11" height="11" rx="2"></rect><rect x="4" y="4" width="11" height="11" rx="2"></rect>',
trash:'<path d="M4 7h16"></path><path d="M9 7V4h6v3"></path><path d="M7 7l1 13h8l1-13"></path>',
image:'<rect x="3" y="5" width="18" height="14" rx="2"></rect><circle cx="9" cy="10" r="1.4"></circle><path d="M5 17l5-4 3 3 4-5 2 2"></path>',
camera:'<rect x="3" y="7" width="18" height="12" rx="2"></rect><path d="M8 7l1.5-2h5L16 7"></path><circle cx="12" cy="13" r="3.5"></circle>',
video:'<rect x="3" y="6" width="13" height="12" rx="2"></rect><path d="M16 10l5-3v10l-5-3z"></path>',
mic:'<rect x="9" y="4" width="6" height="10" rx="3"></rect><path d="M6 11a6 6 0 0 0 12 0"></path><path d="M12 17v3"></path>',
speaker:'<path d="M5 10h4l5-4v12l-5-4H5z"></path><path d="M17 9a4 4 0 0 1 0 6"></path>',
bell:'<path d="M6 9a6 6 0 0 1 12 0v5l2 2H4l2-2z"></path><path d="M10 18a2 2 0 0 0 4 0"></path>',
chat:'<path d="M4 6h16v10H8l-4 4z"></path>',
send:'<path d="M3 20l18-8L3 4l3 7 7 1-7 1z"></path>',
link:'<path d="M10 14l4-4"></path><path d="M7.5 16.5l-2 2a3 3 0 1 1-4.2-4.2l2-2"></path><path d="M16.5 7.5l2-2a3 3 0 1 1 4.2 4.2l-2 2"></path>',
globe:'<circle cx="12" cy="12" r="9"></circle><path d="M3 12h18"></path><path d="M12 3a15 15 0 0 1 0 18"></path><path d="M12 3a15 15 0 0 0 0 18"></path>',
plug:'<path d="M9 8V4"></path><path d="M15 8V4"></path><path d="M8 10h8v2a4 4 0 0 1-4 4v4"></path><path d="M10 20h4"></path>',
cloud:'<path d="M7 18h10a4 4 0 0 0 0-8 5.5 5.5 0 0 0-10.7-1A4 4 0 0 0 7 18z"></path>',
database:'<ellipse cx="12" cy="6" rx="7" ry="3"></ellipse><path d="M5 6v6c0 1.7 3.1 3 7 3s7-1.3 7-3V6"></path><path d="M5 12v6c0 1.7 3.1 3 7 3s7-1.3 7-3v-6"></path>',
shield:'<path d="M12 3l7 3v5c0 5-3.2 7.8-7 10-3.8-2.2-7-5-7-10V6z"></path>',
lock:'<rect x="6" y="11" width="12" height="9" rx="2"></rect><path d="M8 11V8a4 4 0 0 1 8 0v3"></path>',
key:'<circle cx="8" cy="12" r="3"></circle><path d="M11 12h10"></path><path d="M18 12v3"></path><path d="M15 12v2"></path>',
check:'<path d="M5 12l4 4 10-10"></path>',
warning:'<path d="M12 4l9 16H3z"></path><path d="M12 10v4"></path><path d="M12 17h.01"></path>',
x:'<path d="M6 6l12 12"></path><path d="M18 6L6 18"></path>',
clock:'<circle cx="12" cy="12" r="8.5"></circle><path d="M12 7v5l3 2"></path>',
calendar:'<rect x="4" y="5" width="16" height="15" rx="2"></rect><path d="M8 3v4M16 3v4M4 9h16"></path>',
filter:'<path d="M4 6h16"></path><path d="M7 12h10"></path><path d="M10 18h4"></path>',
sliders:'<path d="M4 6h6"></path><circle cx="13" cy="6" r="2"></circle><path d="M16 6h4"></path><path d="M4 12h10"></path><circle cx="17" cy="12" r="2"></circle><path d="M4 18h3"></path><circle cx="10" cy="18" r="2"></circle><path d="M13 18h7"></path>',
code:'<path d="M8 8l-4 4 4 4"></path><path d="M16 8l4 4-4 4"></path><path d="M14 4l-4 16"></path>',
terminal:'<rect x="3" y="5" width="18" height="14" rx="2"></rect><path d="M7 10l3 2-3 2"></path><path d="M12 14h5"></path>',
cpu:'<rect x="8" y="8" width="8" height="8" rx="1"></rect><path d="M12 2v3M12 19v3M2 12h3M19 12h3M5 5l2 2M17 17l2 2M5 19l2-2M17 7l2-2"></path>',
ai:'<path d="M9 4a3 3 0 0 0-3 3v1a3 3 0 0 0 0 6v1a3 3 0 0 0 3 3"></path><path d="M15 4a3 3 0 0 1 3 3v1a3 3 0 0 1 0 6v1a3 3 0 0 1-3 3"></path><path d="M9 7h6M9 12h6M12 4v14"></path>',
brain:'<path d="M10 4a3 3 0 0 0-3 3c0 1-.5 1.6-1 2.2A3.8 3.8 0 0 0 9 16h6a3.8 3.8 0 0 0 3-6.8C17.5 8.6 17 8 17 7a3 3 0 0 0-3-3 3 3 0 0 0-2 1 3 3 0 0 0-2-1z"></path><path d="M10 16v2a2 2 0 0 0 4 0v-2"></path>',
robot:'<rect x="6" y="7" width="12" height="10" rx="3"></rect><path d="M12 3v4"></path><path d="M9 11h.01M15 11h.01"></path><path d="M9 14h6"></path><path d="M8 17v2M16 17v2"></path>',
rocket:'<path d="M12 3c4 1 6 4 7 9-3 1-6 3-9 7-1-3-3-6-7-9 5-1 8-3 9-7z"></path><path d="M9 15l-2 6 6-2"></path>',
spark:'<path d="M12 3l1.8 4.7L18.5 9 13.8 10.8 12 15.5l-1.8-4.7L5.5 9l4.7-1.3z"></path>',
lightning:'<path d="M13 2L5 13h5l-1 9 8-11h-5z"></path>',
chart:'<path d="M4 19h16"></path><path d="M6 15l4-4 3 2 5-6"></path>',
bars:'<path d="M5 19V9"></path><path d="M10 19V5"></path><path d="M15 19v-8"></path><path d="M20 19V7"></path>',
pie:'<path d="M12 3a9 9 0 1 0 9 9h-9z"></path><path d="M12 3v9h9"></path>',
refresh:'<path d="M20 11a8 8 0 1 0 2 5"></path><path d="M20 4v7h-7"></path>',
user:'<circle cx="12" cy="8" r="3.5"></circle><path d="M5 20a7 7 0 0 1 14 0"></path>',
team:'<circle cx="9" cy="8" r="3"></circle><circle cx="16.5" cy="9" r="2.5"></circle><path d="M4 20a6 6 0 0 1 10 0"></path><path d="M14.5 19a4.5 4.5 0 0 1 4.5-3"></path>',
eye:'<path d="M2.5 12S6.5 5.5 12 5.5 21.5 12 21.5 12 17.5 18.5 12 18.5 2.5 12 2.5 12z"></path><circle cx="12" cy="12" r="2.5"></circle>',
tool:'<path d="M14 5a4 4 0 0 0 5 5L9 20l-5-5L14 5z"></path><path d="M16 8l-3-3"></path>'
};

export const ICON_META = [
{ id: "ai", name: "Asistente AI", cat: "ai", use: "pensamiento, ejecución y modos inteligentes" },
{ id: "brain", name: "Razonamiento", cat: "ai", use: "thinking, análisis, procesos largos" },
{ id: "robot", name: "Agente", cat: "ai", use: "subagentes, automatización" },
{ id: "spark", name: "Idea", cat: "ai", use: "creación, inspiración, mejoras" },
{ id: "rocket", name: "Lanzar", cat: "ai", use: "iniciar flujo o tarea" },
{ id: "search", name: "Buscar", cat: "general", use: "buscar dentro del proyecto" },
{ id: "settings", name: "Ajustes", cat: "general", use: "configuración del sistema" },
{ id: "home", name: "Inicio", cat: "general", use: "regresar al panel principal" },
{ id: "menu", name: "Menú", cat: "general", use: "abrir navegación" },
{ id: "grid", name: "Cuadrícula", cat: "general", use: "vista de paneles y módulos" },
{ id: "star", name: "Favorito", cat: "status", use: "marcar o destacar" },
{ id: "heart", name: "Guardado", cat: "status", use: "preferido o aprobado" },
{ id: "pin", name: "Anclar", cat: "status", use: "fijar mensaje o panel" },
{ id: "folder", name: "Carpeta", cat: "files", use: "grupo de archivos y rutas" },
{ id: "file", name: "Archivo", cat: "files", use: "documento o entrada" },
{ id: "upload", name: "Subir", cat: "files", use: "cargar archivos" },
{ id: "download", name: "Descargar", cat: "files", use: "guardar salida o artefacto" },
{ id: "copy", name: "Duplicar", cat: "files", use: "copiar contenido" },
{ id: "trash", name: "Eliminar", cat: "files", use: "borrar elemento" },
{ id: "image", name: "Imagen", cat: "media", use: "adjunto visual" },
{ id: "camera", name: "Cámara", cat: "media", use: "captura o foto" },
{ id: "video", name: "Video", cat: "media", use: "clip o grabación" },
{ id: "mic", name: "Micrófono", cat: "media", use: "voz y audio" },
{ id: "speaker", name: "Altavoz", cat: "media", use: "reproducir audio" },
{ id: "bell", name: "Notificación", cat: "status", use: "alertas y avisos" },
{ id: "chat", name: "Chat", cat: "general", use: "mensajes y conversación" },
{ id: "send", name: "Enviar", cat: "general", use: "mandar mensaje o acción" },
{ id: "link", name: "Enlace", cat: "connect", use: "URL o conexión externa" },
{ id: "globe", name: "Web", cat: "connect", use: "sitio, navegador, internet" },
{ id: "plug", name: "Conector", cat: "connect", use: "plugin, bridge, integración" },
{ id: "cloud", name: "Nube", cat: "connect", use: "sincronización o remoto" },
{ id: "database", name: "Base de datos", cat: "connect", use: "persistencia y memoria" },
{ id: "shield", name: "Seguridad", cat: "status", use: "proteger o verificar" },
{ id: "lock", name: "Bloquear", cat: "status", use: "cerrar acceso" },
{ id: "key", name: "Acceso", cat: "status", use: "clave, llave o permiso" },
{ id: "check", name: "Aprobar", cat: "status", use: "pass, ok o cierre" },
{ id: "warning", name: "Advertencia", cat: "status", use: "precaución o revisión" },
{ id: "x", name: "Cerrar", cat: "status", use: "cancelar o salir" },
{ id: "clock", name: "Tiempo", cat: "status", use: "espera o tiempo restante" },
{ id: "calendar", name: "Calendario", cat: "general", use: "fechas, agenda o historial" },
{ id: "filter", name: "Filtrar", cat: "general", use: "ordenar resultados" },
{ id: "sliders", name: "Controles", cat: "general", use: "parámetros y ajustes finos" },
{ id: "code", name: "Código", cat: "connect", use: "desarrollo y snippets" },
{ id: "terminal", name: "Terminal", cat: "connect", use: "comandos y consola" },
{ id: "cpu", name: "Procesador", cat: "ai", use: "cómputo y motor interno" },
{ id: "lightning", name: "Rápido", cat: "ai", use: "modo veloz o turbo" },
{ id: "chart", name: "Tendencia", cat: "status", use: "progreso y evolución" },
{ id: "bars", name: "Métricas", cat: "status", use: "estadísticas y uso" },
{ id: "pie", name: "Distribución", cat: "status", use: "porcentajes y reparto" },
{ id: "refresh", name: "Actualizar", cat: "general", use: "refrescar o volver a cargar" },
{ id: "user", name: "Usuario", cat: "general", use: "perfil personal" },
{ id: "team", name: "Equipo", cat: "general", use: "staff, grupo o council" },
{ id: "eye", name: "Vista", cat: "general", use: "previsualizar o inspeccionar" },
{ id: "tool", name: "Herramienta", cat: "connect", use: "acción utilitaria o skill" }
];

export function v12Svg(id, cls = 'svg-icon') {
  const svg = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
  svg.setAttribute('class', cls); svg.setAttribute('viewBox', '0 0 24 24'); svg.setAttribute('aria-hidden', 'true');
  svg.setAttribute('fill', 'none'); svg.setAttribute('stroke', 'currentColor');
  svg.setAttribute('stroke-width', '1.7'); svg.setAttribute('stroke-linecap', 'round'); svg.setAttribute('stroke-linejoin', 'round');
  svg.innerHTML = PATHS[id] || '';
  return svg;
}

export const v12Path = id => PATHS[id] || '';
