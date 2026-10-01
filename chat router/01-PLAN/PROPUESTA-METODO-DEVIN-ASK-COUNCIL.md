# Propuesta para aprobación — método de trabajo Devin / YAIWES

**Estado:** BORRADOR, NO ACTIVADO. **Fecha:** 2026-10-01. **Ámbito:** programación o cualquier proyecto con entregables comprobables. **Decisor:** Director para incorporar el método; Judge determinista para declarar PASS de una ejecución concreta. Ninguna simulación de este documento equivale a una llamada real a Kimi, GLM, DeepSeek o NVIDIA.

El proyecto ya tiene dos conjuntos distintos de doce goals: metas de producto en `PLAN-DSL-DAG-00-CONTRATO.yaml` y preguntas de la Puerta de Evidencia en `11-EVIDENCIA/goals.py`. También tiene un `ask_council` C01–C12 de gobernanza y un ASK COUNCIL histórico en `DOC-A00_MISSION_CONTRACT_ASK_COUNCIL.md`. Este último dice `AUTHORIZE` para otra misión; eso no aprueba este borrador. Aquí se propone una capa de revisión del método del ejecutor **sin reemplazar** esos contratos. Para evitar colisiones, sus IDs son `DM-G01..DM-G12` y `DM-C01..DM-C12`. Las recomendaciones de modelos son asesoría; nunca sustituyen la prueba ni el read-back.

## X-Ray forense del trabajo de esta sesión

| Hallazgo observable | Evidencia y límite | Ajuste al método |
|---|---|---|
| Se pidió un plan T-01..T-10 que no aparecía completo en el historial accesible. Se pidió el archivo, se verificó su integridad y luego se consolidó una copia ejecutable; el original quedó preservado. | Conversación de la sesión y commits de consolidación; `PLAN-DSL-DAG-UI.yaml`. Es evidencia de este caso, no garantía de todos los planes futuros. | Congelar fuente, versión y hash; no iniciar ejecución con pasos inferidos. |
| T-05 tenía reglas contradictorias sobre GET y escritura. Se escaló; la decisión B separó evento `RESOURCE_READ` de estado funcional. | [Commit de T-05](https://github.com/maxbry123-commits/router-universal-router-inteligente-/commit/5e2214f60e84fb27f2423f1b63d73cbde5da09e1); pruebas organizativas focalizadas. La persistencia remota sin credencial sigue sin comprobar. | Registrar contradicción, decisión del Director y prueba de no mutación antes de cerrar. |
| La primera prueba visual de T-06 observó overflow móvil y exposición de la clave como valor de un input. Se pausó sin PASS y sin segunda pasada. | `CHECKPOINT.json` y reporte parcial de navegador; no existe aceptación visual final. | Toda ruta con botones, red, storage o secretos exige ensayo real y segunda pasada antes de ofrecer UI. |
| La auditoría de Manus distinguió SQLite/grafo fallback probado de fuente Graphiti/Graphify/FalkorDB/AgentDB descargada y runtime sin verificar; `/chat/send` no llama a `memoria_yaiwes.save`. | `memoria_yaiwes/__init__.py`, `memoria_loader.py`, `router.py` y 8 pruebas de memoria; ninguna demuestra servicios externos vivos. | Matriz por componente: fuente, cableado, health real, operación, read-back, persistencia. |
| La consolidación visual tuvo 38 archivos fuente pero el diff final registró 37 renames 100 % y una copia README con hash idéntico. Se corrigió el checkpoint posterior. | [Commit de consolidación](https://github.com/maxbry123-commits/router-universal-router-inteligente-/commit/1350db458668541a03bf67d7ccc657ab712e68c2) y revisiones 28–29 de Bitácora. | Contrastar el resumen con `git show --summary` y hash; emitir corrección append-only si difiere. |
| Las pruebas focalizadas cerraron 28/28, mientras una suite más amplia había dado 318 aprobadas, 11 fallidas, 6 errores y 1 omitida; el PR actual muestra cero checks CI. | Resultado local y vista del PR; no se compararon los fallos con `main` ni se atribuye causa. | Informar nivel de cobertura y estado CI por separado; no convertir PASS local en PASS global. |
| El checkpoint de recepción sí hace read-back pero solo cuando alguien ejecuta `heartbeat`; el guardia del plan comprueba 100 IDs únicos y SHA-256, **no valida dependencias** en `load_plan()`. | `checkpoint_guard.py` y `PLAN.json` en `AWAITING_UPLOAD`, `started_at: null`. | Validar dependencias y ciclos antes de `VALIDATED`; al trabajo activo añadir recordatorio de 15 minutos, sin prometer daemon autónomo. |
| La Puerta de Evidencia puede marcar `PASS` y G10 «Tests» verdadero con solo comprobar que existe un archivo. | Reproducción local abajo: `puerta.despues` con claim `archivo=README.md`, hechos conocidos y **sin** claim `tests` devolvió `PASS`; `_detalle_goals` deja G10 verdadero por evidencia genérica. | Gate por tipo de claim y prueba obligatoria según riesgo; falta de test requerido = `INCOMPLETE`, jamás PASS. |

El ciclo que sí funcionó fue **leer contrato → inventariar fuente y estado → elegir un delta acotado → implementar → probar → leer de vuelta → registrar GAP → continuar**. Sus fallos en este caso fueron cobertura desigual, cierre prematuro potencial en el verificador y dependencias del plan aún sin comprobación. La revisión adversarial se añade donde cambia la decisión; no exige 12 modelos ni búsquedas repetidas para una tarea pequeña.

## 12 goals del método: pregunta de entrada y comprobación de salida

Cada gate guarda `id`, `pregunta_entrada`, `evidencia_previa`, `comprobacion_salida`, `evidencia_posterior` y `resultado` (`PASS`, `INCOMPLETE`, `CONTRADICTION`, `FAIL` o `NO_APLICA` con motivo). No se permite `PASS` por texto del ejecutor ni por un archivo existente cuando se requiere runtime.

| ID | Goal | Entrada antes de ejecutar | Salida comprobable |
|---|---|---|---|
| DM-G01 | Intención | ¿Qué pide el Director, cuál es el entregable y quién aprueba? | Entregable trazado a la petición; aprobación explícita donde corresponda. |
| DM-G02 | Fuente | ¿Qué archivo/version/hash manda y qué datos faltan? | Original intacto, versión y hash leídos de vuelta; faltantes marcados. |
| DM-G03 | Límites | ¿Qué se prohíbe, qué permisos hay y cuál es el alcance autorizado? | Diff y acciones sin violaciones; excepción autorizada documentada. |
| DM-G04 | Estado | ¿Qué está implementado, descargado, conectado, probado o bloqueado? | Cada afirmación coincide con evidencia actual y conserva estados distintos. |
| DM-G05 | Dependencias | ¿Cuáles son prerrequisitos, IDs y ciclos del DAG? | Dependencias resueltas, IDs únicos, ciclos ausentes; bloqueos quedan en GAP. |
| DM-G06 | Reuso | ¿Qué módulo, contrato, skill o prueba existente evita duplicar? | Se reutilizó o se justificó por evidencia la nueva pieza; interfaz preservada. |
| DM-G07 | Diseño y seguridad | ¿Qué arquitectura, UX, datos y secretos pueden verse afectados? | Contratos, permisos y rutas de secretos revisados sin exposición observada. |
| DM-G08 | Ejecución | ¿Qué delta mínimo y actor lo ejecutarán, con qué criterio de parada? | Código o artefacto producido en la ruta correcta; desvíos y límites registrados. |
| DM-G09 | Prueba | ¿Qué test y entorno real prueban el comportamiento reclamado? | Resultado reproducible, cobertura relevante y errores visibles; sin test requerido = INCOMPLETE. |
| DM-G10 | Integración | ¿Debe funcionar entre procesos, servicios, UI o reinicios? | Llamada/acción real, respuesta y read-back de destino; fuente presente no basta. |
| DM-G11 | Contradicción | ¿Quién puede refutar el resultado y qué evidencia lo derribaría? | Conflictos resueltos o CONTRADICTION; refutación con resultado y corrección. |
| DM-G12 | Entrega y reanudación | ¿Qué debe quedar para que otro agente continúe o el usuario decida? | Commit/diff, Bitácora, STATE, Crazy Wall, CHECKPOINT y HANDOFF coherentes; siguiente paso exacto y límites visibles. |

**Regla de aplicabilidad:** para un informe sin código, DM-G09 pide validación de datos/citas y DM-G10 puede ser `NO_APLICA` motivado; para una UI con backend, ambos requieren evidencia real. El grupo no se autocalifica por mayoría: cualquier fallo crítico de seguridad, contrato o evidencia impide PASS. La matriz no modifica los goals del Director.

## ASK Council: 12 pasos propuestos

Salida de cada paso: `{id, rol, pregunta, evidencia, objecion, recomendacion, estado, accion}`. Estados: `ACEPTAR`, `CONDICIONAR`, `BLOQUEAR`, `NO_APLICA`. El consejo asesora; el Director aprueba el método y el Judge con evidencia decide el cierre de la tarea.

| Paso | Rol de revisión | Pregunta decisiva / artefacto |
|---|---|---|
| DM-C01 | Director / intake | ¿La intención y el entregable coinciden con el texto original? Contrato de misión. |
| DM-C02 | Archivista | ¿Fuente, versión, SHA y autoría están preservados? Inventario de fuentes. |
| DM-C03 | Planificador | ¿Scope, permisos, prohibiciones y parada son inequívocos? Matriz de límites. |
| DM-C04 | Arquitecto | ¿Se respeta el Router, DAG y enchufes existentes? Diagrama de interfaces. |
| DM-C05 | Especialista de reuso | ¿Se revisó lo disponible antes de generar código? Mapa de reuso. |
| DM-C06 | Integrador | ¿Entrada→adapter→runtime→salida→read-back realmente conecta? Traza de integración. |
| DM-C07 | Seguridad/Sentinel | ¿Hay secreto, fuga, permiso o efecto irreversible? Resultado de control. |
| DM-C08 | Ejecutor | ¿El cambio mínimo fue ejecutado sin desvíos? Diff y comandos. |
| DM-C09 | Tester independiente | ¿Fallan los tests o faltan tests obligatorios? Reporte de pruebas. |
| DM-C10 | Revisor adversarial | ¿Qué contradicción o escenario rompe el supuesto principal? Refutaciones. |
| DM-C11 | Sheriff / State Hub | ¿Bitácora, proyecciones, checkpoint y realidad se leen igual? Read-back. |
| DM-C12 | Judge + Director | ¿Cumple la definición de terminado y qué queda para aprobación humana? Veredicto con GAPs; el Director decide cambios de alcance. |

Si el Router dispone de Kimi/GLM/DeepSeek/NVIDIA, sus respuestas pueden alimentar DM-C04, DM-C07 y DM-C10 en paralelo con límites de tiempo y costo, marcadas `ASESORIA`; la decisión final no se delega a un proveedor ni se afirma conectado sin health + llamada + resultado. El Consejo recibe hechos y hashes, no secretos. Si un modelo llega tarde, la tarea no se reescribe retroactivamente: se registra una nueva objeción y se reevalúa antes del cierre.

## Cuatro simulaciones locales (sin modelos externos)

Se ejecutaron en el checkout actual; son pruebas puntuales de decisión, **no** ensayos E2E ni validación de Kimi.

| Simulación | Estímulo | Resultado observado | Decisión de método |
|---|---|---|---|
| S1 — Plan ausente | `load_plan()` con `PLAN.json.status=AWAITING_UPLOAD` y checkpoint en recepción. | Excepción `PLAN_NOT_VALIDATED_100_STEPS`; `started_at=null`. | BLOQUEAR el inicio y esperar archivo original. |
| S2 — Falso PASS documental | `puerta.despues` con un hecho conocido y solo claim de archivo existente `README.md`, sin claim de tests. | `PASS`, G10 `ok=true`, ningún check `tests`. | REFUTADO: el gate actual no puede avalar pruebas de software con ese resultado. |
| S3 — Fuentes en conflicto | Mismo archivo con `pack.conflicts=["fuente A contradice B"]`. | `CONTRADICTION`. | Escalar decisión de fuente; no aceptar por mayoría de modelos. |
| S4 — Prueba fallida | Archivo existente + claim `tests` con comando `false`. | `FAIL`; check de archivo verdadero y de tests falso. | Rechazar cierre pese a presencia del artefacto. |

## Tres refutaciones del método propuesto

1. **«Doce preguntas aseguran PASS».** S2 lo falsifica hoy: G10 puede aparecer aprobado sin ejecutar un test. **Corrección:** reglas de evidencia tipada por riesgo y ausencia de prueba obligatoria = `INCOMPLETE`; test de regresión que reproduzca S2 antes de cambiar el gate. Hasta entonces, no usar ese PASS para aceptar T-06.
2. **«Un checkpoint append-only garantiza recuperación completa».** El guardia escribe log y proyecciones en operaciones separadas; un fallo entre escrituras puede dejar proyección atrasada, y `heartbeat` requiere invocación activa. **Corrección:** recuperación por replay de Bitácora y comprobación de revisión/hash en entrada; evitar declarar atomicidad transversal o un reloj autónomo. El plan de 100 pasos no empieza por una marca temporal en un documento.
3. **«Más agentes y simulaciones validan un runtime».** El código descargado de Graphiti/FalkorDB y respuestas de consejo no prueban conectividad; ni 28 tests locales resuelven el overflow y la clave en DOM de T-06. **Corrección:** elegir el verificador independiente según el riesgo (endpoint real, reinicio, navegador), y exigir read-back; solo paralelizar unidades independientes cuando aporte tiempo sin colisiones.

## Lista concreta para aprobar e incorporar

Estas propuestas están **PENDIENTES DE APROBACIÓN**. No se cambia aún código, reglas de PASS ni fuentes originales. El trabajo sobre el plan nuevo de 100 pasos seguirá su propio protocolo cuando el Director lo suba.

| Prioridad | Cambio propuesto | Destino tras aprobación | Aceptación verificable |
|---|---|---|---|
| P01 | Registrar `DM-G01..12` como anexo del método, sin reemplazar G01..12 de proyecto/Evidence Gate. | `chat router/01-PLAN/` y guía de arquitectura. | Mapeo completo entrada/salida/NO_APLICA y ninguna colisión de IDs. |
| P02 | Formalizar `DM-C01..12` como consejo asesor, con Judge para PASS y Director para cambio de alcance; consejo de modelos solo si está conectado. | `chat router/05-AGENTES/` y contrato de gobierno. | Objeciones, decisión humana y evidencia separadas en una traza. |
| P03 | Impedir PASS del Evidence Gate cuando falta una prueba requerida; cubrir S2 con una regresión y clasificar claims por tipo/riesgo. | `chat router/11-EVIDENCIA/`. | S2 pasa a `INCOMPLETE`; S3 continúa `CONTRADICTION` y S4 `FAIL`. |
| P04 | Validar referencias de dependencia y ciclos antes de marcar `PLAN.json` como `VALIDATED`; mantener fuente original + SHA. | Guardia y tests del plan de 100 pasos. | ID inexistente/ciclo bloquea `start` sin arrancar reloj; plan válido supera read-back. |
| P05 | Separar fuente/adapter/runtime/operación/read-back/reinicio en inventario de memoria. | DSL de memoria, inventario versionado y arquitectura. | Ningún componente descargado figura `CONNECTED` sin prueba de servicio. |
| P06 | Exigir matriz y segunda pasada UI para T-06, incluyendo móvil/tablet/desktop y secreto en DOM antes de READY. | Contrato de aceptación T-06, sin despliegue. | Sin overflow, pruebas de controles/estados/red/storage y evidencias; de lo contrario FAIL/PARTIAL. |
| P07 | Revisar entrada al checkpoint por replay y registrar cadencia real de 15 minutos durante trabajo activo, no mediante promesa de servicio autónomo. | State Hub y handoff. | Revisión monotónica y recuperación probada tras interrupción entre escrituras. |
| P08 | Emitir un cierre de PR que diferencie pruebas locales, suite completa, CI, UI y servicios externos; diff y hashes leídos de vuelta. | Checklist de entrega en guía y handoff. | Nunca PASS global por PASS focalizado ni por mero archivo presente. |

**Decisión solicitada:** aprobar toda la lista P01–P08, aprobar solo IDs indicados, o devolver cambios. Tras aprobación, implementar en el PR existente con pruebas y State Hub; revisar los archivos nuevos del Director por separado, preservando sus originales y sin arrancar el reloj antes de validar los 100 pasos.
