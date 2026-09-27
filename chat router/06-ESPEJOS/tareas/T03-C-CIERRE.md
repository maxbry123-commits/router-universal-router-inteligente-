# T03-C — Auditoría externa + cierre

OBJETIVO: decidir PASS/REVISE de OmniRoute usando evidencia real, no solo pytest.

FUENTES MÍNIMAS:
1. release/tag v3.8.50 y package.json upstream;
2. issue #9576 Node 24/26;
3. issue #9613 better-sqlite3/npm;
4. docs/código exacto para health endpoint y variables runtime;
5. SQLite oficial para mmap cuando aplique.

DIAGNOSTICO.md debe contener:
## VALIDACIÓN EXTERNA DE CIERRE — 2026-09-27

Tabla:
PUNTO | FUENTE/URL | EVIDENCIA | NUESTRA CONFIG | VEREDICTO

Campos finales:
NODE_VERSION_VERIFICADA
OMNIROUTE_REF_VERIFICADA
BETTER_SQLITE3_VERIFICADO
HEALTH_ENDPOINT_VERIFICADO
ENV_VARS_VERIFICADAS
START_COMMAND_VERIFICADO
ISSUES_ABIERTOS_RELEVANTES
RIESGO_RESIDUAL
CAMBIOS_NECESARIOS
VEREDICTO_FINAL: PASS | REVISE

GATE:
python -m pytest "chat router/08-OMNIROUTE" -q
bash -n "chat router/08-OMNIROUTE/start_omniroute.sh"
URLs reales >= 3
VEREDICTO_FINAL: PASS

IMPORTANTE:
"9 passed" + exit global 1 NO significa tests rotos si el fallo pertenece al
gate documental. Clasificar el subgate exacto que falla.
