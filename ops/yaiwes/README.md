# YAIWES HF nine-worker MVP

`launch.py` runs a single `cpu-basic` Hugging Face Job. It refuses to spend compute
without a persistent request, refuses `STOPPED_BY_DIRECTOR`, and refuses a second
running supervisor. OpenAI Agents SDK is the common implementation for nine named
roles; these are **not** the native binaries of Claude Code, OpenHands, etc.

## Launch after secure credentials are available

Provide `HF_TOKEN`, `AGENT_GITHUB_TOKEN` and `OPENAI_API_KEY` as environment secrets,
not command-line arguments or tracked files. Set `HF_NAMESPACE=COMAND-CENTER-1`,
`REPO=maxbry123-commits/router-universal-router-inteligente-`, `QUEUE_REF` to the
published feature branch containing `ops/yaiwes` and the request; optionally set
`OPENAI_MODEL` (default `gpt-4.1-mini`). Run `python ops/yaiwes/launch.py`.

First run only the Grok X-Ray smoke request. Its acceptance test initially fails
until `STATE.json` is created, then verifies hashes against source bytes in Git.
Check the Job logs for `WORKER_PID`, `SENTINEL_HEARTBEAT`, and `SENTINEL_OK`; check
the task branch, checkpoint, tests, read-back and PR before adding requests for
the other eight identities. A `RUNNING` Job alone does not prove that workers ran.

To stop admission and prevent the next launch, publish
`ops/yaiwes/control.json` with `{"state":"STOPPED_BY_DIRECTOR"}` on `QUEUE_REF`.
The Job has a seven-hour timeout; automatic relaunch is not implemented. Do not
claim continuous operation beyond that timeout without launching and checking
the next Job.
