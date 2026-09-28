# HANDOFF ESPEJOS — estado real por tarea (sin evidencia = NO ejecutado)
Actualizado: 2026-09-28 06:12 UTC · GPT-5.6 Sol · Workflow histórico: `.github/workflows/claude-code-espejos.yml`
Regla: una tarea solo cuenta como HECHA si hay commit de cierre en main + archivos con contenido en su carpeta + informe con salida real de tests/aceptación.

## Cómo verificar (cualquiera: Director, GPT, otro Opus)
1. Commits: https://github.com/maxbry123-commits/router-universal-router-inteligente-/commits/main → buscar el commit de la tarea.
2. Carpeta de la tarea (tabla abajo) → debe tener los ARCHIVOS de su tarea, no vacíos.
3. Informe: `chat router/06-ESPEJOS/informes/T0X.md` → salida real de aceptación/tests.
4. Para tareas ejecutadas por el workflow histórico, revisar también Actions. Para T09, el cierre es manual por GPT y exige read-back en main.

## Estado
| Tarea | Qué | Carpeta | Estado real | Evidencia |
|---|---|---|---|---|
| T01 | Gobierno: Sheriff, Judge, Sentinel, contratos, MirrorManager | `chat router/05-AGENTES/gobierno` | RELANZADA 19:35 · antes: SIN EVIDENCIA | ninguna todavía |
| T02 | Colmena: YaiwesHive + EngineeringLoop por el Router | `chat router/05-AGENTES/colmena` | RELANZADA 19:35 · antes: SIN EVIDENCIA | ninguna todavía |
| T03 | OmniRoute estable (v3.8.50, Node 24, better-sqlite3, supervisor, retención) | `chat router/08-OMNIROUTE` | **PASS RUNTIME** · bundle npm precompilado · 1 activa / 9 pausadas · free no-auth HF = BLOCKED_UPSTREAM | `6aba04746b030d633f69bc1c`: 9/9 PASS · `20128` PASS · health 200 · supervisor estable · workflows corregidos `ab89ed4c`, `b7ba32a8` |
| T04 | Pasarela Claude Code ↔ NVIDIA (free-claude-code) + vía DeepSeek Harness | `chat router/09-CLAUDE-CODE` | RELANZADA 19:35 · antes: SIN EVIDENCIA | ninguna todavía |
| T09 | Suite multi-chat: Open WebUI + LibreChat + big-AGI + Jan; Hermes/OpenClaw por gateway común, sin usar sus UIs | `router inteligente universal/Componente open soure router inteligente universal/open-webui/otros-chat` + `chat router/13-CHAT-UI-SUITE` | PASS FUNCIONAL · cierre manual GPT | `informes/T09.md` · main `92bb075fce8fe30b9efc4566e07391b08a2c9d39` · mirror `5a94d71e9785e37e8bf8871518c54a017f702e82` · 4/4 tests + HTTP PASS · gitlinks exactos |

## T09 — plan quirúrgico en 4 salidas
1. **T09-A · inventario + espejo** — fijar `mirror/T09`, registrar fuentes exactas y comprobar que Open WebUI, LibreChat, big-AGI y Jan existen; no modificar código fuente.
2. **T09-B · copia exacta** — copiar LibreChat, big-AGI y Jan debajo del bloque Open WebUI usando la política del motor canónico; preservar archivos de origen, sin reescritura ni recorte.
3. **T09-C · cableado** — crear únicamente un overlay/adaptador fuera del código fuente de las UIs para exponer Hermes y OpenClaw como backends/agentes mediante el Router; no incorporar las UIs propias de Hermes/OpenClaw.
4. **T09-D · sentinela + cierre** — read-back, hashes/rutas, aceptación determinista e informe `T09.md`; solo después publicar el cierre en main y actualizar esta tabla con SHA y PASS/FAIL real.

## T03 — recuperación OOM 2026-09-28

**Causa confirmada:** no eran las 10 instancias. Una sola instancia también moría porque el launcher compilaba OmniRoute desde fuente dentro del Job de 16 GB. `npm install` ejecutaba postinstall pesados y el build Next/Turbopack/webpack agotaba la memoria.

**Solución aplicada:**
- se eliminó el build de Next.js del arranque;
- se usa el bundle oficial precompilado `omniroute@3.8.50` desde npm;
- se omiten opcionales pesados y postinstall generales;
- `better-sqlite3@^13.0.2` se instala y verifica de forma aislada en `~/.omniroute/runtime/`;
- el supervisor T03 conserva lock, backoff, healthcheck y límite RSS del árbol de procesos;
- `start_omniroute_x10.sh` deja **1 instancia activa y 9 pausadas**.

**Prueba real final — HF Job `6aba04746b030d633f69bc1c`:**
- `python -m pytest "chat router/08-OMNIROUTE" -q` → **9 passed**;
- sintaxis de ambos launchers → **PASS**;
- puerto `127.0.0.1:20128` → **PASS**;
- `/api/monitoring/health` → **HTTP 200**;
- supervisor vivo después de la prueba → **PASS**;
- log: `OmniRoute 3.8.50 precompilado OK` + `better-sqlite3 nativo OK`.

**Separación de responsabilidades:** `auto/best-free` sí entró al router y creó un pool de 13 candidatos, pero los upstream gratuitos rechazaron el egress de HF: OpenCode 403 y Felo 400/429; DuckDuckGo devolvió 418 y UncloseAI 502. Prueba directa no-auth `6aba06f36b030d633f69bc4c`: runtime HEALTH PASS, pero ninguno de los modelos probados devolvió contenido utilizable. Esto ya no es un fallo de arranque/RAM de OmniRoute. T03 runtime queda PASS; la disponibilidad de upstream gratuito se registra como bloqueo externo independiente.

**Corrección de orquestación final:** Router central usa `start_omniroute.sh` como launcher principal (`ab89ed4c`); el workflow de prueba espera 1/1 y separa `RUNTIME` de `FREE_PROVIDER` (`b7ba32a8`).

## Por qué no hubo evidencia antes (historial de fallos, ya corregidos)
1. 11:34 Claude Code + LiteLLM: modelo NVIDIA retirado (410) → corregido con probar_modelos.py (catálogo vivo).
2. 12:0x Claude Code + Kimi K3: herramientas cortadas por el puente → cambiado a Aider (T04 arregla Claude Code).
3. 16:45 Aider sin archivos declarados: no escribió nada → cada tarea declara ARCHIVOS.
4. 17:43 Aider escribió pero no guardó: su propio git chocó con el checkout parcial y tomó una línea de diagrama como nombre → `--no-git` + regla de nombres.

## Modelos que responden hoy (probados con clave real)
NVIDIA_API_KEY_1: moonshotai/kimi-k3 = 200 · z-ai/glm-5.3 = 200 · z-ai/glm-5.3-flash = 200. Kimi K2.6 = 404 (no habilitado). DeepSeek V4.1 flash = timeout. Cerebras = 402 (pago).

## Siguiente paso (quien continúe)
- T09: cerrado funcionalmente; no relanzar. Las tres UIs alternativas quedaron como gitlinks/submódulos fijados a los commits exactos verificados y el gateway reutiliza T06.
- Revisar la vuelta lanzada 19:35 con los 4 puntos de "Cómo verificar". Marcar cada tarea HECHA / FALLÓ(causa) en esta tabla.
- T03 hecha → Opus revisa y copia `08-OMNIROUTE/start_omniroute.sh` al Router (`router inteligente universal/keeper/`) y relanza el Router 16 GB.
- T04 hecha → probar Claude Code por la pasarela; si funciona, los espejos pasan a Claude Code.