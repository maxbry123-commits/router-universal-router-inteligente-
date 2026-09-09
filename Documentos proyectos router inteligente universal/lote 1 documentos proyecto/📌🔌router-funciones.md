# ROUTER MAXBRY — 98 FUNCIONES · 4 PANELES

**Fecha:** 2026-07-14 · **Versión:** v5.5 · **Arquitectura:** 3 capas (GitHub ↔ VPS ↔ Destinos)

---

## 📥 PANEL 1 — LISTA DE CONEXIONES + CHAT AI

### Básico
Panel inicial. Ves todas las conexiones enchufadas, con icono+estado. Puedes editar, apagar o borrar cada una. Hay un chat AI que interpreta español y arma fichas solo. Abajo hay un selector para cambiar qué agente/IA controla el chat.

### Funciones
1. `listarConexiones()` — devuelve array con todas las fichas activas
2. `renderizarConexion(item)` — dibuja fila con icono+título+botones
3. `editarConexion(id)` — abre Panel 2 con esa ficha cargada
4. `eliminarConexion(id)` — borra la ficha tras confirmar
5. `toggleConexion(id)` — enciende/apaga sin borrar
6. `crearNuevaConexion()` — abre Panel 2 vacío
7. `buscarConexion(query)` — filtra lista en vivo
8. `ordenarConexiones(campo)` — nombre/estado/tipo/fecha
9. `duplicarConexion(id)` — clona ficha con nuevo id
10. `abrirChatAI()` — enfoca input del chat
11. `enviarMensajeChat(texto)` — IA interpreta y rellena
12. `limpiarChat()` — borra historial visual
13. `exportarChat()` — baja conversación
14. `seleccionarAgenteChat(agente_id)` — qué IA controla el chat
15. `seleccionarModeloChat(modelo_id)` — qué modelo usa
16. `configurarPromptChat(texto)` — system prompt del chat
17. `abrirConfiguracionChat()` — modal con todas las opciones del agente
18. `abrirConfiguracionConectores()` — panel para pre-cargar APIs/MCPs

### Conexión Panel 1 → otros
- → Panel 2: `editarConexion(id)`
- → Backend: `GET /api/connections`, `POST /api/chat`
- → WebSocket: `connection.update`, `chat.token`

---

## ⚙️ PANEL 2 — EDITOR DE FICHA

### Básico
Configuras UNA conexión. Tiene 4 secciones: Entrada (qué recibo, 1-100), Anclaje (qué sé, docs+sandbox+system prompt), Salida (a dónde mando, 1-100), Otras (priority, timeout, etc). Cada sección tiene su ON/OFF.

### Sección ENTRADA
19. `agregarEntradaFicha(tipo, sistema, params)` — suma conector a entrada
20. `eliminarEntradaFicha(idx)` — quita
21. `seleccionarTipoEntrada(tipo)` — api/mcp/doc/webhook/chat/repo/telegram/archivo
22. `seleccionarSistema(tipo, idx)` — elige sistema del catálogo pre-cargado
23. `validarEntrada(entrada)` — enchufe gate v1.5
24. `reordenarEntradas(origen, destino)` — drag&drop
25. `toggleEntrada(idx)` — on/off individual
26. `duplicarEntrada(idx)` — clona slot
27. `probarEntrada(idx)` — ping al sistema
28. `configurarParamsEntrada(idx, params)` — endpoint, headers, auth

### Sección ANCLAJE
29. `anclarDocumento(file)` — sube doc al sandbox
30. `anclarTexto(texto)` — pega texto plano
31. `anclarInstrucciones(texto)` — reglas
32. `editarSystemPrompt(texto)` — prompt del sistema
33. `abrirSandboxCode()` — editor código
34. `ejecutarCodigoSandbox()` — corre el código
35. `toggleAnclaje(tipo)` — on/off anclaje
36. `eliminarAnclaje(id)` — borra anclaje
37. `versionarAnclaje(id)` — git-like
38. `previewAnclaje(id)` — vista previa

### Sección SALIDA
39. `agregarSalidaFicha(tipo, sistema, params)`
40. `eliminarSalidaFicha(idx)`
41. `seleccionarTipoSalida(tipo)` — vps/hf/repo/agente/chat
42. `seleccionarDestino(tipo, idx)` — del catálogo
43. `validarSalida(salida)` — enchufe gate
44. `toggleSalida(idx)`
45. `reordenarSalidas(origen, destino)`
46. `probarSalida(idx)` — ping
47. `configurarParamsSalida(idx, params)`

### Sección OTRAS
48. `configPrioridad(valor)` — 1-10
49. `configFallback(id)` — cadena respaldo
50. `configTimeout(ms)`
51. `configReintentos(n)`
52. `configRateLimit(rpm)`
53. `configModoEnvio(modo)` — primero/todos/espejo
54. `configCredenciales(id, key)` — desde vault
55. `configSchedule(cron)` — programar
56. `configCostoMax(usd)` — tope gasto
57. `configTags(tags[])` — etiquetas
58. `configACL(rules)` — permisos ruta
59. `configNamespace(nombre)` — ai.llm.openrouter
60. `guardarFicha()` — persiste
61. `borrarFicha()` — elimina
62. `probarFicha()` — corre test end-to-end

### Conexión Panel 2 → otros
- → Backend: `PUT /api/connections/{id}`, `POST /api/connections/{id}/test`
- → Vault: `GET /api/vault/{name}`
- → WebSocket: `connection.saved`, `connection.tested`

---

## 🔌 PANEL 4 — CONFIGURACIÓN DE CONECTORES (NUEVO)

### Básico
Aquí pre-cargas TODAS tus APIs, MCPs, webhooks, repos, VPS, HF, Telegram, etc UNA SOLA VEZ. Después aparecen en los selectores del Panel 2 sin tener que meter credenciales cada vez. Es como tu "billetera" de conectores.

### Funciones
63. `listarConectoresPreconfigurados()` — los que ya tienes
64. `agregarConectorPreconfig(tipo, sistema, params)` — suma uno
65. `eliminarConectorPreconfig(id)`
66. `editarConectorPreconfig(id, params)`
67. `toggleConectorPreconfig(id)` — on/off
68. `probarConectorPreconfig(id)` — verifica credenciales
69. `seleccionarCategoria(cat)` — ai/cloud/db/messaging/repos/storage/email/infra/webhooks
70. `importarConectorMasivo(yaml)` — sube varios a la vez
71. `exportarConectores(yaml)` — baja config
72. `probarTodosConectores()` — health check batch
73. `seleccionarSistemasParaFicha(tipo, slot)` — abre modal con pre-cargados

### Conexión Panel 4 → otros
- → Panel 2: alimenta el `seleccionarSistema()` y `seleccionarDestino()`
- → Backend: `GET/POST/PUT/DELETE /api/connectors/lib`
- → Vault: conecta con `guardarSecreto()`

---

## 🤖 PANEL 5 — CONFIGURACIÓN AGENTE/AI DEL CHAT (NUEVO)

### Básico
Aquí cambias qué agente (OpenHand, Claude, MiniMax, OpenClaw) y qué modelo controla el chat del Panel 1. También editas su system prompt y parámetros.

### Funciones
74. `listarAgentesDisponibles()` — Claude, OpenClaw, MiniMax, OpenHand
75. `seleccionarAgenteChat(agente_id)` — activa uno
76. `listarModelosDispon()` — 10 del registry
77. `seleccionarModeloChat(modelo_id)`
78. `editarSystemPromptChat(texto)`
79. `configTemperature(valor)` — 0-1
80. `configMaxTokens(valor)`
81. `configTopP(valor)`
82. `configFrecuenciaP(valor)`
83. `configPresenciaP(valor)`
84. `probarAgenteChat(mensaje)` — ping
85. `resetAgenteChat()` — valores default
86. `verHistorialAgente()` — últimas N conversaciones
87. `crearAgenteCustom(nombre, config)` — crea uno nuevo

### Conexión Panel 5 → otros
- → Panel 1: alimenta `seleccionarAgenteChat()`
- → Backend: `GET/PUT /api/chat/agent`, `GET /api/agents/registry`
- → Model Registry: `GET /api/models/registry`

---

## 📊 PANEL 3 — EXTRAS

### Básico
12 paneles adicionales para monitorear, configurar y operar el sistema completo.

### Funciones
88. `panelProvider()` — 18 gateways con toggle+test
89. `panelModelos()` — 10 modelos con metadatos
90. `panelMarketplace()` — instalar/desinstalar conectores
91. `panelMapaRed()` — grafo visual de nodos
92. `panelLiveGraph()` — D3 animado en vivo
93. `panelTrazabilidad()` — trace_id inspector
94. `panelCostes()` — gasto por provider/agente
95. `panelSecretVault()` — AES-256 credenciales
96. `panelScheduler()` — cron jobs
97. `panelCola()` — pendientes/ejecutando/pausadas
98. `panelRecovery()` — circuit breaker

### Conexión Panel 3 → otros
- → Backend: múltiples endpoints según panel
- → WebSocket: `provider.status`, `cost.update`, `queue.update`, `cb.open`
- → Mapa: alimenta `obtenerMapaRed()`

---

## 🔄 FLUJO HORIZONTAL TRANSVERSAL

```
TÚ ─escribes→ [P1 chat AI] ─interpreta→ [P2 armas] ─guarda→ [P4 pre-carga] ─monitorea→ [P3 extras] ─resultado
                          ↓                                              ↓                ↓
                    [P5 agente/modelo]                              [Vault seguro]   [P5 también]
```

---

## 📡 MAPA DE COMUNICACIÓN

| Origen | Destino | Método | Trigger |
|--------|---------|--------|---------|
| P1 → P2 | abrir ficha | interno | click ✏️ |
| P1 → Backend | GET /api/connections | REST | mount |
| P1 → P5 | cambio agente | interno | click config |
| P2 → Backend | PUT /api/connections/{id} | REST | guardar |
| P2 → P4 | lee conectores | GET | al montar |
| P2 → Vault | GET /api/vault/{n} | REST | al usar credencial |
| P3 → Backend | múltiples | REST+WS | tiempo real |
| P4 → Vault | POST /api/vault | REST | al guardar conector |
| P5 → P1 | set agente | interno | al cambiar |
| P5 → Backend | GET /api/agents/registry | REST | al montar |
| P4 → P2 | alimenta selectores | interno | al elegir |

---

## ✅ TOTAL: 98 funciones distribuidas en 5 paneles
