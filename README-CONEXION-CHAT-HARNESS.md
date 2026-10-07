# HANDOFF — Cableado del chat YAIWES v6

Actualizado: 2026-10-07.

> ESTADO VIGENTE. Este documento sustituye las referencias históricas a Router de 32 GB, Router detenido y schedules HF antiguos. El circuito actual usa un único Router principal publicado por `LIVE_URL.json`. No contiene claves ni secretos.

## 0. Estado ejecutivo

- Chat producción: https://riu-jev-bridge.vercel.app/
- Frontend fuente: https://github.com/maxbry123-commits/router-universal-router-inteligente-/tree/main/chat%20router/chat%20frontend
- Router HF oficial actual: `6ac593acfbc85ba6823baf04`
- Base Router actual: https://6ac593acfbc85ba6823baf04--8000.hf.jobs
- Puerta fija del chat: https://6ac593acfbc85ba6823baf04--8000.hf.jobs/plugins/puente_chat/call
- `LIVE_URL.json`: https://github.com/maxbry123-commits/router-universal-router-inteligente-/blob/main/router%20inteligente%20universal/LIVE_URL.json
- Backend `puente_chat`: https://github.com/maxbry123-commits/router-universal-router-inteligente-/tree/main/router%20inteligente%20universal/plugins/puente_chat
- Estado HF comprobado al actualizar este handoff: un solo Job Router en `RUNNING`; el Job duplicado `6ac5ab6a404719ba3766487f` fue cancelado.
- Vercel producción comprobado `READY`; `config.js` de producción ya apunta también como fallback a `6ac593...`.

## 1. Flujo global real

```text
USUARIO / NAVEGADOR
        ↓
https://riu-jev-bridge.vercel.app/
        ↓
Vercel sirve shell.html + shell.js + panel-chat.html + panel-chat.js
        ↓
api.js
        ↓
lee LIVE_URL.json de GitHub cada ~30 s
        ↓
Router HF oficial :8000
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
harness / proveedor / herramientas / modelo
        ↓
memoria + almacenamiento
        ↓
/plugins/puente_chat/call/resultado
        ↓
api.js hace polling
        ↓
panel-chat.js pinta la respuesta
```

## 2. Frontend del chat

Raíz:
https://github.com/maxbry123-commits/router-universal-router-inteligente-/tree/main/chat%20router/chat%20frontend

Archivos principales:

- `shell.html`: shell principal que abre en `/`.
- `shell.js`: carga el panel Chat por defecto y monta las otras vistas.
- `panel-chat.html`: DOM del chat, controles, pestañas, adjuntos, anclas, sandbox y motor.
- `panel-chat.js`: comportamiento del chat.
- `api.js`: cliente HTTP; resuelve el Router vivo y habla con `puente_chat`.
- `config.js`: fallback y catálogo visible del frontend.
- `shell.css`, `responsive.css`: estilos.
- `vercel.json`: reescrituras Vercel.

Enlaces directos:

- https://github.com/maxbry123-commits/router-universal-router-inteligente-/blob/main/chat%20router/chat%20frontend/api.js
- https://github.com/maxbry123-commits/router-universal-router-inteligente-/blob/main/chat%20router/chat%20frontend/config.js
- https://github.com/maxbry123-commits/router-universal-router-inteligente-/blob/main/chat%20router/chat%20frontend/panel-chat.js
- https://github.com/maxbry123-commits/router-universal-router-inteligente-/blob/main/chat%20router/chat%20frontend/panel-chat.html
- https://github.com/maxbry123-commits/router-universal-router-inteligente-/blob/main/chat%20router/chat%20frontend/shell.js
- https://github.com/maxbry123-commits/router-universal-router-inteligente-/blob/main/chat%20router/chat%20frontend/vercel.json

### Resolución del backend

`config.js` tiene el Router oficial como fallback, pero la autoridad es `LIVE_URL.json`.

`api.js` ejecuta `liveRouter()` y consulta:

https://raw.githubusercontent.com/maxbry123-commits/router-universal-router-inteligente-/main/router%20inteligente%20universal/LIVE_URL.json

Si cambia el Job HF por una renovación legítima, `api.js` reemplaza `apiBase` y `harnessUrl` sin cambiar el frontend.

Para una conversación, la UI usa principalmente:

```text
POST <LIVE_URL>/plugins/puente_chat/call/chat_async
POST <LIVE_URL>/plugins/puente_chat/call/resultado
```

`api.js` crea una sesión por pestaña/chat y conserva el identificador en `sessionStorage`.

## 3. Vercel

Proyecto: `riu-jev-bridge`

Producción:
https://riu-jev-bridge.vercel.app/

El proyecto está conectado al repo:
https://github.com/maxbry123-commits/router-universal-router-inteligente-

Rama de producción: `main`.

Vercel aloja la interfaz. El cómputo del Router, el puente, la memoria y las herramientas viven en HF.

El deployment que restauró el selector completo y dejó el fallback en el Router oficial quedó `READY` en producción con commit:

`c196da57f48de9cc55e93018c9227744fe649d68`

## 4. Router HF oficial

Job vigente al actualizar este documento:

`6ac593acfbc85ba6823baf04`

URL:
https://6ac593acfbc85ba6823baf04--8000.hf.jobs

HF lo reporta como `RUNNING`, flavor `cpu-basic`, con timeout de `86400` segundos (24 h). El código y la etiqueta del Router lo identifican como el Router CPU de 16 GB.

El arranque del Job hace:

```text
bucket router-bundle.tar.gz
        ↓
extraer /app
        ↓
cd /app/router inteligente universal
        ↓
python riu_kernel.py --watch
        +
uvicorn public_chat_app:app --host 0.0.0.0 --port 8000
```

IMPORTANTE: el Job no clona GitHub en cada arranque. Carga el artefacto operativo `router-bundle.tar.gz` desde el bucket HF. GitHub es la fuente de código/documentación y `LIVE_URL.json`; el bundle HF es el artefacto con el que se inicia el runtime.

## 5. Kernel, renovación y regla de un solo Router

Código:
https://github.com/maxbry123-commits/router-universal-router-inteligente-/blob/main/router%20inteligente%20universal/riu_kernel.py

`riu_kernel.py --watch` vive dentro del Job principal. No hay actualmente un HF Scheduled Job separado para mantener el Router.

El kernel:

1. Lee `control/router-current.json` del bucket.
2. Comprueba `/health` del Router registrado.
3. Si está sano y le quedan más de 20 minutos de vida, no crea otro Router.
4. Cuando necesita sucesor, crea un nuevo Job.
5. Espera a que el sucesor responda sano.
6. Publica el nuevo Job en el bucket y en GitHub `LIVE_URL.json`.
7. Sincroniza memoria del predecesor.
8. Cancela el predecesor.

Regla operativa:

- Normal: **1 Router HF RUNNING**.
- Handover autorizado: puede haber 2 brevemente mientras el sucesor pasa health-check; después debe volver a 1.
- Un segundo Router persistente que no sea el publicado en `LIVE_URL.json` es una anomalía y no debe conservarse.

Incidente 2026-10-07: `6ac5ab6a404719ba3766487f` estaba RUNNING sin ser el Router publicado; fue cancelado. No había referencias a ese Job en `main`.

## 6. Entrada pública del backend

Código:
https://github.com/maxbry123-commits/router-universal-router-inteligente-/blob/main/router%20inteligente%20universal/public_chat_app.py

`public_chat_app.py` envuelve la aplicación principal y mantiene las credenciales internas del lado servidor. Para las rutas públicas del chat, plugin, memoria, archivos y fichas, añade internamente la clave del chat antes de pasar la petición al Router.

La interfaz de Vercel no contiene las claves de proveedores.

## 7. Aplicación backend / Chat MVP

Código:
https://github.com/maxbry123-commits/router-universal-router-inteligente-/blob/main/router%20inteligente%20universal/integration/chat_mvp/app.py

Monta, entre otras superficies:

- `/plugins` — Plugin Host.
- `/chat/*` — API de chat general.
- `/chat/jobs/*` — trabajos paralelos.
- `/chat/route` y `/chat/router/status` — routing resiliente.
- `/v1/router/*` — puerta OpenAI-compatible para Hermes/OpenClaw.
- `/gh/accounts`, `/control/*`, `/groups` — puente UI.
- `/omniroute/*` — proxy OmniRoute.
- `/memoria/*` — memoria YAIWES.
- `/health`, `/v1/models`, `/v1/chat/completions` — gateway.

## 8. `puente_chat`: backend específico de la UI

Raíz:
https://github.com/maxbry123-commits/router-universal-router-inteligente-/tree/main/router%20inteligente%20universal/plugins/puente_chat

Archivos:

- `plugin.py`: harness del chat, ejecución, recuperación, modelos, memoria de sesión, polling y L4 bajo demanda.
- `herramientas.py`: herramientas disponibles al harness.
- `ficha.json`: ficha del plugin.
- `fichas/`: fichas/modelos/pipelines.

Código principal:
https://github.com/maxbry123-commits/router-universal-router-inteligente-/blob/main/router%20inteligente%20universal/plugins/puente_chat/plugin.py

Protocolo del frontend:

```text
POST /plugins/puente_chat/call/chat_async
→ {estado:"procesando", proceso_id}

POST /plugins/puente_chat/call/resultado
→ resultado final
```

Para modelos HF locales, el plugin puede encender un L4 temporal. Esos L4 son **respaldos de modelo**, no otro Router principal: tienen etiqueta propia, límite duro, barrendero y apagado automático.

## 9. Harness y DeepSeek

No existe un segundo "Router DeepSeek" ni un servidor harness DeepSeek separado.

DeepSeek forma parte del harness de proveedores del Router.

Proveedor directo definido en:
https://github.com/maxbry123-commits/router-universal-router-inteligente-/blob/main/router%20inteligente%20universal/integration/chat_mvp/providers.py

Ahí existe el proveedor `deepseek` con API OpenAI-compatible y base pública `https://api.deepseek.com/v1`; las claves salen del banco/vault o del entorno del servidor y no se envían al navegador.

Routing/fallback:
https://github.com/maxbry123-commits/router-universal-router-inteligente-/blob/main/router%20inteligente%20universal/integration/chat_mvp/resilience.py

Ese archivo define además `DEEPSEEK_FLASH` como `deepseek-ai/DeepSeek-V4-Flash` mediante el proveedor HF y lo incluye en cadenas autorizadas como `default`, `assistants`, `minor`, `g2` y `chat_nvidia` según la política de cada grupo.

Por tanto hay que distinguir:

```text
DeepSeek proveedor directo
providers.py → api.deepseek.com/v1

DeepSeek V4 Flash en cadenas del Router
resilience.py → proveedor HF → router.huggingface.co/v1
```

Ninguna de esas dos rutas requiere un segundo Job Router CPU.

## 10. Proveedores

Registry:
https://github.com/maxbry123-commits/router-universal-router-inteligente-/blob/main/router%20inteligente%20universal/integration/chat_mvp/providers.py

El backend contempla NVIDIA, HF Router, Groq, OpenAI, DeepSeek, Moonshot/Kimi, MiniMax y API local. Las claves se resuelven servidor-side.

El `puente_chat` usa además sus fichas para modelos/pipelines visibles en el selector de la UI.

## 11. Memoria y almacenamiento

### A. Store del Chat MVP

Código base:
https://github.com/maxbry123-commits/router-universal-router-inteligente-/blob/main/router%20inteligente%20universal/integration/chat_mvp/router.py

`get_store()` crea el Store bajo `RIU_DATA_DIR` y conserva conversaciones, mensajes, documentos, agentes, grafo y registros locales.

`sync_to_bucket()` puede copiar el snapshot SQLite y documentos al bucket HF bajo `riu-chat/`.

### B. memoria_yaiwes

Loader HTTP:
https://github.com/maxbry123-commits/router-universal-router-inteligente-/blob/main/router%20inteligente%20universal/integration/chat_mvp/memoria_loader.py

Paquete de memoria:
https://github.com/maxbry123-commits/router-universal-router-inteligente-/tree/main/chat%20router/04-MEMORIA/memoria_yaiwes

API:

- `GET /memoria/health`
- `POST /memoria/save`
- `GET /memoria/load`
- `GET /memoria/search`

`memoria_yaiwes` usa SQLite como fallback siempre escribible, además del grafo SQLite y adaptadores opcionales para otros componentes si existe runtime real.

### C. GAP de fuente detectado 2026-10-07

`puente_chat/plugin.py` intenta importar:

`integration.chat_mvp.memory_runtime`

para su `_contexto()` y `_guardar()` por sesión, pero **ese archivo no existe actualmente en `main`**.

El plugin atrapa la excepción y por eso el chat no cae; sin embargo, desde el código GitHub actual no se puede certificar que la memoria específica del `puente_chat` sea reproducible al 100 % solo desde `main`.

Esto NO invalida las rutas `/memoria/*`, el `Store` ni el cableado del chat. Sí significa que hay que reparar o reemplazar ese import antes de declarar **100 % PASS de memoria de sesión del puente**.

No borrar esta observación hasta tener una prueba real donde `memoria_guardada=true` y recuperación de turno sobreviva a reinicio/cambio de Job.

## 12. Banco de claves y seguridad

Las credenciales viven servidor-side. No deben guardarse en este handoff.

El Router desbloquea/inyecta sus secretos al runtime y el frontend nunca debe contener tokens de proveedores, GitHub o HF.

Autenticación interna del Router: `X-API-Key`.

## 13. Dos superficies de chat que no deben confundirse

### UI principal Vercel

```text
Vercel frontend
→ api.js
→ puente_chat
→ chat_async / resultado
```

Esta es la pantalla operativa del usuario.

### Chat MVP general del Router

```text
/chat/send
/chat/providers
/chat/conversations
/chat/route
/v1/router/*
```

Estas rutas forman la infraestructura general del Router y las puertas para agentes/SDKs. No sustituyen a `puente_chat` como backend específico de la UI Vercel.

## 14. Fuente de verdad

Orden de autoridad:

1. HF `ps`: qué Job está realmente RUNNING.
2. GitHub `LIVE_URL.json`: qué Router debe usar el frontend.
3. `config.js`: fallback estático.
4. Vercel producción: versión de frontend que ve el usuario.
5. Bucket HF `control/router-current.json`: registro interno del kernel.

`LIVE_URL.json` y `router-current.json` deben señalar al mismo Router principal.

## 15. Checklist de recuperación

Si el chat falla:

1. Revisar HF Jobs: debe existir un Router principal RUNNING.
2. Leer `LIVE_URL.json` y comprobar que su `job_id` coincide.
3. Probar `/health` del Job desde un entorno con acceso a `hf.jobs`.
4. Abrir `https://riu-jev-bridge.vercel.app/chat/ui/config.js` y revisar fallback + `liveUrl`.
5. Verificar `api.js` y su `liveRouter()`.
6. Verificar `/plugins/puente_chat/call/chat_async` y `/resultado` en logs del Job.
7. Verificar memoria y `memoria_guardada` si el problema es continuidad de conversación.
8. No crear un segundo Router manual para "probar". Si hace falta sucesor, debe hacerlo el mecanismo de handover autorizado.

## 16. Estado PASS / GAP al cerrar este handoff

| Componente | Estado |
|---|---|
| Vercel producción | PASS / READY |
| Frontend `config.js` → Router oficial | PASS |
| `api.js` → `LIVE_URL.json` dinámico | PASS |
| Un solo Router HF principal RUNNING | PASS |
| `LIVE_URL.json` → `6ac593...` | PASS |
| Router → `public_chat_app.py` | PASS por runtime activo |
| Backend → Plugin Host → `puente_chat` | PASS; tráfico `chat_async/resultado` observado en logs |
| Harness proveedores | PASS en código/routing |
| DeepSeek como proveedor/ruta, no Router aparte | PASS arquitectónico |
| `/memoria/*` + `memoria_yaiwes` fuente | PRESENTE |
| memoria específica `puente_chat` vía `memory_runtime` | **GAP DE FUENTE: falta archivo en `main`** |
| Reproducibilidad total GitHub → bundle HF | REQUIERE mantener proceso de empaquetado/sync del bundle |

## 17. Enlaces de recuperación rápida

Handoff canónico:
https://github.com/maxbry123-commits/router-universal-router-inteligente-/blob/main/README-CONEXION-CHAT-HARNESS.md

Chat producción:
https://riu-jev-bridge.vercel.app/

Frontend:
https://github.com/maxbry123-commits/router-universal-router-inteligente-/tree/main/chat%20router/chat%20frontend

Backend puente:
https://github.com/maxbry123-commits/router-universal-router-inteligente-/tree/main/router%20inteligente%20universal/plugins/puente_chat

Router kernel:
https://github.com/maxbry123-commits/router-universal-router-inteligente-/blob/main/router%20inteligente%20universal/riu_kernel.py

LIVE URL:
https://github.com/maxbry123-commits/router-universal-router-inteligente-/blob/main/router%20inteligente%20universal/LIVE_URL.json

Chat backend app:
https://github.com/maxbry123-commits/router-universal-router-inteligente-/blob/main/router%20inteligente%20universal/integration/chat_mvp/app.py

Proveedores:
https://github.com/maxbry123-commits/router-universal-router-inteligente-/blob/main/router%20inteligente%20universal/integration/chat_mvp/providers.py

Routing resiliente:
https://github.com/maxbry123-commits/router-universal-router-inteligente-/blob/main/router%20inteligente%20universal/integration/chat_mvp/resilience.py

Memoria:
https://github.com/maxbry123-commits/router-universal-router-inteligente-/tree/main/chat%20router/04-MEMORIA/memoria_yaiwes
