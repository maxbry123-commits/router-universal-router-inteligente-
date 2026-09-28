# HANDOFF ESPEJOS — estado real por tarea (sin evidencia = NO ejecutado)
Actualizado: 2026-09-28 03:00 UTC · GPT-5.6 Sol · Workflow histórico: `.github/workflows/claude-code-espejos.yml`
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
| T03 | OmniRoute estable (v3.8.50, Node 24, better-sqlite3, supervisor, retención) | `chat router/08-OMNIROUTE` | RELANZADA 19:35 · antes: SIN EVIDENCIA | ninguna todavía |
| T04 | Pasarela Claude Code ↔ NVIDIA (free-claude-code) + vía DeepSeek Harness | `chat router/09-CLAUDE-CODE` | RELANZADA 19:35 · antes: SIN EVIDENCIA | ninguna todavía |
| T09 | Suite multi-chat: conservar Open WebUI y copiar debajo sus 3 chats disponibles (LibreChat, big-AGI, Jan), cableados a Hermes/OpenClaw sin usar las UIs propias de esos agentes | `router inteligente universal/Componente open soure router inteligente universal/open-webui` + `chat router/13-CHAT-UI-SUITE` | PLANIFICADA · ejecución manual GPT · mirror `mirror/T09` | fuentes verificadas en `frontend/main/UI YAIWES/componentes open soure UI YAIWES/` |

## T09 — plan quirúrgico en 4 salidas
1. **T09-A · inventario + espejo** — fijar `mirror/T09`, registrar fuentes exactas y comprobar que Open WebUI, LibreChat, big-AGI y Jan existen; no modificar código fuente.
2. **T09-B · copia exacta** — copiar LibreChat, big-AGI y Jan debajo del bloque Open WebUI usando la política del motor canónico; preservar archivos de origen, sin reescritura ni recorte.
3. **T09-C · cableado** — crear únicamente un overlay/adaptador fuera del código fuente de las UIs para exponer Hermes y OpenClaw como backends/agentes mediante el Router; no incorporar las UIs propias de Hermes/OpenClaw.
4. **T09-D · sentinela + cierre** — read-back, hashes/rutas, aceptación determinista e informe `T09.md`; solo después publicar el cierre en main y actualizar esta tabla con SHA y PASS/FAIL real.

## Por qué no hubo evidencia antes (historial de fallos, ya corregidos)
1. 11:34 Claude Code + LiteLLM: modelo NVIDIA retirado (410) → corregido con probar_modelos.py (catálogo vivo).
2. 12:0x Claude Code + Kimi K3: herramientas cortadas por el puente → cambiado a Aider (T04 arregla Claude Code).
3. 16:45 Aider sin archivos declarados: no escribió nada → cada tarea declara ARCHIVOS.
4. 17:43 Aider escribió pero no guardó: su propio git chocó con el checkout parcial y tomó una línea de diagrama como nombre → `--no-git` + regla de nombres.

## Modelos que responden hoy (probados con clave real)
NVIDIA_API_KEY_1: moonshotai/kimi-k3 = 200 · z-ai/glm-5.3 = 200 · z-ai/glm-5.3-flash = 200. Kimi K2.6 = 404 (no habilitado). DeepSeek V4.1 flash = timeout. Cerebras = 402 (pago).

## Siguiente paso (quien continúe)
- T09: continuar exclusivamente desde `mirror/T09`; no declarar PASS sin read-back de las 3 copias, overlay Hermes/OpenClaw y aceptación determinista.
- Revisar la vuelta lanzada 19:35 con los 4 puntos de "Cómo verificar". Marcar cada tarea HECHA / FALLÓ(causa) en esta tabla.
- T03 hecha → Opus revisa y copia `08-OMNIROUTE/start_omniroute.sh` al Router (`router inteligente universal/keeper/`) y relanza el Router 16 GB.
- T04 hecha → probar Claude Code por la pasarela; si funciona, los espejos pasan a Claude Code.
