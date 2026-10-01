# 📂 readme chat Arquitectura
Proyecto: **CHAT YAIWES (chat router)** — separado del Router Inteligente Universal (el Router solo se usa como servicio).
Fuente de verdad de las instrucciones: `../00-INSTRUCCIONES/` · Plan y DSL DAG: `../01-PLAN/PLAN-MAESTRO-CHAT.yaml` · Estado: `../03-ESTADO/`.
Cuando todo esté probado, esta raíz se exporta sin historial al repo YAIWES (M43, M44).

## 1. Capas (de arriba abajo)
```
TÚ (chat en Vercel = solo pantalla)
  │
  ▼
ROUTER YAIWES (HF Job 16 GB de pago, siempre encendido)  ← único punto de entrada de modelos para TODOS (M44.1-2)
  ├─ OmniRoute privado (misma máquina, 127.0.0.1:20128)   ← proveedores + fallback
  ├─ APIs propias: NVIDIA (Kimi K3 / DeepSeek V4 si existen) → Cerebras → Groq → DeepSeek V4 Flash solo con claves del Director (M43)
  ├─ Cola de tareas + vigilante: enciende procesadores 16 GB (80%) y cadena 32 GB (85%, hasta 10) (M30, M31)
  └─ Conector MCP de Claude (misma máquina; letrero fijo Vercel) (M33)
  │
  ▼
DEEPSEEK HARNESS (Cordis) = cerebro operativo del chat: plugins Router, memoria, skills, tools, sandbox (M7, M42)
  │
  ▼
EVIDENCE/SEARCH GATE (doc 26): parser → 12 goals → búsquedas → evidence pack → ejecutor → verificación → 12 goals → Sheriff
  │
  ▼
JERARQUÍA DE AGENTES (doc 23)
  Rowboat (director) → Hermes + OpenClaw (plan A/B, debate, supervisión) → Sheriff (código) → Ruflo (colmena)
  → Colmena → Sentinel (vigila) → Hermes + OpenClaw (revisión cruzada) → Judge (código): PASS / REVISE / BLOCK
  │
  ▼
CADENA DE INGENIERÍA en MIRROR aislado (doc 22, M43)
  Claude Code diseña → Grok ejecuta → Claude Code revisa y corrige → Meta ×4 (código, tests, visual, adversarial) → Meta Code corrige → Sheriff → merge selectivo
  Trabajo nuevo → mirror nuevo con SOLO el equipo de ingeniería y SOLO el sistema a tocar.
  │
  ▼
STATE HUB (doc 24): único escritor. Eventos → BITACORA.jsonl (inmutable) → STATE.json, CRAZY_WALL.json, HANDOFF.md, TASK.json por tarea
  │
  ▼
MEMORIA Y ALMACENAMIENTO (componentes del Director, solo cablear — M44.4)
  Conversaciones y documentos: Router (store) · Grafo/tiempo: Graphiti + FalkorDB · Memoria de agentes: Memanto · Grafo de código: Graphify
  Experiencia de agentes: AgentDB · Archivos grandes: HF Storage Bucket · Relacional/caché: PostgreSQL + Redis (como servicio)
```

## 2. Reglas fijas
- Todos los agentes y el chat usan **nuestro Router** para cualquier modelo (M44.1-2). Sin APIs de Anthropic.
- Todos los agentes tienen acceso a HF y a todos los repos de GitHub (M43).
- Nadie escribe estado a mano: todo pasa por el State Hub (doc 24).
- Sheriff y Judge son código, no IA. La IA que ejecuta no cierra su propio trabajo (doc 26).
- Descargas solo con el motor de descarga y extracción. Nada de código desde cero si hay componente descargado.
- Todo lo de este proyecto vive en esta raíz; nada suelto fuera (M44.3).

## 3. Dónde vive cada cosa (hoy)
| Pieza | Dónde | Estado |
|---|---|---|
| Pantalla del chat | Vercel `riu-jev-bridge` | Publicada (pendiente base aprobada por el Director) |
| Router + OmniRoute | Job HF 16 GB (`riu-router-job-central.yml`) | Router OK; OmniRoute en prueba |
| Conector MCP | Space del conector (temporal) → irá a la máquina 16 GB | Funciona sin OAuth |
| Agentes | `router inteligente universal/Componente open soure…/` + forks `maxbry123-commits/openclaw`, `/hermes-agent` | Descargados, sin conectar |
| Estado del proyecto | `../03-ESTADO/` | Iniciado 27-sep |

## 4. Auditoría de recuperación — 2026-10-01 (rama de trabajo)

Este apartado describe el código comprobado en la rama del PR; el esquema de arriba es el objetivo de arquitectura y no demuestra servicios en producción.

- Manus dejó `../04-MEMORIA/memoria_yaiwes/__init__.py`, el loader `integration/chat_mvp/memoria_loader.py` y las rutas autenticadas `/memoria/health`, `/memoria/save`, `/memoria/load`, `/memoria/search`. SQLite persiste tras reiniciar el proceso; el grafo SQLite ofrece un fallback de relación. La prueba local focalizada pasó 8/8 con `PYTHONPATH` que incluye el Router y `04-MEMORIA`.
- Graphiti y Graphify tienen código fuente descargado, pero el adaptador solo detecta endpoints configurados y supone rutas HTTP genéricas; no hay servicio Graphiti/FalkorDB ni índice Graphify del chat verificado. FalkorDB y AgentDB figuran como `EXTRACTED_VERIFIED` en la evidencia RDC, sin runtime conectado. El inventario antiguo conserva `GAP_ABSENT` para ambos: leer la evidencia posterior antes de interpretar ese valor.
- El envío normal `/chat/send` registra el turno en el store del Router y, en esta rama, también invoca la fachada de memoria con scope de propietario y read-back. Una caída de esta memoria secundaria deja el turno principal intacto y devuelve `🚩 PENDIENTE`. Las pruebas locales usan un proveedor simulado; el puente H-1 de snapshot/restauración HF, Memanto operativo, PostgreSQL y Redis siguen sin verificación de extremo a extremo. M-0..M-7 reflejan avance local con GAPs; no declarar cobertura integral de memoria.
- El DAG T-01 reunió capturas y componentes visuales; su ubicación actual es `../01-PLAN/REFERENCIAS-UI/` (65 referencias UI, 5 diagramas del Router y 12 capturas del chat) y `../01-PLAN/SKILLS-MAXBRY-UI/` (82 skills y componentes). Los catálogos suman 82 PNG; `/chat/org/visual-references` verifica SHA-256 y devuelve metadatos autenticados sin bytes de imagen. Las rutas antiguas escritas en los bloques literales son procedencia, no rutas ejecutables. Las imágenes todavía no están conectadas al frontend ni inspeccionadas visualmente una por una.
- Durante el trabajo activo, guardar un checkpoint al entrar y como máximo cada 15 minutos; leer `../03-ESTADO/CHECKPOINT.json`, proyectar Bitácora → STATE/Crazy Wall/Handoff y hacer read-back. Esta cadencia requiere que el agente invoque la guardia: no es un daemon ni una Automation independiente. La guardia auxiliar de 100 IDs se creó al interpretar el ejemplo de 100 pasos del Director; no hay evidencia de un archivo separado prometido y su reloj permanece en cero. No bloquea el trabajo con los DAG existentes.
- La auditoría de cuatro pasadas y el orden de implementación están en `../01-PLAN/PLAN-ACCION-XRAY.md`; los JSON de `../01-PLAN/AUDITORIA-4-PASADAS*.json` detallan los resultados por archivo. La presencia de fuentes y hashes no implica conexiones externas, ejecución de skills o aceptación T-06.
- La Puerta T-11 normaliza consultas con IDs reproducibles, registra errores por adaptador en `observations` y conserva resultados del adaptador que sí responde. Un error requerido deja el paquete `INCOMPLETE`. `EvidencePacket.packet_hash` se recalcula al verificar el contenido local; no firma el paquete ni acredita la identidad de un reviewer. El adaptador GitHub tiene timeout HTTP de 10 s y la búsqueda local comprueba un plazo entre archivos; 🚩 PENDIENTE: cancelación dura de E/S local bloqueada y autenticación de receipts externos.
- Los eventos nuevos del State Hub llevan `schema` v2, `event_id` y `payload_hash` recalculado al leer. El replay local reconstruye snapshots perdidos y comprueba read-back de la Bitácora antes de proyectar. Los eventos heredados permanecen sin hash para compatibilidad; 🚩 PENDIENTE: integridad/autenticación de la historia heredada, append-only remoto verificable y concurrencia entre procesos.

## 5. T-06 — web app responsive en validación

El shell real usa paneles HTML/JS servidos por el Router, operaciones `/chat/*` y `/chat/org/*` y el contrato visual V07. El inventario de controles está en `../01-PLAN/T-06-INVENTARIO.md`. La capa responsive aplica grid fluido, navegación horizontal contenida, controles táctiles de 44 px, foco visible y transiciones de color opcionales con `prefers-reduced-motion`. Son cambios de implementación; su calidad visual y funcional sigue pendiente de una segunda prueba real desktop/tablet/mobile.

En el mismo origen, si `RIU_ROUTER_API_KEY` está configurada, `/chat/ui/*` pide autenticación Basic al navegador con usuario `router` y contraseña igual a esa clave; el middleware verifica por comparación constante e inyecta `X-API-Key` internamente para las rutas protegidas existentes. El JavaScript del shell no solicita ni guarda la clave; las solicitudes llevan `credentials: same-origin`. La clave continúa siendo requerida por el backend y debe configurarse junto con su identidad en `RIU_AGENT_API_KEYS` para los endpoints del Router. Una prueba local con TestClient verifica desafío 401, acceso a asset y API, y credenciales incorrectas; no equivale a validación visual en Chrome ni a servicios externos conectados. Si la clave no se configura, la UI mantiene el régimen de acceso del despliegue previo: no considerar esa configuración segura para acceso público.
