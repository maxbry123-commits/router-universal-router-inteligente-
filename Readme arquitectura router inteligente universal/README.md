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

## Hugging Face Jobs — cómputo real
Jobs forma parte del flujo externo `Router/GitHub source -> HF Job compute -> resultado/evidencia -> GitHub/state` sin convertirse en segundo orquestador. Documentación oficial: https://huggingface.co/docs/hub/en/jobs y https://huggingface.co/docs/hub/en/jobs-configuration . `cpu-upgrade` se reserva para cargas que realmente necesitan 8 vCPU/32 GB; auditorías mínimas pueden usar `cpu-basic`.

RIU-0030 verificó cómputo real con Job `6aa1c5fd21047bf1b0370d4d`, `cpu-upgrade`, `success`.

RIU-0031 auditó el boundary del catálogo HF: identidad conectada `COMAND-CENTER-1`, OAuth autenticado; Job `6aa1d38621047bf1b0370f3f` completó con `public_model_count=0` y `hf_token_present=false`. La documentación de Jobs trata `HF_TOKEN` como secreto explícito, no como built-in automático. Por tanto, público 0 no demuestra privado 0 y ningún `model_id→especialidad→adapter→FastAPI` puede registrarse todavía. Auditoría: `router inteligente universal/integration/huggingface/RIU-0031-HF-CATALOG-TOKEN-AUDIT.md`, commit `505d54c23120f96cec42dde5c26cd001c20092b9`.

## Reglas
- `REUSE > PATCH > ADAPT > GENERATE`.
- Prohibido monolito.
- Secretos solo por entorno/Vault.
- Archivo presente != integrado.
- Donor capaz != contrato específico del Router.
- HF Job success != model catalog ni E2E.
- Público HF 0 != privado HF 0.
- PASS exige ruta + SHA/diff + read-back + test/log + URL cuando aplique.
- Filtro LLM únicamente con policy explícita definida/recuperada.
- `tel.workflow/v3` es el contrato vigente de este LOOP.

## C10 Resilience — verificado
Producción `router inteligente universal/engine/resilience.py`, commit `6b408a781d886a8bde43c3f62b48247d872afd36`; test `a0e74c04c93dfc2cc0c96da9c31234d98b44333c`; HF Job `6aa1ae8221047bf1b03707ff` = `5 passed in 0.10s`.

## C11/C12/C13
C11 Semantic Cache, C12 Cost Optimizer y C13 CodeSandbox dual siguen `ADAPT_CANDIDATE/AUDIT_ONLY` hasta recuperar sus contratos Router-owned exactos.

## GAPs activos
- `GAP-HF-CATALOG-001`: boundary de credencial privada; reintentar sólo con ruta segura explícita.
- `GAP-BEHAVIOR-CONTRACT-001`: no existe policy standalone allow/deny recuperada.
- `GAP-R004-EXTRACTION-001`.
- `GAP-C03-CONTRACT-001`.
- `GAP-C01-API-CONTRACT-001`.
- `GAP-C11-SEMANTIC-CACHE-CONTRACT-001`.
- `GAP-C12-COST-POLICY-CONTRACT-001`.
- `GAP-C13-SANDBOX-CONTRACT-001`.

## Último delta LOOP
RIU-0031: Council12 + 3 refutaciones + cross-check + CODA + `verify_final=PASS_AUDIT_ONLY_NO_MODEL_CLAIM`. Progreso 96%; Paso 2 ACTIVE; Paso 3 PENDING.
