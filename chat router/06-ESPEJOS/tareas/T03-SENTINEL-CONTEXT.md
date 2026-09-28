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
- pytest/acceptance exit: 1
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
sin respuesta del modelo; usar evidencia determinista
