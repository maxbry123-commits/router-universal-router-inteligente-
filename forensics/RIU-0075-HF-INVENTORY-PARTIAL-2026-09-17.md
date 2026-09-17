# RIU-0075 — Hugging Face Full Inventory (PARTIAL / FAIL-CLOSED)

Contract: `tel.workflow/v3` · Date: 2026-09-17

## Fresh identity
- Account: `COMAND-CENTER-1`
- Auth: OAuth
- Scopes: `jobs`, `openid`, `profile`, `read-mcp`, `read-repos`
- No secret/token value recorded.

## Fresh Jobs window
The direct HF connector returned exactly **100 Jobs** and reported total=100 for this call.
Status distribution in this visible window:
- COMPLETED: 8
- CANCELED: 1
- ERROR: 91

The connector still returns 100 when requested with `limit=0`; therefore this is a **window/cap**, not proof that account history contains only 100 Jobs.

## Scheduled Jobs
Exactly **2** were returned fresh:
1. `6aa1af2821047bf1b0370810` — active, `*/15 * * * *`, `cpu-basic`.
2. `6aa1ac575527934177ebd8ce` — suspended, `*/15 * * * *`, `cpu-basic`.

The active job downloads `watchdog.py`, `hf_zip_engine.py`, and `watchdog-state.json` from a stale GitHub raw path.

## Fresh watchdog repeat-check
Three recent executions:
- `6aac7b7e5c02253cfb145296`
- `6aac77fa5c02253cfb1451e1`
- `6aac74765c02253cfb1450ea`

All three logs terminate with:
`urllib.error.HTTPError: HTTP Error 404: Not Found`

Classification: **stable reproducible GAP, not flakiness**.

## Public account resources from no-token Job
Job `6aac7d015c02253cfb1452fd` ran without HF_TOKEN:
- MODELS 0
- DATASETS 0
- SPACES 3
  - `COMAND-CENTER-1/claude-github-mcp-backup`
  - `COMAND-CENTER-1/owner_HF_1`
  - `COMAND-CENTER-1/yaiwes-ui-factory`

Because `HF_TOKEN_PRESENT=False`, this **does not prove** that private model/dataset repositories are absent.
Its attempt to list authenticated Jobs via CLI failed, as expected without a token.

## Model inventory in RIU source of truth
`router inteligente universal/integration/huggingface/model_registry.json`
contract: `RIU-HF-MODEL-REGISTRY-V8`
contains **20 slots**. This is the current Router registry, not proof of all account-private Hub resources.

## Connector GAP
The advertised HF `model_search` capability returned backend `Tool model_search not found` during this run.
This is treated as a connector/tool GAP, not as zero models.

## Cross-project filtering
The current 100-Job window also contains MiniMax/Kimi/YAIWES references from other account work.
Those references are **excluded from Router model inventory** unless they are explicitly registered or wired into RIU with evidence.

## Historical evidence
Older project evidence recorded a much larger job history (961 Jobs in an authenticated prior introspection run), but it is **not used as a fresh current total**.

## Closure status
`PARTIAL / GAP`
Verified fresh:
- identity
- current visible 100-Job window
- 2 scheduled jobs
- active watchdog stable 404
- 3 public Spaces
- canonical 20-slot Router registry

Still missing for full closure:
- account-private model/dataset/resource inventory
- uncapped current Jobs history
- deduplicated account-wide model refs
- runtime verification for every model promoted to operational status
