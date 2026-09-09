# C12 Cost Optimizer — donor audit

Contract: `tel.workflow/v3` · mode `FAIL_CLOSED_LOOP`.

## Decision
`ADAPT_CANDIDATE / AUDIT_ONLY`.

## Evidence
- Local donor: `router inteligente universal/Componente open soure router inteligente universal/litellm/`.
- `pyproject.toml` identifies package `litellm` version `1.100.0`, MIT license, repository `https://github.com/BerriAI/litellm`.
- Donor provides multi-provider LLM interface capability and can serve as a cost/usage data source candidate.

## Fail-closed contract check
C12 is defined by architecture as `Cost Optimizer — presupuesto/policy`, but the Router-owned contract does not currently define the exact budget scopes, hard/soft limits, accounting interval, currency normalization, provider/model price source authority, fallback behavior, quota rollover, per-agent/per-task ownership, or the exact Enchufe boundary.

Therefore LiteLLM capability is NOT equivalent to C12 integration. No production optimizer code is generated in this delta.

## GAP
`GAP-C12-COST-POLICY-CONTRACT-001`: exact Router cost/budget policy is not recovered.

## Acceptance / refutations
1. LiteLLM presence != C12 integrated.
2. Provider cost metadata != Router budget policy.
3. Inferring limits, intervals or price authority would violate `FAIL_CLOSED_LOOP`.

Council12: PASS for safe audit-only delta.
Cross-check: PASS against Handoff C12 and REUSE > PATCH > ADAPT > GENERATE.
CODA: PASS_SAFE_AUDIT_DELTA.
verify_final: PASS_C12_AUDIT_ONLY_CONTRACT_GAP_RECORDED.
