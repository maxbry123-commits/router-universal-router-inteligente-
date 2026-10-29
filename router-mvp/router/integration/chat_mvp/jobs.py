"""Parallel agent jobs through the Router: each job = one agent + one model + optional GitHub commit. No sandbox:
the commit uses the real account token selected by name. Each job is a single-node riu.dag/v1 plan, so it keeps the
deterministic rules (literal input block, PASS only from `expect`, hash-chained ledger).
Concurrency is capped (default 8) to protect provider rate limits.
"""
from __future__ import annotations

import asyncio
from concurrent.futures import ThreadPoolExecutor
from typing import Any

from fastapi import APIRouter, Depends, Header, HTTPException
from pydantic import BaseModel, Field

from . import dag as dagmod
from . import dag_cli
from . import github_tools as gh
from . import providers as prov
from .router import _auth, get_store
from .store import Store

COMMITTABLE = {"PASS"}


def _one(store: Store, owner: str, job: dict[str, Any], executor: Any, agents: dict[str, str],
         github_byok: str | None, put_file: Any) -> dict[str, Any]:
    plan = {"schema": dagmod.SCHEMA, "id": job["id"], "input_block": job.get("input_block") or job["instructions"],
            "nodes": [{"id": "J", "stage": "worker", "agent": job.get("agent_id"), "model": {"provider": job["provider"], "model": job["model"]},
                       "instructions": job["instructions"], "expect": job.get("expect"), "retries": int(job.get("retries", 0)),
                       "max_tokens": int(job.get("max_tokens", 1024))}]}
    out: dict[str, Any] = {"id": job["id"], "agent_id": job.get("agent_id"), "model": f"{job['provider']}/{job['model']}", "commit": None, "error": None}
    try:
        res = dagmod.run_dag(plan, executor, agents=agents, known_providers=set(prov.PROVIDERS))
    except dagmod.DagError as exc:
        return {**out, "status": "INVALID", "error": str(exc)}
    node = res["nodes"]["J"]
    out.update(status=res["status"], verdict=node["status"], checks_failed=node.get("checks_failed", []),
               reply_preview=(node.get("reply") or "")[:400], ledger_valid=res["ledger_valid"])
    target = job.get("github")
    if target:
        allow = res["status"] in COMMITTABLE or (target.get("allow_unverified") and res["status"] == "UNVERIFIED")
        if not allow:
            out["error"] = f"NOT_COMMITTED_STATUS_{res['status']}"
            return out
        token = gh.token_for(target["account"], github_byok)
        if not token:
            out["error"] = "GITHUB_ACCOUNT_NOT_CONFIGURED"
            return out
        try:
            out["commit"] = put_file(token, target["repo"], target["path"], node["reply"],
                                     target.get("message") or f"job {job['id']} by {job.get('agent_id')} ({res['status']})", target.get("branch"))
        except gh.GitHubError as exc:
            out["error"] = str(exc)
    return out


def run_jobs(store: Store, owner: str, jobs: list[dict[str, Any]], *, max_parallel: int = 8, keys: dict[str, str] | None = None,
             github_byok: str | None = None, executor: Any = None, put_file: Any = None) -> list[dict[str, Any]]:
    executor = executor or dag_cli.build_executor(store, owner, keys)
    put_file = put_file or gh.put_file
    agents = {a["id"]: a["system_prompt"] for a in store.agents()}
    with ThreadPoolExecutor(max_workers=max(1, min(max_parallel, len(jobs)))) as pool:
        return list(pool.map(lambda j: _one(store, owner, j, executor, agents, github_byok, put_file), jobs))


class JobReq(BaseModel):
    id: str = Field(pattern=r"^[A-Za-z0-9_.-]{1,64}$")
    agent_id: str | None = None
    provider: str
    model: str
    instructions: str = Field(min_length=1, max_length=20000)
    input_block: str | None = None
    expect: dict[str, Any] | None = None
    retries: int = Field(default=0, ge=0, le=2)
    max_tokens: int = Field(default=1024, ge=1, le=8192)
    github: dict[str, Any] | None = None  # {account, repo, path, message?, branch?, allow_unverified?}


class JobsReq(BaseModel):
    jobs: list[JobReq] = Field(min_length=1, max_length=100)
    max_parallel: int = Field(default=8, ge=1, le=32)


def build_jobs_router() -> APIRouter:
    r = APIRouter()

    @r.post("/chat/jobs/run")
    async def jobs_run(req: JobsReq, owner: str = Depends(_auth),
                       x_provider_keys: str | None = Header(default=None, alias="X-Provider-Keys"),
                       x_github_token: str | None = Header(default=None, alias="X-GitHub-Token")) -> dict[str, Any]:
        import json

        keys: dict[str, str] = {}
        if x_provider_keys:
            try:
                parsed = json.loads(x_provider_keys)
            except json.JSONDecodeError as exc:
                raise HTTPException(status_code=400, detail="X_PROVIDER_KEYS_INVALID_JSON") from exc
            keys = {str(k): str(v) for k, v in parsed.items()} if isinstance(parsed, dict) else {}
        st = get_store()
        results = await asyncio.to_thread(run_jobs, st, owner, [j.model_dump() for j in req.jobs], max_parallel=req.max_parallel,
                                          keys=keys, github_byok=x_github_token)
        return {"results": results, "passed": sum(1 for x in results if x.get("status") == "PASS"), "total": len(results)}

    return r
