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
- `red/enchufe_gate.py`: Gate C15 compatible v1.5→v2.0. Conserva `validar_contrato_conexion()` para fichas v1.5 y detecta fichas v2 para delegar validación estructural a `EnchufeV2` e invariantes a `validator_v2`; no duplica el contrato v2.
- `domain/schemas/enchufe_v2.py`: C05 Pydantic v2 materializado 1:1 desde JSON Schema FABLES, con defaults explícitos de compatibilidad v1.5→v2; validación estructural solamente.
- `enchufe/validator_v2.py`: contrato v2 recuperado desde FABLES Enchufe Universal v2; invariantes semánticas/normalización v1.5→v2 + compatibilidad datatype.
- `red/red_universal.py`: R-003 recuperado por REUSE desde fuente canónica; propietario único del mapa/rutas/failover/broadcast/espejo/salud de la red; no duplica orquestación.
- `red/conectores.py`: HTTP/MCP/GitHub/HuggingFace/DB/VPS/Memoria/Interno/Webhook preservados; integración solo con registry + test.
- `red/conector_gitlab.py`: adapter GitLab v6 separado.
- `red/conector_mcp_app.py`: extensión mínima de `ConectorMCP`; fail-closed.
- `red/connector_registry.py`: registro explícito fail-closed de conectores verificados.
- `tests/`: tests contractuales separados; incluye compatibilidad Gate v1.5 y Gate v2, validator, schema y RedUniversal.
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

## C15 Enchufe Gate v1.5→v2.0 — PATCH verificado
Fuentes contractuales: Gate v1.5 en `2📌🔌ROUTER_UNIVERSAL_RED_CONEXIONES.md`, blob `692daca7ace7ac983aeb585dd05ac281e571f2f3`; Enchufe Universal v2, blob `1f2de5b0578391164e6f6f7331507299130e8579`.
PATCH producción: `router inteligente universal/red/enchufe_gate.py`, commit `4e256e1332d41f9177e0df4806bb749cbd1f1e54`, blob `b5fdc15a4b4c3747425d7db86a81f2c4e409de9e`.
Compatibilidad: fichas v1.5 mantienen su ruta histórica; fichas v2/`agent` pasan por `EnchufeV2.model_validate()` + `validator_v2.validar()`; errores v2 fallan cerrado.
Tests: `test_enchufe_gate_v15.py` commit `e938ff557670d27763c6d5b507fd2946e1cd6702`; `test_enchufe_gate_v2.py` commit `8536808a3a53cab0afb89b007f5e7095bf37a047`.
Verificación remota: dos harness iniciales fueron refutados por loader/cache; HF Job final `6aa16ff732d5d0c22c5b0912`, fijado al commit exacto `8536808a...`, terminó `5 passed in 0.09s`.

## GAP-BEHAVIOR-CONTRACT-001
No existe todavía evidencia de policy standalone allow/deny del comportamiento LLM. El GAP permanece abierto y fail-closed; no se deriva policy de schemas, validator, perfiles ni vendors.

## Último delta LOOP
P02 auditó C15 contra sus dos fuentes de verdad y aplicó únicamente el delta demostrado de compatibilidad v2. La firma pública v1.5 permanece; el contrato v2 se reutiliza en sus módulos propios. Siguiente delta 1×1: auditar R-004 `infrastructure/backup/respaldo.py` y REUSE solo si su presencia/ownership quedan demostrados. Paso 2 sigue ACTIVE; Paso 3 sigue PENDING.
