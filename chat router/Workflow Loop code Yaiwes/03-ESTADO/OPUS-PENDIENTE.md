# OPUS — PENDIENTE CRÍTICO (Router · HF · Vercel · conector) + ESTADO DE LO EN CURSO
Actualizado: 2026-09-27 20:00 UTC. Solo Opus toca esto (los espejos lo tienen prohibido). Formato compacto para IA.
Leer antes: `chat router/Workflow Loop code Yaiwes/03-ESTADO/RECOVERY.yaml` · Reglas: `chat router/Workflow Loop code Yaiwes/01-PLAN/PLAN-DSL-DAG-00-CONTRATO.yaml`.

## A. ESTADO DE LO EN CURSO (verificar con evidencia, no con palabras)
| Qué | Dónde | Estado 20:00 | Cómo verificar |
|---|---|---|---|
| T01 gobierno | chat router/Workflow Loop code Yaiwes/05-AGENTES/gobierno | ✅ CÓDIGO EN MAIN (commit 8807d5e, 641 líneas, 17 tests escritos) · tests: VER aviso "tests" del job | Actions → Claude Code Espejos → run 36344878757 → espejo (T01) |
| T02 colmena | chat router/Workflow Loop code Yaiwes/05-AGENTES/colmena | 🟡 corriendo (run 36344878757) | commit "espejo T02" en main |
| T03 OmniRoute estable | chat router/08-OMNIROUTE | 🟡 corriendo (run 36344878757) | commit "espejo T03" |
| T04 pasarela Claude Code | chat router/Workflow Loop code Yaiwes/09-CLAUDE-CODE | 🟡 corriendo (run 36344878757) | commit "espejo T04" |
| T05 funciones chat | chat router/Workflow Loop code Yaiwes/10-CHAT-FUNCIONES | 🟡 lanzado 19:58 | commit "espejo T05" |
| T06 Hermes+OpenClaw | chat router/Workflow Loop code Yaiwes/05-AGENTES/asistentes | 🟡 lanzado 19:58 | commit "espejo T06" |
| T07 puerta evidencia | chat router/Workflow Loop code Yaiwes/11-EVIDENCIA | 🟡 lanzado 19:58 | commit "espejo T07" |
| T08 motores fábrica | chat router/Workflow Loop code Yaiwes/12-FABRICA-MOTORES | 🟡 lanzado 19:58 | commit "espejo T08" |
| Memoria/almacenamiento | chat router/04-MEMORIA (Manus) | 🟡 Manus (SQLite cableado, 39 tests PASS) | bloque STATE HUB en 03-ESTADO/HANDOFF.md |
| Sentinelas ×3 | .github/workflows/sentinelas.yml (cada 20 min) | ✅ escribiendo informes | chat router/06-EQUIPO/SENTINELA-*.md |
| Plan 4 objetivos | .github/workflows/mini-router-plan-4-objetivos.yml | ⚠️ proveedor por defecto cerebras (402) → probablemente falla | Actions → Mini Router |
Tabla por tarea con historial de fallos: `chat router/Workflow Loop code Yaiwes/06-ESPEJOS/HANDOFF-ESPEJOS.md`.

## B. PENDIENTE DE OPUS (orden de ejecución)
### B1. Revisar entregas de los espejos (cada 1-2 h)
- Por cada T0X: commit en main + archivos con contenido + aviso "tests" en el job. Marcar HECHA/FALLÓ en HANDOFF-ESPEJOS.md. Si FALLÓ: leer avisos del job, corregir la tarea (.md) y relanzar solo ese T0X (botón Claude Code Espejos, input tareas=T0X).

### B2. Router (HF Job 16 GB de pago)
1. Plan 4 objetivos → proveedor NVIDIA: en `.github/workflows/mini-router-plan-4-objetivos.yml` cambiar `default: cerebras` y `PROVEEDOR: … 'cerebras'` → `nvidia`; pasar NVIDIA_API_KEY_1..4 ya están.
2. Instalar T03 cuando pase: copiar `chat router/08-OMNIROUTE/start_omniroute.sh` (+ supervisor, mantenimiento) a `router inteligente universal/keeper/`; relanzar `riu-router-job-central.yml` (flavor cpu-basic, 48h); ejecutar `prueba-omniroute-router.yml` (relee LIVE_URL cada intento) → PASS = status encendido + /v1/models + 1 respuesta.
3. Añadir OmniRoute como proveedor del Router (nodo A-2): en `integration/chat_mvp/providers.py` proveedor `omniroute` base `http://127.0.0.1:20128/v1`; ruta: omniroute + nvidia; DeepSeek solo con claves.
4. Aviso modelos en el chat (A-3): ruta `/chat/modelos-disponibles` que use `agents-yaiwes/common/routes.py: disponibles()` (Kimi K3 > GLM-5 > DeepSeek V4) → el chat lo muestra al abrir (rojo si no hay).
5. Montar módulos de los espejos en el Router (cuando pasen): `app.py` ya monta `ui_bridge` y `omniroute_proxy` dentro de try; añadir igual `10-CHAT-FUNCIONES/rutas.py` (build_router) y la colmena (T02) vía un loader que añada `chat router/` al sys.path.
6. Autoescalado (A-4): cola en el Router + vigilante (16 GB extra al 80% tope 3; cadena 32 GB al 85% tope 10; apagar tras 15 min sin tareas).
7. Diagnóstico si el Router cae: `diagnostico-router-job.yml` (lee estado y log del Job). Causa previa conocida: faltaba `httpx` (ya añadido al lanzador).

### B3. Hugging Face
1. Puente de almacenamiento H-1: snapshot SQLite + adjuntos → dataset privado `COMAND-CENTER-1/yaiwes-hf-memoria`; al arrancar el Router restaurar si SQLite vacío. Coordinar con Manus (04-MEMORIA).
2. Conector MCP: Space `COMAND-CENTER-1/claude-github-mcp-backup` (cpu-basic gratis, SIN OAuth, dirección secreta `/<MCP_SECRET_PATH>/mcp`, webhook dispara el lanzador único). Director pidió llevarlo a la máquina 16 GB con letrero fijo en Vercel (`/mcp/<secreto>` → LIVE_URL): hacerlo SOLO con prueba previa de conexión antes de apagar el Space.
3. Spaces `omniroute-1..5`: pausados (no cobran). Borrar o reutilizar solo con orden del Director.
4. Memoria HF de arquitectura: actualizar `README-HUGGINGFACE.md` (raíz) y el dataset `yaiwes-hf-memoria` con cada cambio.

### B4. Vercel (proyecto `riu-jev-bridge`, id prj_m8Lk3iaB3eN6dwlIq1ND2un8FWTD)
1. Despliegue automático APAGADO (commandForIgnoringBuildStep = "exit 0"). No publicar por commit.
2. Un solo despliegue final cuando el Director lo ordene: base del chat aprobada (chat de Manus / Open WebUI; FLAG-2: pedir enlace) + `/api` hacia el Router + letrero `/mcp` y `/omniroute/v1`.
3. Límite Hobby agotado (402 DEPLOYMENT_DISABLED) hasta que se reinicie el cupo; no gastar despliegues.

### B5. Pendiente del Director (pedir, no inventar)
GROQ_API_KEY_n en secretos del repo del Router · enlace del chat de Manus · aprobar plan del T-3000 · facturación de Cerebras si la quiere (hoy eliminado).
