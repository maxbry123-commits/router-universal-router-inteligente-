# PARCHE DE RECUPERACIÓN — leer COMPLETO antes de hacer nada

Fecha del corte: 16-oct-2026, 23:30 (hora Bogotá, UTC-5). Dueño: **Antonio Mendoza**.
Este documento reemplaza cualquier suposición. **Si algo no está aquí, NO lo inventes: pregúntale a Antonio en una lista corta.**

---

## 0. Reglas para el Grok Bot que retoma (obligatorias)

1. **No alucines.** No inventes archivos, commits, tiempos, modelos ni resultados. Todo dato sale de GitHub, del bucket o de una prueba real que tú corras.
2. **Lo primero que haces es verificar el estado** (sección 3) y responderle a Antonio con 5 líneas como máximo: qué está en producción, qué está en ramas y qué sigue. Todavía no programas nada.
3. **Idioma:** español. **Estilo:** mínimo, sin explicaciones largas. **Tiempos** siempre como `X s YYY ms`.
4. **No reportas nada como hecho hasta que esté probado** en el chat real en vista Android simulada (Playwright, 412 px, red 4G) y funcionando. Regla literal de Antonio: *"No me lo pasas hasta que esté probado y funcionando."*
5. **Un agente por tarea, en paralelo.** Cada mejora va en su propia rama. Después, otro agente (revisor/integrador) la revisa **3 veces**, la cablea, la prueba en el PC y en Android y solo entonces la fusiona a main.
6. **Frontend:** cambios quirúrgicos ("grado milimétrico"), con otro agente que compruebe que no se rompió nada. Las propuestas se presentan como **HTML funcional** (no maquetas estáticas) o como imágenes.
7. **Backend:** el código se escribe (puede usar modelos open source); otro agente lo revisa con 3 tests y simulaciones.
8. **Cero fricción:** escala a Antonio solo cuando algo está listo o con una **lista de preguntas** si hay dudas.
9. **No dupliques trabajo** (ahorro de tokens): no vuelvas a descargar ni a leer lo que ya se leyó, no hagas deploys dobles ni pongas agentes a hacer lo mismo. Pero sí todas las pruebas necesarias.
10. **El código ya probado se copia de repo a repo en GitHub** y solo se cablea; no hace falta bajarlo al PC y volver a subirlo.
11. **NUNCA borres nada sin un "sí" explícito de Antonio.** NUNCA imprimas ni subas secretos.
12. **Nada se puede perder:** todo (chats, agentes, archivos, anclas) persiste en el sistema de memoria y almacenamiento existente (sección 5).
13. Al elegir modelos (por ejemplo el mejor para código), decide por **la opinión real de la comunidad de desarrolladores**, no por lo que dice el proveedor.
14. **Aprobación permanente:** Antonio autorizó push a main y redeploy del Space/Vercel sin volver a preguntar ("Súbelo, déjalo operativo, no preguntes más nada"), siempre que esté probado.

---

## 1. Qué es el proyecto

Un chat/router de IA propio de Antonio, con varios modelos ("fichas"), anclas de archivos, una Constitución (contrato o guardián), memoria persistente y herramientas.

| Pieza | Dónde |
|---|---|
| Chat en vivo (frontend en Vercel) | https://riu-jev-bridge.vercel.app/ |
| Panel YAIWES | https://riu-jev-bridge.vercel.app/yaiwes/ |
| Backend (HF Space) | `COMAND-CENTER-1/riu-router` |
| Repo principal | https://github.com/maxbry123-commits/router-universal-router-inteligente- (rama `main`) |
| Repo frontend antiguo | `maxbry123-commits/frontend` (los componentes YAIWES ya se migraron y se borraron de ahí) |
| Bucket HF (código + memoria) | `COMAND-CENTER-1/yaiwes-memoria-storage` |
| Frontend del chat | `chat router/chat frontend/` (api.js, panel-chat.js, panel-chat.html, shell.html, contexto.js, chat-ancla.js, anclaje-propuestas.js, tools-ventana.js, config.js, chat-selectores.js, vercel.json, build.sh) |
| Plugins backend | `router inteligente universal/plugins/` (puente_chat, fichas_qwen, hf_storage, banco…) |
| Memoria | `chat router/04-MEMORIA/memoria_yaiwes` |

### Arquitectura que NO se cambia
```
COMPONENTE → HARNESS (puente_chat / ruta DeepSeek, como PLUGINS, no puentes) → HTTP → FICHA → MODELO
```
- El chat llama a `chat_async`, que devuelve un `request_id` idempotente, y luego hace polling a `/resultado` (long-poll de 8 s, máximo 3 a la vez). `/resultado` devuelve `parcial` y la burbuja pinta texto parcial.
- Vercel hace proxy (rewrites) de `/plugins`, `/vault`, `/health` y `/mcp` hacia el Space, sin caché y con 120 s de tope.
- `build.sh` pone `?v=<sha>` a los JS, así que **no hay que limpiar la caché**: basta con cerrar y abrir la pestaña.
- Qwen siempre en stream, con `enable_thinking:false` en preguntas simples. Solo reintenta ante errores de red, 5xx, 429 o timeouts.

### Cómo se despliega el Space (paso a paso, sin saltarse ninguno)
1. Lee `router-inteligente-universal/codigo/router-bundle.json` del bucket **justo antes** de empezar (otro agente pudo haber desplegado).
2. Reconstruye **desde el bundle vigente** `router-bundle.tar.gz`, cambiando SOLO los archivos de tu rama.
3. Backup: `router-bundle.tar.gz.bak-<fecha>-<sha>` y `router-bundle.json.bak-…`.
4. Sube el bundle y actualiza `router-bundle.json`.
5. Reinicia el Space y espera `/health` = 200.
6. Prueba en vivo en Android. Si algo falla, restaura el `.bak`.
**Nunca hagas dos deploys del Space a la vez.**

### Credenciales
- En el box no hay credencial de git: usa el conector de GitHub (`push_files`, `create_or_update_file`) o `gh` autenticado. No pidas tokens en el chat.
- Los secretos solo por nombre: `HF_TOKEN`, `FICHA_CLAVE_BANCO`, `RIU_VAULT_PASSPHRASE` (secretos del Space), y las variables `RIU_FICHA4_TIMEOUT` y `RIU_ROUTER_URL`. Las claves de modelos viven cifradas en el vault o banco. Ver `HANDOFF/SECRETOS.md`.

---

## 2. Qué ya está HECHO y en producción (probado en Android)

| Cosa | Estado / commit | Evidencia |
|---|---|---|
| **Latencia del chat** (objetivo principal, resuelto tras 6 días) | Causas: un TypeError en `pintarFichaPill` en móvil, fetch sin tope de tiempo, un auto-reload de version.js, `/resultado` llenando los 8 slots y el thinking de Qwen. Todo corregido. | Qwen Max/Flash, Team 5 y Ask consil entre unos 1 s 851 ms y 2 s 800 ms |
| UI limpia | `8830875d` | Se quitó la tarjeta de notificación; la campana va en la barra superior, Control pasó a Configuración y Router y Emergencia son un solo botón |
| YAIWES + Proyectos | `1caebda01f` → `01afbe784d` | Panel /yaiwes/ (48 subpaneles); botones "＋ Nuevo proyecto" y "Proyectos: archivos y procesos" |
| Anclas ON/OFF + Constitución OFF por defecto | `483efde6ce` | ⚠️ Con ON, el texto propio de la Constitución NO llega al modelo (ver 4.1) |
| Memoria segura (memoria-audit) | `90b77a5d9e`, `e758027117`, `fd03ea1d25`; bundle `af1e25ff…` | Un reinicio ya no pisa el bucket con una base vacía |
| Arreglo de memoria con red caída | En main `ca7de01ce2`; bundle `aa7c30e2…` (23:07) | ⚠️ No consta la prueba en vivo: verificar |
| Panel de anclaje A (barra única) | `34ab6087` | El ⚓ abre A; B y C con `?panel=b` / `?panel=c`; botón "Clásico" |
| NVIDIA/Groq tools-staff | main `7972a78b18`; bundle `232d525c…` | Glimmer 2–4 s; Nemotron Ultra con caída a Super; tool de código GLM-5.3 → Step 5 → DeepSeek V4.1 Flash (30 s); ventana 🧰 con 15 recursos; GROQ_API_KEY_1 eliminada |
| Historial persistente + botón ↺ | main `e1d7550a44` | ⚠️ El integrador lo fusionó, pero no consta la prueba en vivo: verificar |
| HANDOFF | main `97f8673490` | Esta carpeta |

---

## 3. Primer paso al retomar: VERIFICAR (no programar)

1. `GET https://riu-jev-bridge.vercel.app/health` → 200.
2. Lee `router-bundle.json` del bucket y anota el sha vigente.
3. `GET /memoria/health` (por el proxy) → SQLite CONNECTED, y anota el conteo de registros.
4. En main, revisa con `list_commits` los últimos 20 commits. **Ojo:** después de la pausa entraron commits de OTRO hilo (OpenClaw `f149a70eff`, 23:15) y en `/workspace/b11` hay cambios de "Hermes" sin subir. **No son de este plan: pregúntale a Antonio antes de tocarlos.**
5. Prueba en Android los 6 selectores Qwen (Team qwen 3.8 Max/Flash, Team 5 MVP Max/Flash, Ask consil code/frontend) y el historial tras recargar.
6. Reporta a Antonio en 5 líneas como máximo.

---

## 4. Lo que falta, en orden de prioridad

### 4.1 Listo en rama, falta integrar (revisión ×3, deploy y prueba en Android)
| Rama | Qué es | Qué falta |
|---|---|---|
| `secretos-watchdog-mcp-rebase` | Ventana de secretos `/claves` (cifrada; solo muestra la máscara), watchdog cada 60 s (reinicia el Space tras 3 fallas de /health, máximo 1 cada 30 min) y MCP Streamable HTTP en `/mcp` con token | El PIN `RIU_SECRETOS_PIN`: Antonio lo escribió en una tarjeta segura y está en el entorno del box. Guárdalo como secreto del Space con la API de HF sin imprimirlo. Si no existe, pídeselo a Antonio con un formulario seguro. |
| `orquestador-agentes-rebase` | **Chat BOTS v2**: sección debajo del chat abierto; cada agente es un sub-chat con semáforo, stream de 4 líneas, botón +, mirror, selector de la Ficha 4, memoria/sandbox/ID propios, máximo 50 por sección y la tool `crear_agente` siempre visible. Sandbox en HF Jobs con ejecución real; router de deploy a GitHub, HF y Vercel con el token cifrado y confirmación en cada "Desplegar". | **Pregunta abierta a Antonio:** HF Jobs tiene la red abierta. ¿Lo usamos así, esperamos a noviembre por Vercel Sandbox sin red, o paga Vercel Pro? Falta exponer `status`/`reiniciar` para el watchdog. |
| `constitucion-contrato` | La Constitución como contrato o sentinela (valida la entrada y la salida, con ON/OFF), ventana y selector de system prompt aparte, anclaje de archivos real y ejecutable, integración con Graphiti y Graphify, y el arreglo de `constitucion_texto` vs `constitucion.texto` | Revisar ×3, probar con la regla de prueba "termina con SENTINELA7" en los 6 selectores con ON y OFF, y luego deploy. Graphiti NO va en producción si sube la latencia. |

### 4.2 A medias (ramas `wip/`; continuar, NO publicar hasta que esté probado)
| Rama | Estado |
|---|---|
| `wip/consil-latencia` | Ask consil tarda 94 s o más en un chat con un archivo anclado ("Di solo: hola"); en un chat nuevo, unos 3 s. Hay un arreglo inicial (vía rápida cuando la pregunta no habla del archivo) sin probar. |
| `wip/room-conferencias` | La sección **ROOM CONFERENCIAS** (varias LLM debaten; eliges participantes y rondas; historial persistente) y el control **A− / A+** de tamaño de texto. No está revisado ni probado. |
| `wip/skills-maxbry-ui` | Instalar los **22 componentes RUI/RIU** del plan de skills Maxbry UI y los demás. Van 2 de 22 (grid-reveal y voice-note). |
| `wip/grokbot-evolucionado` | Antonio pidió **20 o más propuestas** para un Grok Bot evolucionado, sacadas de Ask consil + simulaciones. Cada propuesta sale de una sesión nueva e independiente, que recibe el historial de la propuesta anterior + un "goal de evolución". Van 18 y faltan las imágenes y la síntesis. Incluir sí o sí: **Grok y Grok Build no pueden hablarle a Grok Bot**, es una fricción de copiar y pegar que hay que resolver. |

### 4.3 Pendientes sin rama
- Nemotron repite la identidad del modelo anterior al cambiar de selector en el mismo chat (le llega el historial).
- `/memoria/*` es público (cualquiera con la URL puede leer y escribir). Proponer token o PIN y preguntarle a Antonio.
- Graphiti está apagado en producción: sus llamadas a la Ficha 4 compiten con el chat. Hay que separarlas o limitarlas antes de prenderlo, y sincronizar su base con el bucket.
- Rotar las claves que Antonio pegó en el chat y borrar `/workspace/.model_keys.env` (con su sí).
- `/workspace/tsdeploy`: unos 1,4 GB de temporales (borrar solo con su sí).
- La opción 4 (servir el frontend desde el Space) queda como opción; no hacer sin pedido.
- La sección "ROOM" y "Chat BOTS" viven como pestañas o secciones del chat, igual que Chat 1, 2 y 3.

### 4.4 NO hacer (Antonio lo descartó)
- Los puntos de UI 1–3 (latido, estados de la burbuja, botón Reintentar): "no cambiar".
- SSE (Front 7). El punto 8.
- Activar la Constitución por defecto (va en OFF y solo se prende con su botón).

---

## 5. Sistema de memoria (nada se pierde)
- **SQLite primario:** `/tmp/riu-data/riu_chat.sqlite3`, con RLock y busy_timeout de 5000.
- Réplicas: graph-sqlite-fallback, state-hub `BITACORA.jsonl`, dataset-yaiwes (solo lectura) y Graphiti (apagado).
- **Sync al bucket cada 60 s** y restauración en frío al arrancar. Si la restauración falla, la subida se bloquea para no pisar el bucket (arreglo de red caída en `ca7de01ce2`).
- Backups en el bucket: `backups/pre-memoria-audit-20261016-2245*.sqlite3`.
- Los chats del frontend se respaldan completos en `/memoria` (`chat-ui:hist:<sesion>`) y las pestañas en `chat-ui:pestanas`.

---

## 6. PROMPT PARA PEGAR EN EL GROK BOT NUEVO

```
Eres el asistente de programación de Antonio Mendoza para su chat/router de IA. Retomas un trabajo en curso desde otro chat.
ANTES DE NADA lee completo este archivo en GitHub y obedécelo al pie de la letra:
https://github.com/maxbry123-commits/router-universal-router-inteligente-/blob/main/HANDOFF/PARCHE-RECUPERACION.md
(y como apoyo: HANDOFF/ARQUITECTURA.md, HANDOFF/TAREAS.md, HANDOFF/PREFERENCIAS.md y HANDOFF/SECRETOS.md en el mismo repo).

Reglas:
- Español, respuestas mínimas, tiempos en formato "X s YYY ms".
- No inventes nada: si un dato no está en el repo, el bucket o una prueba tuya, pregúntame en una lista corta.
- Primero haz SOLO la sección 3 (verificar el estado) y respóndeme en 5 líneas como máximo: qué está en producción, qué está en ramas y qué sigue. No programes todavía.
- Luego sigue la sección 4 en orden: un agente por tarea en su propia rama, revisión ×3 por otro agente, prueba en el chat real en vista Android (412 px, 4G) y solo entonces merge y deploy. No me reportes nada hasta que esté probado y funcionando.
- No toques la arquitectura COMPONENTE → HARNESS → HTTP → FICHA → MODELO.
- Nunca borres nada sin mi sí y nunca imprimas secretos.
- Tienes aprobación permanente para push a main y redeploy cuando esté probado.
```
