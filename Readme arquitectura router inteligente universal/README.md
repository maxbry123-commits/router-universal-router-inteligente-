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
- `domain/schemas/enchufe_v2.py`: C05 Pydantic v2.
- `enchufe/validator_v2.py`: contrato v2 recuperado.
- `red/red_universal.py`: propietario único de mapa/rutas/failover/broadcast/espejo/salud.
- `red/conectores.py` + `red/connector_registry.py`: conectores y registro fail-closed.
- `engine/resilience.py`: C10 aislado, sin ownership de routing.
- `tests/`: tests contractuales separados.
- `integration/huggingface/`: bridge/auditorías HF; prohibido inventar `model_id`.
- `integration/audits/`: decisiones REUSE/PATCH/ADAPT/GENERATE y GAPs por componente.

## Hugging Face Jobs — RIU-0030 VERIFIED COMPUTE
La arquitectura admite Jobs como cómputo real externo del proyecto sin convertirlo en segundo orquestador: `Router/GitHub source -> HF Job compute -> resultado/evidencia -> GitHub/state`. Documentación oficial consultada: https://huggingface.co/docs/hub/en/jobs y https://huggingface.co/docs/hub/en/jobs-configuration . `cpu-upgrade` corresponde a 8 vCPU/32 GB.

Job real: `6aa1c5fd21047bf1b0370d4d`, flavor `cpu-upgrade`, resultado `success`, clonando y auditando el repo Router dentro de Hugging Face Jobs. Auditoría: `router inteligente universal/integration/huggingface/RIU-0030-HF-JOBS-COMPUTE-AUDIT.md`, commit `0acb4f31a0ff784bae7037b62bac36074e15850f`.

Este PASS demuestra capacidad de cómputo real, no catálogo LLM privado, no model_id, no FastAPI por modelo y no E2E Paso 3.

## Reglas
- `REUSE > PATCH > ADAPT > GENERATE`.
- Prohibido monolito.
- Secretos solo por entorno/Vault.
- Archivo presente != integrado.
- Donor capaz != contrato específico del Router.
- HF Job success != model catalog ni E2E.
- PASS exige ruta + SHA/diff + read-back + test/log + URL cuando aplique.
- Filtro LLM únicamente con policy explícita definida/recuperada.
- `tel.workflow/v3` es el contrato vigente de este LOOP.

## C10 Resilience — verificado
Producción `router inteligente universal/engine/resilience.py`, commit `6b408a781d886a8bde43c3f62b48247d872afd36`; test `a0e74c04c93dfc2cc0c96da9c31234d98b44333c`; HF Job `6aa1ae8221047bf1b03707ff` = `5 passed in 0.10s`.

## C11/C12/C13
C11 Semantic Cache, C12 Cost Optimizer y C13 CodeSandbox dual siguen `ADAPT_CANDIDATE/AUDIT_ONLY` hasta recuperar sus contratos Router-owned exactos.

## GAPs activos
- `GAP-HF-CATALOG-001`: privados/endpoints sin `model_id` confirmado.
- `GAP-BEHAVIOR-CONTRACT-001`: no existe policy standalone allow/deny recuperada.
- `GAP-R004-EXTRACTION-001`.
- `GAP-C03-CONTRACT-001`.
- `GAP-C01-API-CONTRACT-001`.
- `GAP-C11-SEMANTIC-CACHE-CONTRACT-001`.
- `GAP-C12-COST-POLICY-CONTRACT-001`.
- `GAP-C13-SANDBOX-CONTRACT-001`.

## Último delta LOOP
RIU-0030 verificó Hugging Face Jobs como cómputo real del Router con `cpu-upgrade`; Council12 + 3 refutaciones + cross-check + CODA + `verify_final=PASS_HF_JOBS_COMPUTE_REAL_NO_CATALOG_CLAIM`. Progreso 96%; Paso 2 ACTIVE; Paso 3 PENDING.
