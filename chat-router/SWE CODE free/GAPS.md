# GAPS — SWE CODE y SWEN CODE free (checklist)

Estado verificado en `main`. ✅ = hecho con prueba o evidencia en el repo · ⏳ = depende de HF/Grok (no es código).

## Los 16 pedidos

| # | Gap | Estado | Evidencia |
|---|---|---|---|
| 1 | Acceso a GitHub y Hugging Face igual que el chat | ✅ | Todo modelo pasa por el Harness: `github_*`, `almacen`; `ARQUITECTURA.md` §2 |
| 2 | Motores de descarga/extracción | ✅ | herramienta `archivos` (`test_archivos.py`) |
| 3 | Recuperar sesiones Qwen/DeepSeek con varias cuentas | ✅ | `INSTRUCCIONES.md` §7/§7a (`/refresh_session`, rotación, `/v1/queue`) |
| 4 | OpenClaw conoce pasos y funcionamiento | ✅ | `INSTRUCCIONES.md`, `agente.md`, §7d |
| 5 | README + arquitectura + handoff detallados | ✅ | `ARQUITECTURA.md`, `HANDOFF.md`, `README.md` |
| 6 | Enlaces de dónde está todo | ✅ | `HANDOFF.md` tabla «Dónde está todo» |
| 7 | Auto-evolución | ✅ | `evolucion.py` + `test_evolucion.py` (5) |
| 8 | Liquid y cada función del chat como un modelo del selector, con formato de salida | ✅ | `swe.py`, `prompt.formato()` a todo modelo, `test_swe.py` |
| 9 | Respaldo Groq → NVIDIA → HF local | ✅ | `swe.llamar` (`test_swe.py`) y `mini_router.py` (`test_mini_router.py`) |
| 10 | OpenClaw usa la misma memoria del chat | ✅ | herramienta `memoria` (bucket `riu-chat/`), `ARQUITECTURA.md` §3 |
| 11 | Cambiar de selector conserva el historial | ✅ | historial por `contexto_previo` + `_sin_identidades` (`test_mcp_sesion.py`) |
| 12 | Selector Groq/NVIDIA conectado al agente que despliega | ✅ | el pipeline cae a Groq/NVIDIA (`mini_router.py`, `swe.py`) |
| 13 | Recuperar selectores del chat y editar sin romper los nuevos | ✅ | revert de `de27bac18b` + grupos SWE (`selector-modelos.test.mjs`) |
| 14 | Selector SWE CODE con 2 opciones (free y SWEN) | ✅ | grupos «SWE CODE (local HF)» y «SWEN CODE free (web)» |
| 15 | APK descargable en Configuración | ✅ | sección «Agente móvil (APK)» al principio (`apk-configuracion.test.mjs`); ⏳ build/`/apk` en el Space |
| 16 | Modelos funcionando en la UI de OpenClaw | ✅ código | `provider-openclaw.json`; ⏳ redeploy del Space |

## Los 5 adicionales

| # | Gap | Estado | Evidencia |
|---|---|---|---|
| 17 | «Detener» no llegaba al Router (ruta `cancelar` inexistente, tareas zombi retomadas al reiniciar) | ✅ | `test_cancelar.py` |
| 18 | Modelos SWE decían correr en «QwenCloud» | ✅ | `test_mcp_sesion.py` (identidad por plataforma) |
| 19 | Ids `hf-*` del selector se tomaban por fichas viejas (respondía Qwen) | ✅ | `app.py` + `test_mcp_sesion.py` |
| 20 | «SWEN CODE free …» no se interpretaba en el Router (modo, modelo, sección, pipeline) | ✅ | `swe.activar` + `TestActivacion`/`TestPipeline` |
| 21 | Raíz del repo con una tercera carpeta (enlaces sueltos de Devin) | ✅ | solo `router-mvp/` y `chat-router/` |

## Pendiente fuera del código (Grok / HF)

1. Redeploy del Space al último `main` (`/health.commit`; el Space clona `main` al arrancar).
2. Ruta `GET /v1/queue` en el proxy `:7860` → bridge `:7870`.
3. Proceso `puente-movil` en el servidor Riu.
4. Cuentas web: las entrega OpenClaw por llamada (nunca en secrets).
5. Tareas pendientes viejas en el bucket (`riu-chat/tareas/pendientes.json` tiene 9 sin terminar): se retoman en cada reinicio; ahora «Detener» las corta, pero estas 9 hay que cortarlas una vez con `cancelar`.
