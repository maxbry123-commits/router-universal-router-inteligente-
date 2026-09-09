# RIU-0027 — C11 Semantic Cache donor audit

Contract: `tel.workflow/v3` · mode: `FAIL_CLOSED_LOOP`

## INPUT literal
C11 is defined by the project handoff as `Semantic Cache`, state `MISSING`, action `GENERATE/ADAPT sobre Redis/vector similarity`. The current LOOP requires `REUSE > PATCH > ADAPT > GENERATE`, one delta at a time, no speculative implementation, and all connections through Enchufe Universal.

## Evidence read from main
- Component index/handoff blob: `1182154d2a96497867f29529cf97871a18a9434b`.
- Open-source donor root tree: `router inteligente universal/Componente open soure router inteligente universal/`.
- Donor root tree SHA: `5322af570d72fe2e6feb67426d9d299e08fadad1`.
- `redis-py/` is physically present in the donor root and readable from main.
- The handoff also inventories Redis/redis-py plus vector candidates Qdrant/Chroma/Sentence-Transformers for storage/cache capability.
- Upstream URL for redis-py: `https://github.com/redis/redis-py`.

## Contract audit
Recovered project material defines the capability family (Redis/vector similarity) but does **not** define the Router-owned semantic-cache contract needed to implement it safely: canonical cache-key derivation, embedding/model identity and versioning, similarity metric, threshold, TTL/eviction, namespace/tenant isolation, invalidation rules, serialization schema, stale-result policy, privacy boundary, failure/fallback semantics, or the exact Enchufe/registry interface for C11.

## Decision
`ADAPT_CANDIDATE / AUDIT_ONLY`.

No production C11 code is generated in this delta. Donor capability is not treated as integration. A new fail-closed gap is recorded: `GAP-C11-SEMANTIC-CACHE-CONTRACT-001`.

## Acceptance / verification
- Local donor presence: PASS.
- Architecture ownership: PASS; C11 remains behind the Router/Enchufe boundary.
- Exact implementation contract: FAIL/MISSING -> GAP.
- Runtime test: NOT APPLICABLE because no production code was changed.
- External download/extraction skill: NOT INVOKED; no external component was added or downloaded.

## Council12 / refutations / cross-check / CODA
Council12: PASS for audit-only delta (objective, INPUT, destination, state, evidence, reuse, architecture, concurrency, dependency, test applicability, rollback, closure).

Refutations:
1. `redis-py` present != semantic cache integrated.
2. Redis/vector capability != Router cache policy/contract.
3. An inferred threshold/TTL/embedding policy would violate FAIL_CLOSED_LOOP.

Cross-check: Handoff ↔ README architecture ↔ STATE ↔ CHECKPOINT ↔ PLAN ↔ RECOVERY = PASS for keeping C11 unimplemented.
CODA: `PASS_SAFE_AUDIT_DELTA`.
verify_final: `PASS_C11_AUDIT_ONLY_CONTRACT_GAP_RECORDED`.
