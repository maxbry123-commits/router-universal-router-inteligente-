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
- `integration/audits/C03-CONFIG-DONOR-AUDIT.md`: provenance C03; donor `pydantic-settings` válido como ADAPT_CANDIDATE, no integración.
- Capa/filtro LLM: **NO materializada** mientras `GAP-BEHAVIOR-CONTRACT-001` permanezca abierto.
- C19/R-004 backup: **NO integrado** mientras `GAP-R004-SOURCE-001` permanezca abierto.
- C03 Config: **NO integrado** mientras `GAP-C03-CONTRACT-001` permanezca abierto; donor capaz no autoriza inventar campos/env.

## Reglas
- `REUSE > PATCH > ADAPT > GENERATE`.
- Prohibido monolito.
- Secretos solo por entorno/Vault.
- Archivo presente != integrado.
- Declaración documental != source/ownership demostrado.
- Donor capaz != contrato específico del Router.
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
El Handoff identifica `R-004 infrastructure/backup/respaldo.py` como existente completo, pero source/ownership físico no fue recuperado. No generar ni copiar sustituto hasta recuperar fuente canónica.

## GAP-C03-CONTRACT-001
C03 exige configuración inmutable y env como única fuente. El donor físico `pydantic-settings` está disponible, declara MIT y soporte Pydantic v2 (`README` blob `84c893ab07d3282555622f69cee358686ba4ea99`; `pyproject` blob `21c3e4780e6da923cccf8435498930f4d9e1bece`; upstream `https://github.com/pydantic/pydantic-settings`). Sin embargo no se han recuperado nombres de variables/campos, requeridos, defaults ni perfiles propios del Router. Estado: `ADAPT_CANDIDATE`, no integrado; no inventar `settings.py`.

## Último delta LOOP
P02 ejecutó exclusivamente la auditoría/provenance C03 y la persistió en commit `fa787fe101858ecd2ddf02e1f9ff25238a2148ef`. Council12 + 3 refutaciones + cross-check + CODA + verify_final validan el cierre de auditoría, no de C03. Progreso se mantiene 93%; Paso 2 ACTIVE; Paso 3 PENDING.
