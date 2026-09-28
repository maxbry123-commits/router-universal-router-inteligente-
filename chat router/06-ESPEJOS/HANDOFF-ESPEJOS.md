# HANDOFF ESPEJOS — estado real por tarea (sin evidencia = NO ejecutado)
Actualizado: 2026-09-28 03:08 UTC · GPT-5.6 Sol · Workflow histórico: `.github/workflows/claude-code-espejos.yml`
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
| T03 | OmniRoute estable (v3.8.50, Node 24, better-sqlite3, supervisor, retención) | `chat router/08-OMNIROUTE` | RECUPERACIÓN ACTIVA · fix evita OOM, falta localizar fase bloqueada antes de 20128 | OOM previo x10 `6ab9dc4052d0dbd7f1d9f760` · OOM previo x1 `6ab9f74152d0dbd7f1d9fe15` · fix `6aba013252d0dbd7f1da005c` CANCELED sin OOM, ~12/16 GB estable |
| T04 | Pasarela Claude Code ↔ NVIDIA (free-claude-code) + vía DeepSeek Harness | `chat router/09-CLAUDE-CODE` | RELANZADA 19:35 · antes: SIN EVIDENCIA | ninguna todavía |
| T09 | Suite multi-chat: Open WebUI + LibreChat + big-AGI + Jan; Hermes/OpenClaw por gateway común, sin usar sus UIs | `router inteligente universal/Componente open soure router inteligente universal/open-webui/otros-chat` + `chat router/13-CHAT-UI-SUITE` | PASS FUNCIONAL · cierre manual GPT | `informes/T09.md` · main `92bb075fce8fe30b9efc4566e07391b08a2c9d39` · mirror `5a94d71e9785e37e8bf8871518c54a017f702e82` · 4/4 tests + HTTP PASS · gitlinks exactos |

## T09 — plan quirúrgico en 4 salidas
1. **T09-A · inventario + espejo** — fijar `mirror/T09`, registrar fuentes exactas y comprobar que Open WebUI, LibreChat, big-AGI y Jan existen; no modificar código fuente.
2. **T09-B · copia exacta** — copiar LibreChat, big-AGI y Jan debajo del bloque Open WebUI usando la política del motor canónico; preservar archivos de origen, sin reescritura ni recorte.
3. **T09-C · cableado** — crear únicamente un overlay/adaptador fuera del código fuente de las UIs para exponer Hermes y OpenClaw como backends/agentes mediante el Router; no incorporar las UIs propias de Hermes/OpenClaw.
4. **T09-D · sentinela + cierre** — read-back, hashes/rutas, aceptación determinista e informe `T09.md`; solo después publicar el cierre en main y actualizar esta tabla con SHA y PASS/FAIL real.

## T03 — recuperación OOM 2026-09-28

Diagnóstico confirmado antes de tocar runtime:
- x10 instancias: HF `cpu-basic` 16 GB terminó `OOMKilled / exit 137`.
- 1 sola instancia: volvió a terminar `OOMKilled / exit 137` antes de abrir `20128`; por tanto 10 instancias NO son la causa única.
- prueba instrumentada upstream v3.8.50: `npm ci` simple falla; fallback `npm install` ejecuta postinstall generales (Playwright/Chromium, ONNX Runtime, etc.) y eleva RAM; luego `npm run build` con Turbopack llevó el cgroup hasta ~15.997 GB / 16 GB.
- `better-sqlite3` cargó correctamente en la prueba instrumentada; no es la causa primaria.

Plan quirúrgico:
1. Sustituir instalación por la receta upstream reproducible: `npm ci --include=optional --no-audit --no-fund --legacy-peer-deps --ignore-scripts`.
2. Ejecutar solo bindings/scripts nativos necesarios y validar `better-sqlite3` fail-closed.
3. Compilar con `OMNIROUTE_USE_TURBOPACK=0`, workers limitados y heap de build controlado.
4. Arrancar 1 instancia por defecto y exigir `health + /v1/models + chat model=auto` antes de escalar.
5. Solo tras PASS actualizar esta sección y el informe T03 con evidencia real.

Ejecución GPT-5.6 Sol 2026-09-28 05:54 UTC:
- validado que `build:backend` existe en upstream v3.8.50;
- lanzada prueba aislada del script actual de `main` con `OMNIROUTE_INSTANCIAS=1`, sin clonar el monorepo completo, para medir el fix sin contaminación de memoria;
- HF Job de prueba: `6aba013252d0dbd7f1da005c`;
- resultado: el Job fue `CANCELED` sin OOM; RAM se estabilizó ~11.99/16 GB y nunca abrió `20128`.
- siguiente microtarea: diagnóstico ≤10 min con tail vivo de `/tmp/omniroute.log` para identificar si el bloqueo está en lockfile/install, `better-sqlite3`, `build:backend`/Webpack o arranque; NO relanzar pruebas anteriores ni modificar el lanzador hasta tener la fase exacta.

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