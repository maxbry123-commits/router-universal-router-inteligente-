# T07 — CONTEXTO COMPACTO DE EJECUCIÓN

OBJETIVO:
Implementar YAIWES Evidence/Search Gate como capa determinista que investiga
ANTES del ejecutor y vuelve a verificar DESPUÉS. La misma IA que ejecuta no
puede cerrar su propio trabajo por opinión.

ALCANCE ÚNICO:
chat router/11-EVIDENCIA

ARCHIVOS:
- parser.py
- goals.py
- compilador_busquedas.py
- buscadores.py
- extractor.py
- ranking.py
- evidence_pack.py
- verificador.py
- puerta.py
- tests/__init__.py
- tests/test_puerta.py
- README.md

## Fuente literal verificada
Documento 26:
chat router/00-INSTRUCCIONES/INPUT-BLOCK-VERBATIM-PARTE-5-C-DOCS-24-26-M40.md

## Microflujo obligatorio

INPUT
→ PARSER DETERMINISTA
→ 12 GOALS ENTRADA
→ QUERY COMPILER
→ SEARCH FANOUT
→ EXTRACT + RANK
→ EVIDENCE PACK
→ [LLM FILTER opcional]
→ EXECUTOR
→ OUTPUT CLAIMS
→ VERIFY SEARCH
→ 12 GOALS SALIDA
→ SHERIFF
  ├─ PASS → FINAL
  ├─ INCOMPLETE/NEED_EVIDENCE → BUSCAR MÁS
  ├─ CONTRADICTION/FIXABLE → CORREGIR
  └─ FAIL → REEJECUTAR/REPLAN

## 12 Goals exactos del Director

G01 Objetivo
- entrada: ¿Qué pidió exactamente?
- salida: ¿Se consiguió exactamente?

G02 Entidades
- entrada: ¿Qué proyecto/version/ruta?
- salida: ¿Se trabajó sobre esas mismas?

G03 Restricciones
- entrada: ¿Qué está prohibido?
- salida: ¿Se respetó todo?

G04 Dependencias
- entrada: ¿Qué necesita funcionar?
- salida: ¿Funcionan realmente?

G05 Fuente oficial
- entrada: ¿Existe documentación oficial?
- salida: ¿Resultado coincide con ella?

G06 Versión
- entrada: ¿Cuál es la versión vigente?
- salida: ¿Se usó la correcta?

G07 Configuración
- entrada: ¿Qué configuración necesita?
- salida: ¿Está configurada así?

G08 Integración
- entrada: ¿Con qué debe conectarse?
- salida: ¿Está realmente conectado?

G09 Ejecución
- entrada: ¿Qué debe ejecutar?
- salida: ¿Se ejecutó?

G10 Tests
- entrada: ¿Cómo demostramos PASS?
- salida: ¿Pasaron las pruebas?

G11 Contradicciones
- entrada: ¿Las fuentes discrepan?
- salida: ¿Aparecieron contradicciones?

G12 Evidencia
- entrada: ¿Tenemos evidencia suficiente?
- salida: ¿Podemos demostrar el cierre?

## Parser sin LLM
task_type permitidos:
SEARCH, INSTALL, DOWNLOAD, EXTRACT, DEPLOY, MODIFY_CODE, DEBUG, TEST,
COMPARE, AUDIT, RESEARCH, VERIFY.

Salida:
task_type, targets, requirements, constraints, forbidden, verification.

## Query compiler sin LLM
Usar plantillas deterministas por task_type y por goal.
Ejemplo G06:
- "{component}" latest release
- site:github.com "{component}" releases
- "{component}" changelog

## Search fan-out
- GitHub Search API
- documentación por URL/urllib
- búsqueda local del repo
- SIMULADO=1 sin red

Normalizar:
query, source, url, title, date, snippet, source_type, retrieved_at.

## Extractor sin LLM
HTML/Markdown
→ títulos/párrafos/code blocks
→ términos coincidentes
→ ventanas de contexto
→ fragmentos exactos.

## Ranking sin LLM
SCORE:
exact_match
+ BM25
+ source_authority
+ recency
+ identifier_match
+ corroboration
- duplication
- stale_penalty

Fusionar motores con Reciprocal Rank Fusion (RRF).

## Evidence Pack
Campos mínimos:
task, known_facts, requirements, constraints, conflicts, unknown, sources.
Tope aproximado 2K–8K tokens.

## Verificación posterior
resultado → claims/actions → comprobaciones:
- archivos
- versión
- HTTP
- tests
- logs/trace
- restricciones/prohibiciones

## Veredictos
PASS
INCOMPLETE
CONTRADICTION
FAIL

## Fuentes técnicas de referencia para investigar, NO para copiar ciegamente
- CRAG: https://github.com/HuskyInSalt/CRAG
- RARR: https://github.com/anthonywchen/RARR
- SAFE: https://github.com/google-deepmind/long-form-factuality
- RAGChecker: https://github.com/amazon-science/RAGChecker

Estas fuentes sirven para contrastar patrones de recuperación/verificación.
La arquitectura de T07 sigue siendo la definida por Documento 26.

## Orden de implementación
1. tests/test_puerta.py primero.
2. goals.py + parser.py.
3. compilador_busquedas.py + buscadores.py.
4. extractor.py + ranking.py.
5. evidence_pack.py.
6. verificador.py + puerta.py.
7. README.md.
8. Ejecutar aceptación una vez.
9. Corregir solo traceback real.

## Casos de prueba mínimos
- PASS completo.
- INCOMPLETE por evidencia insuficiente.
- CONTRADICTION por fuentes/claims incompatibles.
- FAIL por restricción violada o evidencia de ejecución fallida.
- SIMULADO=1 no hace red.
- G01..G12 presentes.
- RRF/BM25 deterministas.
- la verificación posterior no confía en la afirmación del ejecutor.

## Reglas
- cero red en tests
- stdlib para BM25; no añadir dependencia innecesaria
- no LLM obligatoria para parser/query/extractor/ranking/gates
- no escribir fuera del ALCANCE
- no duplicar "chat router/"
- no copiar README de otra tarea
- máximo 500 líneas/archivo
- PASS solo con aceptación real exit 0 + checks independientes
