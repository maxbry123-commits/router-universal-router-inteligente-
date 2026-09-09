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
- `red/enchufe_gate.py`: gate canónico v1.5; compatibilidad v2 debe preservarse.
- `domain/schemas/enchufe_v2.py`: C05 Pydantic v2 materializado 1:1 desde JSON Schema FABLES, con defaults explícitos de compatibilidad v1.5→v2; validación estructural solamente.
- `enchufe/validator_v2.py`: contrato v2 recuperado desde FABLES Enchufe Universal v2; invariantes semánticas/normalización v1.5→v2 + compatibilidad datatype.
- `red/red_universal.py`: R-003 recuperado por REUSE desde fuente canónica; propietario único del mapa/rutas/failover/broadcast/espejo/salud de la red; no duplica orquestación.
- `red/conectores.py`: HTTP/MCP/GitHub/HuggingFace/DB/VPS/Memoria/Interno/Webhook preservados; integración solo con registry + test.
- `red/conector_gitlab.py`: adapter GitLab v6 separado.
- `red/conector_mcp_app.py`: extensión mínima de `ConectorMCP`; fail-closed.
- `red/connector_registry.py`: registro explícito fail-closed de conectores verificados.
- `tests/`: tests contractuales separados; `test_validator_v2_contract.py` fija invariantes recuperadas, `test_enchufe_v2_schema.py` fija C05 y `test_red_universal_r003.py` fija routing/failover/task_id/health/mapa de R-003.
- `integration/huggingface/`: auditoría/bridge HF y evidencia; prohibido inventar `model_id`.
- Capa/filtro LLM: **NO materializada** mientras `GAP-BEHAVIOR-CONTRACT-001` permanezca abierto; debe vivir detrás de boundary `guard/plugin`, no dentro del core.

## Reglas
- `REUSE > PATCH > ADAPT > GENERATE`.
- Prohibido monolito.
- Secretos solo por entorno/Vault.
- Archivo presente != integrado.
- PASS exige ruta + SHA/diff + read-back + test/log + URL cuando aplique.
- `GAP-HF-CATALOG-001` permanece no bloqueante hasta disponer de evidencia real de privados/endpoints HF.
- Filtro LLM únicamente con policy explícita definida/recuperada; C05 schema, `validator_v2`, perfiles cognitivos o donor `guardrails` no autorizan inferir semántica adicional.

## Validator v2 — recuperación verificada
Fuente contractual: `Documentos proyectos router inteligente universal/lote 1 documentos proyecto/🧩🧩🔌🔌🔌FABLES CREO ESTA NUEVA VERSIÓN ENCHUFE_UNIVERSAL_v2🔌🔌🧩🧩🧩 enchufe para la fichas 🏗️🏗️🏗️🏗️✅✅✅✅.md`, blob `1f2de5b0578391164e6f6f7331507299130e8579`.
Materialización: `router inteligente universal/enchufe/validator_v2.py`, commit `2e20488e384ad658675d1ccaf6726fa1edd02034`, blob `418f230e705d18525aae63d6930311ccb7b9297b`.
Test: `router inteligente universal/tests/test_validator_v2_contract.py`, final commit `de9326ff0167a04024a09fc60617c8bf6b75ae28`, blob `4aa5d4a878f582b82f254cd5ff1fda8d9161fe14`.
Verificación remota: HF Job `6aa15fea900620b5c77e6fa1`, COMPLETED, `6 passed in 0.02s`.

## C05 Enchufe Schema Pydantic v2 — materialización verificada
Contrato estructural: JSON Schema del mismo documento FABLES + DOC-A02 C05.
Materialización: `router inteligente universal/domain/schemas/enchufe_v2.py`, commit `14d86fb07caa02e552a2c5a7788c197084a8d11f`, blob `faf0b8a2f1474c044143728bf7fdfd41d1a751fa`.
Test: `router inteligente universal/tests/test_enchufe_v2_schema.py`, commit `96448365568950d9bbd7405f58e001f7eb419f1c`, blob `53d4ee813b51000609532817ca1b5d02a71459f8`.
Verificación remota: HF Job `6aa165be32d5d0c22c5b07df`, descarga exacta desde `main`, COMPLETED/success, `4 passed in 0.09s`.

## R-003 RedUniversal — REUSE verificado
Fuente contractual: `Documentos proyectos router inteligente universal/lote 1 documentos proyecto/2📌🔌ROUTER_UNIVERSAL_RED_CONEXIONES.md`, blob `692daca7ace7ac983aeb585dd05ac281e571f2f3`.
Materialización: `router inteligente universal/red/red_universal.py`, commit `189a605fbccf703a81269d05777573c14acb68fb`, blob `66154b60ad53aa797094df8741389c8427f9bec0`.
Test: `router inteligente universal/tests/test_red_universal_r003.py`, commit `b7ed873fa8c8b8f848d46c3fd1217206a51480c3`, blob `2be8bcf56fac0bb1c88b0f18edd0330538364726`.
Primera verificación HF `6aa16b3e32d5d0c22c5b0874` fue refutada por aplanar la estructura del harness; StrategyDelta preservó `red/` + `tests/`. Verificación final HF `6aa16b68900620b5c77e7259`: `5 passed in 0.05s`.

## GAP-BEHAVIOR-CONTRACT-001
No existe todavía evidencia de policy standalone allow/deny del comportamiento LLM. El GAP permanece abierto y fail-closed; no se deriva policy de schemas, validator, perfiles ni vendors.

## Último delta LOOP
P02 detectó por auditoría física que R-003 faltaba del code root pese al Handoff; se reutilizó la implementación canónica, se verificó read-back por blob y se ejecutó test remoto real sobre archivos exactos de `main`. Siguiente delta 1×1: auditar C15 Gate v1.5→v2.0 y aplicar PATCH mínimo solo si el contrato lo demuestra. Paso 2 sigue ACTIVE; Paso 3 sigue PENDING.
