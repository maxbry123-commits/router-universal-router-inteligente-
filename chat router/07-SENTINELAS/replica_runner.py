"""Runner único para las réplicas chat/fabrica/plan4.

No contiene reglas de gobierno: importa el LOOP común desde
05-AGENTES/gobierno/sentinel_loop.py. Cada réplica solo cambia REPLICAS.yaml.
"""
from __future__ import annotations

import datetime as dt
import hashlib
import json
import os
import pathlib
import subprocess
import sys
import urllib.request

import yaml

ROOT = pathlib.Path("chat router")
GOBIERNO = ROOT / "05-AGENTES" / "gobierno"
sys.path.insert(0, str(GOBIERNO))

from sentinel_loop import (  # noqa: E402
    SentinelDAG,
    SentinelDSL,
    SentinelOrchestrator,
    SentinelResearchPlanner,
    SentinelSheriff,
    update_state,
)

BASE = ROOT / "07-SENTINELAS"
CFG_PATH = BASE / "REPLICAS.yaml"


def sh(cmd: list[str], timeout: int = 120) -> tuple[int, str]:
    try:
        p = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        return p.returncode, (p.stdout + p.stderr)[-12000:]
    except subprocess.TimeoutExpired:
        return 124, "TIMEOUT"


def utc_now() -> str:
    return dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%MZ")


def loop_version() -> str:
    """Huella única: las 3 réplicas deben ejecutar exactamente esta versión."""
    paths = (
        GOBIERNO / "sentinel_loop.py",
        BASE / "replica_runner.py",
        BASE / "REPLICAS.yaml",
        BASE / "CONTRATOS.yaml",
    )
    h = hashlib.sha256()
    for path in paths:
        h.update(str(path).encode("utf-8"))
        h.update(path.read_bytes())
    return h.hexdigest()[:16]


def gh_json(endpoint: str) -> object:
    rc, out = sh(["gh", "api", endpoint])
    if rc != 0:
        return {}
    try:
        return json.loads(out)
    except json.JSONDecodeError:
        return {}


def repo_head(repo: str) -> str:
    data = gh_json(f"repos/{repo}/commits/main")
    return str(data.get("sha", "")) if isinstance(data, dict) else ""


def recent_commits(repo: str) -> list[dict]:
    data = gh_json(f"repos/{repo}/commits?per_page=12")
    if not isinstance(data, list):
        return []
    out = []
    for item in data:
        commit = item.get("commit", {})
        out.append({
            "sha": item.get("sha", "")[:10],
            "date": commit.get("author", {}).get("date", ""),
            "message": str(commit.get("message", "")).splitlines()[0],
        })
    return out


def recent_runs(repo: str) -> list[dict]:
    data = gh_json(f"repos/{repo}/actions/runs?per_page=15")
    runs = data.get("workflow_runs", []) if isinstance(data, dict) else []
    return [{
        "id": r.get("id"),
        "name": r.get("name"),
        "status": r.get("status"),
        "conclusion": r.get("conclusion"),
        "created_at": r.get("created_at"),
    } for r in runs]


def load_json(path: str) -> dict:
    p = pathlib.Path(path)
    if not p.exists():
        return {}
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return {}


def select_priority_task(cfg: dict) -> dict:
    state_path = cfg.get("task_state_path")
    if not state_path:
        return {}
    states = load_json(state_path)
    for tid in cfg.get("task_priority", []):
        st = states.get(tid, {})
        if st.get("status") != "PASS":
            return {
                "task_id": tid,
                "status": st.get("status", "UNKNOWN"),
                "attempt": st.get("attempt", 0),
                "failure": st.get("last_failure", ""),
                "next_action": st.get("next_action", ""),
                "evidence": st.get("evidence", {}),
            }
    return {"task_id": "", "status": "ALL_PASS"}


def research_community(cfg: dict, packet: dict) -> list[dict]:
    """Busca evidencia comunitaria real; el pool puede crecer hasta 20 fuentes."""
    failure = packet.get("failure", "")
    literal = packet.get("error_literal", "")
    query = (literal or failure or "failure").replace("\n", " ")[:120]
    findings: list[dict] = []

    for repo in cfg.get("research_repos", []):
        rc, out = sh([
            "gh", "search", "issues", query,
            "--repo", repo, "--limit", "3",
            "--json", "title,url,state,updatedAt",
        ])
        if rc != 0:
            continue
        try:
            for item in json.loads(out or "[]"):
                item["source"] = f"GitHub:{repo}"
                findings.append(item)
                if len(findings) >= packet["max_sources"]:
                    return findings
        except json.JSONDecodeError:
            pass

    # Stack Overflow: sin credenciales; sirve como fuente independiente.
    try:
        from urllib.parse import quote
        url = (
            "https://api.stackexchange.com/2.3/search/advanced"
            f"?site=stackoverflow&order=desc&sort=relevance&pagesize=5&q={quote(query)}"
        )
        with urllib.request.urlopen(url, timeout=20) as r:
            data = json.loads(r.read())
        for item in data.get("items", []):
            findings.append({
                "source": "StackOverflow",
                "title": item.get("title"),
                "url": item.get("link"),
            })
            if len(findings) >= packet["max_sources"]:
                break
    except Exception:
        pass
    return findings[:packet["max_sources"]]


def nvidia(prompt: str) -> tuple[str, str]:
    for key_name in (
        "NVIDIA_API_KEY_1", "NVIDIA_API_KEY_2",
        "NVIDIA_API_KEY_3", "NVIDIA_API_KEY_4",
    ):
        key = os.environ.get(key_name)
        if not key:
            continue
        for model in ("moonshotai/kimi-k3", "z-ai/glm-5.3", "z-ai/glm-5.3-flash"):
            body = json.dumps({
                "model": model,
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": 1100,
                "temperature": 0.1,
            }).encode()
            req = urllib.request.Request(
                "https://integrate.api.nvidia.com/v1/chat/completions",
                data=body,
                headers={
                    "Authorization": f"Bearer {key}",
                    "Content-Type": "application/json",
                },
            )
            try:
                with urllib.request.urlopen(req, timeout=120) as r:
                    text = json.loads(r.read())["choices"][0]["message"]["content"]
                    return text, f"{model}@{key_name}"
            except Exception:
                continue
    return "", "ninguno"


def build_evidence(cfg: dict) -> tuple[dict, dict]:
    repo = cfg["repository"]
    head = repo_head(repo)
    commits = recent_commits(repo)
    runs = recent_runs(repo)
    priority = select_priority_task(cfg)

    active = False
    failure = ""
    error_literal = ""
    if priority:
        active = priority.get("status") == "ACTIVE"
        failure = priority.get("failure", "")
        ev = priority.get("evidence", {})
        error_literal = str(ev.get("pytest_tail", ""))[-1000:]

    objective = {
        "head_fresh": bool(head),
        "recent_commits_observed": bool(commits),
        "runs_observed": bool(runs),
        "priority_goal_observed": bool(cfg.get("priority_goals")),
    }
    evidence = {
        "observed_sha": head,
        "current_sha": repo_head(repo),
        "executor_active": active,
        "workflow_false_green": False,
        "unauthorized_change": False,
        "failure_class": failure,
        "error_literal": error_literal,
        "objective_evidence": objective,
        "recent_commits": commits,
        "recent_runs": runs,
        "priority_task": priority,
    }
    return evidence, priority


def write_report(
    spec, cfg: dict, state: dict, result: dict,
    evidence: dict, research: dict | None, model: str,
) -> None:
    report = pathlib.Path(spec.report_path)
    report.parent.mkdir(parents=True, exist_ok=True)
    priority = evidence.get("priority_task", {})
    version = loop_version()
    lines = [
        f"# {spec.sentinel_id.upper()} — {utc_now()}",
        f"(LOOP común · versión: {version} · modelo investigador: {model})",
        "",
        f"OBJETIVO: {spec.objective}",
        f"ESTADO LOOP: {result['state']} · {result['reason']}",
        f"OBSERVED_SHA: {evidence.get('observed_sha', '')[:12]}",
        "",
        "PRIORIDADES:",
    ]
    lines += [f"{i+1}. {g}" for i, g in enumerate(spec.priority_goals)]
    if priority:
        lines += [
            "",
            "OBJETIVO ACTIVO:",
            f"- tarea: {priority.get('task_id', '-')}",
            f"- estado: {priority.get('status', '-')}",
            f"- intento: {priority.get('attempt', 0)}",
            f"- fallo: {priority.get('failure', '') or 'ninguno registrado'}",
            f"- siguiente: {priority.get('next_action', '') or 'verificar'}",
        ]
    if research:
        lines += [
            "",
            "INVESTIGACIÓN:",
            f"- fuentes consultadas: {len(research.get('findings', []))}",
            f"- mínimo independiente objetivo: {research['packet']['min_independent_sources']}",
            "",
            research.get("analysis", "sin análisis"),
        ]
    lines += [
        "",
        "CONTROL:",
        "- PASS no lo decide la LLM.",
        "- Cada ciclo relee HEAD; un informe con SHA viejo queda inválido.",
        "- Si el mismo fallo se repite, escala a investigación antes de reintentar.",
        "- El sentinela solo puede escribir informes/órdenes, no código del objetivo.",
    ]
    report.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_order(spec, cfg: dict, result: dict, evidence: dict, research: dict | None) -> None:
    path = pathlib.Path(cfg["order_path"])
    path.parent.mkdir(parents=True, exist_ok=True)
    priority = evidence.get("priority_task", {})
    order = {
        "schema": "yaiwes.sentinel-order/v1",
        "sentinel": spec.sentinel_id,
        "generated_at": utc_now(),
        "loop_version": loop_version(),
        "observed_sha": evidence.get("observed_sha"),
        "objective": spec.objective,
        "priority_task": priority.get("task_id"),
        "state": result["state"],
        "reason": result["reason"],
        "executor_instruction": (
            "No regenerar trabajo válido. Corregir solo la causa demostrada, "
            "ejecutar aceptación real y devolver evidencia."
        ),
        "research_packet": research["packet"] if research else None,
        "research_findings": research["findings"] if research else [],
    }
    path.write_text(yaml.safe_dump(order, allow_unicode=True, sort_keys=False), encoding="utf-8")


def main() -> None:
    replica = os.environ.get("PROYECTO") or (
        sys.argv[sys.argv.index("--replica") + 1] if "--replica" in sys.argv else ""
    )
    all_cfg = yaml.safe_load(CFG_PATH.read_text(encoding="utf-8"))
    if replica not in all_cfg["replicas"]:
        raise SystemExit(f"réplica desconocida: {replica}")

    cfg = dict(all_cfg["replicas"][replica])
    cfg["research_sources"] = list(all_cfg.get("research_pool", []))
    spec = SentinelDSL.parse(cfg)
    SentinelDAG.build(spec)

    sheriff = SentinelSheriff()
    allowed, reason = sheriff.validate_write_paths([
        spec.report_path, cfg["state_path"], cfg["order_path"],
    ])
    if not allowed:
        raise SystemExit(reason)

    previous = load_json(cfg["state_path"])
    evidence, priority = build_evidence(cfg)
    orch = SentinelOrchestrator()
    result = orch.next_action(spec, previous, evidence)

    # Tarea subordinada no PASS: la réplica debe intervenir aunque su propia
    # observación/frescura esté sana.
    if priority and priority.get("status") not in ("PASS", "ALL_PASS", "ACTIVE"):
        result = {
            "state": "RESEARCH" if previous.get("same_failure_count", 0) >= 2 else "REVISE",
            "reason": priority.get("failure") or "priority_task_not_pass",
        }

    research = None
    model = "no requerido"
    if result["state"] in {"REVISE", "RESEARCH"}:
        packet = SentinelResearchPlanner.build(
            spec,
            result["reason"],
            evidence.get("error_literal", ""),
            {"component": priority.get("task_id") if priority else spec.objective},
        )
        findings = research_community(cfg, packet)
        prompt = (
            f"Eres INVESTIGADOR, no juez. Sentinela={spec.sentinel_id}. "
            f"Objetivo={spec.objective}. Fallo={result['reason']}.\n"
            f"Error literal={packet['error_literal']}\n"
            f"Evidencia comunidad={json.dumps(findings, ensure_ascii=False)[:5000]}\n"
            "No declares PASS. Responde máximo 12 líneas: "
            "CAUSA_RAIZ, EVIDENCIA, NO_REGENERAR, REPARAR, ACEPTACION."
        )
        analysis, model = nvidia(prompt)
        research = {
            "packet": packet,
            "findings": findings,
            "analysis": analysis or "Sin respuesta LLM; conservar evidencia y reintentar investigación.",
        }

    state = update_state(previous, result, evidence)
    state["loop_version"] = loop_version()
    if research:
        state["research_packet"] = research["packet"]
        state["research_findings"] = research["findings"]
    state_path = pathlib.Path(cfg["state_path"])
    state_path.parent.mkdir(parents=True, exist_ok=True)
    state_path.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")

    write_order(spec, cfg, result, evidence, research)
    write_report(spec, cfg, state, result, evidence, research, model)
    print(json.dumps({
        "replica": replica,
        "loop_version": loop_version(),
        "state": result["state"],
        "reason": result["reason"],
        "priority": priority.get("task_id") if priority else None,
        "research_sources": len(research["findings"]) if research else 0,
    }))


if __name__ == "__main__":
    main()
