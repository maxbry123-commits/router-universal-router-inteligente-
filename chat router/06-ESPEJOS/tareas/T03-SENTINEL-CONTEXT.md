# T03 — CONTEXTO DEL SENTINELA

OBJETIVO: OmniRoute estable v3.8.50 con Node soportado por upstream, better-sqlite3, supervisor con backoff, retención DB y auditoría externa
ALCANCE: chat router/08-OMNIROUTE
ARCHIVOS OBLIGATORIOS:
- start_omniroute.sh
- supervisor_omniroute.py
- mantenimiento_db.py
- tests/test_supervisor.py
- DIAGNOSTICO.md
- README.md

ACEPTACIÓN: python -m pytest 'chat router/08-OMNIROUTE' -q && bash -n 'chat router/08-OMNIROUTE/start_omniroute.sh' && grep -q 'VALIDACIÓN EXTERNA DE CIERRE' 'chat router/08-OMNIROUTE/DIAGNOSTICO.md' && grep -q 'NODE_VERSION_VERIFICADA' 'chat router/08-OMNIROUTE/DIAGNOSTICO.md' && grep -q 'OMNIROUTE_REF_VERIFICADA' 'chat router/08-OMNIROUTE/DIAGNOSTICO.md' && grep -q 'BETTER_SQLITE3_VERIFICADO' 'chat router/08-OMNIROUTE/DIAGNOSTICO.md' && grep -q 'HEALTH_ENDPOINT_VERIFICADO' 'chat router/08-OMNIROUTE/DIAGNOSTICO.md' && grep -q 'VEREDICTO_FINAL: PASS' 'chat router/08-OMNIROUTE/DIAGNOSTICO.md' && test $(grep -Ec 'https?://' 'chat router/08-OMNIROUTE/DIAGNOSTICO.md') -ge 3

EVIDENCIA ACTUAL:
- causa: STALE_REPORT
- faltan: []
- pytest/acceptance exit: 0
- scope_escape: False
- objective_drift: False

REGLAS:
- No regenerar archivos que ya pasen.
- No escribir fuera del ALCANCE.
- Si falta conocimiento, investigar antes de inventar.
- Corregir solo la causa demostrada y volver a ejecutar aceptación.

FUENTES ENCONTRADAS:
- Repositorio oficial/upstream: diegosouzapw/OmniRoute https://github.com/diegosouzapw/OmniRoute

ANÁLISIS DEL INVESTIGADOR:
CAUSA_RAIZ: Veredicto STALE_REPORT indica que el informe/artefacto de evidencia no corresponde al estado actual del repo (hash/timestamp desactualizado), no un fallo funcional: pytest_exit=0 y 9/9 passed confirman que OmniRoute v3.8.50 con Node soportado, better-sqlite3, supervisor con backoff y retención DB funcionan.

EVIDENCIA: Salida literal "9 passed in 2.06s", pytest_exit=0, faltan=[]; upstream diegosouzapw/OmniRoute confirma compatibilidad de versiones declaradas.

GAPS: (1) No hay evidencia de auditoría externa ejecutada (solo tests internos). (2) Falta artefacto que vincule commit-hash con el reporte (causa del STALE). (3) Sin verificación de backoff del supervisor bajo fallo real ni de retención DB con datos envejecidos. (4) Protocolo no define cómo refrescar el reporte tras cambios.

NO_REGENERAR: No regenerar código de OmniRoute, ni configuración de better-sqlite3/supervisor/retención; los tests pasan, tocarlos introduce riesgo innecesario.

REPARAR: Regenerar únicamente el reporte de evidencia con hash del commit actual, timestamp y salida pytest fresca; adjuntar resultado de auditoría externa (o ejecutarla) y pruebas de backoff/retención como evidencia complementaria.

ACEPTACION: Reporte con commit-hash coincidente con HEAD, pytest_exit=0, auditoría externa documentada y evidencia de backoff + retención → veredicto PASS.
