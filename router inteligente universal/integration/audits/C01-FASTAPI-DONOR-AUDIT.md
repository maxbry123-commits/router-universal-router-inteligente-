# C01 FastAPI donor audit

Contract: `tel.workflow/v3` · mode `FAIL_CLOSED_LOOP`

## Scope
Single safe P02 delta. Audit only; no production API code generated.

## Architecture requirement
C01 is `API Gateway REST/WS`, state `MISSING`, action `GENERATE`, with routers for Panels 1–5 and no business logic. The canonical flow remains `Enchufe Gate -> EnchufeV2 -> validator_v2 -> RedUniversal -> connector_registry -> connectors` and FastAPI may only live behind `api/` as an adapter/surface, never as a second workflow owner.

## Local donor evidence
- Local path: `router inteligente universal/Componente open soure router inteligente universal/fastapi/`
- `pyproject.toml` blob: `06c82344a7010eefaf98f567468dea8be5a5ae10`
- Upstream declared by donor: `https://github.com/fastapi/fastapi`
- License: MIT
- Python: `>=3.10`
- Core dependencies declared locally: Starlette, Pydantic v2, typing-extensions, typing-inspection, annotated-doc.
- Local donor directory contains source/docs/tests and a MIT `LICENSE` blob `3e92463e6bd522a2a21e5f0a80d8089d6c4be20d`.

## Decision
`ADAPT_CANDIDATE`, not integrated.

FastAPI is suitable as the external REST/WS surface, but the project evidence reviewed in this delta does not define the exact Panel 1–5 endpoint paths, request/response schemas, auth binding, websocket event contract, or error envelope. Generating those details would violate FAIL_CLOSED_LOOP and the rule that donor capability is not the Router contract.

## GAP-C01-API-CONTRACT-001
Missing exact API surface contract for Panels 1–5: routes, methods, schemas, auth/error semantics and WS/SSE binding. Until recovered, do not generate production `api/` routers.

## Council12 / refutations / cross-check / CODA
Council12 result: PASS_AUDIT_ONLY. Source/destination/ownership/license/dependency fit are evidenced; runtime implementation is intentionally blocked by missing project-specific API contract.

Refutations:
1. FastAPI source present != C01 integrated.
2. FastAPI supports REST/WS != project Panel 1–5 contract recovered.
3. Donor audit PASS != C01 runtime PASS != P02 closed != Step 3 E2E.

Cross-check: Handoff C01 + README architecture + STATE/CHECKPOINT/PLAN/RECOVERY agree on `REUSE > PATCH > ADAPT > GENERATE`, no-monolith ownership, and fail-closed generation.

CODA: persist audit and GAP; continue only with another independent P02 delta whose source and contract are sufficient.

`verify_final = PASS_AUDIT_ONLY`
