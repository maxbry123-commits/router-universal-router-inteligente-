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
Handoff blob `1182154d2a96497867f29529cf97871a18a9434b` define C11 como `MISSING`, `GENERATE/ADAPT sobre Redis/vector similarity`. Donor root tree `5322af570d72fe2e6feb67426d9d299e08fadad1` confirma biblioteca local y `redis-py/`; upstream `https://github.com/redis/redis-py`.

Auditoría: `router inteligente universal/integration/audits/C11-SEMANTIC-CACHE-DONOR-AUDIT.md`, commit `e03782dcc413efab22399f2df3dc30c6a60a053e`.

Decisión: `ADAPT_CANDIDATE / AUDIT_ONLY`. No producir C11 hasta recuperar contrato exacto de cache-key, embedding/model version, metric/threshold, TTL/invalidation, namespace/privacy, serialization, fallback/stale policy y boundary Enchufe. Donor Redis/vector no constituye integración.

## GAPs activos
- `GAP-HF-CATALOG-001`: privados/endpoints sin `model_id` confirmado.
- `GAP-BEHAVIOR-CONTRACT-001`: no existe policy standalone allow/deny recuperada.
- `GAP-R004-EXTRACTION-001`: PDF exacto demostrado, código Python exacto no materializado.
- `GAP-C03-CONTRACT-001`: donor settings válido, contrato Router no recuperado.
- `GAP-C01-API-CONTRACT-001`: FastAPI donor válido, contrato Paneles 1–5 incompleto.
- `GAP-C11-SEMANTIC-CACHE-CONTRACT-001`: donors Redis/vector presentes, policy/contrato semantic-cache no recuperado.

## Último delta LOOP
RIU-0027 auditó exclusivamente C11 Semantic Cache y registró el GAP contractual sin generar producción. Council12 + 3 refutaciones + cross-check + CODA + `verify_final=PASS_C11_AUDIT_ONLY_CONTRACT_GAP_RECORDED`. Progreso se conserva en 95% porque auditoría sin runtime PASS no equivale a implementación; Paso 2 ACTIVE; Paso 3 PENDING.
