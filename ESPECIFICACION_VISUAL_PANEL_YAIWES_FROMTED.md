# Especificación visual y funcional del panel — YAIWES / FROMTED / referencias

> Documento construido a partir de **74 capturas únicas** recibidas en la conversación.  
> Objetivo: que una IA que **no pueda analizar imágenes** entienda qué hay en cada pantalla, qué hace cada componente, cómo se relacionan los estados y cómo traducirlo a HTML/CSS/JS y a estructuras de datos.

---

## 0. Cómo leer este archivo

Este documento no intenta copiar marcas externas píxel por píxel. Extrae y normaliza:

1. **Jerarquía visual**: paneles, barras, tarjetas, modales, listas, tabs, inputs.
2. **Semántica**: qué representa cada bloque y para qué sirve.
3. **Interacciones**: click, toggle, select, escribir, conectar, inspeccionar, ejecutar, programar.
4. **Estados**: conectado, desconectado, activo, error, bloqueado, esperando intervención, listo para merge, etc.
5. **Flujos**: cómo pasa el usuario de una pantalla a otra.
6. **Contrato de datos**: propiedades mínimas para reconstruir la UI.
7. **Código de referencia**: HTML/CSS/JS genérico y reusable.

---

# 1. Lenguaje visual global

## 1.1 Tema principal oscuro

Las capturas convergen en un diseño oscuro, con tarjetas redondeadas, separación amplia y acentos de color solo para estados y acciones.

### Paleta V07 observada

```css
:root {
  --bg: #1B1B1B;
  --panel: #202020;
  --module: #2A2A2A;
  --selected: #3C3C3C;
  --mask: #484848;

  --text: #EDEDED;
  --text-soft: #BDBDBD;
  --text-dim: #8D8D8D;

  --accent-green: #36D58A;
  --accent-blue: #2F80FF;
  --accent-cyan: #18C7E8;
  --accent-orange: #FF8A2A;
  --accent-red: #FF445F;
  --accent-lime: #C7FF2C;

  --border: rgba(255,255,255,.12);
  --border-strong: rgba(255,255,255,.22);
  --shadow: 0 12px 28px rgba(0,0,0,.28);
}
```

### Regla visual principal

```text
FONDO OSCURO FIJO
    ↓
PANELES / MÓDULOS EN GRIS
    ↓
SOLO EL COMPONENTE ACTIVO RECIBE ACENTO
    ↓
ESTADOS IMPORTANTES = VERDE / AZUL / NARANJA / ROJO
```

El color vivo no debe aclarar todo el fondo. Se usa como:

- borde activo;
- texto de estado;
- icono activo;
- toggle encendido;
- botón primario;
- aviso;
- badge.

---

## 1.2 Geometría

Patrón observado:

```css
.card       { border-radius: 18px; }
.card-sm    { border-radius: 12px; }
.button     { border-radius: 12px; }
.pill       { border-radius: 999px; }
.modal      { border-radius: 22px; }
.input      { border-radius: 16px; }
```

En móvil:

- padding lateral aproximado: `16–24px`;
- separación entre módulos: `12–20px`;
- botones principales grandes;
- bottom sheets y modales casi a ancho completo;
- navegación inferior o barra lateral compacta.

---

# 2. Arquitectura visual resumida

Las capturas pueden agruparse en 7 familias de interfaz:

```text
A. CLAUDE / CONECTORES
B. FROMTED / EDITOR VISUAL Y REFERENCIAS
C. MANUS / AGENTE, TAREAS, HABILIDADES Y AUTOMATIZACIONES
D. GROK / MODOS, BOT Y AJUSTES
E. DEVIN / AGENTE DE CÓDIGO, PR, ENTORNO Y COMANDOS
F. YAIWES / MAXBRY ROUTER / DAG / CONECTORES UNIVERSALES
G. PATRONES VISUALES DE DASHBOARD
```

---

# 3. A — Configuración de conectores tipo Claude

## 3.1 Pantalla: lista de conectores

Elementos detectados:

- modal `Configuración`;
- tabs superiores:
  - `Yo`;
  - `Claude Code`;
  - `Claude In Chrome`;
  - `Habilidades`;
  - `Conectores`;
  - en una captura también `Plugins`;
- pestaña activa `Conectores`;
- subtabs `Tuyos` / `Descubrir`;
- buscador;
- filtro;
- botón `+ Agregar`;
- tabla:
  - `Conector`;
  - `Tipo`;
  - `Estado`;
- filas visibles:
  - Firecrawl;
  - Vercel;
  - alphaXiv;
  - GitHub Official;
  - Integración con GitHub;
  - Macaly Cloud;
  - MCP_SECRET_HF;
- estado:
  - check = conectado;
  - `Conectar` = desconectado;
  - `Reconectar` + advertencia = error parcial.

### Modelo de datos

```json
{
  "connector": {
    "id": "mcp_secret_hf",
    "name": "MCP_SECRET_HF",
    "type": "web",
    "custom": true,
    "status": "error",
    "action": "reconnect"
  }
}
```

---

## 3.2 Pantalla: detalle del conector

Componentes:

- back `Tus conectores`;
- menú `⋮`;
- icono/logo;
- URL o endpoint;
- mensaje `Todavía no estás conectado`;
- botón `Conectar`;
- toast/alerta inferior derecha.

### Estado de error observado

La UI comunica un fallo de registro con el servicio de inicio de sesión del conector y sugiere:

```text
INTENTO DE CONEXIÓN
  ↓
REGISTRO / LOGIN
  ↓
FALLO
  ↓
TOAST DE ERROR
  ↓
REINTENTAR O CONFIGURAR CLIENT ID
```

### HTML conceptual

```html
<section class="connector-detail card">
  <header>
    <button aria-label="volver">←</button>
    <span>Tus conectores</span>
    <button aria-label="menu">⋮</button>
  </header>

  <div class="connector-hero">
    <div class="connector-logo">🤗</div>
    <p class="endpoint">https://example.space/...</p>
    <p class="status-text">Todavía no estás conectado</p>
    <button class="primary">Conectar</button>
  </div>

  <aside class="toast toast-warning">
    No se pudo registrar el conector.
  </aside>
</section>
```

---

# 4. B — FROMTED: editor visual, tema y librería de iconos

## 4.1 Editor visual de tema

La captura grande de edición está dividida en **tres columnas**:

```text
┌────────────────┬─────────────────────────┬──────────────────┐
│ Editor visual  │ Vista móvil funcional  │ Biblioteca 2D   │
│ de texto/color │ de referencia           │ + 50 iconos      │
└────────────────┴─────────────────────────┴──────────────────┘
```

### Columna izquierda

Controles observados:

- `Grises aprobados`;
- `Tema visual`;
- `Qué quieres colorear`;
- `10 colores vivos`;
- `Estilo de letra`;
- escala de texto;
- `Paletas combinadas`;
- `Restablecer textos`;
- `Exportar ajustes JSON`.

### Grises aprobados

```json
{
  "background": "#1B1B1B",
  "panel": "#202020",
  "module": "#2A2A2A",
  "selected": "#3C3C3C",
  "mask": "#484848"
}
```

### Temas visibles

```text
Gris oscuro
Little
Negro mate
Blanco
Cristal
Naranja
Azules
```

### Tipos de texto editables

- títulos;
- subtítulos;
- escritura general;
- texto de entrada;
- placeholder;
- salidas y respuestas;
- texto de botones;
- símbolos 2D;
- etiquetas;
- ayudas/notas;
- texto de estado.

---

## 4.2 Vista funcional móvil central

La maqueta móvil contiene:

1. barra superior;
2. título del producto;
3. bloque introductorio;
4. selector `Modo de respuesta`;
5. textarea/input principal;
6. acciones:
   - adjuntar;
   - web;
   - thinking;
7. botón `Mostrar salida`;
8. módulo `Salida - Resultados`;
9. estados funcionales:
   - En curso;
   - Encendido;
   - Advertencia;
   - Descarga.

### Flujo funcional

```text
INPUT
  ↓
SELECCIÓN DE MODO
  ↓
ADJUNTOS / WEB / THINKING
  ↓
ENVIAR
  ↓
SALIDA
  ↓
ESTADO FUNCIONAL
```

---

## 4.3 Biblioteca de iconos

La captura muestra una biblioteca de aproximadamente 50 mini iconos organizados en grid.

Categorías visibles:

- Inicio
- Menú
- Buscar
- Ajustes
- Usuario
- Equipo
- Carpeta
- Archivo
- Documento
- Imagen
- Cámara
- Vídeo
- Micrófono
- Sonido
- Subir
- Descargar
- Enlace
- Conector
- Escudo
- Candado
- Desbloquear
- Confirmar
- Cerrar
- Alerta
- Información
- Ayuda
- Avisos
- Calendario
- Reloj
- Enviar
- Adjuntar
- Web
- Conexión
- Nube
- Datos
- Servidor
- Procesador
- Código
- Terminal
- Error
- Rama Git
- Barras
- Gráfica
- Filtros
- Actualizar
- Filtrar
- Lista
- Cuadrícula
- Favorito
- Robot

### Función del panel

Permite:

```text
SELECCIONAR ICONO
   ↓
ASIGNARLO A UN BOTÓN
   ↓
CONFIGURAR COLOR ACTIVO
   ↓
PREVISUALIZAR
```

---

# 5. Perfil visual YAIWES / biblioteca de apariencias

La pantalla de perfil visual tiene:

- sidebar izquierdo;
- preview móvil central;
- panel derecho de apariencia.

## Sidebar

Entradas:

- Chat;
- Archivos;
- Crazy Wall;
- Configuración.

## Vista móvil

Tabs superiores:

- Chat;
- Archivos;
- Actividades.

Contenido:

- bienvenida;
- tarjeta de ayuda;
- `Modo Rápido`;
- textarea;
- botón enviar;
- accesos rápidos:
  - nuevo proyecto;
  - mis archivos;
  - Crazy Wall;
- navegación inferior:
  - Inicio;
  - Archivos;
  - Actividad;
  - Ajustes.

## Biblioteca de apariencias

Temas visibles:

```text
Little
Negro mate
Cristal
Naranja + negro
Azules
Blanco + negro
Gris oscuro
```

El tema `Gris oscuro` aparece seleccionado en la captura.

---

# 6. Patrones visuales de referencia

## 6.1 Dashboard social oscuro

Características:

- sidebar persistente;
- categorías;
- lista de contactos;
- panel dashboard;
- feed en tarjetas;
- selector de vista;
- ordenamiento;
- botón `New post`;
- cards con imagen, autor, métricas y acciones.

Uso recomendado dentro de YAIWES:

```text
SIDEBAR = navegación global
TOPBAR = contexto y acciones
GRID = módulos / resultados
CARD = tarea / agente / evidencia
```

---

## 6.2 Dashboard financiero

Patrones visuales extraíbles:

- tarjetas resumen en la parte superior;
- gráfico central;
- panel lateral de acción principal;
- tabs secundarios;
- rating/progreso;
- navegación lateral.

Aplicación potencial:

```text
MÉTRICAS DEL ROUTER
↓
CONSUMO / COSTO / TOKENS / LATENCIA
↓
GRÁFICA
↓
DETALLE DEL PROVEEDOR
```

---

## 6.3 Kit de controles oscuro

Controles detectados:

- input normal;
- input con acción buscar;
- carrusel de imagen;
- radio;
- toggles;
- botones cuadrados;
- botones redondeados;
- icon buttons;
- slider vertical;
- progreso circular;
- estados `off/on`.

---

# 7. C — Manus: agente, tareas, habilidades y automatización

## 7.1 Home del agente

Elementos:

- toggle superior `Tareas / Agent`;
- saludo del agente;
- espacio central para conversación;
- input inferior;
- botón `+`;
- micrófono;
- menú `…`.

### Estado vacío

```text
AGENTE EN LÍNEA
↓
ESPERA INPUT
↓
USUARIO ESCRIBE
↓
TAREA / RESPUESTA
```

---

## 7.2 Subtareas

Pantalla de estado vacío:

```text
Subtareas
[icono jerárquico]
Aún no hay subtareas
```

Contrato:

```json
{
  "screen": "subtasks",
  "count": 0,
  "emptyState": true
}
```

---

## 7.3 Menú de cuenta

Módulos visibles:

- plan;
- créditos;
- compartir;
- tareas programadas;
- conocimiento;
- Mail Manus;
- controles de datos;
- navegador en la nube;
- habilidades;
- conectores;
- integraciones;
- idioma;
- apariencia;
- borrar caché;
- ayuda;
- versión;
- cerrar sesión.

---

## 7.4 Añadir al chat

Bottom sheet con accesos:

### Entrada de archivos

- Cámara
- Imagen
- Archivo
- Archivos recientes

### Contexto / trabajo

- Tareas recientes
- Habilidades
- Plan

### Generación

- Crear imagen
- Editar imagen
- Generar audio
- Crear vídeo
- Crear juegos
- Crear diapositivas
- Crear sitio web
- Desarrollar aplicaciones
- Crear hoja de cálculo

### Investigación / automatización

- Wide Research
- Tareas programadas
- Conectar mi computadora
- Playbook

---

## 7.5 Habilidades

Popup de habilidades con listado de skills y etiquetas `Oficial`.

Patrón:

```html
<div class="skill-row">
  <span class="icon">🧩</span>
  <div>
    <strong>Nombre de habilidad</strong>
    <small>Descripción breve...</small>
  </div>
  <span class="badge">Oficial</span>
</div>
```

---

## 7.6 Menú contextual de tarea/chat

Acciones:

- Añadir al proyecto
- Renombrar
- Ver todos los archivos
- Programar una tarea
- Fijar
- Favorito
- Archivar
- Eliminar

Esto es un menú de acciones sobre la **entidad conversación/tarea**.

---

## 7.7 Información de la tarea

Métricas:

```text
Páginas vistas
Comandos ejecutados
API llamada
Archivos creados
Créditos usados
Tiempo trabajado
Calificación
Fecha de creación
```

### Contrato

```json
{
  "taskMetrics": {
    "pagesViewed": 0,
    "commandsExecuted": 0,
    "apiCalls": 0,
    "filesCreated": 0,
    "creditsUsed": 0,
    "workTime": "4s"
  }
}
```

---

## 7.8 Tareas recientes

Bottom sheet con:

- buscador;
- lista de tareas;
- subtítulo/descripción;
- selector circular a la derecha.

---

## 7.9 Estado "Necesita tu intervención"

El agente puede detener su avance cuando necesita una decisión humana.

```text
AGENTE
  ↓
DETECTA DECISIÓN O DATO FALTANTE
  ↓
ESTADO: NECESITA TU INTERVENCIÓN
  ↓
MUESTRA OPCIONES
  ↓
USUARIO RESPONDE
  ↓
CONTINÚA
```

---

## 7.10 Modal de rama

Pregunta:

```text
¿Quieres una dirección diferente?
```

Función:

- crear una rama alternativa;
- preservar la tarea original;
- explorar otra dirección sin destruir el flujo anterior.

Botones:

- `Probar rama ahora`
- `Entendido`

---

## 7.11 Nueva automatización

Campos observados:

- botón cerrar;
- título `Nueva automatización`;
- botón `Crear`;
- icono de automatización;
- `Nombre de la automatización`;
- sección `Programación`;
- `Seleccionar programación o activador`;
- `Instrucciones del proyecto`;
- selector de modo `Auto`;
- notificaciones:
  - push;
  - correo electrónico.

### Modelo

```json
{
  "automation": {
    "name": "",
    "trigger": null,
    "instructions": "",
    "mode": "auto",
    "notifications": {
      "push": false,
      "email": false
    }
  }
}
```

---

## 7.12 Conector GitHub dentro de Manus

Pantalla de autorización:

- logo GitHub;
- descripción;
- tipo de conector = App;
- autor;
- sitio web;
- política de privacidad;
- paso `Autorizar cuenta`;
- paso `Autorizar repositorio`;
- botón `Agregar Repositorios`.

Flujo:

```text
AUTORIZAR CUENTA
  ↓
SELECCIONAR / AUTORIZAR REPOSITORIO
  ↓
CONECTOR DISPONIBLE PARA EL AGENTE
```

---

# 8. D — Grok: modos, bots y ajustes

## 8.1 Composer principal

Tabs superiores:

- Pregunta
- Imagine

Acciones:

- menú;
- chip de conectores;
- input;
- botón `+`;
- selector de modo;
- micrófono;
- botón voz/hablar.

---

## 8.2 Selector de modo

Opciones visibles:

```text
Build
Heavy
Expert
Fast
```

El estado seleccionado se indica con check.

Semántica:

```json
{
  "mode": "expert",
  "description": "thinks_hard"
}
```

---

## 8.3 Lista de bots

Bots visibles:

- Grok Bot
- Orquestador HF
- Sentinela
- Orquestador Chat
- Revisor Agentes

Cada bot tiene:

- avatar/color;
- nombre;
- último mensaje;
- fecha;
- punto de no leído.

---

## 8.4 Ajustes del bot

Controles detectados:

- plugins;
- auto-review;
- reglas de auto-review;
- zona horaria automática;
- zona horaria;
- ordenador del bot;
- notificaciones;
- apariencia;
- idioma;
- háptica;
- ayuda;
- privacidad;
- términos;
- comentarios;
- cerrar sesión.

### Auto-review

Descripción observada: exigir aprobación para acciones consideradas arriesgadas.

Patrón:

```text
ACCIÓN
  ↓
CLASIFICACIÓN DE RIESGO
  ↓
SI ES RIESGOSA → APROBACIÓN HUMANA
  ↓
EJECUTAR
```

---

# 9. E — Devin: agente de código

## 9.1 Composer principal Agent / Ask

Elementos:

- toggle `Agent / Ask`;
- textarea;
- botón `+`;
- comandos;
- ajustes;
- razonamiento;
- micrófono;
- audio;
- enviar;
- selector de repositorio;
- selector de rama.

### Menú de contexto del agente

Opciones visibles:

- Virtual environment
- Security profile
- Notable repositories
- Manage MCP connectors

---

## 9.2 Comandos slash

Popup con:

- búsqueda;
- `/ask`;
- `/scan`;
- acción `Switch to Ask mode`.

Contrato:

```json
{
  "commands": [
    {"name": "/ask", "action": "switch_to_ask"},
    {"name": "/scan", "action": "scan_repository"}
  ]
}
```

---

## 9.3 Selector de rama

Dropdown:

- campo `Search branches...`;
- rama activa;
- check de selección.

---

## 9.4 Connections

Pantalla:

- información de MCP;
- acceso a `Customize`;
- Devin Desktop;
- integraciones;
- GitHub vinculado;
- acción `Unlink user`.

---

## 9.5 Environment

Tabs:

```text
Blueprints
Snapshots
Advanced
Outposts
```

### Blueprints

- snapshot construido;
- botón `View snapshot`;
- `Organization blueprint`;
- repositorios;
- búsqueda de repositorio.

### Configuración de snapshots

- `Auto-build snapshots`;
- `Differential builds`;
- `Clone repositories on all platforms`;
- `Build schedule`;
- selector frecuencia;
- próxima ejecución;
- `Save schedule`.

### Snapshot detalle

Propiedades:

- Active;
- Ubuntu;
- Status = Success;
- Trigger;
- Platform;
- Started;
- Duration;
- Delete;
- Activate this snapshot.

### Outposts

Permite ejecutar sesiones en máquinas propias.

Comando observado:

```bash
devin worker start
```

---

## 9.6 Configuración de agentes de sesión

Campos:

- Default agent;
- API default agent;
- Default platform.

Valores visibles:

```text
Default agent: Normal
API default: Use org default
Platform: Ubuntu
```

---

## 9.7 Custom commands

Bloque:

- `Manage commands`;
- `Add Command`;
- estado vacío `No commands configured`.

---

## 9.8 Usage limits

Ejemplo:

```text
Batch limit: 30 sessions
Message usage limit: ...
```

---

## 9.9 Pull request settings

Toggles visibles:

- Share prompts in PRs;
- Require @Devin to respond;
- Require session access for PR comments;
- Auto-add reviewer;
- Allow PRs to be opened by session participants.

Select:

- Open PRs as: Devin.

Secciones:

- Responding to bots;
- Security profiles.

---

## 9.10 PR Review

Pantallas de revisión muestran:

- repo;
- PR;
- branch origen/destino;
- número de archivos;
- líneas agregadas/eliminadas;
- trial banner;
- estado `Ready to merge`;
- botón `Merge`;
- menú:
  - Create a merge commit;
  - Squash and merge;
  - Rebase and merge;
- tabs:
  - Changes;
  - Description;
  - Discussion;
- análisis de Devin;
- resumen;
- evidencias;
- lista de archivos;
- diff;
- terminal/progress.

### Ajustes del diff

Opciones:

- Split view
- Unified view
- Hide whitespace
- Smart diffs
- Comments
- Hide highlights
- File tree on left

---

# 10. F — YAIWES / MAXBRY ROUTER

Esta familia constituye el bloque más importante para reproducir el panel propio.

## 10.1 Navegación lateral

Barra vertical estrecha con iconos.

Estados:

```text
icono normal = gris
icono seleccionado = marco/acento verde
```

Secciones inferidas:

- conexiones;
- plantillas;
- ejecución;
- recursos;
- seguridad;
- ingeniería/configuración.

---

## 10.2 Header global

Ejemplo:

```text
Y
Connections · Fichas universales
V6.0
IMMUTABLE
[Cadena AI]
```

o

```text
Templates · DAG inmutables
V6.0
IMMUTABLE
[Cadena AI]
```

---

## 10.3 Plantillas DAG inmutables

Regla explícita de UI:

```text
SOLO SELECCIÓN Y EJECUCIÓN
NO SE EDITA EL DAG EN RUNTIME
SENTINEL BLOQUEA MODIFICACIONES
```

Plantillas observadas:

| ID | Nombre | Nodos | Tipo |
|---|---|---:|---|
| T01 | SIMPLE | 3 | system |
| T03 | REASONING-3 | 5 | reasoning |
| T06 | REASONING-6 | 8 | reasoning |
| T11 | RESEARCH PRO | 12 | research |
| T13 | RESEARCH ADV | 16 | research |
| T14 | CODE | 9 | code |
| T15 | ASK-COUNCIL | 9 | multi-agent |
| T16 | DEBATE | 8 | multi-agent |
| T17 | CONSENSUS | 11 | multi-agent |

Cada card muestra badge `LOCKED`.

La plantilla seleccionada usa borde/acento verde.

---

## 10.4 Preparar cadena de programación AI

Modal/panel:

```text
Preparar Cadena de Programación AI
DAG LOCKED
Selección de plantilla inmutable
```

Columna izquierda:

- lista de plantillas.

Columna derecha:

- resumen;
- nombre plantilla;
- `IMMUTABLE`;
- profundidad;
- investigación;
- Sentinel;
- Judge;
- explicación de por qué se usa la plantilla.

---

## 10.5 Profundidad de razonamiento

Opciones visibles:

```text
SIMPLE
R3
R4
R6
R8
R12
```

Solo una activa.

---

## 10.6 Nivel de investigación

```text
NONE
R1
R2
R3
```

---

## 10.7 Opciones

Toggles:

```text
Sentinel activo (fijo)
Judge al final
Evidence Graph
WHY THIS TEMPLATE
Permitir escalación
```

Además:

```text
Max retries = 2
```

Botones:

- Cancelar
- Aplicar cadena y continuar

---

## 10.8 Run / ejecución

Pantalla:

```text
Run · RESEARCH ADV
READY
SENTINEL OK
[Preparar cadena]
```

Tarjeta de estado:

```text
Plantilla T11 cargada.
DAG inmutable verificado por Sentinel.
12 nodos.
Evidence Graph activo.
```

Badges:

- R3 RESEARCH
- RED/BLUE READY

---

## 10.9 Engineering Control

Toggles observados:

- MCP Connectors = ON
- GitHub Adapter = ON
- HuggingFace Tools = OFF
- SSH / Remote Hosts = OFF
- Evidence Graph Export = ON
- Circuit Breaker = ON

### Contrato

```json
{
  "engineeringControl": {
    "mcpConnectors": true,
    "githubAdapter": true,
    "huggingFaceTools": false,
    "sshRemoteHosts": false,
    "evidenceGraphExport": true,
    "circuitBreaker": true
  }
}
```

---

## 10.10 Connections / Fichas universales

Cabecera:

```text
MAXBRY ROUTER
Orquestador Determinista de DAGs & Conectores Universales
V6.0 CORE
IMMUTABLE
RAM 14.8 GB
```

Sección:

```text
Canvas de Fichas / Conectores
Puertos universales 1–100
```

Botón:

```text
+ Conectar Nueva Ficha
```

---

## 10.11 Tarjeta de conector

### GitHub

```text
Conector GitHub
namespace: repo.github.main
status: CONNECTED

Input Ports: 01 - 50
Output Ports: 01 - 50
Transport: HTTPS API
Health: OK
[Inspeccionar]
```

### Hugging Face

```text
HuggingFace Hub
namespace: ai.hf.hub
status: CONNECTED

Input Ports: 01 - 20
Output Ports: 01 - 25
Transport: REST API
Health: OK
[Inspeccionar]
```

---

## 10.12 Registrar nueva ficha / conector

Campos:

```text
connector_id
namespace
puertos
transport
```

Ejemplo:

```json
{
  "connector_id": "ConectorNuevo",
  "namespace": "custom.plugin.main",
  "ports": "01-50",
  "transport": "HTTPS API"
}
```

Botones:

- Cancelar;
- Aplicar y Continuar.

---

## 10.13 Inspeccionar conector

Modal:

- ID;
- namespace;
- status;
- input ports;
- output ports;
- transport;
- health;
- JSON equivalente;
- desconectar;
- cerrar.

Ejemplo:

```json
{
  "connector_id": "Conector GitHub",
  "namespace": "repo.github.main",
  "puertos": "01 - 50",
  "transport": "HTTPS API",
  "health": "OK"
}
```

---

## 10.14 Marketplace / lista de conectores

Pantalla alternativa:

- buscador;
- Gmail;
- Google Calendar;
- Google Drive;
- GitHub;
- Notion;
- Stripe;
- botones conectar/desconectar.

Regla:

```text
CONECTADO → botón Desconectar
DESCONECTADO → botón Conectar
```

---

# 11. G — Arquitectura, ejecución y evidencia observada en PR

Varias capturas muestran el panel de revisión de código y documentos arquitectónicos.

Elementos clave observados:

- plan de ejecución;
- inventario;
- arquitectura en capas;
- bloques de prueba;
- bloqueos reales;
- lista de evidencias;
- nodos abiertos;
- archivos agregados;
- runtime;
- cola/autoscaling;
- terminal de ejecución;
- estados de merge.

Estos pantallazos aportan un patrón importante:

```text
PLAN
  ↓
ARCHIVOS
  ↓
EJECUCIÓN
  ↓
EVIDENCIA
  ↓
REVISIÓN
  ↓
MERGE
```

No basta con que exista un archivo: la UI debe diferenciar entre:

```text
CREATED
TESTED
VERIFIED
READY
MERGED
BLOCKED
```

---

# 12. Componentes universales detectados

## 12.1 Navegación

```text
Sidebar
Topbar
Tabs
Bottom navigation
Breadcrumb
Back button
Overflow menu
```

## 12.2 Entrada

```text
Textarea
Text input
Search input
Selector
Dropdown
Radio
Toggle
Slider
File attach
Voice input
Command input
```

## 12.3 Estado

```text
Badge
Toast
Alert
Empty state
Progress
Health
Connected
Disconnected
Locked
Ready
Warning
Error
Needs intervention
```

## 12.4 Trabajo

```text
Task card
Agent card
Connector card
Template card
Repository card
PR card
Metric card
Evidence card
```

---

# 13. Contrato de componente universal

Una IA sin visión puede reconstruir cualquier módulo usando este contrato:

```json
{
  "id": "connector-github",
  "type": "connector-card",
  "title": "Conector GitHub",
  "subtitle": "repo.github.main",
  "status": "connected",
  "appearance": {
    "surface": "module",
    "selected": false,
    "accent": "green"
  },
  "data": {
    "inputPorts": "01-50",
    "outputPorts": "01-50",
    "transport": "HTTPS API",
    "health": "OK"
  },
  "actions": [
    {
      "id": "inspect",
      "label": "Inspeccionar",
      "event": "open_connector_detail"
    }
  ]
}
```

---

# 14. Estado global sugerido para frontend

```js
const appState = {
  theme: {
    mode: "dark-v07",
    background: "#1B1B1B",
    panel: "#202020",
    module: "#2A2A2A",
    selected: "#3C3C3C",
    mask: "#484848"
  },

  navigation: {
    activeSection: "connections"
  },

  chain: {
    template: "RESEARCH_ADV",
    reasoningDepth: "R6",
    researchLevel: "R2",
    immutable: true,
    sentinel: true,
    judge: true,
    evidenceGraph: true,
    whyThisTemplate: true,
    allowEscalation: true,
    maxRetries: 2
  },

  engineering: {
    mcp: true,
    github: true,
    huggingFace: false,
    ssh: false,
    evidenceExport: true,
    circuitBreaker: true
  },

  connectors: []
};
```

---

# 15. HTML semántico de referencia

```html
<!doctype html>
<html lang="es">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>YAIWES Control Panel</title>
  <link rel="stylesheet" href="app.css" />
</head>

<body>
  <div class="app-shell">

    <aside class="sidebar" aria-label="Navegación principal">
      <div class="brand">Y</div>

      <button class="nav-icon active" data-route="connections">◌</button>
      <button class="nav-icon" data-route="templates">▣</button>
      <button class="nav-icon" data-route="run">▶</button>
      <button class="nav-icon" data-route="resources">▤</button>
      <button class="nav-icon" data-route="security">🛡</button>
      <button class="nav-icon" data-route="engineering">⚙</button>
    </aside>

    <main class="workspace">

      <header class="topbar">
        <div>
          <strong id="screen-title">Connections · Fichas universales</strong>
        </div>

        <div class="topbar-actions">
          <span class="badge">V6.0</span>
          <span class="badge badge-locked">IMMUTABLE</span>
          <button class="button ghost">Cadena AI</button>
        </div>
      </header>

      <section class="hero card">
        <h1>MAXBRY ROUTER</h1>
        <p>Orquestador Determinista de DAGs & Conectores Universales</p>

        <div class="badge-row">
          <span class="badge">V6.0 CORE</span>
          <span class="badge badge-locked">IMMUTABLE</span>
        </div>

        <div class="metric-card">
          <small>RAM</small>
          <strong>14.8 GB</strong>
        </div>
      </section>

      <section class="section-header">
        <div>
          <h2>Canvas de Fichas / Conectores</h2>
          <p>Puertos universales 1–100</p>
        </div>

        <button class="button primary" id="new-connector">
          + Conectar Nueva Ficha
        </button>
      </section>

      <section id="connector-list" class="stack"></section>

    </main>
  </div>

  <dialog id="connector-modal" class="modal"></dialog>

  <script src="app.js"></script>
</body>
</html>
```

---

# 16. CSS de referencia

```css
* {
  box-sizing: border-box;
}

html,
body {
  margin: 0;
  min-height: 100%;
  background: var(--bg);
  color: var(--text);
  font-family: Inter, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
}

body {
  --bg: #1B1B1B;
  --panel: #202020;
  --module: #2A2A2A;
  --selected: #3C3C3C;
  --mask: #484848;
  --text: #EDEDED;
  --muted: #939393;
  --green: #36D58A;
  --border: rgba(255,255,255,.12);
}

button,
input,
select,
textarea {
  font: inherit;
}

.app-shell {
  min-height: 100vh;
  display: grid;
  grid-template-columns: 92px 1fr;
}

.sidebar {
  border-right: 1px solid var(--border);
  padding: 20px 12px;
  display: flex;
  flex-direction: column;
  gap: 14px;
  align-items: center;
}

.brand,
.nav-icon {
  width: 58px;
  height: 58px;
  border-radius: 14px;
}

.brand {
  display: grid;
  place-items: center;
  background: #103123;
  color: var(--green);
  font-weight: 800;
}

.nav-icon {
  border: 1px solid transparent;
  background: transparent;
  color: var(--muted);
}

.nav-icon.active {
  border-color: rgba(54,213,138,.35);
  background: rgba(54,213,138,.08);
  color: var(--green);
}

.workspace {
  width: min(1120px, 100%);
  margin: 0 auto;
  padding: 0 28px 40px;
}

.topbar {
  min-height: 88px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  border-bottom: 1px solid var(--border);
}

.topbar-actions,
.badge-row {
  display: flex;
  gap: 10px;
  align-items: center;
}

.badge {
  padding: 7px 12px;
  border-radius: 999px;
  background: rgba(54,213,138,.12);
  color: var(--green);
  font-size: 12px;
  font-weight: 700;
}

.badge-locked {
  color: #B6D63D;
  background: rgba(182,214,61,.12);
}

.card {
  background: var(--panel);
  border: 1px solid var(--border);
  border-radius: 20px;
  padding: 24px;
}

.hero {
  margin-top: 24px;
}

.metric-card {
  width: 150px;
  margin-top: 18px;
  background: #111714;
  border: 1px solid var(--border);
  border-radius: 14px;
  padding: 18px;
}

.metric-card strong {
  display: block;
  margin-top: 4px;
  font-size: 28px;
  color: #FFC451;
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: end;
  gap: 20px;
  margin: 28px 0 14px;
}

.button {
  border: 1px solid var(--border);
  background: var(--module);
  color: var(--text);
  padding: 12px 18px;
  border-radius: 12px;
  cursor: pointer;
}

.button.primary {
  background: var(--green);
  border-color: var(--green);
  color: #07150F;
  font-weight: 800;
}

.button.ghost {
  background: transparent;
}

.stack {
  display: grid;
  gap: 14px;
}

.connector-card {
  background: var(--panel);
  border: 1px solid var(--border);
  border-radius: 18px;
  padding: 20px;
}

.connector-card.connected {
  border-color: rgba(54,213,138,.22);
}

.connector-meta {
  display: grid;
  grid-template-columns: 1fr auto;
  gap: 8px 24px;
  background: #111714;
  border-radius: 12px;
  padding: 16px;
  margin-top: 16px;
}

.status-ok {
  color: var(--green);
}

@media (max-width: 760px) {
  .app-shell {
    grid-template-columns: 64px 1fr;
  }

  .workspace {
    padding-inline: 14px;
  }

  .topbar {
    align-items: flex-start;
    padding: 18px 0;
  }

  .topbar-actions {
    flex-wrap: wrap;
    justify-content: flex-end;
  }

  .section-header {
    align-items: stretch;
    flex-direction: column;
  }
}
```

---

# 17. JavaScript de referencia

```js
const connectors = [
  {
    id: "github",
    name: "Conector GitHub",
    namespace: "repo.github.main",
    status: "connected",
    inputPorts: "01 - 50",
    outputPorts: "01 - 50",
    transport: "HTTPS API",
    health: "OK"
  },
  {
    id: "hf",
    name: "HuggingFace Hub",
    namespace: "ai.hf.hub",
    status: "connected",
    inputPorts: "01 - 20",
    outputPorts: "01 - 25",
    transport: "REST API",
    health: "OK"
  }
];

function connectorCard(c) {
  return `
    <article class="connector-card ${c.status}">
      <header>
        <strong>${c.name}</strong>
        <span class="badge">${c.status.toUpperCase()}</span>
      </header>

      <p>${c.namespace}</p>

      <div class="connector-meta">
        <span>Input Ports:</span><span>${c.inputPorts}</span>
        <span>Output Ports:</span><span>${c.outputPorts}</span>
        <span>Transport:</span><span>${c.transport}</span>
      </div>

      <footer>
        <span class="status-ok">Health: ${c.health}</span>
        <button class="button inspect" data-id="${c.id}">
          Inspeccionar
        </button>
      </footer>
    </article>
  `;
}

function renderConnectors() {
  const el = document.querySelector("#connector-list");
  el.innerHTML = connectors.map(connectorCard).join("");
}

function openConnector(id) {
  const connector = connectors.find(x => x.id === id);
  const modal = document.querySelector("#connector-modal");

  modal.innerHTML = `
    <h2>Inspeccionar · ${connector.name}</h2>
    <pre>${JSON.stringify(connector, null, 2)}</pre>
    <button class="button" onclick="this.closest('dialog').close()">
      Cerrar
    </button>
  `;

  modal.showModal();
}

document.addEventListener("click", event => {
  const inspect = event.target.closest(".inspect");
  if (inspect) openConnector(inspect.dataset.id);
});

renderConnectors();
```

---

# 18. HTML para selector de plantilla DAG

```html
<section class="dag-builder card">
  <header class="section-header">
    <div>
      <h2>Preparar Cadena de Programación AI</h2>
      <p>Selección de plantilla inmutable · sin edición de DAG</p>
    </div>
    <span class="badge badge-locked">DAG LOCKED</span>
  </header>

  <div class="dag-grid">
    <div class="template-list">
      <button class="template-card">T01 · SIMPLE · 3 nodos</button>
      <button class="template-card">T03 · REASONING-3 · 5 nodos</button>
      <button class="template-card">T06 · REASONING-6 · 8 nodos</button>
      <button class="template-card">T11 · RESEARCH PRO · 12 nodos</button>
      <button class="template-card selected">T13 · RESEARCH ADV · 16 nodos</button>
      <button class="template-card">T14 · CODE · 9 nodos</button>
      <button class="template-card">T15 · ASK-COUNCIL · 9 nodos</button>
    </div>

    <aside class="template-summary card">
      <small>RESUMEN</small>
      <h3>RESEARCH ADV</h3>
      <div class="badge-row">
        <span class="badge badge-locked">IMMUTABLE</span>
        <span class="badge">R6</span>
        <span class="badge">R2</span>
      </div>
      <p>Sentinel: ON</p>
      <p>Judge: ON</p>
    </aside>
  </div>
</section>
```

---

# 19. HTML para automatizaciones

```html
<section class="automation-form">
  <header>
    <button aria-label="cerrar">×</button>
    <h1>Nueva automatización</h1>
    <button class="button primary">Crear</button>
  </header>

  <label>
    Nombre de la automatización
    <input type="text" placeholder="Nombre de la automatización" />
  </label>

  <section>
    <h2>Programación</h2>
    <button class="card add-trigger">
      + Seleccionar programación o activador
    </button>
  </section>

  <section>
    <h2>Instrucciones del proyecto</h2>
    <textarea placeholder="Dile al agente qué debe hacer"></textarea>
  </section>

  <section>
    <h2>Notificaciones</h2>

    <label class="toggle-row">
      <span>Notificaciones push</span>
      <input type="checkbox" />
    </label>

    <label class="toggle-row">
      <span>Correo electrónico</span>
      <input type="checkbox" />
    </label>
  </section>
</section>
```

---

# 20. Máquina de estados recomendada

```js
const Status = Object.freeze({
  IDLE: "idle",
  READY: "ready",
  RUNNING: "running",
  CONNECTED: "connected",
  DISCONNECTED: "disconnected",
  WARNING: "warning",
  ERROR: "error",
  BLOCKED: "blocked",
  LOCKED: "locked",
  NEEDS_INTERVENTION: "needs_intervention",
  VERIFIED: "verified",
  SUCCESS: "success",
  READY_TO_MERGE: "ready_to_merge"
});
```

### Transición general

```text
IDLE
 ↓
READY
 ↓
RUNNING
 ├─→ SUCCESS
 ├─→ WARNING
 ├─→ ERROR
 └─→ NEEDS_INTERVENTION
```

### Conectores

```text
DISCONNECTED
   ↓ connect
CONNECTING
   ├─→ CONNECTED
   └─→ ERROR
          ↓ retry
       CONNECTING
```

### DAG

```text
SELECT TEMPLATE
   ↓
LOCKED
   ↓
VALIDATE SENTINEL
   ↓
READY
   ↓
RUN
```

---

# 21. Modelo de datos unificado

```json
{
  "ui": {
    "theme": "dark-v07",
    "density": "comfortable",
    "mobileFirst": true
  },

  "router": {
    "name": "MAXBRY ROUTER",
    "version": "6.0",
    "immutable": true,
    "ram": "14.8 GB"
  },

  "navigation": {
    "active": "connections"
  },

  "templates": [
    {"id":"T01","name":"SIMPLE","nodes":3},
    {"id":"T03","name":"REASONING-3","nodes":5},
    {"id":"T06","name":"REASONING-6","nodes":8},
    {"id":"T11","name":"RESEARCH PRO","nodes":12},
    {"id":"T13","name":"RESEARCH ADV","nodes":16},
    {"id":"T14","name":"CODE","nodes":9},
    {"id":"T15","name":"ASK-COUNCIL","nodes":9},
    {"id":"T16","name":"DEBATE","nodes":8},
    {"id":"T17","name":"CONSENSUS","nodes":11}
  ],

  "chainConfig": {
    "templateId": "T13",
    "reasoning": "R6",
    "research": "R2",
    "sentinel": true,
    "judge": true,
    "evidenceGraph": true,
    "whyThisTemplate": true,
    "allowEscalation": true,
    "maxRetries": 2
  },

  "connectors": [
    {
      "name": "Conector GitHub",
      "namespace": "repo.github.main",
      "inputPorts": "01-50",
      "outputPorts": "01-50",
      "transport": "HTTPS API",
      "health": "OK",
      "status": "connected"
    },
    {
      "name": "HuggingFace Hub",
      "namespace": "ai.hf.hub",
      "inputPorts": "01-20",
      "outputPorts": "01-25",
      "transport": "REST API",
      "health": "OK",
      "status": "connected"
    }
  ]
}
```

---

# 22. Mapa funcional completo

```text
USUARIO
  │
  ├── CHAT / AGENTE
  │     ├── input
  │     ├── adjuntos
  │     ├── voz
  │     ├── comandos
  │     └── modos
  │
  ├── TAREAS
  │     ├── recientes
  │     ├── subtareas
  │     ├── programación
  │     └── métricas
  │
  ├── PLANTILLAS DAG
  │     ├── SIMPLE
  │     ├── REASONING
  │     ├── RESEARCH
  │     ├── CODE
  │     ├── COUNCIL
  │     ├── DEBATE
  │     └── CONSENSUS
  │
  ├── CADENA AI
  │     ├── profundidad
  │     ├── investigación
  │     ├── Sentinel
  │     ├── Judge
  │     ├── Evidence Graph
  │     └── retries
  │
  ├── CONECTORES
  │     ├── GitHub
  │     ├── Hugging Face
  │     ├── Gmail
  │     ├── Calendar
  │     ├── Drive
  │     ├── Notion
  │     └── Stripe
  │
  ├── ENGINEERING CONTROL
  │     ├── MCP
  │     ├── GitHub Adapter
  │     ├── HF Tools
  │     ├── SSH
  │     ├── Evidence Export
  │     └── Circuit Breaker
  │
  └── EVIDENCIA / REVISIÓN
        ├── archivos
        ├── diff
        ├── tests
        ├── terminal
        ├── estados
        └── merge
```

---

# 23. Inventario de las 74 capturas únicas

> Capturas repetidas enviadas más de una vez fueron consolidadas como un mismo estado visual.

| Archivo | Contenido principal |
|---|---|
| 1000078506.png | Marketplace de conectores: Gmail, Calendar, Drive, GitHub, Notion, Stripe |
| 1000078507.png | MAXBRY Router, cards GitHub/HF |
| 1000078508.png | Modal registrar nueva ficha/conector |
| 1000078509.png | MAXBRY Router con confirmación de registro |
| 1000078510.png | Preparar cadena AI con plantillas |
| 1000078511.png | Engineering Control |
| 1000078512.png | Run / ejecución / Sentinel |
| 1000078513.png | Plantillas DAG inmutables |
| 1000078514.png | Inspección de Conector GitHub |
| 1000078515.png | Preparar cadena: selección + resumen |
| 1000078516.png | Profundidad, investigación y toggles |
| 1000078517.png | Configuración completa + aplicar cadena |
| 1000078518.png | Resumen lateral de plantilla RESEARCH ADV |
| 1000079095.png | Manus: autorización del conector GitHub |
| 1000079099.png | Manus: estado necesita intervención |
| 1000079100.png | Manus: información/métricas de la tarea |
| 1000079101.png | Manus: menú contextual de tarea |
| 1000079102.png | Manus: Añadir al chat, primera mitad |
| 1000079103.png | Manus: Añadir al chat, herramientas adicionales |
| 1000079104.png | Manus: listado de habilidades |
| 1000079105.png | Manus: tareas recientes |
| 1000079106.png | Manus Agent: home |
| 1000079107.png | Manus Agent: home duplicado/estado equivalente |
| 1000079108.png | Manus: subtareas vacías |
| 1000079109.png | Manus: cuenta, plan y accesos |
| 1000079110.png | Manus: ajustes generales |
| 1000079111.png | Grok: lista de bots |
| 1000079112.png | Grok Bot: ajustes superiores |
| 1000079113.png | Grok Bot: ajustes inferiores |
| 1000079114.png | Grok Bot: conversación y rutinas |
| 1000079115.png | Devin: home Agent / Ask |
| 1000079116.png | Devin: environment/security/MCP popup |
| 1000079117.png | Devin: comandos slash |
| 1000079118.png | Devin Ask: selección de rama |
| 1000079119.png | Devin: Connections |
| 1000079120.png | Devin: detalle de Snapshot |
| 1000079121.png | Devin: auto-build y schedule |
| 1000079122.png | Devin: Outposts |
| 1000079123.png | Devin: Environment / Blueprints |
| 1000079124.png | Devin: comportamiento de links PR |
| 1000079125.png | Documento arquitectura: mini arquitectura |
| 1000079126.png | Documento arquitectura: inventario |
| 1000079127.png | Documento arquitectura: 3 capas |
| 1000079128.png | Documento arquitectura: bloques de ejecución |
| 1000079129.png | Documento arquitectura: bloqueos reales |
| 1000079130.png | Documento arquitectura: continuación |
| 1000079131.png | PR Review: Ready to merge |
| 1000079132.png | PR Review: opciones de merge |
| 1000079133.png | PR Review: diff de arquitectura |
| 1000079134.png | PR Review: terminal/progress |
| 1000079135.png | PR Review: menú de visualización del diff |
| 1000079136.png | PR Review: archivos de cadena/cola |
| 1000079137.png | PR Review: archivos router/runtime |
| 1000079138.png | PR Review: archivos de staff |
| 1000079139.png | PR Review: Summary |
| 1000079140.png | PR Review: evidencias/nodos abiertos |
| 1000079141.png | PR Review: análisis de Devin |
| 1000079142.png | Devin: agentes de sesión |
| 1000079143.png | Devin: comandos + usage limits |
| 1000079144.png | Devin: configuración de pull requests |
| 1000079145.png | Devin: PR, bots y security profiles |
| 1000079146.png | Grok: selector Build/Heavy/Expert/Fast |
| 1000079147.png | Grok: composer Pregunta |
| 1000079148.png | Nueva automatización: formulario principal |
| 1000079149.png | Nueva automatización: notificaciones |
| 1000079164.png | Manus: modal de rama alternativa |
| 1000079301.png | Dashboard social oscuro de referencia |
| 1000079302.png | Kit de controles oscuros |
| 1000079303.png | Dashboard financiero oscuro |
| 1000079323.png | Perfil visual FROMTED/YAIWES |
| 1000079327.png | Editor de tema + preview + biblioteca 2D |
| 1000079441.png | Claude: conectores y estado reconectar |
| 1000079451.png | Claude: lista de conectores |
| 1000079459.png | Claude: detalle MCP con error de registro |

---

# 24. Instrucción para otra IA sin visión

Copiar este bloque como contexto:

```text
Estás reconstruyendo una interfaz móvil/desktop oscura llamada YAIWES/FROMTED.

No necesitas ver las imágenes originales.

Usa fondo #1B1B1B.
Usa panel #202020.
Usa módulos #2A2A2A.
Usa seleccionado #3C3C3C.
Usa máscara #484848.

La interfaz debe ser modular y mobile-first.

Los bloques principales son:
1. Chat/agente.
2. Tareas y automatizaciones.
3. Conectores.
4. Plantillas DAG inmutables.
5. Preparación de cadena AI.
6. Engineering Control.
7. Ejecución y estados.
8. Evidencia/revisión.
9. Configuración visual.

Nunca ilumines todo el fondo con el color activo.
Usa el color activo solamente en bordes, iconos, badges, toggles y botones.

Los DAG no se editan en runtime.
La plantilla se selecciona y luego se configura:
- profundidad de razonamiento;
- nivel de investigación;
- Sentinel;
- Judge;
- Evidence Graph;
- WHY THIS TEMPLATE;
- escalación;
- retries.

Los conectores se representan como cards con:
- nombre;
- namespace;
- estado;
- input ports;
- output ports;
- transport;
- health;
- botón Inspeccionar.

Los estados fundamentales son:
idle, ready, running, connected, disconnected, warning, error,
blocked, locked, needs_intervention, verified, success, ready_to_merge.

Mantén una barra lateral compacta en desktop y un diseño apilado en móvil.
Todos los controles deben tener estados visibles y eventos explícitos.
```

---

# 25. Resumen final

El conjunto de capturas describe un sistema que combina:

```text
CHAT
+ AGENTES
+ TAREAS
+ AUTOMATIZACIONES
+ CONECTORES
+ DAGs INMUTABLES
+ CONTROL DE INGENIERÍA
+ EJECUCIÓN
+ EVIDENCIA
+ REVISIÓN DE CÓDIGO
+ TEMAS / ICONOS / APARIENCIA
```

La estructura de UI recomendada es:

```text
SHELL
├── SIDEBAR
├── TOPBAR
└── WORKSPACE
    ├── HERO / STATUS
    ├── TABS
    ├── CARDS
    ├── INPUTS
    ├── CONNECTORS
    ├── DAG BUILDER
    ├── EXECUTION
    ├── EVIDENCE
    └── MODALS / BOTTOM SHEETS
```

La regla transversal es:

```text
PETICIÓN
→ CONFIGURACIÓN
→ SELECCIÓN
→ VALIDACIÓN
→ EJECUCIÓN
→ ESTADO
→ EVIDENCIA
→ REVISIÓN
→ CIERRE
```

Este archivo puede usarse directamente como especificación de reconstrucción para una IA de código que no disponga de visión.
