# Tareas (handoff)

**Estado: TODO EN PAUSA por orden de Antonio (t101 «Detente», t102 «Pon todo en pausa…»), 16-oct-2026 ~23:15 hora Bogotá (UTC-5).** No hay agentes corriendo. Nada se despliega ni se fusiona hasta que Antonio lo pida.

## 1. Hecho y en producción (main + Space)
- Latencia del chat resuelta: chat_async + long-poll, idempotencia, parcial en la burbuja. Qwen Max ~2–4.5 s, Flash ~2 s.
- Qwen Token Plan optimizado (stream, thinking off en simples, reintentos y timeouts).
- **memoria-audit** → bundle `af1e25ff` (main `fd03ea1d25`): restauración en frío, autosync no pisa el bucket si el restore falla, grafo fallback por scope.
- **tools-staff** → main `7972a78b18`, bundle `232d525c…`: Glimmer 2–4 s (antes ~18 s), Nemotron Ultra→Super (Ultra da 503), tool NVIDIA de código GLM-5.3 (claves 2–5), GROQ_API_KEY_1 retirada, ventana 🧰 con 15 recursos.
- **Panel de anclaje A** (barra única, por defecto en ⚓; `?panel=b|c` y «Clásico» disponibles) → `34ab608788`.
- **Anclas / Constitución ON/OFF** (OFF por defecto) → main `483efde6ce`.
- **YAIWES** en https://riu-jev-bridge.vercel.app/yaiwes/ (48 subpaneles) y **Proyectos** («＋ Nuevo proyecto», ventana archivos y procesos). Componentes viejos borrados del repo frontend (`76ed2233`).
- **historial-persistente** → fusionado a main (`cc0bf9e1cd` + merge `e1d7550a44`, 22:57): ↺ recupera todos los chats aunque se borren los datos del sitio. ⚠️ El integrador fusionó pero **la prueba en vivo en Android quedó sin confirmar**: repetirla.
- **Memoria con red caída** (reintento con backoff + fusión local↔bucket + respaldo `backups/pendiente-<fecha>.sqlite3`) → main `ca7de01ce2`, bundle `aa7c30e2…` subido a las 23:07. ⚠️ No consta reinicio del Space con este bundle ni prueba en vivo: verificar con /health y prueba Android.
- Además en main (otro hilo, t144u–t146u): limpieza de `agentes/`, borrado de la copia vieja de Hermes, Hermes Agent v0.22.2 (`140b5fd91a`) y OpenClaw v2026.10.4 (`f149a70eff`, 23:15, **después** de la pausa: confirmar con Antonio si ese hilo debía seguir). `/workspace/b11` tenía cambios locales de modos de archivo en Hermes sin subir (no es de estas tareas).

## 2. Ramas listas sin integrar (revisión triple → Android → main)
- `secretos-watchdog-mcp` (`51d49bc6db`) y su versión rebasada sobre main **`secretos-watchdog-mcp-rebase`** (`6ee77d4203`, +2/-1, usar esta): secretos cifrados en el chat (`/claves`, enmascarados), watchdog cada 60 s (repara y avisa en la campana; reinicia el Space tras 3 fallas, máx. 1/30 min), MCP Streamable HTTP en `/mcp` con token. 22 tests + 3 simulaciones OK. **Pendiente: PIN `RIU_SECRETOS_PIN`**: Antonio lo escribe y se guarda como secreto del Space (nunca en el chat).
- `orquestador-agentes-rebase` (`9dc637165f`) = **Chat BOTS v2**: agentes bajo cada chat, persistidos en la memoria del chat (sobrevive reinicio), sandbox real en HF Jobs (6 s 627 ms), tope 50 por sección, tokens de deploy cifrados en el banco, «Desplegar» siempre pide confirmación. **Pendiente: decisión de Antonio sobre la red de HF Jobs.**
- `constitucion-contrato` (`08a7123655`, +3/-3): Constitución sentinela (contrato en la entrada + validador determinista + 1 juez-corrector solo si falla, ON/OFF), system prompt guardable, «Anclar archivo real», anclaje a grafo SQLite + Graphiti (`RIU_SENTINELA_GRAPHITI=1`, solo anclaje, por Harness→Ficha 4) + Graphify (AST) como acciones de `fichas_qwen`, e incluye el **fix `constitucion_texto` vs `constitucion.texto`**. Código completo (backend + frontend 1/2 y 2/2); falta revisión triple y prueba Android.

## 3. WIP (a medias, subido tal cual)
- `wip/consil-latencia`: con anclas, un input trivial (≤160 chars) que no se refiere a lo anclado va por FAST en Ficha 2/3. Sin probar en vivo.
- `wip/room-conferencias`: pestaña ROOM CONFERENCIAS junto a Chat 1/2/3 + control A−/A+ (`texto-tamano.js`). Sin revisar ni probar.
- `wip/skills-maxbry-ui`: RUI 16 grid-reveal y RUI 22 voice-note portados (`rui-media.js/css`) y usados en `canvas-visor.js`; fuentes tsx de referencia en `wip-notas/`. Faltan el resto de los 22 componentes y el inventario.
- `wip/grokbot-evolucionado`: `research/grokbot-evolucionado/` con 18 de 20+ propuestas (cada una en sesión nueva) + scripts. Faltan 2+ propuestas, imágenes y síntesis.

## 4. Pendientes y preguntas abiertas
- Ask consil con un archivo anclado tarda 94 s o más incluso con «hola» (chat nuevo ~3 s). Arreglo en `wip/consil-latencia`.
- Fix `constitucion_texto` (con ON el texto no llega al modelo): hecho en `constitucion-contrato`, sin integrar.
- Nemotron repite la identidad del modelo anterior al cambiar de selector.
- `/memoria` es público (cualquiera con la URL puede leer).
- Rotar las claves pegadas en el chat y borrar `/workspace/.model_keys.env` del box viejo (con el sí de Antonio).
- Opción 4 (frontend servido desde el Space): en espera.
- `/workspace/tsdeploy` y `/workspace/dep` del box viejo ocupan ~1,4 GB cada uno de temporales de deploy (borrar solo con el sí de Antonio).
- Preguntas a Antonio: red de HF Jobs para Chat BOTS; PIN de secretos; elegir panel B/C si no quiere A.

## 5. Pedidos de Antonio (t100), estado
- Nada se pierde: todo en la memoria/almacenamiento existentes (SQLite + bucket + grafo) → memoria-audit, historial y red caída en main; Chat BOTS persiste en la memoria del chat.
- Chat BOTS bajo el chat abierto; herramienta para crear agentes siempre visible → `orquestador-agentes-rebase`.
- Sandbox con ejecución real + router de deploy (GitHub/HF/Vercel solo con token) → `orquestador-agentes-rebase` (HF Jobs; deploy con confirmación).
- 50 agentes por sección → hecho en la rama.
- ROOM CONFERENCIAS (los modelos debaten entre ellos) → `wip/room-conferencias`.
- A−/A+ tamaño de texto → `wip/room-conferencias`.
- Secretos en el chat, watchdog, MCP HTTP → `secretos-watchdog-mcp-rebase`.
- Skills Maxbry UI: instalar los 22 componentes RUI → `wip/skills-maxbry-ui` (2 de 22).
- Grok Bot evolucionado: 20+ propuestas por Ask consil, cada una en sesión nueva (historial de la anterior + goal), con imágenes; incluye que Grok/Grok Build hablen directo con Grok Bot → `wip/grokbot-evolucionado` (18).
- Constitución anclada a Graphiti/Graphify por el harness DeepSeek como plugins (no puentes) → `constitucion-contrato`.
- Sistema de migración (este HANDOFF) → hecho.

## 6. Estado del deploy (16-oct-2026 23:15, hora Bogotá)
- `router-bundle.json` vigente en el bucket: sha256 `aa7c30e23b3f…` (main `ca7de01c`, base `232d525c`), subido 23:07.
- `GET https://riu-jev-bridge.vercel.app/health` → 200 (`status: ok`). Space `/health` → 200.
- Backups en el bucket: `router-bundle.tar.gz.bak-<fecha>-<sha>`.

<!-- AUTO:INICIO -->
## Estado automático (2026-10-16 23:17, hora Bogotá UTC-5)

### Ramas
| Rama | Último commit | Fecha (UTC-5) | vs main (+/-) | Mensaje |
|---|---|---|---|---|
| `wip/grokbot-evolucionado` | 55c08475b3 | 2026-10-16 23:15 | +1/-1 | WIP grokbot-evolucionado: 18 de 20+ propuestas (Ask consil/fichas Qwen, cada una en sesion |
| `secretos-watchdog-mcp-rebase` | 6ee77d4203 | 2026-10-16 23:11 | +2/-2 | watchdog: reinicio del Space tras 3 fallas de /health (max 1 cada 30 min, RIU_WATCHDOG_RES |
| `wip/skills-maxbry-ui` | 94deec367f | 2026-10-16 23:15 | +1/-15 | WIP skills-maxbry-ui: RUI 16 grid-reveal + RUI 22 voice-note portados a rui-media.js/css y |
| `wip/room-conferencias` | 56a29fcb6b | 2026-10-16 23:14 | +1/-15 | WIP room-conferencias + A-/A+: pestaña ROOM CONFERENCIAS junto a Chat 1/2/3 (room-conferen |
| `wip/consil-latencia` | 7381877196 | 2026-10-16 23:14 | +1/-5 | WIP consil-latencia: con anclas, un input trivial (<=160 chars) que no se refiere a lo anc |
| `secretos-watchdog-mcp` | 51d49bc6db | 2026-10-16 23:09 | +2/-15 | watchdog: reinicio del Space tras 3 fallas de /health (max 1 cada 30 min, RIU_WATCHDOG_RES |
| `constitucion-contrato` | 08a7123655 | 2026-10-16 23:04 | +3/-4 | Constitución sentinela (frontend 2/2): sentinela.js (plantilla, system prompt guardable, A |
| `orquestador-agentes-rebase` | 9dc637165f | 2026-10-16 22:51 | +4/-10 | orquestador (rebase) 4/4: pruebas v1 |
| `orquestador-agentes` | ff58ee46c3 | 2026-10-16 22:49 | +7/-15 | orquestador v2.1: tokens de deploy cifrados (scrypt+AES-256-GCM con RIU_VAULT_PASSPHRASE,  |
| `handoff-migracion` | 4251edba46 | 2026-10-16 22:45 | +3/-15 | HANDOFF: fechas en UTC-5 (Bogotá), SECRETOS.md verificado con API HF (solo nombres), actua |
| `memoria-audit` | 7040d575bd | 2026-10-16 22:28 | +2/-15 | test_dag_final: usar memoria_yaiwes de 04-MEMORIA, no la copia vieja de workflow |
| … | — | — | — | 0 sin acceso y 22 sin revisar (define GITHUB_TOKEN) |

### Últimos commits en main (hora UTC-5)
- f149a70eff 2026-10-16 23:15 t146u: OpenClaw v2026.10.4 (openclaw/openclaw 383c124c) via motores canonicos, identico al tag salvo
- 140b5fd91a 2026-10-16 23:11 t146u: Hermes Agent v0.22.2 (NousResearch/hermes-agent d923a5eb) via motor_2+engine, motor_1, motor_
- 877952f948 2026-10-16 23:05 t145u: borrar copia vieja de Hermes (Componentes del Router/hermes-agent v2026.9.14, 13.030 archivos
- ca7de01ce2 2026-10-16 23:05 storage_lifecycle: restore fallido se reintenta con backoff 30-60 s, FUSIONA lo escrito localmente c
- 02847b8b2b 2026-10-16 22:59 t144u: agentes/ queda solo con chat-router-05-AGENTES, plan-opus-agentes y handoffs-agentes; borrar 
- e1d7550a44 2026-10-16 22:57 merge historial-persistente: botón ↺, respaldo completo de mensajes en /memoria y lista de pestañas 
- cc0bf9e1cd 2026-10-16 22:53 historial: respaldo completo en /memoria (cada mensaje user/bot/err sin recorte, cola si no hay red)
- 7972a78b18 2026-10-16 22:52 tools-staff (revision): Nemotron intenta Ultra primero y cae a Super con 503/404 (10 min de espera);
- b8a4e5ef74 2026-10-16 22:49 tools-staff: ficha NVIDIA Glimmer + Nemotron 3 Super con 1 clave (thinking off via chat_template_kwa
- fd03ea1d25 2026-10-16 22:48 storage_lifecycle: excepcion inesperada en restore => GAP_RESTORE_EXC (bloquea autosync, nunca queda

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
