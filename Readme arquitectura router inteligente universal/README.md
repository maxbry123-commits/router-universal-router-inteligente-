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
`Enchufe Gate -> validator_v2 -> RedUniversal -> connector_registry -> adapters/conectores -> destinos`
DAGs/modelos no pueden alterar este ownership. Componentes externos son donor/adapter/plugin, nunca segundo orquestador.

## Separación vigente
- `red/enchufe_gate.py`: gate canónico v1.5; compatibilidad v2 debe preservarse.
- `enchufe/validator_v2.py`: contrato v2 recuperado desde FABLES Enchufe Universal v2 y materializado; validación/normalización v1.5→v2 + compatibilidad datatype.
- `red/conectores.py`: HTTP/MCP/GitHub/HuggingFace/DB/VPS/Memoria/Interno/Webhook preservados; integración solo con registry + test.
- `red/conector_gitlab.py`: adapter GitLab v6 separado.
- `red/conector_mcp_app.py`: extensión mínima de `ConectorMCP`; fail-closed.
- `red/connector_registry.py`: registro explícito fail-closed de conectores verificados.
- `tests/`: tests contractuales separados; `test_validator_v2_contract.py` fija los seis casos previstos por la fuente.
- `integration/huggingface/`: auditoría/bridge HF y evidencia; prohibido inventar `model_id`.
- Capa/filtro LLM: **NO materializada** mientras `GAP-BEHAVIOR-CONTRACT-001` permanezca abierto; debe vivir detrás de boundary `guard/plugin`, no dentro del core.

## Reglas
- `REUSE > PATCH > ADAPT > GENERATE`.
- Prohibido monolito.
- Secretos solo por entorno/Vault.
- Archivo presente != integrado.
- PASS exige ruta + SHA/diff + read-back + test/log + URL cuando aplique.
- `GAP-HF-CATALOG-001` permanece no bloqueante hasta disponer de evidencia real de privados/endpoints HF.
- Filtro LLM únicamente con policy explícita definida/recuperada; `validator_v2`, perfiles cognitivos o donor `guardrails` no autorizan inferir semántica adicional.

## Validator v2 — recuperación verificada
Fuente contractual: `Documentos proyectos router inteligente universal/lote 1 documentos proyecto/🧩🧩🔌🔌🔌FABLES CREO ESTA NUEVA VERSIÓN ENCHUFE_UNIVERSAL_v2🔌🔌🧩🧩🧩 enchufe para la fichas 🏗️🏗️🏗️🏗️✅✅✅✅.md`, blob `1f2de5b0578391164e6f6f7331507299130e8579`.
Materialización: `router inteligente universal/enchufe/validator_v2.py`, commit `2e20488e384ad658675d1ccaf6726fa1edd02034`, blob `418f230e705d18525aae63d6930311ccb7b9297b`.
Test: `router inteligente universal/tests/test_validator_v2_contract.py`, final commit `de9326ff0167a04024a09fc60617c8bf6b75ae28`, blob `4aa5d4a878f582b82f254cd5ff1fda8d9161fe14`.
Verificación remota: HF Job `6aa15fea900620b5c77e6fa1`, sparse-clone de `main`, COMPLETED, `6 passed in 0.02s`.

## GAP-BEHAVIOR-CONTRACT-001
El 404 de `enchufe/validator_v2.py` fue resuelto recuperando el archivo desde la fuente FABLES. El GAP se refina: todavía no existe evidencia de una policy standalone allow/deny del comportamiento LLM. StrategyDelta: revisar únicamente fuentes de verdad restantes; solo materializar una policy explícita detrás de `guard/plugin`.

## Último delta LOOP
P02 recuperó y materializó `validator_v2` desde fuente contractual, corrigió únicamente el harness de test tras una primera refutación, y cerró con seis tests remotos PASS. Paso 2 sigue ACTIVE; Paso 3 sigue PENDING.
