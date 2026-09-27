# T07 — CONTEXTO DEL SENTINELA

OBJETIVO: Puerta de evidencia con los 12 goals (doc 26)
ALCANCE: chat router/11-EVIDENCIA
ARCHIVOS OBLIGATORIOS:
- parser.py
- goals.py
- compilador_busquedas.py
- buscadores.py
- extractor.py
- ranking.py
- evidence_pack.py
- verificador.py
- puerta.py
- tests/test_puerta.py
- README.md

ACEPTACIÓN: SIMULADO=1 python -m pytest 'chat router/11-EVIDENCIA' -q

EVIDENCIA ACTUAL:
- causa: NO_ENTREGADO
- faltan: ['parser.py', 'goals.py', 'compilador_busquedas.py', 'buscadores.py', 'extractor.py', 'ranking.py', 'evidence_pack.py', 'verificador.py', 'puerta.py', 'tests/test_puerta.py', 'README.md']
- pytest/acceptance exit: 4
- scope_escape: False
- objective_drift: False

REGLAS:
- No regenerar archivos que ya pasen.
- No escribir fuera del ALCANCE.
- Si falta conocimiento, investigar antes de inventar.
- Corregir solo la causa demostrada y volver a ejecutar aceptación.

CHEQUEOS INDEPENDIENTES DEL OBJETIVO:
- for g in G01 G02 G03 G04 G05 G06 G07 G08 G09 G10 G11 G12; do grep -q "$g" 'chat router/11-EVIDENCIA/goals.py' || exit 1; done
- grep -Eq 'SEARCH.*INSTALL.*DOWNLOAD.*EXTRACT.*DEPLOY|SEARCH' 'chat router/11-EVIDENCIA/parser.py'
- grep -q 'BM25' 'chat router/11-EVIDENCIA/ranking.py'
- grep -Eq 'RRF|Reciprocal' 'chat router/11-EVIDENCIA/ranking.py'
- grep -q 'known_facts' 'chat router/11-EVIDENCIA/evidence_pack.py'
- grep -q 'conflicts' 'chat router/11-EVIDENCIA/evidence_pack.py'
- grep -q 'unknown' 'chat router/11-EVIDENCIA/evidence_pack.py'
- grep -q 'PASS' 'chat router/11-EVIDENCIA/puerta.py'
- grep -q 'INCOMPLETE' 'chat router/11-EVIDENCIA/puerta.py'
- grep -q 'CONTRADICTION' 'chat router/11-EVIDENCIA/puerta.py'
- grep -q 'FAIL' 'chat router/11-EVIDENCIA/puerta.py'
- grep -q 'SIMULADO' 'chat router/11-EVIDENCIA/buscadores.py'

FUENTES ENCONTRADAS:
- Repositorio oficial/upstream: HuskyInSalt/CRAG https://github.com/HuskyInSalt/CRAG
- Repositorio oficial/upstream: anthonywchen/RARR https://github.com/anthonywchen/RARR
- Repositorio oficial/upstream: google-deepmind/long-form-factuality https://github.com/google-deepmind/long-form-factuality
- Repositorio oficial/upstream: amazon-science/RAGChecker https://github.com/amazon-science/RAGChecker
- Repositorio oficial/upstream: pytest-dev/pytest https://github.com/pytest-dev/pytest
- GitHub:HuskyInSalt/CRAG: considering running CRAG on Mac M1 series computers? https://github.com/HuskyInSalt/CRAG/issues/12
- GitHub:google-deepmind/long-form-factuality: nvidia-cublas-cu12 requirement is not satisfied https://github.com/google-deepmind/long-form-factuality/issues/12
- GitHub:amazon-science/RAGChecker: ValueError: axes don't match array https://github.com/amazon-science/RAGChecker/issues/12
- GitHub:pytest-dev/pytest: list test dependencies better https://github.com/pytest-dev/pytest/issues/12

ANÁLISIS DEL INVESTIGADOR:
CAUSA_RAIZ: El ejecutor nunca creó los 11 archivos requeridos (NO_ENTREGADO); pytest falla con exit 4 porque la ruta "chat router/11-EVIDENCIA" no existe — probablemente el workspace no fue inicializado o la ruta con espacio no se resolvió/creó.

EVIDENCIA: pytest_exit=4 + "file or directory not found: chat router/11-EVIDENCIA" confirma ausencia total de artefactos, no fallo de tests. La evidencia comunidad (CRAG, RARR, long-form-factuality, RAGChecker) es solo referencial para diseño de verificación RAG; no aporta código entregable. Issue pytest#12 refuerza declarar dependencias de test explícitas.

GAPS: (1) No se conoce el contenido del doc 26 con los 12 goals — sin él no se puede implementar goals.py ni la puerta. (2) Protocolo de rutas: ¿el workspace es "chat router/11-EVIDENCIA" literal con espacio? Requiere quoting o normalización. (3) Sin criterios de aceptación por goal (umbrales, fixtures de evidencia).

NO_REGENERAR: No rebuscar evidencia comunidad ni reintentar pytest hasta que existan los archivos; no modificar la ruta del workspace sin confirmar convención.

REPARAR: 1) Crear directorio "chat router/11-EVIDENCIA" (con quoting). 2) Materializar los 11 archivos: parser.py, goals.py (12 goals del doc 26), compilador_busquedas.py, buscadores.py, extractor.py, ranking.py, evidence_pack.py, verificador.py, puerta.py, tests/test_puerta.py, README.md. 3) Declarar deps de test (pytest) en README/requirements. 4) Ejecutar pytest con ruta entrecomillada.

ACEPTACION: Los 11 archivos existen en la ruta; `pytest "chat router/11-EVIDENCIA"` exit=0 con tests de puerta verdes cubriendo los 12 goals; veredicto pasa de NO_ENTREGADO a evaluable.
