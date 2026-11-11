# Simulaciones del prototipo YAIWES Cognitive OS v0.1

**Modo: SIMULATED_ONLY**. La evaluación de 16 estrategias ocurre en paralelo y produce una recomendación. Los 'modelos' en estas simulaciones son `MockDecider` + `MockCouncil(3)` y NO son pesos reales. Los steps agregan hechos simulados con la etiqueta `SIMULATED_EXECUTION`; no hay acceso a internet, GitHub ni Hugging Face.

El runner realiza 10 ciclos completos independientes desde un estado vacío con destino autorizado en fixture y 10 variaciones con etapas precargadas/bloqueos. Cada uno de los 12 procesos se repite **al menos diez veces**. El objetivo fue probar rutas, restricciones, determinismo y estados terminales, no medir exactitud de modelos científicos.

Flujo completo simulado:

```text
DISCOVER → VERIFY → { XRAY || LICENSE } → { COMPARE || DOCUMENT }
 → PLAN → RESOLVE → BUILD → TEST → COUNCIL → PROMOTE → COMPLETE
```

La notación `||` aquí expresa **alternativas independientes listas en el grafo**; la versión ejecuta una acción por turno, pero decide evaluando simultáneamente los posibles pasos. Las estrategias corren en paralelo; el executor real aún no.

## ¿Qué hace cada uno de los 12 procesos?

- DISCOVER: candidato encontrado.
- VERIFY: fuente verificable.
- XRAY: estructura de código auditada.
- LICENSE: licencia sin bloqueos.
- COMPARE: novelty/diferencias frente al registry.
- DOCUMENT: guía de uso y errores.
- PLAN: plan de absorción.
- RESOLVE: dependencias identificadas.
- BUILD: capsule compilada.
- TEST: pruebas con resultado estructurado.
- COUNCIL: gate revisa 12 goals, roles opcionales.
- PROMOTE: publicación solo con autorización de destino.

## Conclusión condicionada

En la simulación sintética, completar un objetivo no depende de la LLM: depende de precondiciones que puede comprobar el kernel. En el mundo real, **el éxito exige adaptadores de observación y ejecución que produzcan evidencia auténtica**. Los 16 mecanismos son exploradores/estimadores de alternativas; el state machine, los constraints, la auditoría y la prueba controlan la publicación.
