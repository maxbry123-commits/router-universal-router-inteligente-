# Arquitectura router inteligente universal

Repositorio: `maxbry123-commits/router-universal-router-inteligente-`
Rama: `main`
Contrato operativo: `tel.workflow/v3`
Modo: `FAIL_CLOSED_LOOP`

## Alcance autorizado — 3 pasos
1. Integrar componentes open source disponibles en la raíz del Router y auditar LLM/Hugging Face para adapters/FastAPI por modelo confirmado.
2. Cablear, podar duplicación y escribir solo código faltante; capa/filtro LLM únicamente cuando exista contrato definido/recuperado.
3. Ejecutar tests reales Hugging Face + GitHub + API + agentes.

## Raíz activa de código
Todo código integrado vive bajo `router inteligente universal/`.
Biblioteca donor/open source: `router inteligente universal/Componente open soure router inteligente universal/`.

## Núcleo de conexión
`Enchufe Gate -> EnchufeV2(Pydantic) -> validator_v2 -> RedUniversal -> connector_registry -> adapters/conectores -> destinos`
DAGs/modelos no pueden alterar este ownership. Componentes externos son donor/adapter/plugin, nunca segundo orquestador.

## Separación vigente
- `red/enchufe_gate.py`: Gate C15 compatible v1.5→v2.0.
- `domain/schemas/enchufe_v2.py`: C05 Pydantic v2 materializado desde JSON Schema FABLES.
- `enchufe/validator_v2.py`: contrato v2 recuperado desde FABLES Enchufe Universal v2.
- `red/red_universal.py`: R-003 recuperado por REUSE desde fuente canónica; propietario único del mapa/rutas/failover/broadcast/espejo/salud de la red.
- `red/conectores.py`: HTTP/MCP/GitHub/HuggingFace/DB/VPS/Memoria/Interno/Webhook preservados; integración solo con registry + test.
- `red/conector_gitlab.py`: adapter GitLab v6 separado.
- `red/conector_mcp_app.py`: extensión mínima de `ConectorMCP`; fail-closed.
- `red/connector_registry.py`: registro explícito fail-closed de conectores verificados.
- `tests/`: tests contractuales separados.
- `integration/huggingface/`: auditoría/bridge HF y evidencia; prohibido inventar `model_id`.
- Capa/filtro LLM: **NO materializada** mientras `GAP-BEHAVIOR-CONTRACT-001` permanezca abierto.
- C19/R-004 backup: **NO integrado** mientras `GAP-R004-SOURCE-001` permanezca abierto; una clasificación `EXISTING_COMPLETE` sin blob/source/ownership no autoriza REUSE ni GENERATE.

## Reglas
- `REUSE > PATCH > ADAPT > GENERATE`.
- Prohibido monolito.
- Secretos solo por entorno/Vault.
- Archivo presente != integrado.
- Declaración documental != source/ownership demostrado.
- PASS exige ruta + SHA/diff + read-back + test/log + URL cuando aplique.
- `GAP-HF-CATALOG-001` permanece no bloqueante hasta disponer de evidencia real de privados/endpoints HF.
- Filtro LLM únicamente con policy explícita definida/recuperada.

## C15 Enchufe Gate v1.5→v2.0 — PATCH verificado
Fuentes contractuales: Gate v1.5 blob `692daca7ace7ac983aeb585dd05ac281e571f2f3`; Enchufe Universal v2 blob `1f2de5b0578391164e6f6f7331507299130e8579`.
PATCH producción: `router inteligente universal/red/enchufe_gate.py`, commit `4e256e1332d41f9177e0df4806bb749cbd1f1e54`, blob `b5fdc15a4b4c3747425d7db86a81f2c4e409de9e`.
Verificación remota: HF Job `6aa16ff732d5d0c22c5b0912`, fijado al commit `8536808a...`, `5 passed in 0.09s`.

## GAP-BEHAVIOR-CONTRACT-001
No existe evidencia de policy standalone allow/deny del comportamiento LLM. El GAP permanece fail-closed; no se deriva policy de schemas, validator, perfiles ni vendors.

## GAP-R004-SOURCE-001
El Handoff identifica `R-004 infrastructure/backup/respaldo.py` como existente completo, pero el árbol activo no contiene esa ruta. La API de commits devuelve historial vacío tanto para la ruta bajo `router inteligente universal/` como root-relative. Auditoría materialmente distinta de ramas `download/router-missing-07`, `forensic-router-50-recovery` e `import/maxbry-router-code` tampoco encontró `respaldo`. Decisión arquitectónica: no generar ni copiar un sustituto hasta recuperar source canónico + ownership; después deberá hacerse REUSE exacto + read-back/blob + test.

## Último delta LOOP
P02 ejecutó exclusivamente la auditoría R-004. Council12 + 3 refutaciones + cross-check + CODA + verify_final validan la decisión fail-closed: la auditoría queda cerrada, C19 no. Progreso se mantiene 93%; Paso 2 ACTIVE; Paso 3 PENDING.
