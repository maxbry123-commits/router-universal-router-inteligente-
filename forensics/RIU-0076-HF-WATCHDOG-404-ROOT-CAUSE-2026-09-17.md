# RIU-0076 — HF Scheduled Watchdog 404 Root Cause / Containment

Contract: `tel.workflow/v3`
Date: 2026-09-17

## Broken scheduled resource
- HF Scheduled Job: `6aa1af2821047bf1b0370810`
- Schedule: `*/15 * * * *`
- Prior state: active
- Command fetched:
  - `watchdog.py`
  - `hf_zip_engine.py`
  - `watchdog-state.json`
  from historical folder `➡️📂motor extracción de zip con huggueface/`.

## Fresh failure evidence
Recent Jobs:
- `6aac7b7e5c02253cfb145296`
- `6aac77fa5c02253cfb1451e1`
- `6aac74765c02253cfb1450ea`

All reproduce `urllib.error.HTTPError: HTTP Error 404: Not Found`.

## Git forensic evidence
Historical source repository: `maxbry123-commits/frontend`.

Historical files:
- `hf_zip_engine.py` added in commit `8e548c21fb86c2175630bc6e6ef499486c930e96`, blob `f3b8cd88524b0ec8064f73f8a7bf60ea005696be`.
- `watchdog-state.json` added in commit `16f3e159823e3d8dc62fad10c80981ea022a84ef`, blob `94ab0c506ef8b7706720859d2fcdc30703a346cf`.
- latest historical watchdog blob observed: `b462ab2ba5d7ec1eaa88087f3e0b77f3314c0e14`.

Commit `e0b3cd3bc9e33c8184009d5507f2e1e4bd6bfb49`:
`fix(motors): keep single canonical motors root`
explicitly removed all three files and the historical root. The scheduled command was never migrated, causing stable 404s.

## Canonical motor replacement evidence
Current immutable motor system is protected by `MOTOR-CODE-LOCK.json`.
Canonical source repository: `maxbry123-commits/frontend`.

Current relevant motor:
- `hf_download_extract_engine.py`
- blob SHA `91e6e4486692eab314be5c7130d8310d3c855397`

Controller:
- `motor_2_queue_download_extract.py`
- blob SHA `84d566e2ee4e98e42eb3a864026d067d48caabd9`

The motor skill requires explicit runtime inputs such as `QUEUE_FILE`, `STATE_FILE`, `ENGINE_PATH`, `INDEX_PATH`, and when publishing `DEST_REPO/DEST_BRANCH/DEST_ROOT`. The obsolete schedule does not provide these inputs. Restoring/renaming historical code or guessing destinations would violate fail-closed motor rules.

## Authorized containment
The obsolete Scheduled Job `6aa1af2821047bf1b0370810` was suspended.
Independent read-back:
- `scheduled inspect`: suspended=true
- `scheduled ps`: resource present and suspended=true
- total scheduled resources remain 2

No resource was deleted and no secret value was exposed.

## Verdict
`RESOLVED_OBSOLETE_SCHEDULE_SUSPENDED`

This closes the repeated-404 incident itself.
It does **not** claim a canonical replacement schedule is operational.

Replacement schedule remains `GAP_DESTINATION_INPUT` until the exact queue/state/index/destination contract is explicitly defined and then one-shot tested before scheduling.
