# HANDOFF — Cableado del chat YAIWES v7

Actualizado: 2026-10-07.

> ESTADO VIGENTE. Este documento describe el cableado actual del chat YAIWES en `main`: frontend Vercel, backend FastAPI, `puente_chat`, proveedores/DeepSeek, memoria/almacenamiento y las dos vías autorizadas del Router hacia Hugging Face. No contiene claves ni secretos.

## 0. Estado ejecutivo

- Chat producción: https://riu-jev-bridge.vercel.app/
- Frontend fuente: https://github.com/maxbry123-commits/router-universal-router-inteligente-/tree/main/chat%20router/chat%20frontend
- Backend Chat MVP: https://github.com/maxbry123-commits/router-universal-router-inteligente-/tree/main/router%20inteligente%20universal/integration/chat_mvp
- Backend `puente_chat`: https://github.com/maxbry123-commits/router-universal-router-inteligente-/tree/main/router%20inteligente%20universal/plugins/puente_chat
- Router HF principal publicado actualmente: `6ac593acfbc85ba6823baf04`
- Base principal actual: https://6ac593acfbc85ba6823baf04--8000.hf.jobs
- Puerta principal del chat: https://6ac593acfbc85ba6823baf04--8000.hf.jobs/plugins/puente_chat/call
- `LIVE_URL.json`: https://github.com/maxbry123-commits/router-universal-router-inteligente-/blob/main/router%20inteligente%20universal/LIVE_URL.json
- Memoria canónica: https://github.com/maxbry123-commits/router-universal-router-inteligente-/tree/main/chat%20router/04-MEMORIA/memoria_yaiwes
- Adaptador `memory_runtime.py`: PRESENTE en `main`.
- Segunda vía Router → Hugging Face: AUTORIZADA como ruta de respaldo directa y separada; no debe confundirse con un duplicado accidental del Router principal.
- Los Jobs L4 temporales de modelos `hf-*` son además respaldos de modelo bajo demanda; tampoco deben confundirse con el Router principal ni con la segunda vía Router→HF.

## 1. Flujo global real

```text
USUARIO / NAVEGADOR
        ↓
https://riu-jev-bridge.vercel.app/
        ↓
Vercel sirve shell.html + panel-chat.html + panel-chat.js
        ↓
api.js
        ↓
lee LIVE_URL.json
        ↓
RUTA PRINCIPAL
Router HF publicado :8000
        ↓
public_chat_app.py
        ↓
integration/chat_mvp/app.py
        ↓
Plugin Host /plugins
        ↓
/plugins/puente_chat/call/chat_async
        ↓
puente_chat/plugin.py
        ↓
proveedor / DeepSeek / HF / NVIDIA / Groq / herramientas
        ↓
memory_runtime.py
        ↓
memoria_loader.py
        ↓
memoria_yaiwes
        ↓
Store / SQLite / grafo / almacenamiento
        ↓
/plugins/puente_chat/call/resultado
        ↓
api.js hace polling
        ↓
panel-chat.js pinta la respuesta
```

Ruta adicional autorizada:

```text
CHAT / ROUTER
      ↓
SEGUNDA VÍA DE RESPALDO
      ↓
HUGGING FACE DIRECTO
      ↓
modelo / servicio disponible
```

La segunda vía HF es deliberada. No debe ser eliminada durante limpiezas de Jobs o auditorías de duplicados.

## 2. Frontend del chat

Raíz exacta:
https://github.com/maxbry123-commits/router-universal-router-inteligente-/tree/main/chat%20router/chat%20frontend

Archivos principales:

- `panel-chat.html`: DOM principal del chat.
- `panel-chat.js`: comportamiento, controles, historial visible, anclas y acciones.
- `api.js`: cliente HTTP; resuelve Router, llama `puente_chat`, maneja polling, sesión y respaldo HF.
- `config.js`: fallback estático y catálogo visible de modelos/motores.
- `shell.html` / `shell.js`: shell general.
- `panel-archivos.html/js`: archivos y adjuntos.
- `panel-canvas.html/js`: panel Canvas.
- `panel-org.html/js`: organización/agentes.
- `panel-seguimiento.html/js`: seguimiento.
- `responsive.css`, `shell.css`: estilos.
- `vercel.json`: rewrites de Vercel.

Enlaces directos:

- https://github.com/maxbry123-commits/router-universal-router-inteligente-/blob/main/chat%20router/chat%20frontend/panel-chat.html
- https://github.com/maxbry123-commits/router-universal-router-inteligente-/blob/main/chat%20router/chat%20frontend/panel-chat.js
- https://github.com/maxbry123-commits/router-universal-router-inteligente-/blob/main/chat%20router/chat%20frontend/api.js
- https://github.com/maxbry123-commits/router-universal-router-inteligente-/blob/main/chat%20router/chat%20frontend/config.js
- https://github.com/maxbry123-commits/router-universal-router-inteligente-/blob/main/chat%20router/chat%20frontend/shell.js
- https://github.com/maxbry123-commits/router-universal-router-inteligente-/blob/main/chat%20router/chat%20frontend/vercel.json

### Resolución del backend desde el navegador

`config.js` contiene fallback estático. La ruta dinámica del principal se resuelve desde:

https://raw.githubusercontent.com/maxbry123-commits/router-universal-router-inteligente-/main/router%20inteligente%20universal/LIVE_URL.json

`api.js` ejecuta `liveRouter()` y actualiza `apiBase` y `harnessUrl` cuando cambia el Job publicado.

Protocolo principal:

```text
POST <LIVE_URL>/plugins/puente_chat/call/chat_async
POST <LIVE_URL>/plugins/puente_chat/call/resultado
```

La UI conserva un identificador de sesión en `sessionStorage` para la continuidad de cada estancia del chat.

## 3. Vercel

Proyecto: `riu-jev-bridge`

Producción:
https://riu-jev-bridge.vercel.app/

Chat:
https://riu-jev-bridge.vercel.app/chat/ui/panel-chat.html

Repositorio:
https://github.com/maxbry123-commits/router-universal-router-inteligente-

Rama de producción: `main`.

Vercel aloja el frontend. El cómputo, proveedores, memoria, herramientas y Router viven fuera del navegador.

## 4. Router HF principal

Router publicado actualmente:

`6ac593acfbc85ba6823baf04`

URL:
https://6ac593acfbc85ba6823baf04--8000.hf.jobs

`LIVE_URL.json` vigente:
https://github.com/maxbry123-commits/router-universal-router-inteligente-/blob/main/router%20inteligente%20universal/LIVE_URL.json

El arranque actual del principal usa el artefacto operativo `router-bundle.tar.gz` del bucket HF y ejecuta:

```text
router-bundle.tar.gz
        ↓
/app
        ↓
router inteligente universal
        ↓
riu_kernel.py --watch
        +
uvicorn public_chat_app:app --host 0.0.0.0 --port 8000
```

IMPORTANTE: GitHub es la fuente de código/documentación; el bundle HF es el artefacto de runtime. Un cambio en `main` debe llegar al bundle/runtime antes de considerarse desplegado en el Job principal.

## 5. Dos vías autorizadas de Router / HF

### Vía A — Router principal publicado

Es el Router cuyo URL está en `LIVE_URL.json` y que usa normalmente el frontend.

Kernel:
https://github.com/maxbry123-commits/router-universal-router-inteligente-/blob/main/router%20inteligente%20universal/riu_kernel.py

El kernel mantiene el Router principal y permite handover controlado entre predecesor y sucesor.

### Vía B — Router de respaldo directo a Hugging Face

Existe como segunda vía autorizada para el chat. Se conserva y no debe eliminarse por el simple hecho de no coincidir con `LIVE_URL.json`.

La regla correcta ya no es "todo segundo Router es anomalía". Hay que distinguir:

1. Router principal publicado por `LIVE_URL.json`.
2. Router/vía de respaldo directa a Hugging Face, autorizada.
3. Handover temporal principal→sucesor, autorizado.
4. Job duplicado accidental sin papel definido, que sí es anomalía.

Workflow histórico relacionado con Router persistente HF:
https://github.com/maxbry123-commits/router-universal-router-inteligente-/blob/main/.github/workflows/riu-router-job-central.yml

Runtime persistente relacionado:
https://github.com/maxbry123-commits/router-universal-router-inteligente-/blob/main/router%20inteligente%20universal/agents-yaiwes/common/router_job_persistent.py

No desactivar ni borrar esta segunda vía sin una orden explícita del Director.

## 6. Entrada pública del backend

Código:
https://github.com/maxbry123-commits/router-universal-router-inteligente-/blob/main/router%20inteligente%20universal/public_chat_app.py

`public_chat_app.py` envuelve la aplicación principal y mantiene credenciales internas del lado servidor para las puertas públicas autorizadas.

La interfaz de Vercel no debe contener claves de proveedores.

## 7. Backend Chat MVP

Raíz exacta:
https://github.com/maxbry123-commits/router-universal-router-inteligente-/tree/main/router%20inteligente%20universal/integration/chat_mvp

Entrada:
https://github.com/maxbry123-commits/router-universal-router-inteligente-/blob/main/router%20inteligente%20universal/integration/chat_mvp/app.py

Superficies principales:

- `/plugins` — Plugin Host.
- `/chat/*` — API general del chat.
- `/chat/jobs/*` — trabajos paralelos.
- `/chat/route`, `/chat/router/status` — routing resiliente.
- `/v1/router/*` — puerta OpenAI-compatible para Hermes/OpenClaw.
- `/gh/accounts`, `/control/*`, `/groups` — puente UI.
- `/memoria/*` — memoria YAIWES.
- `/health`, `/v1/models`, `/v1/chat/completions` — gateway.

Archivos clave:

- `app.py` — composición FastAPI.
- `router.py` — API chat, conversaciones, mensajes y sincronización.
- `store.py` — SQLite/documentos/cache/grafo.
- `providers.py` — proveedores externos.
- `resilience.py` — fallback, circuit breaker y políticas.
- `policies.json` — cadenas declarativas vigentes.
- `memoria_loader.py` — loader HTTP de memoria.
- `memory_runtime.py` — compatibilidad `puente_chat` ↔ memoria canónica.

## 8. `puente_chat`: harness específico de la UI

Raíz:
https://github.com/maxbry123-commits/router-universal-router-inteligente-/tree/main/router%20inteligente%20universal/plugins/puente_chat

Código principal:
https://github.com/maxbry123-commits/router-universal-router-inteligente-/blob/main/router%20inteligente%20universal/plugins/puente_chat/plugin.py

Herramientas:
https://github.com/maxbry123-commits/router-universal-router-inteligente-/blob/main/router%20inteligente%20universal/plugins/puente_chat/herramientas.py

Ficha plugin:
https://github.com/maxbry123-commits/router-universal-router-inteligente-/blob/main/router%20inteligente%20universal/plugins/puente_chat/ficha.json

Fichas/modelos/pipelines:
https://github.com/maxbry123-commits/router-universal-router-inteligente-/tree/main/router%20inteligente%20universal/plugins/puente_chat/fichas

Funciones del puente incluyen:

- `chat_async` / `resultado`.
- contexto de sesión.
- checkpoints para recuperación.
- archivos del chat.
- handoff editable.
- sandbox.
- herramientas GitHub/HF.
- modelos API.
- modelos HF de respaldo bajo demanda.

### L4 temporales `hf-*`

`api.js` y `puente_chat` pueden encender Jobs L4 temporales para modelos HF concretos. Son respaldo de modelo, con ciclo de vida limitado y apagado automático.

Esto es distinto de:

- Router principal.
- segunda vía Router→HF autorizada.

## 9. Harness y DeepSeek

DeepSeek es un proveedor/modelo dentro del sistema de routing; no debe confundirse con el segundo Router de respaldo.

Proveedor directo:
https://github.com/maxbry123-commits/router-universal-router-inteligente-/blob/main/router%20inteligente%20universal/integration/chat_mvp/providers.py

Registro:

```text
deepseek
→ https://api.deepseek.com/v1
```

DeepSeek V4 Flash en cadenas del Router se resuelve por HF cuando la política lo selecciona.

Routing/fallback:
https://github.com/maxbry123-commits/router-universal-router-inteligente-/blob/main/router%20inteligente%20universal/integration/chat_mvp/resilience.py

Diferencia:

```text
DeepSeek API directa
providers.py
→ api.deepseek.com/v1

DeepSeek V4 Flash
resilience/policies
→ proveedor HF
→ router.huggingface.co/v1

Segunda vía Router→HF
→ transporte/respaldo del sistema
→ NO es "un servidor DeepSeek"
```

## 10. Proveedores y JSON vigentes

Registry de proveedores:
https://github.com/maxbry123-commits/router-universal-router-inteligente-/blob/main/router%20inteligente%20universal/integration/chat_mvp/providers.py

Resiliencia:
https://github.com/maxbry123-commits/router-universal-router-inteligente-/blob/main/router%20inteligente%20universal/integration/chat_mvp/resilience.py

Políticas JSON:
https://github.com/maxbry123-commits/router-universal-router-inteligente-/blob/main/router%20inteligente%20universal/integration/chat_mvp/policies.json

Fichas JSON del harness:
https://github.com/maxbry123-commits/router-universal-router-inteligente-/tree/main/router%20inteligente%20universal/plugins/puente_chat/fichas

Hay dos niveles JSON que no deben confundirse:

```text
policies.json
→ orden/fallback/routing por grupo

plugins/puente_chat/fichas/*.json
→ definición concreta de modelos, motores y pipelines del harness
```

El runtime HF también puede consumir copias de fichas desde el bucket. Para certificar una versión concreta hay que comparar `main` con el bundle/fichas efectivamente cargados por el Job.

## 11. Memoria y almacenamiento

### A. Store del Chat MVP

Store:
https://github.com/maxbry123-commits/router-universal-router-inteligente-/blob/main/router%20inteligente%20universal/integration/chat_mvp/store.py

API/Store wiring:
https://github.com/maxbry123-commits/router-universal-router-inteligente-/blob/main/router%20inteligente%20universal/integration/chat_mvp/router.py

Contiene o gestiona:

- conversaciones.
- mensajes.
- documentos.
- agentes.
- cache.
- grafo.
- snapshot SQLite.

### B. memoria_yaiwes canónica

Paquete:
https://github.com/maxbry123-commits/router-universal-router-inteligente-/tree/main/chat%20router/04-MEMORIA/memoria_yaiwes

Implementación:
https://github.com/maxbry123-commits/router-universal-router-inteligente-/blob/main/chat%20router/04-MEMORIA/memoria_yaiwes/__init__.py

Loader:
https://github.com/maxbry123-commits/router-universal-router-inteligente-/blob/main/router%20inteligente%20universal/integration/chat_mvp/memoria_loader.py

API:

- `GET /memoria/health`
- `POST /memoria/save`
- `GET /memoria/load`
- `GET /memoria/search`

La memoria canónica utiliza SQLite escribible como base siempre disponible, grafo SQLite fallback y adaptadores opcionales a otros componentes cuando hay runtime real.

### C. `memory_runtime.py` — GAP DE FUENTE CERRADO

Archivo actual:
https://github.com/maxbry123-commits/router-universal-router-inteligente-/blob/main/router%20inteligente%20universal/integration/chat_mvp/memory_runtime.py

Estado actual: PRESENTE en `main`.

Su función es mantener compatibilidad con `puente_chat`, exponiendo:

- `memory(store)` → devuelve la única fachada canónica de `memoria_yaiwes`.
- `scope_for(owner, scope)` → namespace determinista y acotado de la sesión.

Así el flujo queda:

```text
puente_chat
   ↓
memory_runtime.py
   ↓
memoria_loader._memory()
   ↓
memoria_yaiwes
   ↓
Store / SQLite / grafo
```

No crear una segunda base de memoria para resolver esta compatibilidad.

### D. Persistencia y bucket HF

El runtime principal puede usar almacenamiento local temporal y sincronización/snapshot hacia bucket HF. Debido a que el Job actual arranca desde `router-bundle.tar.gz`, la certificación completa exige probar:

1. guardar un turno.
2. confirmar `memoria_guardada=true`.
3. recuperarlo en la misma sesión.
4. sincronizar/snapshot al almacenamiento persistente.
5. cambiar/reiniciar Job.
6. recuperar el mismo turno.

Hasta completar esa prueba E2E, el GAP de archivo está cerrado pero la persistencia trans-Job debe tratarse como verificación pendiente.

## 12. Banco de claves y seguridad

Las credenciales viven servidor-side. Nunca se deben colocar en este handoff ni en el frontend.

Autenticación interna del Router: `X-API-Key`.

Los proveedores toman las claves del banco/vault o variables autorizadas del runtime.

## 13. Superficies que no deben confundirse

### UI Vercel

```text
Vercel
→ api.js
→ puente_chat
→ chat_async / resultado
```

### Chat MVP general

```text
/chat/send
/chat/providers
/chat/conversations
/chat/route
/v1/router/*
```

### Respaldo HF de modelo

```text
modelo hf-*
→ Job L4 temporal
→ resultado
→ apagado
```

### Segunda vía Router→HF

```text
Router/chat
→ ruta de respaldo autorizada
→ Hugging Face directo
```

Son cuatro superficies/roles distintos.

## 14. Fuente de verdad

Para el Router principal:

1. HF Jobs: estado real de Jobs.
2. GitHub `LIVE_URL.json`: principal que debe consumir la UI.
3. Bucket HF `control/router-current.json`: principal registrado por kernel.
4. `config.js`: fallback frontend.
5. Vercel producción: frontend efectivamente servido.

Para la segunda vía HF:

- verificar su workflow/runtime específico y su estado por separado.
- no exigir que aparezca en `LIVE_URL.json`, porque `LIVE_URL.json` identifica el principal.

Para código/runtime:

- GitHub `main` = fuente de código.
- `router-bundle.tar.gz` / fichas del bucket = artefacto cargado por el runtime principal.

## 15. Checklist de recuperación

Si falla el chat:

1. Revisar el Router principal en HF.
2. Leer `LIVE_URL.json` y comprobar que el principal coincide.
3. Probar `/health`.
4. Verificar Vercel `config.js` y `api.js`.
5. Verificar `/plugins` y `puente_chat`.
6. Verificar `chat_async` → `resultado`.
7. Verificar `providers.py`, `resilience.py`, `policies.json` y fichas si el problema es un modelo.
8. Verificar `/memoria/health`.
9. Verificar `memory_runtime.py` y `memoria_guardada` si falla continuidad.
10. Verificar Store/SQLite/bucket si falla persistencia entre Jobs.
11. Si el principal falla, revisar también la segunda vía Router→HF autorizada.
12. No cancelar la segunda vía HF solo porque no sea el Job de `LIVE_URL.json`.
13. Cancelar únicamente Jobs cuya función haya sido identificada como duplicado accidental o no autorizado.

## 16. Estado PASS / GAP actual

| Componente | Estado |
|---|---|
| Frontend fuente `chat router/chat frontend` | PRESENTE |
| Vercel producción | PASS / READY en última comprobación |
| `api.js` → `LIVE_URL.json` | PASS en código |
| Router principal publicado | PRESENTE |
| Backend `app.py` | PRESENTE |
| Plugin Host → `puente_chat` | PASS en última prueba runtime |
| `puente_chat` | PRESENTE / READY en última prueba runtime |
| Proveedores | PRESENTES |
| DeepSeek directo | PRESENTE en `providers.py` |
| DeepSeek V4 Flash vía HF | PRESENTE en routing/políticas |
| Segunda vía Router→HF | AUTORIZADA; PRESERVAR |
| L4 temporales `hf-*` | RESPALDO DE MODELO; PRESERVAR |
| `/memoria/health` | PASS en última prueba runtime |
| `memoria_yaiwes` | PRESENTE |
| `memory_runtime.py` | **GAP DE FUENTE CERRADO: PRESENTE EN MAIN** |
| Store SQLite/grafo | PRESENTE; CONNECTED en última prueba runtime |
| Persistencia de memoria después de cambio completo de Job | VERIFICACIÓN E2E PENDIENTE |
| GitHub `main` → bundle HF | REQUIERE mantener sincronización/empaquetado |

## 17. Enlaces de recuperación rápida

Handoff canónico:
https://github.com/maxbry123-commits/router-universal-router-inteligente-/blob/main/README-CONEXION-CHAT-HARNESS.md

Chat producción:
https://riu-jev-bridge.vercel.app/chat/ui/panel-chat.html

Frontend completo:
https://github.com/maxbry123-commits/router-universal-router-inteligente-/tree/main/chat%20router/chat%20frontend

Backend Chat MVP:
https://github.com/maxbry123-commits/router-universal-router-inteligente-/tree/main/router%20inteligente%20universal/integration/chat_mvp

Backend `app.py`:
https://github.com/maxbry123-commits/router-universal-router-inteligente-/blob/main/router%20inteligente%20universal/integration/chat_mvp/app.py

Backend `puente_chat`:
https://github.com/maxbry123-commits/router-universal-router-inteligente-/tree/main/router%20inteligente%20universal/plugins/puente_chat

`plugin.py`:
https://github.com/maxbry123-commits/router-universal-router-inteligente-/blob/main/router%20inteligente%20universal/plugins/puente_chat/plugin.py

Memoria canónica:
https://github.com/maxbry123-commits/router-universal-router-inteligente-/tree/main/chat%20router/04-MEMORIA/memoria_yaiwes

`memory_runtime.py`:
https://github.com/maxbry123-commits/router-universal-router-inteligente-/blob/main/router%20inteligente%20universal/integration/chat_mvp/memory_runtime.py

Store:
https://github.com/maxbry123-commits/router-universal-router-inteligente-/blob/main/router%20inteligente%20universal/integration/chat_mvp/store.py

Proveedores:
https://github.com/maxbry123-commits/router-universal-router-inteligente-/blob/main/router%20inteligente%20universal/integration/chat_mvp/providers.py

Routing resiliente:
https://github.com/maxbry123-commits/router-universal-router-inteligente-/blob/main/router%20inteligente%20universal/integration/chat_mvp/resilience.py

Políticas JSON:
https://github.com/maxbry123-commits/router-universal-router-inteligente-/blob/main/router%20inteligente%20universal/integration/chat_mvp/policies.json

Fichas JSON `puente_chat`:
https://github.com/maxbry123-commits/router-universal-router-inteligente-/tree/main/router%20inteligente%20universal/plugins/puente_chat/fichas

LIVE URL:
https://github.com/maxbry123-commits/router-universal-router-inteligente-/blob/main/router%20inteligente%20universal/LIVE_URL.json

Kernel principal:
https://github.com/maxbry123-commits/router-universal-router-inteligente-/blob/main/router%20inteligente%20universal/riu_kernel.py

Workflow Router HF de respaldo/persistente:
https://github.com/maxbry123-commits/router-universal-router-inteligente-/blob/main/.github/workflows/riu-router-job-central.yml

Runtime Router persistente HF:
https://github.com/maxbry123-commits/router-universal-router-inteligente-/blob/main/router%20inteligente%20universal/agents-yaiwes/common/router_job_persistent.py
