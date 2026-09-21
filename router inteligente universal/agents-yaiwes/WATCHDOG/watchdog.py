"""WATCHDOG (hourly, deterministic, no LLM, no paid tokens).

Reads every agent's Crazy Wall, writes WATCHDOG/STATUS.md and appends WATCHDOG/LOG.md. If some agent is not CLOSED (blocked, or "running" for
more than 60 minutes without a state update) and no `RIU Agents Run` is in progress, it re-dispatches `RIU Agents Run` (which resumes only the
pending steps), at most 3 times per set of closed steps. It never edits chains, never creates agents and never touches anything else: those
decisions are Claude's (see README-WATCHDOG-NOTAS-DE-CLAUDE.md).
"""
from __future__ import annotations

import calendar
import json
import os
import time
import urllib.request
from pathlib import Path

HERE = Path(__file__).resolve().parent
AG = HERE.parent
MAX_RETRIES, STALE_SECONDS = 3, 3600


def load(p: Path) -> dict:
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception:  # noqa: BLE001
        return {}


def age_seconds(ts: str | None) -> float:
    try:
        return time.time() - calendar.timegm(time.strptime(ts, "%Y-%m-%dT%H:%M:%SZ"))
    except Exception:  # noqa: BLE001
        return 0.0


def snapshot() -> list[dict]:
    rows = []
    for d in sorted(AG.glob("agent-*")):
        if not d.is_dir():
            continue
        top = load(d / "crazy_wall.state.json")
        steps = {s.parent.name: load(s) for s in sorted((d / "steps").glob("*/crazy_wall.state.json"))} if (d / "steps").exists() else {}
        chain = top.get("chain") or list(steps)
        closed = [k for k, v in steps.items() if v.get("status") == "CLOSED"]
        gaps = [g for v in steps.values() for g in v.get("gaps", [])][:2]
        rows.append({"agent": d.name, "status": top.get("status", "SIN_ESTADO"), "framework": top.get("framework", "?"), "closed": closed, "total": len(chain),
                     "blocked_at": (top.get("failed") or [None])[0], "stale": top.get("status") == "RUNNING" and age_seconds(top.get("updated_at")) > STALE_SECONDS,
                     "gaps": " | ".join(g[:120] for g in gaps) or "-"})
    return rows


def api(method: str, path: str, body: dict | None = None) -> dict:
    req = urllib.request.Request("https://api.github.com/repos/" + os.environ["GITHUB_REPOSITORY"] + path, method=method,
                                 data=json.dumps(body).encode() if body else None,
                                 headers={"Authorization": "Bearer " + os.environ["GITHUB_TOKEN"], "Accept": "application/vnd.github+json", "User-Agent": "riu-watchdog"})
    with urllib.request.urlopen(req, timeout=30) as r:  # noqa: S310
        raw = r.read().decode()
        return json.loads(raw) if raw else {}


def main() -> int:
    rows = snapshot()
    pending = [r for r in rows if r["status"] != "CLOSED" or r["stale"]]
    sig = json.dumps({r["agent"]: r["closed"] for r in rows}, sort_keys=True)
    retries = load(HERE / "retries.json")
    if retries.get("sig") != sig:
        retries = {"sig": sig, "count": 0}
    action = "nada que hacer: todos los agentes CLOSED" if not pending else "hay agentes pendientes"
    if pending:
        try:
            running = api("GET", "/actions/workflows/riu-agents-run.yml/runs?status=in_progress&per_page=1").get("total_count", 0)
            queued = api("GET", "/actions/workflows/riu-agents-run.yml/runs?status=queued&per_page=1").get("total_count", 0)
            if running or queued:
                action = "hay pendientes; una ronda ya está en curso: no se lanza otra"
            elif retries["count"] >= MAX_RETRIES:
                action = f"hay pendientes; {MAX_RETRIES} reintentos sin avance: ESCALAR A CLAUDE (mejorar el DSL DAG, la ruta o crear agentes)"
            else:
                api("POST", "/actions/workflows/riu-agents-run.yml/dispatches", {"ref": "main"})
                retries["count"] += 1
                action = f"hay pendientes; se lanzó `RIU Agents Run` (reintento {retries['count']}/{MAX_RETRIES})"
        except Exception as exc:  # noqa: BLE001
            action = f"hay pendientes; no se pudo consultar/lanzar la ronda ({type(exc).__name__})"
    (HERE / "retries.json").write_text(json.dumps(retries), encoding="utf-8")
    now = time.strftime("%Y-%m-%d %H:%M:%SZ", time.gmtime())
    lines = [f"# WATCHDOG — estado de los agentes ({now})", "", f"**Acción:** {action}", "",
             "| agente | marco | estado | pasos cerrados | bloqueado en | GAPs |", "|---|---|---|---|---|---|"]
    lines += [f"| {r['agent']} | {r['framework']} | {r['status']}{' (sin avance > 60 min)' if r['stale'] else ''} | {len(r['closed'])}/{r['total']} | {r['blocked_at'] or '-'} | {r['gaps']} |" for r in rows]
    lines += ["", "Claude lee este archivo al abrir sesión o cuando el Director lo pida, y decide (nada de esto lo decide el watchdog): corregir `ROUTE.json`, editar un `chain.yaml`, o crear agentes."]
    (HERE / "STATUS.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    with (HERE / "LOG.md").open("a", encoding="utf-8") as fh:
        fh.write(f"- {now} · {sum(1 for r in rows if r['status'] == 'CLOSED')}/{len(rows)} agentes CLOSED · {action}\n")
    print(f"::notice title=RIU_WATCHDOG::{action} | " + " ".join(f"{r['agent']}={r['status']}({len(r['closed'])}/{r['total']})" for r in rows))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
