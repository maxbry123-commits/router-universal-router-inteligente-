# SWE CODE free · auditoría 3× por modelo · 2026-11-02

**Rama:** main · **Alcance:** exclusivamente selector `swen-code-free`.
**No tocar:** SWE CODE local, Groq, NVIDIA, Vercel, HF Space, ni historia de conversaciones.

## Cinco opciones autorizadas (únicas)
`web-qwen38max`, `web-claude-sonnet`, `web-qwen37max`, `web-dsv4-flash`, `swecode-consulta`.

## Pruebas reales a través del MCP instalado en este chat

Se intentaron **3 solicitudes por cada identificador del selector (15 en total)**,
con `ficha_qwen=ficha5-mvp` y `modelo` igual al identificador exacto.
Todas fueron rechazadas **ANTES de inferencia** por el servidor MCP:
`INVALID_ARGUMENT: modelo no permitido en el plan personal`.

| Opción | Intento 1 | Intento 2 | Intento 3 |
|---|---|---|---|
| Qwen 3.8 Max web | BLOQUEO MCP | BLOQUEO MCP | BLOQUEO MCP |
| Claude Sonnet 5.5 web | BLOQUEO MCP | BLOQUEO MCP | BLOQUEO MCP |
| Qwen 3.7 Max web | BLOQUEO MCP | BLOQUEO MCP | BLOQUEO MCP |
| DeepSeek V4 Flash web | BLOQUEO MCP | BLOQUEO MCP | BLOQUEO MCP |
| Ask Cónsil | BLOQUEO MCP | BLOQUEO MCP | BLOQUEO MCP |

**Conclusión honesta:** no está confirmado que el Space/Gateway esté respondiendo.
El MCP instalado permite otros identificadores personales distintos de los 5 WEB,
por lo que no es un cliente de pruebas de los selectores SWE CODE free.
No utilizar alias de otros modelos ni aceptar un LLM local como falsa prueba.

## 15 pruebas deterministas del selector, sin inferencia

Para cada uno de los cinco identificadores se verificaron tres escenarios:
1. Identidad: conserva el modelo exacto sin cambiar a Liquid/HF.
2. Selección del agente: permite OpenClaw, OpenHands o Codex; `modelo_tool` sigue siendo WEB.
3. Handoff: conserva la conversación y contexto anterior con IDs distintos, con workflow individual.

**15/15 PASS** en evaluación JavaScript sobre código de la rama `main`.
Prueba reproducible: `tests/swen_selector_3x.mjs` (Node 22, sin paquetes adicionales).

## Ask Cónsil · 3 escenarios simulados

1. Cuatro opiniones válidas, Qwen 3.8 Max arbitra: PASS.
2. Claude no disponible, salida 🚩 y resto del consejo prosigue: PASS.
3. Fallo del árbitro, no se inventa una respuesta final: PASS.

**3/3 PASS simulados**. No demuestra que las cuentas web hayan contestado.

## GAPS corregidos y publicados

- `modelo_tool` web se convertía silenciosamente al local porque `normSeleccion` no reconocía WEB: corregido.
- `endpoint_modelo()` daba `KeyError` con proveedor `web` en flujo de agentes: corregido para llamar al bridge existente.
- El contrato de tarea individual WEB arrastraba `modelo_lector` Liquid y `modelo_revisor` HF: eliminado para SWE CODE free.
- El selector mostraba workflows Liquid/4 pasos aunque SWEN era exclusivamente web: ocultado/restringido a Individual sólo en esa ventana.
- `swecode-consulta` podía caer silenciosamente a un respaldo local si fallaba el árbitro: ahora conserva error sin cambiar de modelo.
- `openclaw-ui/src/contract.ts` carecía de `defineFeatureContract({pluginId,operations})` y rompía la carga de herramientas: reconstruido a partir de la versión anterior válida.

## Pendientes de validación real

🚩 Probar el endpoint desplegado `/plugins/deepseek_harness/modelos/v1/chat/completions` con la credencial del usuario y cada ID WEB (3 veces).
🚩 Comprobar salud de las sesiones autorizadas, conexión y facturación/respuesta de Claude Gateway.
🚩 Ejecutar una tool REAL no destructiva con autorización y recibo, para certificar la orquestación y delegación OpenClaw → agente elegido.
🚩 No dar por hecho que el código ya está desplegado o que hay disponibilidad real sin estos resultados.

**La ejecución con distintos agentes está cableada a los adaptadores existentes y depende de instalación, permisos y políticas del Harness; la configuración actual no acredita por sí sola que OpenClaw sea siempre el orquestador cuando se selecciona otro ejecutor.**

## Revisión adicional posterior — GAP causal identificado

**GAP crítico localizado y corregido en** `chat/backend/deepseek_harness/server.py`:
el bloque `if tools is True` enviaba **todas** las solicitudes `tools: true`
a `_mvp_modelo_compat()`, incluso `web-*` y `swecode-consulta`.
Eso desviaba el modelo seleccionado fuera del bridge de suscripciones web;
el Router MVP podía rechazar el ID o devolver un modelo de respaldo no solicitado.

**Corrección:** separar el destino antes de la rama Tools ON:
- Modelo `web-*` o `swecode-*` → Harness → **SWE CODE web-bridge** con `tools:true`, sin LLM traductor.
- Modelos propios Router MVP → mantienen su motor y catálogo MCP.
- `ejecutor_tools` preserva OpenClaw u otro ejecutor según el selector.
- El bridge bloquea fallback de modelo web/Ask Cónsil a Liquid/HF/NVIDIA.

**Resultado de repetir los 15 intentos reales desde este ChatGPT con el MCP
`riu_router_github.chat`:** 0/15 admitidos. Los 15 obtuvieron
`MCP_MODELO_NO_PERMITIDO` antes de llegar a SWE CODE free.
**Este conector personal usa una lista de modelos API distinta del catálogo
web de SWE CODE free. No comprueba los cinco selectores ni puede verificar
suscripciones con esos IDs.** No se deben atribuir esas negativas al servidor de
modelos web sin pruebas adicionales.

**Pruebas adicionales de código actual:** 15/15 del selector + 3/3 del Consejo
simulados (PASS); verificaciones de enrute `Tools ON` y no-fallback (PASS).

**Prueba REAL preparada en el repositorio**:
`tests/swen_live_3x.mjs`, ejecutable desde el mismo servidor con sus
credenciales existentes. Envía 3 consultas por ID vía Harness, registra HTTP,
modelo efectivo, respuesta no vacía, dictamen de Ask Cónsil y anomalías.
El script no crea infraestructura adicional ni publica secretos. **No se
ejecutó desde este entorno: no tiene acceso HTTP/autenticación a ese Space**.

**Criterio de cierre:** 15/15 `PASS` de pruebas REALES desde el propio
servidor y recibo de una ejecución de herramienta con el agente elegido.
Hasta entonces, publicar código no equivale a acreditar despliegue funcional.
