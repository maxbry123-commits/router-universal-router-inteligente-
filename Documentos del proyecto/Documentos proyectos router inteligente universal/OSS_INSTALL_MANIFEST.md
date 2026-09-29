# OPEN-SOURCE COMPONENT ACQUISITION MANIFEST

Rule: no Git LFS for the planned GitHub incorporation. If an upstream artifact cannot be incorporated through ordinary Git because of size/binary limits, stop and request the original archive from the user; do not reconstruct it.

## Target: router

| Component | Role | Destination | Acquisition state |
|---|---|---|---|
| LiteLLM | API/provider routing dependency | router | REFERENCED; exact pinned source acquisition pending |
| MCP/FastMCP | tool/provider protocol | router | REFERENCED; exact pinned source acquisition pending |
| Hugging Face Hub tooling | HF execution/deployment interface | router | INTEGRATION PRESENT; exact pinned source acquisition pending |

## Target: osquestador-auditor

| Component | Role | Destination | Acquisition state |
|---|---|---|---|
| BM25/BM25s | lexical retrieval | osquestador-auditor root | REQUIRED; exact pinned source acquisition pending |
| HNSW | vector index | osquestador-auditor root | REQUIRED; exact pinned source acquisition pending |
| vector/graph memory stack | persistent retrieval | osquestador-auditor root | REQUIRED; provider selection/source pin pending |

## Agent software

Hermes is already captured in agentes with an exact upstream ref and archive SHA. Other names referenced by the project (OpenClaw, OpenHands, OpenCode, Mimo Code, SmolAgents, mini-SWE-agent) are not marked installed here unless complete upstream source acquisition is pinned and verified.

## Integrity rule
SOURCE -> EXACT REF -> ACQUIRE -> HASH -> DESTINATION -> READ-BACK -> VERIFY

A manifest entry is not an installation claim.
