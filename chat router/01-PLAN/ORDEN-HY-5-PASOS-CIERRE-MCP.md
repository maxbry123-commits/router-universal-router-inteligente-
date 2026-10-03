# ORDEN DE HY — CIERRE MCP FUNCIONAL (2026-10-03) — 5 pasos, 3 salidas
Fuente: mensajes de Hy. Reglas: sin GitHub Actions; sin tocar el Router; HF solo procesador pago 16 GB RAM (job temporal); Vercel solo puente; ahorrar tokens.

## Paso 1 (salida 1) — Memoria/almacenamiento completo
- Terminar memoria y conectarla al Router SIN tocar el Router, por plugins via DeepSeek Harness.
- Puente a Hugging Face (Dataset COMAND-CENTER-1/yaiwes-hf-memoria privado). El Router deberia exponer MCP para conectar almacenamiento con HF; si no existe -> PENDIENTE anotado aqui, en Crazy Wall, bitacora, STATE JSON, handoff y README arquitectura.
- Plan base: 01-PLAN/DSL-DAG-MEMORIA-ALMACENAMIENTO.yaml (SQLite primario; graphiti/graphify/memanto adaptadores; FalkorDB/PostgreSQL/Redis/AgentDB = GAP si falta servicio).

## Paso 2 (salida 2) — Motores para bajar skills faltantes
- Usar los motores de descarga; todo organizado en un solo archivo raiz segun la plantilla. No re-descargar lo existente. Destino lo da el plan (frontend es FUENTE, no destino).

## Paso 3 (salida 3) — Workflow operativo
- Sin GitHub Actions. Probar conectado al Router sin job; si no funciona, job HF temporal SOLO en el procesador pago de 16 GB RAM (ningun otro procesador HF autorizado).
- Debe quedar operativo con lo que haya.

## Paso 4 — Auditoria (4 pasadas, archivo por archivo)
- Lista simple enumerada de lo que falta, con trazabilidad al archivo; anotar en Crazy Wall/bitacora/STATE JSON; indice handoff que ubique lo que falta en el archivo del plan.

## Paso 5 — Skills y contratos (sin sobre-ingenieria)
- Encadenar skills como DSL DAG; schema identico + Sheriff por skill; no escribir todo el codigo: usar motor de copia o funcion de copiar de GitHub. Tabla previa: nombre | fuente oficial | commit fijado | existe ya | SKILL.md y recursos | licencia | mecanismo de ejecucion | uso en chat | evidencia. Origen/codigo ausente -> GAP.

## Pendientes previos vigentes
- Haiku: X-Ray forense (T-11-04) ; Sol GPT: diagrama Archify con info de Haiku.
- Nombre/raiz del workflow (sin emoji; raiz oficial `chat router/📂 workflow Loops code Yaiwes/`): sin renombrar ni mover hasta confirmar.
