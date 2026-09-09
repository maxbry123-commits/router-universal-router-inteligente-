# RECOVERY PATCH — ROUTER INTELIGENTE UNIVERSAL

Contrato: `tel.workflow/v3` · modo `FAIL_CLOSED_LOOP`.

## Estado válido
- Plan limitado a 3 pasos.
- Paso 1: componentes centralizados; owner público HF 0; privados/endpoints FLAG no bloqueante.
- Paso 2 ACTIVE: Gate/conectores/registry + validator/schema/RedUniversal recuperados y verificados.
- C15 `red/enchufe_gate.py` preserva firma pública v1.5 y delega fichas v2 a `domain/schemas/enchufe_v2.py` + `enchufe/validator_v2.py`; HF Job `6aa16ff732d5d0c22c5b0912` = `5 passed in 0.09s`.
- C10 `engine/resilience.py` materializado desde contrato explícito DOC-A02 + v6: R5 Retry (`intentos=3`, `base_ms=500`) + R6 Circuit Breaker CLOSED→OPEN→HALF_OPEN. Producción commit `6b408a781d886a8bde43c3f62b48247d872afd36`, blob `6a92375926909864d6fe604b4966b306a9aac449`; test final commit `a0e74c04c93dfc2cc0c96da9c31234d98b44333c`, blob `77ce9fef2e899215eff9ed2dc2f473adc82950b7`; HF Job `6aa1ae8221047bf1b03707ff` = `5 passed in 0.10s`.
- C10 no resuelve ni registra conectores: recibe una operación ya autorizada; ownership de conexión permanece Enchufe Universal/RedUniversal.
- Filtro de comportamiento LLM continúa fail-closed por ausencia de policy standalone explícita.
- R-004 permanece bloqueado: fuente Python exacta no materializada; no regenerar desde PDF/contrato.
- C03 donor `pydantic-settings` permanece `ADAPT_CANDIDATE`; contrato de campos/env/defaults/perfiles ausente.
- C01 donor FastAPI permanece `ADAPT_CANDIDATE`; falta contrato exacto Paneles 1–5 para rutas/métodos/schemas/auth/error/WS.
- Paso 3 pendiente.

## Boot de recuperación
1. Leer STATE/CHECKPOINT/PLAN/BITACORA/README arquitectura/Handoff y mantener `tel.workflow/v3` aunque la guía maestra v4 exista como documento no vigente para este LOOP.
2. Verificar HEAD/blobs y último delta cerrado: RIU-0026 / C10.
3. Mantener todos los GAP fail-closed hasta nueva evidencia contractual/materializable.
4. Continuar una tarea P02 independiente solo si source/contrato son suficientes; aplicar `REUSE > PATCH > ADAPT > GENERATE`.
5. Después de cualquier delta: read-back/blob + test/log cuando corresponda + persistencia.
6. C01 solo generar/adaptar API cuando exista contrato exacto; C03 solo ADAPT con campos/env; filtro LLM solo con policy standalone explícita.

## GAPs activos
- `GAP-HF-CATALOG-001`: no inventar modelos.
- `GAP-BEHAVIOR-CONTRACT-001`: schema/validator/perfiles no equivalen a policy standalone.
- `GAP-R004-EXTRACTION-001`: PDF demostrado ≠ fuente Python exacta recuperada.
- `GAP-C03-CONTRACT-001`: donor válido ≠ contrato del Router.
- `GAP-C01-API-CONTRACT-001`: FastAPI disponible ≠ contrato Paneles 1–5 recuperado.

## StrategyDelta RIU-0026
1. HF Job inicial falló porque la imagen carecía de `git`.
2. Segundo intento instaló git, pero no produjo evidencia final útil con suficiente rapidez.
3. StrategyDelta materialmente distinto: descargar por raw GitHub únicamente los dos blobs del commit fijado y ejecutar pytest aislado; PASS `5 passed in 0.10s`.

## Refutaciones RIU-0026
1. C10 presente ≠ C10 verificado; se exigió test remoto fijado a commit.
2. C10 PASS ≠ integración real de conectores/API/agentes del Paso 3.
3. Retry/Breaker no puede convertirse en segundo router; Enchufe Universal/RedUniversal conserva ownership.
