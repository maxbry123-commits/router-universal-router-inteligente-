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
- El envío normal `/chat/send` registra el turno en el store del Router y no invoca `memoria_yaiwes.save`; la prueba de memoria usa `/memoria/save`. El puente H-1 de snapshot/restauración HF, Memanto operativo, PostgreSQL y Redis siguen sin verificación de extremo a extremo. M-0..M-7 reflejan avance local con GAPs; no declarar cobertura integral de memoria.
- El DAG T-01 reunió capturas y componentes visuales bajo `../../📂 Skills Maxbry UI fromtend/`. Una pasada adicional reunió 38 documentos FROMTED, scripts, manifiestos y archivos del laboratorio visual antes sueltos en la raíz: 37 renames Git 100 % y una copia de README Rare UI con SHA-256 idéntico. Las imágenes de arquitectura de la carpeta del Router permanecen con su documentación.
- Durante la recepción del próximo plan, guardar un checkpoint al entrar y como máximo cada 15 minutos de trabajo activo; leer `../03-ESTADO/CHECKPOINT.json`, proyectar Bitácora → STATE/Crazy Wall/Handoff y hacer read-back. Esta cadencia requiere que el agente invoque la guardia: no es un daemon ni una Automation independiente. El reloj de 3 h 45 min / 95 % no empieza hasta validar el original de 100 pasos.
