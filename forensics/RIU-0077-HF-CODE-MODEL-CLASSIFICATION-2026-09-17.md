# RIU-0077 — Hugging Face Code Model Classification

Contract: `tel.workflow/v3` · Date: 2026-09-17

Scope: classify the 20 current RIU registry slots using fresh Hugging Face repository metadata. This is a classification audit; it does not convert catalog presence into runtime PASS.

## Code-specialized
### HF-M04 — `unsloth/Qwen3-Coder-30B-A3B-Instruct-GGUF`
Fresh Hub metadata:
- task: text-generation
- base model: `Qwen/Qwen3-Coder-30B-A3B-Instruct`
- quantized from the Coder base model
- GGUF / Qwen3 / conversational
Verdict: **CODE_SPECIALIZED / RUNTIME_GAP**.
Reason: explicit Coder base model establishes specialization. Current RIU evidence still has canceled/timeout inference attempts, so it is not marked operational.

## Code-trained but generalist
### HF-M15 — `dphn/dolphin-2.9.1-yi-1.5-34b`
Fresh Hub metadata lists training datasets:
- `m-a-p/CodeFeedback-Filtered-Instruction`
- `cognitivecomputations/dolphin-coder`
alongside general instruction, math, function-calling and agent datasets.
Verdict: **CODE_CAPABLE_TRAINING_EVIDENCE / NOT_CODE_SPECIALIZED / RUNTIME_GAP**.

## Not promoted to Code-specialized
The remaining 18 registry slots expose general text-generation, conversational, telecom/multimodal, or generic model metadata in the fresh Hub lookup. No explicit Code-specialized model identity/tag/base-model evidence was returned for them in this audit.
They may be capable of coding, but capability is not equivalent to specialization and is not inferred here.

## Runtime rule
`CLASSIFIED_CODE != OPERATIONAL_CODE`.
Before a Code route is marked READY:
1. run a deterministic code task;
2. require executable/parseable output;
3. test failure path;
4. record Job ID, log and exact model revision/variant.

## Result
- dedicated Code models: **1** (HF-M04)
- code-trained generalist: **1** (HF-M15)
- remaining registry slots not proven Code-specialized: **18**
- operationally verified Code route from M04/M15 in this audit: **0**
