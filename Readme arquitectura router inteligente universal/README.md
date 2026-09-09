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
- `integration/huggingface/`: auditoría/bridge HF; prohibido inventar `model_id`.
- `integration/audits/`: decisiones REUSE/PATCH/ADAPT/GENERATE y GAPs por componente.

## Reglas
- `REUSE > PATCH > ADAPT > GENERATE`.
- Prohibido monolito.
- Secretos solo por entorno/Vault.
- Archivo presente != integrado.
- Declaración documental != source/ownership demostrado.
- Donor capaz != contrato específico del Router.
- PASS exige ruta + SHA/diff + read-back + test/log + URL cuando aplique.
- Filtro LLM únicamente con policy explícita definida/recuperada.
- `tel.workflow/v3` es el contrato vigente de este LOOP.

## C10 Resilience — verificado
Producción `router inteligente universal/engine/resilience.py`, commit `6b408a781d886a8bde43c3f62b48247d872afd36`; test `a0e74c04c93dfc2cc0c96da9c31234d98b44333c`; HF Job `6aa1ae8221047bf1b03707ff` = `5 passed in 0.10s`.

## C11 Semantic Cache — RIU-0027 AUDIT_ONLY
Donor Redis/vector disponible; decisión `ADAPT_CANDIDATE / AUDIT_ONLY`. No producir C11 hasta recuperar contrato exacto de cache-key, embedding/model version, metric/threshold, TTL/invalidation, namespace/privacy, serialization, fallback/stale policy y boundary Enchufe.

## C12 Cost Optimizer — RIU-0028 AUDIT_ONLY
Handoff define C12 como `MISSING`, `GENERATE; presupuesto/policy`. Donor local `router inteligente universal/Componente open soure router inteligente universal/litellm/`; `pyproject.toml` identifica `litellm` 1.100.0, licencia MIT y upstream `https://github.com/BerriAI/litellm`.

Auditoría: `router inteligente universal/integration/audits/C12-COST-OPTIMIZER-DONOR-AUDIT.md`, commit `d34b0ff83e81537d0d1da9ad26db327a0ea552d8`.

Decisión: `ADAPT_CANDIDATE / AUDIT_ONLY`. No producir C12 hasta recuperar scopes de presupuesto, hard/soft limits, accounting interval, currency normalization, price-source authority, fallback/rollover, ownership agente/tarea y boundary Enchufe exacto.

## GAPs activos
- `GAP-HF-CATALOG-001`: privados/endpoints sin `model_id` confirmado.
- `GAP-BEHAVIOR-CONTRACT-001`: no existe policy standalone allow/deny recuperada.
- `GAP-R004-EXTRACTION-001`: PDF exacto demostrado, código Python exacto no materializado.
- `GAP-C03-CONTRACT-001`: donor settings válido, contrato Router no recuperado.
- `GAP-C01-API-CONTRACT-001`: FastAPI donor válido, contrato Paneles 1–5 incompleto.
- `GAP-C11-SEMANTIC-CACHE-CONTRACT-001`: donors Redis/vector presentes, policy/contrato semantic-cache no recuperado.
- `GAP-C12-COST-POLICY-CONTRACT-001`: LiteLLM/cost metadata presente, budget policy Router no recuperada.

## Último delta LOOP
RIU-0028 auditó exclusivamente C12 Cost Optimizer y registró el GAP contractual sin generar producción. Council12 + 3 refutaciones + cross-check + CODA + `verify_final=PASS_C12_AUDIT_ONLY_CONTRACT_GAP_RECORDED`. Progreso se conserva en 95% porque auditoría sin runtime PASS no equivale a implementación; Paso 2 ACTIVE; Paso 3 PENDING.
