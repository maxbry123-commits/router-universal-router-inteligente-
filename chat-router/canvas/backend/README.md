# Backend del Canvas Visual · YAIWES

Motor backend determinista y **fail-closed** del Canvas Visual y de las 3 ventanas
Mirror / Diff‑Editor / Deploy. **Un solo proceso FastAPI**: la API REST, el MCP y
el frontend estático viven en la misma aplicación (HF Spaces arranca un proceso).

Este documento es la **fuente de verdad de la arquitectura**: nombra cada módulo,
su responsabilidad y sus reglas duras. El auditor X‑Ray cruza estas líneas con el
código real y emite el veredicto; los ficheros que no se nombran aquí aparecen
como HUÉRFANOS (código sin documentación), que es exactamente lo que este README
cierra.

- Esquema de ejecución: **backend/ARCHITECTURE_DAG.json**
- Arranque: `python3 -m uvicorn api:app --host 0.0.0.0 --port 7860`
- Servido por: **backend/api.py** (punto de entrada único)

---

## 1 · Capa HTTP · api_gateway

| elemento | función |
|---|---|
| **backend/api.py** | módulo de entrada: enruta REST, WebSocket, MCP y frontend. No contiene lógica de negocio. |
| **backend/health.py** | módulo agregador: estado real de los 6 adapters con contadores OK / OMITIDO / ERROR. |
| **backend/canvas_engine.py** | módulo orquestador: carga aislada de adapters, render de diagramas y motions, conversión entre herramientas. |
| **backend/audio_engine.py** | módulo de voz: resumen de ≤150 palabras, traducción opcional, TTS con edge‑tts y respaldo en pyttsx3, caché por hash. |
| **backend/mcp_router.py** | módulo MCP: protocolo JSON‑RPC sobre FastAPI, allowlist por ventana, rechazo de credenciales, límite de payload. Sustituye al servidor http.server retirado. |
| **audit_runner** (backend/xray/audit_runner) | módulo runner: único punto que invoca al auditor X‑Ray; lo usan la API y el router MCP. |
| **gaps_store** (backend/xray/gaps_store) | módulo de almacenamiento: gaps en modo append‑only con evidencia validada contra el inventario. |

### Rutas que expone la API

`GET /health` · `POST /render/diagram` · `POST /render/motion` · `POST /convert` ·
`POST /audio/explain` · `GET /audio/{audio_id}` · `POST /gaps` · `GET /gaps` ·
`GET /xray/{artifact}` · `POST /xray/audit` · `WS /ws/progress` ·
`POST /mcp` · `GET /mcp/health` · `DELETE /mcp` · `POST /guide/match` · `GET /guide/status` ·
`GET /ui/` (frontend estático)

---

## 2 · Capa de adapters (fail‑closed)

Cada adapter es un módulo independiente con dos funciones: **ping** y **render**.
Si el motor no está instalado, el adapter devuelve **OMITIDO** con su comando de
ping exacto. **Nunca** se inventa un SVG ni un diagrama falso.

| módulo | función |
|---|---|
| **backend/adapters/excalidraw.py** | módulo adaptador: convierte elementos Excalidraw en un diagrama contra la API de Excalidraw. |
| **backend/adapters/mermaid.py** | módulo adaptador: renderiza código Mermaid a SVG con el comando mmdc. |
| **backend/adapters/d2.py** | módulo adaptador: renderiza código D2 a SVG con el comando d2. |
| **backend/adapters/hyperframes.py** | módulo adaptador: genera motion HTML a partir de una especificación. |
| **backend/adapters/remotion.py** | módulo adaptador: genera una composición Remotion desde props. |
| **backend/adapters/rive.py** | módulo adaptador: genera una animación Rive desde un fichero y una máquina de estados. |

---

## 3 · Capa de despliegue · deploy_engine

| elemento | función |
|---|---|
| **backend/deploy/deploy_engine.py** | módulo motor de deploy: 10 checks fail‑closed, dry‑run por defecto, expected HEAD, push transaccional de un solo commit, read‑back y manifiesto. |
| **backend/deploy/mcp_server.py** | módulo shim: reexporta la API del router MCP y avisa si alguien intenta arrancarlo como servidor standalone ya retirado. |
| **backend/deploy/ledger.jsonl** | bitácora append‑only de las ejecuciones del nodo de despliegue. |

**Reglas duras del módulo de deploy** (verificadas por el propio motor):

1. `dry_run` por defecto: el plan **no escribe nada** en disco.
2. `expected_head` obligatorio; si el HEAD no coincide → **CONFLICT** y aborta.
3. **Nunca** force‑push: la ref se mueve con force en false y se comprueba que el
   padre del commit nuevo es el HEAD esperado.
4. **Sin LFS**: aborta si aparece un puntero LFS o un .gitattributes con LFS.
5. **Sin GitHub Actions**: aborta si hay algo bajo .github/workflows.
6. **Sin symlinks** y **sin rutas fuera de la raíz** de destino.
7. **Límites de tamaño**: máximo por fichero y máximo total (12.582.912 B por
   defecto), comprobados en el check de tamaño.
8. **Sin credenciales**: ni en el payload ni dentro del contenido de los ficheros
   (compara contra los tokens del entorno).
9. **Doble autorización**: variable de entorno de autorización + token de entorno
   coincidente; el token nunca viaja en el payload ni en los logs.
10. **Read‑back**: sha256 del bloque escrito == sha256 local, y tras el push se
    relee el commit nuevo y su árbol.

**Transporte del push**: Git Data API (blobs → tree → commit → ref) produce **un
solo commit** para todos los ficheros. El método anterior (PUT sobre contents por
fichero) generaba un commit por fichero.

---

## 4 · Capa MCP · allowlist por ventana

El router MCP expone 7 herramientas, pero **cada ventana solo puede llamar a las
suyas**. Una herramienta fuera de la allowlist se rechaza con el código −32601.

| ventana | herramientas permitidas | función |
|---|---|---|
| w1 · MIRROR | memory_profile, memory_index | módulo de contexto: estado real del proyecto y búsqueda en la documentación. |
| w2 · DIFF | render_diagram, render_motion, audio_explain | módulo de producción: diagramas, motions y voz explicativa. |
| w3 · DEPLOY | xray_audit, deploy_plan | módulo de verificación: auditoría X‑Ray y plan de despliegue. |

Reglas del router: origen validado (403), payload máximo (413), credenciales en
payload rechazadas (−32002), ventana no identificada rechazada (−32602), sesiones
con identificador y tope, y **todos los errores en forma JSON‑RPC válida**.

Las herramientas se ejecutan **en proceso** contra los motores reales: el modelo
no lee el corpus, pide herramienta y recibe el resultado mínimo.

---

## 5 · Capa de la guía viva

| módulo | función |
|---|---|
| **backend/guide/grammar.py** | módulo gramatical: descompone una frase de acción en verbo, sujeto, adjetivo y estado. |
| **backend/guide/match.py** | módulo de emparejamiento: cruza la acción con el catálogo, devuelve veredicto y parche quirúrgico por líneas. |
| **backend/guide/trigger.py** | módulo disparador: construye y valida el contrato de ejecución por pasos. |
| **backend/guide/discovery.py** | módulo de descubrimiento: busca candidatos en las fuentes configuradas con caché y presupuesto. |
| **backend/guide/guide_actions.json** | catálogo de acciones de la guía (ejemplos de referencia del parche). |

---

## 6 · Capa de frontend (servido por la misma app)

| elemento | función |
|---|---|
| **frontend/index.html** | página índice del Canvas: entrada a las 4 vistas del canvas visual. |
| **frontend/shared/api.js** | módulo de cliente: base de API same‑origin, fetch real, tema de 7 apariencias, utilidades de estado. |
| **frontend/shared/ws.js** | módulo de WebSocket: suscripción al progreso con reconexión y origen validado. |
| **frontend/shared/theme.css** | módulo de estilos: los 7 temas de la ley de diseño. |
| **frontend/shared/app.css** | módulo de estilos: geometría, tarjetas y estados demostrables. |
| **frontend/w_mcp.js** | módulo cliente MCP del navegador: initialize, listado de herramientas y llamada, con allowlist por ventana. |
| **frontend/v1_canvas.html** | ventana 1 del canvas: render de diagramas y audio explicativo. |
| **frontend/v2_progress.html** | ventana 2 del canvas: progreso real, mapa de 10 vistas y gaps. |
| **frontend/v3_architecture.html** | ventana 3 del canvas: arquitectura declarativa e historial. |
| **frontend/v4_audit.html** | ventana 4 del canvas: auditoría X‑Ray, gaps y acciones priorizadas. |
| **frontend/w1_mirror.html** | ventana Mirror:Trae el código (URL, fichero, texto o IA) y calcula su sha256. |
| **frontend/w2_diff_editor.html** | ventana Diff‑Editor: editor quirúrgico que solo cambia las líneas declaradas. |
| **frontend/w3_deploy.html** | ventana Deploy: destino, dry‑run, autorización y commit transaccional. |

---

## 7 · Reglas transversales (fail‑closed)

1. **0 MOCK**: si un motor no está, se dice OMITIDO con su comando de ping; si un
   dato no existe, se escribe UNKNOWN; nunca se estima un porcentaje.
2. **1 función = 1 fichero**: los módulos enrutan, la lógica vive en su módulo.
3. **Sin secretos**: ningún token en el código, los logs, el HTML ni los payloads;
   solo se leen del entorno y se redactan en la salida.
4. **Sin LFS y sin GitHub Actions**, por contrato.
5. **Todo error dice la causa real**: el motivo viaja en la respuesta, nunca un
   mensaje genérico.
6. **Un solo proceso**: API + MCP + frontend en la misma aplicación FastAPI.
