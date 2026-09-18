# RIU-0081 — Agent model mix

Contract: `tel.workflow/v3`
Date: 2026-09-17
Status: `POLICY_DEFINED / RUNTIME_STATUS_PRESERVED`

## Principle
Many agents do not imply many large models loaded simultaneously.
RIU uses task classification + logical worker lanes + identity failover to select the smallest model tier that satisfies the task and only escalates when required.

## Tier A — tiny / triage / deterministic assist
Candidates from the 20-slot registry:
- M10 `Qwen/Qwen2.5-0.5B-Instruct` (~0.5B)
- M01 `Qwen/Qwen3-0.6B` (~0.75B; real CPU evidence)
- M07 `Qwen/Qwen2.5-1.5B-Instruct` (~1.5B)

Use:
- classification
- intent/tag extraction
- short structured transforms
- routing hints
- simple summaries
- heartbeat/agent utility calls

Rule: deterministic code stays deterministic; the small model is not used where rules already solve the task exactly.

## Tier B — small agents
- M12 `Qwen/Qwen2.5-3B-Instruct`
- M11 `Qwen/Qwen3-4B`

Use:
- normal agent turns
- moderate tool selection
- compact planning
- structured extraction with more context

## Tier C — standard agents
- M05 `Qwen/Qwen2.5-7B-Instruct`
- M20 `Qwen/Qwen2.5-7B-Instruct-AWQ`
- M03 `Qwen/Qwen3-8B` (compute verified, Router readiness still partial)

Use:
- general multi-step agent work
- tool reasoning
- larger context
- fallback when Tier A/B confidence/verification fails

This tier matches the project's preference for ~7B-class models for many agents.

## Tier D — specialist / large escalation
- M04 `unsloth/Qwen3-Coder-30B-A3B-Instruct-GGUF`: Code-specialized, runtime GAP
- M14 Qwen3-32B: runtime/hardware GAP
- M15 Dolphin Yi 34B: code-trained generalist, runtime/hardware GAP
- M08 OTel 31B: domain model, runtime/hardware GAP
- M13 GPT-OSS 120B, M19 Qwen 72B, M16 DeepSeek-V4 class: large/provider-first until direct compute is proven

Use only by explicit task class/escalation and only when the exact model route is operationally verified.

## Escalation contract
1. Router classifies task deterministically when possible.
2. Select lowest eligible tier.
3. Execute one identity/model route.
4. Verify output contract.
5. On retryable quality/capability failure, escalate one tier or route to a specialist.
6. On auth/quota/health failure, use identity/mirror failover within the same tier before increasing model size.
7. Record escalation reason and final route.

## Cost/concurrency
- No requirement to keep all models loaded.
- HF1/HF2/HF3 are logical lanes; jobs are scheduled on demand.
- >50 API identities are registry entries, not 50 simultaneous workers.
- Large models are provider/Endpoint first unless a measured Job path is justified.

## Closure
The agent model-tier policy is defined.
No model's runtime status is upgraded by this document.
Future readiness changes must come from exact-model inference tests and Router hot-path evidence.
