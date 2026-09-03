# UNIVERSAL ROUTER CONTRACT

Canonical owner: router-universal-router-inteligente-

## All application repositories route through this boundary
- frontend
- agentes
- Orquestador-Maxbry-
- osquestador-auditor

Grupo-Trabajo-1 remains control/evidence and is not an application runtime.

## Responsibilities
- API provider routing
- Hugging Face execution routing
- request/response normalization
- authentication by runtime secret reference
- retry/timeout policy
- provider selection
- audit correlation ID propagation

## Required runtime references
- ROUTER_BASE_URL
- HF_EXECUTION_BASE_URL
- MEMORY_BASE_URL
- ROUTER_AUTH_REF
- HF_AUTH_REF
- MEMORY_AUTH_REF

Secrets must be supplied by the deployment secret store. They must never be committed.

## Canonical flow
application -> router -> API/HF/memory -> router -> application

## HF boundary
The router is the single application-facing entry point for Hugging Face execution. Persistent memory is owned by osquestador-auditor.

## Status
Routing contract installed. Live endpoint connectivity and HF execution are separate verification gates.
