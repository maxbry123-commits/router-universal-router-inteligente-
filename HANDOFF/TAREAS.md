# Tareas (handoff)

## Hecho (en main y Space, probado en Android)
- Latencia del chat resuelta: chat_async + long-poll, idempotencia, parcial en la burbuja. Qwen Max 2–4.5 s, Flash ~2 s.
- Qwen Token Plan optimizado (stream, thinking off en simples, reintentos y timeouts).
- Constitución con botón ON/OFF, OFF por defecto (main `483efde6ce`). Fallo abierto: con ON el texto no llega al modelo (campos distintos chat/ficha), en corrección.
- YAIWES en https://riu-jev-bridge.vercel.app/yaiwes/ (48 subpaneles). Componentes viejos borrados del repo frontend (`76ed2233`).
- Proyectos: "＋ Nuevo proyecto" y ventana de archivos y procesos.

## En curso (rama → estado)
- `memoria-audit` → auditoría de memoria y almacenamiento + arreglos; pendiente revisión triple.
- `orquestador-agentes` → prototipo funcional (Playwright Android OK). Respuestas de Antonio: persistir todo en la memoria/bucket, herramienta siempre visible, sección "chat BOTS" bajo el chat, sandbox con código real y despliegue a GitHub/HF/Vercel solo con token, 50 agentes por sección.
- `panel-anclaje-v2` → 3 propuestas (`?panel=a|b|c`); A recomendada; falta que Antonio elija.
- `historial-persistente` → botón ↺ recuperar; pendiente revisión triple.
- `constitucion-contrato` → contrato sentinela ON/OFF, anclaje real, Graphiti/Graphify por canal harness (sin rama publicada aún).
- `tools-staff` → Nemotron 3 Pro, ficha NVIDIA de código, retirar GROQ_API_KEY_1, ficha 4 en tools (sin rama publicada aún).
- `handoff-migracion` → esta carpeta.

## Pendiente
- Ask council + simulaciones: Grok Bot evolucionado, ≥20 propuestas con imágenes (Grok/Grok Build hablando con Grok Bot sin copiar y pegar).
- Secretos en el chat, watchdog, MCP HTTP, ventana ROOM CONFERENCIAS, tamaño de texto del chat.
- Instalar los componentes faltantes del skill Maxbry UI (22 componentes RIU).
- Rotar las claves pegadas en el chat y borrar `/workspace/.model_keys.env` (con el sí de Antonio).
- Opción 4 (frontend desde el Space): en espera.

<!-- AUTO:INICIO -->
## Estado automático (2026-10-16 22:45, hora Bogotá UTC-5)

### Ramas
| Rama | Último commit | Fecha (UTC-5) | vs main (+/-) | Mensaje |
|---|---|---|---|---|
| `handoff-migracion` | 477e57a956 | 2026-10-16 22:43 | +2/-0 | HANDOFF: secretos (solo nombres) + actualizar.py (regenera TAREAS y sube al bucket handoff |
| `historial-persistente` | 733126e4d6 | 2026-10-16 22:38 | +1/-0 | historial: botón ↺ recuperar (une IndexedDB/localStorage + /memoria del Router por sesión, |
| `orquestador-agentes` | a68ba7b627 | 2026-10-16 22:28 | +3/-0 | orquestador (3/3): prueba Playwright vista Android 412 px |
| `memoria-audit` | 7040d575bd | 2026-10-16 22:28 | +2/-0 | test_dag_final: usar memoria_yaiwes de 04-MEMORIA, no la copia vieja de workflow |
| `panel-anclaje-v2` | c4e519217a | 2026-10-16 22:27 | +1/-0 | anclaje: 3 propuestas de panel 0 fricción (?panel=a|b|c) sin reemplazar el clásico; A barr |
| … | — | — | — | 6 sin acceso y 46 sin revisar (define GITHUB_TOKEN) |

### Últimos commits en main (hora UTC-5)
- 483efde6ce 2026-10-16 21:58 anclas: un solo botón ON/OFF por ancla (Constitución y Mi handoff), Constitución OFF por defecto con
- 01afbe784d 2026-10-16 21:51 anclas fuera de esta rama (las hace anclas-constitucion): revertidos anclaje-destinos.js y gobernanz
- 8830875d6b 2026-10-16 21:47 UI: quita tarjeta Chat (Reintentar/campana/Router repetido), campana en barra móvil, Control en Conf
- e4ad186402 2026-10-16 21:46 puente_chat: acciones groq_agentes/tools_estado permitidas en ficha; Kimi K3 retirado por NVIDIA -> 
- 1caebda01f 2026-10-16 21:45 anclas: encendido/apagado de cada ancla en la hoja (Constitución apagada por defecto: gobernanza_act
- feff5e8729 2026-10-16 21:43 NVIDIA ficha unica (Glimmer / Kimi K3 125 s) + Groq como tool groq_agente (pool 20) + ventana Tools 
- 57960d4f1b 2026-10-16 21:26 YAIWES panel: rutas absolutas (/config.js, /yaiwes/puente-yaiwes.js) para que /yaiwes sin barra carg
- c9e4ef139d 2026-10-16 21:16 informe: sin reasoning_content en turnos previos; hilos anyio 100; request_id persistido; progreso c
- 71377af029 2026-10-16 21:15 YAIWES panel servido en /yaiwes (Vercel): puente con modelo qw-<slug> + fichas_qwen ficha 1 (Team qw
- 6b359103ad 2026-10-16 21:10 incorporar YAIWES: UI interface + fabrica-ui en frontend/yaiwes, docs backend en backend/yaiwes; pue

### BITACORA state-hub (últimos)
- seq 6 2026-09-27 00:49 RIU-0121 RUNNING: M-1 PASS: paquete memoria_yaiwes en chat router/04-MEMORIA y un solo memoria_loader.py monta /memoria/health, save, load → next: siguiente nodo DSL; H-1 reservado a Opus
- seq 7 2026-09-27 00:49 RIU-0121 RUNNING: M-2 PASS: SQLite existente del Router reutilizado como fuente principal; tabla memoria_yaiwes sobrevive cierre y reinici → next: siguiente nodo DSL; H-1 reservado a Opus
- seq 8 2026-09-27 00:49 RIU-0121 RUNNING: M-3 PASS: State Hub append-only registra eventos y regenera BITACORA, STATE, CRAZY_WALL y HANDOFF. → next: siguiente nodo DSL; H-1 reservado a Opus
- seq 9 2026-09-27 00:49 RIU-0121 RUNNING: M-4 PASS parcial: grafo SQLite fallback guarda relación y búsqueda; Graphiti presente como fuente pero sin servicio, Fal → next: siguiente nodo DSL; H-1 reservado a Opus
- seq 10 2026-09-27 00:49 RIU-0121 RUNNING: M-5 GAP controlado: Memanto presente sin contrato runtime verificable; Graphify presente como fuente read-only; no se fi → next: siguiente nodo DSL; H-1 reservado a Opus
- seq 11 2026-09-27 00:49 RIU-0121 RUNNING: M-6 GAP controlado: PostgreSQL, Redis y AgentDB sin servicio/runtime verificable; SQLite cubre como fallback. → next: siguiente nodo DSL; H-1 reservado a Opus
- seq 12 2026-09-27 00:49 RIU-0121 RUNNING: M-7 PASS local: 3 pruebas de reinicio, grafo y State Hub; suite de memoria/chat/Secret Bank 30 PASS. H-1 no ejecutado; c → next: siguiente nodo DSL; H-1 reservado a Opus
- seq 13 2026-09-27 02:36 RIU-0121 COMPLETED: M-0..M-7 COMPLETADOS: 13 componentes auditados; SQLite, State Hub y grafo fallback cableados; FalkorDB (927 archivos) y  → next: H-1 reservado a Opus; no ejecutar HF RW ni despliegue Vercel
<!-- AUTO:FIN -->
