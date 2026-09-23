# ➡️📂 OSQUESTADOR COMAND CENTER HF

Repo: maxbry123-commits/router-universal-router-inteligente-
Branch: main
Schema: yaiwes.node-executor/xray-v2
Mode: FAIL_CLOSED
Scope: HUGGING FACE ONLY
Updated: 2026-09-22 22:02 America/Bogota

## OBJETIVO
Dirigir exclusivamente el frente Hugging Face sin mezclar tareas de otros proyectos.

## REGLAS PERMANENTES
- SCOPE_LOCK = HF_ONLY.
- Claude/orquestador dirige y audita; los agentes ejecutan.
- Cero sobreingeniería.
- Máximo 3 pasos por tarea: REUTILIZAR/ADAPTAR -> CABLEAR/EJECUTAR -> PROBAR.
- Reutilizar componentes OSS antes de escribir código nuevo.
- Componentes externos: solo motores canónicos de main.
- Prohibido construir desde cero una solución equivalente sin autorización explícita del Director.
- Código nuevo únicamente para adaptar, mejorar, integrar o cablear componentes.
- Jobs del proyecto: solo hardware autorizado de 32 GB RAM.
- No declarar PASS sin ejecución real + evidencia observable.
- Credenciales por referencias/broker; nunca exponer secretos.

## HANDOFF INTERNO
Fuentes a leer antes de ejecutar:
- Claude notas/
- Handoff router inteligente universal.md
- bitácora stated JSON Craxy wall plan checkpoint router inteligente universal/
- router inteligente universal/integration/huggingface/
- router inteligente universal/agents-yaiwes/
- ➡️📂motores de descarga extracción copiado movimiento archivos router-universal-router-inteligente-/

## LOOP PERMANENTE
1. LEER: este archivo + handoff + objetivos/tareas HF.
2. ESTADO: revisar agentes HF y Jobs activos.
3. INVESTIGAR: GitHub + Hugging Face + comunidad solo si falta evidencia.
4. DELEGAR: entregar objetivo, origen, destino, restricciones y PASS.
5. PARALELIZAR: tareas independientes en agentes separados sin pisarse.
6. ACTUALIZAR: este archivo con estado, evidencia, GAP, FIX y siguiente acción.
7. REPORTAR: qué se hizo + qué falta.

## NODE DAG
NodeInput
-> RESEARCH
-> EXECUTE
-> VALIDATE
-> CLOSED | BLOCKED

ANTI_LOOP:
- NO_NEW_EVIDENCE: NO_RESEARCH
- NO_FIX: NO_RETEST
- NO_STATE_CHANGE: NO_REPEAT
- NO_FAKE_PASS
- MAX_RETRIES: 2

## COLA DE TRABAJO HF
- Inventariar Jobs activos y validar RAM.
- Mantener regla 32 GB RAM.
- Validar Storage Buckets/volúmenes autorizados.
- Validar modelos/repos/weights remotos necesarios.
- Validar endpoints/puertos/health cuando una tarea los use.
- Registrar coste/estado/resultado sin lanzar recursos no autorizados.
- Mantener trazabilidad en Crazy Wall/Handoff.

## FORMATO DE ORDEN A AGENTE
NODO: <id>
OBJETIVO: <literal>
SCOPE: HF_ONLY
ORIGEN: <URL/ruta>
DESTINO: <URL/ruta>
REGLAS:
- EXECUTOR_ONLY
- MAX_3_STEPS
- NO_OVERENGINEERING
- OSS_FIRST
- CANONICAL_MOTORS_ONLY
- NO_CODE_FROM_ZERO_WITHOUT_AUTHORIZATION
- 32GB_ONLY
PASS:
- execution_real
- test_real
- observable_evidence
- read_back

## TELEMETRÍA
[NODO:{nodo}]
[STEP:{step}]
[ACCIÓN:{accion}]
[RESULTADO:{resultado}]
[GAP:{gap}]
[FIX:{fix}]
[TEST:{test}]
[ESTADO:{estado}]
[SIGUIENTE:{siguiente}]
