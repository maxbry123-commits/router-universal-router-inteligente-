"""Deterministic gates for DAG agent nodes; model replies never approve themselves."""
from __future__ import annotations

import hashlib
import importlib.util
import json
import re
import sys
from collections.abc import Callable
from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parents[3]
AGENTS = ROOT / "chat router/05-AGENTES"


def _government(name: str) -> Any:
    module_name = f"yaiwes_government_{name}"
    if module_name in sys.modules:
        return sys.modules[module_name]
    spec = importlib.util.spec_from_file_location(module_name, AGENTS / "gobierno" / f"{name}.py")
    if spec is None or spec.loader is None:
        raise RuntimeError(f"AGENT_CONTRACT_MISSING:{name}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    try:
        spec.loader.exec_module(module)
    except Exception:
        sys.modules.pop(module_name, None)
        raise
    return module


def registry() -> dict[str, Any]:
    data = yaml.safe_load((AGENTS / "AGENTES.yaml").read_text(encoding="utf-8"))
    if data.get("schema") != "yaiwes.agentes/v1":
        raise ValueError("AGENT_REGISTRY_SCHEMA_INVALID")
    return data


def graph() -> dict[str, Any]:
    data = registry()
    roles = [row for section in ("jerarquia", "colmena_ingenieria", "apoyo") for row in data[section]]
    ids = {row["id"] for row in roles} | {"director"}
    edges = data["grafo"]
    if len(ids) != len(roles) + 1 or any(len(edge) != 2 or not set(edge) <= ids for edge in edges):
        raise ValueError("AGENT_GRAPH_INVALID")
    if ["meta_fixer", "codex"] not in edges or ["codex", "sentinel"] not in edges:
        raise ValueError("AGENT_CODEX_REVIEW_MISSING")
    return {"schema": "yaiwes.agent_graph/v1", "nodes": [
        {"id": "director", "rol": "director"},
        *[{"id": row["id"], "rol": row.get("rol", "support")} for row in roles],
    ], "edges": edges}


def validate_node(node: dict[str, Any]) -> list[str]:
    roles = {row["id"]: row for section in ("jerarquia", "colmena_ingenieria", "apoyo")
             for row in registry()[section]}
    errors: list[str] = []
    agent = node.get("agente")
    if not isinstance(agent, str) or agent not in roles or not roles[agent].get("rol") or node.get("rol") != roles[agent]["rol"]:
        errors.append("AGENT_INVALID_ROLE")
    if not isinstance(node.get("id"), str) or not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]{0,63}", node["id"]):
        errors.append("AGENT_ID_INVALID")
    paths = node.get("allowed_paths")
    if not isinstance(paths, list) or not paths or any(not isinstance(p, str) or not p for p in paths):
        errors.append("AGENT_ALLOWED_PATHS_INVALID")
    if node.get("puertas") != ["sheriff", "judge"]:
        errors.append("AGENT_GATES_REQUIRED")
    if node.get("output_schema") != "yaiwes.result/v1":
        errors.append("AGENT_RESULT_SCHEMA_INVALID")
    job = node.get("input")
    if not isinstance(job, dict):
        errors.append("AGENT_JOB_INVALID")
    else:
        try:
            _government("contratos").Job.from_dict(job)
        except (ValueError, TypeError, KeyError):
            errors.append("AGENT_JOB_INVALID")
        if paths != job.get("scope") or not job.get("acceptance"):
            errors.append("AGENT_JOB_SCOPE_INVALID")
    checklist = node.get("checklist")
    if not isinstance(checklist, dict) or not checklist or any(type(v) is not bool for v in checklist.values()):
        errors.append("AGENT_CHECKLIST_INVALID")
    if node.get("loop") or node.get("retries") or node.get("escalate_to"):
        errors.append("AGENT_ONE_ATTEMPT_REQUIRED")
    budget = node.get("token_budget")
    if budget is not None and (type(budget) is not int or budget <= 0):
        errors.append("AGENT_TOKEN_BUDGET_INVALID")
    return errors


def truth_check(truth: dict[str, dict[str, Any]] | None) -> str | None:
    if not isinstance(truth, dict) or any(not isinstance(truth.get(k), dict) for k in
                                          ("CORE", "CONTRATOS", "DECISIONES", "GRAFO")):
        return "ACTIVE_TRUTH_MISSING"
    resolved: dict[str, Any] = {}
    for layer in ("CORE", "CONTRATOS", "DECISIONES", "GRAFO"):
        for key, value in truth[layer].items():
            if key in resolved and resolved[key] != value:
                return f"ACTIVE_TRUTH_CONFLICT:{key}"
            resolved[key] = value
    return None


def preflight(node: dict[str, Any], step: int, total: int, previous_pass: bool,
              truth: dict[str, dict[str, Any]] | None) -> str | None:
    job = node["input"]
    if node.get("step") != step or node.get("total_steps") != total or (step > 1 and not previous_pass):
        return "P1_STEP_ORDER"
    if not all(node["checklist"].values()):
        return "P1_CHECKLIST_FAILED"
    ok, _reason = _government("sheriff").Sheriff().validate({"tasks": [{
        "id": node["id"], "acceptance": job["acceptance"],
        "dependencies": node.get("needs", []), "allowed_paths": node["allowed_paths"],
    }, *[{"id": dep, "acceptance": ["dependency"]} for dep in node.get("needs", [])]]})
    if not ok:
        return "SHERIFF_DENIED"
    return truth_check(truth)


def _hash(data: Any) -> str:
    return hashlib.sha256(json.dumps(data, sort_keys=True, ensure_ascii=False).encode()).hexdigest()


def postflight(node: dict[str, Any], reply: str, usage: dict[str, Any],
               reviews: dict[str, dict[str, Any]] | None, evidence: dict[str, Any] | None,
               archive: Callable[[dict[str, Any]], bool] | None) -> tuple[str | None, dict[str, Any]]:
    checkpoint = {"input_sha256": _hash(node["input"]), "output_sha256": _hash(reply),
                  "step": node["step"], "total_steps": node["total_steps"]}
    try:
        result = _government("contratos").Result.from_dict(json.loads(reply))
    except (ValueError, TypeError, KeyError):
        return "AGENT_RESULT_INVALID", checkpoint
    if result.job_id != node["input"]["job_id"] or result.agent != node["agente"]:
        return "AGENT_RESULT_MISMATCH", checkpoint
    if any(path not in node["allowed_paths"] for path in result.changed_files):
        return "P1_SCOPE_DRIFT", checkpoint
    if result.status != "PASS":
        return "AGENT_RESULT_NOT_PASS", checkpoint
    budget = node.get("token_budget")
    used = int(usage.get("prompt_tokens") or 0) + int(usage.get("completion_tokens") or 0)
    if budget is not None and used >= int(budget) * 0.8:
        if archive is None or not archive(checkpoint):
            return "P2_ARCHIVE_REQUIRED", checkpoint
        checkpoint["archived"] = True
    if evidence is None or reviews is None:
        return "JUDGE_EVIDENCE_MISSING", checkpoint
    if evidence.get("input_sha256") != checkpoint["input_sha256"] or evidence.get("output_sha256") != checkpoint["output_sha256"]:
        return "JUDGE_EVIDENCE_HASH_MISMATCH", checkpoint
    if evidence.get("changed_files") != result.changed_files:
        return "JUDGE_CHANGED_FILES_MISMATCH", checkpoint
    verdict = _government("judge").Judge().decide(node["input"], evidence,
                                                      reviews.get("hermes", {}), reviews.get("openclaw", {}))
    return (None if verdict == "PASS" else f"JUDGE_{verdict}"), checkpoint


def event(node: dict[str, Any], status: str, reason: str) -> dict[str, str]:
    return {"type": "CHECKPOINT_RECORDED" if status == "PASS" else "TASK_BLOCKED",
            "project": "chat-yaiwes", "task": node["id"], "actor": node["agente"],
            "phase": "AGENT_GATE", "status": "RUNNING" if status == "PASS" else "BLOCKED",
            "next": "NEXT_NODE" if status == "PASS" else "DIRECTOR_INTERVENTION",
            "summary": f"{status}: {reason}"}


if __name__ == "__main__":
    target = ROOT / "chat router/03-ESTADO/AGENT_GRAPH.json"
    target.write_text(json.dumps(graph(), ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
