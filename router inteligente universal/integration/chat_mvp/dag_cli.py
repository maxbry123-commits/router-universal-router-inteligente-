"""CLI for riu.dag/v1 plans written by Claude:  python -m integration.chat_mvp.dag_cli plan.dag.json --out result.json

Runs every node through the Router hot path with the provider keys from the environment (never printed),
using the response cache and the usage log. Exit code 0 for PASS/UNVERIFIED, 1 for FAIL.
"""
from __future__ import annotations

import argparse
import json
import os
import tempfile
from pathlib import Path
from typing import Any, Callable

from . import core, dag
from . import providers as prov
from .store import Store
from .ui_bridge import _emit_state_event
from .usage import UsageLog


def build_executor(store: Store, owner: str, keys: dict[str, str] | None = None) -> Callable[..., dict[str, Any]]:
    def executor(*, messages: list[dict[str, str]], max_tokens: int, provider: str | None = None, model: str | None = None,
                 group: str | None = None) -> dict[str, Any]:
        if group is not None:  # route node: the group's model chain, same callable and policy as /chat/route (lazy: needs fastapi)
            from . import model_pool, resilience, route_api
            out = resilience.run_policy(group, messages, max_tokens, call=route_api._call, pool=model_pool.POOL)
            UsageLog(store).record(owner=owner, provider=out["route"]["provider"], model=out["route"]["model"], usage=out.get("usage"), from_cache=False)
            return out
        if provider not in prov.PROVIDERS:
            raise ValueError("PROVIDER_UNKNOWN")
        key = (keys or {}).get(provider) or prov.resolve_key(provider)
        if not key and provider != "local":
            raise ValueError(f"PROVIDER_KEY_MISSING:{provider}")
        if provider == "hf":
            core.hf_gate(model)
        return core.run_completion(store, owner, provider, key, model, messages, max_tokens)

    return executor


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("plan")
    ap.add_argument("--out")
    ap.add_argument("--owner", default="claude-brain")
    args = ap.parse_args(argv)
    plan = json.loads(Path(args.plan).read_text(encoding="utf-8"))
    store = Store(os.getenv("RIU_DATA_DIR") or tempfile.mkdtemp())
    agents = {a["id"]: a["system_prompt"] for a in store.agents()}
    result = dag.run_dag(plan, build_executor(store, args.owner), agents=agents, known_providers=set(prov.PROVIDERS),
                         state_emit=_emit_state_event if any(n.get("type") == "agent" for n in plan["nodes"]) else None)
    result["usage_summary"] = UsageLog(store).summary()["totals"]
    if args.out:
        Path(args.out).parent.mkdir(parents=True, exist_ok=True)
        Path(args.out).write_text(json.dumps(result, ensure_ascii=False, indent=1), encoding="utf-8")
    per = ",".join(f"{k}={v['status']}" for k, v in result["nodes"].items())
    print(f"::notice title=RIU_DAG::id={plan.get('id')} status={result['status']} ledger_valid={result['ledger_valid']} nodes={per}")
    return 0 if result["status"] in ("PASS", "UNVERIFIED") else 1


if __name__ == "__main__":
    raise SystemExit(main())
