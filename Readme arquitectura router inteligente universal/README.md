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
- `red/red_universal.py`: R-003 REUSE; propietario único del mapa/rutas/failover/broadcast/espejo/salud.
- `red/conectores.py`: conectores base preservados; integración solo con registry + test.
- `red/connector_registry.py`: registro explícito fail-closed de conectores verificados.
- `tests/`: tests contractuales separados.
- `integration/huggingface/`: auditoría/bridge HF; prohibido inventar `model_id`.
- `integration/audits/C03-CONFIG-DONOR-AUDIT.md`: donor `pydantic-settings` = ADAPT_CANDIDATE, no integración.
- `integration/audits/R004-PDF-EXTRACTION-AUDIT.md`: R-004 identidad/origen demostrados, fuente Python exacta bloqueada.
- `integration/audits/C01-FASTAPI-DONOR-AUDIT.md`: donor FastAPI auditado; `ADAPT_CANDIDATE`, no integración.
- Capa/filtro LLM: **NO materializada** mientras `GAP-BEHAVIOR-CONTRACT-001` permanezca abierto.
- C19/R-004 backup: **NO integrado** mientras `GAP-R004-EXTRACTION-001` permanezca abierto.
- C03 Config: **NO integrado** mientras `GAP-C03-CONTRACT-001` permanezca abierto.
- C01 API Gateway: **NO integrado** mientras `GAP-C01-API-CONTRACT-001` permanezca abierto.

## Reglas
- `REUSE > PATCH > ADAPT > GENERATE`.
- Prohibido monolito.
- Secretos solo por entorno/Vault.
- Archivo presente != integrado.
- Declaración documental != source/ownership demostrado.
- Donor capaz != contrato específico del Router.
- PASS exige ruta + SHA/diff + read-back + test/log + URL cuando aplique.
- Filtro LLM únicamente con policy explícita definida/recuperada.

## C15 Enchufe Gate v1.5→v2.0 — PATCH verificado
Fuentes contractuales: Gate v1.5 blob `692daca7ace7ac983aeb585dd05ac281e571f2f3`; Enchufe Universal v2 blob `1f2de5b0578391164e6f6f7331507299130e8579`.
PATCH producción: `router inteligente universal/red/enchufe_gate.py`, commit `4e256e1332d41f9177e0df4806bb749cbd1f1e54`, blob `b5fdc15a4b4c3747425d7db86a81f2c4e409de9e`.
Verificación remota: HF Job `6aa16ff732d5d0c22c5b0912`, `5 passed in 0.09s`.

## GAPs activos
- `GAP-HF-CATALOG-001`: privados/endpoints sin `model_id` confirmado.
- `GAP-BEHAVIOR-CONTRACT-001`: no existe policy standalone allow/deny recuperada.
- `GAP-R004-EXTRACTION-001`: PDF exacto demostrado, código Python exacto no materializado.
- `GAP-C03-CONTRACT-001`: donor settings válido, campos/env/defaults/perfiles del Router no recuperados.
- `GAP-C01-API-CONTRACT-001`: FastAPI donor válido, pero faltan rutas/métodos/schemas/auth/error envelope/WS-SSE para Paneles 1–5.

## C01 FastAPI donor — AUDIT verificado
Donor local: `router inteligente universal/Componente open soure router inteligente universal/fastapi/`.
`pyproject.toml` blob `06c82344a7010eefaf98f567468dea8be5a5ae10`; `LICENSE` blob `3e92463e6bd522a2a21e5f0a80d8089d6c4be20d`; upstream declarado `https://github.com/fastapi/fastapi`; MIT; Python `>=3.10`; Pydantic v2 + Starlette.
Auditoría: `router inteligente universal/integration/audits/C01-FASTAPI-DONOR-AUDIT.md`, commit `c8d297ed1046445c74190d6ba51bc1a39307462d`.
Decisión: `ADAPT_CANDIDATE`, no integrar hasta recuperar contrato API del Router.

## Último delta LOOP
RIU-0025 auditó únicamente C01/FastAPI. Council12 + 3 refutaciones + cross-check + CODA + `verify_final=PASS_AUDIT_ONLY`; no se escribió producción ni se adelantó Paso 3. Progreso se mantiene 93%; Paso 2 ACTIVE; Paso 3 PENDING.
