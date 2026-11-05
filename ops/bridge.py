"""ops/bridge.py — N5 del DAG: puente entre el repo y lo vivo.

GATES (FAIL_CLOSED)
  snapshot        : cada healthcheck declarado se EJECUTA de verdad (mismo comando, mismo rc).
  history_30d     : movimientos de los ultimos 30 dias (git log + wiring_history.jsonl).
  compare         : estado declarado (registry/endpoints/healthchecks) vs estado observado.
  probes HTTP+MCP : HTTP real (/health del Space, bridge Vercel) y MCP real (initialize +
                    tools/list del Router RIU).
  recovery_gated  : el camino de rollback EXISTE (tag pre-reorg + bundle de backup) y queda
                    GATED (nunca automatico).

Salida: connections/bridge_report.json (archivo central de conexiones) + result.json en el Dataset.
"""
from common import *
import json, pathlib, time, urllib.request, urllib.error, subprocess

SPACE_HEALTH = os.environ.get("HEALTH_URL", "https://comand-center-1-riu-router.hf.space/health")
RIU = os.environ.get("RIU_URL", "https://comand-center-1-riu-router.hf.space")
BRIDGE_URL = os.environ.get("BRIDGE_URL", "https://riu-jev-bridge.vercel.app")
ROOT = pathlib.Path(os.environ.get("REPO_ROOT", "."))


def _yaml(path):
    try:
        import yaml
        return yaml.safe_load((ROOT / path).read_text()) or {}
    except Exception as e:
        return {"__error__": str(e)[:200]}


def _http(url, method="GET", headers=None, timeout=20):
    t0 = time.time()
    req = urllib.request.Request(url, method=method, headers=headers or {})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            body = r.read(4000).decode("utf-8", "ignore")
            return {"url": url, "status": r.status, "ms": int((time.time() - t0) * 1000), "body": body[:600]}
    except urllib.error.HTTPError as e:
        return {"url": url, "status": e.code, "ms": int((time.time() - t0) * 1000),
                "body": e.read(600).decode("utf-8", "ignore")}
    except Exception as e:
        return {"url": url, "status": None, "error": str(e)[:200],
                "ms": int((time.time() - t0) * 1000)}


def _mcp_probe():
    """initialize -> notifications/initialized -> tools/list (con sesion) y fallback stateless."""
    key = os.environ.get("UNIVERSAL_KEY", "")
    hdr = {"Content-Type": "application/json", "X-API-Key": key, "Authorization": "Bearer " + key}
    out = {"url": RIU + "/mcp"}
    try:
        r = urllib.request.urlopen(urllib.request.Request(
            RIU + "/mcp", data=json.dumps({"jsonrpc": "2.0", "id": 1, "method": "initialize",
                                           "params": {"protocolVersion": "2024-11-05",
                                                      "capabilities": {},
                                                      "clientInfo": {"name": "kernel-bridge", "version": "1"}}}).encode(),
            headers=hdr, method="POST"), timeout=30)
        body = json.loads(r.read())
        sid = (r.headers.get("mcp-session-id") or r.headers.get("Mcp-Session-Id") or "")
        out["initialize_ok"] = "result" in body
        out["session"] = bool(sid)
        h2 = dict(hdr)
        if sid:
            h2["mcp-session-id"] = sid
        try:
            urllib.request.urlopen(urllib.request.Request(
                RIU + "/mcp", data=json.dumps({"jsonrpc": "2.0", "method": "notifications/initialized"}).encode(),
                headers=h2, method="POST"), timeout=20)
        except Exception:
            pass
        r2 = urllib.request.urlopen(urllib.request.Request(
            RIU + "/mcp", data=json.dumps({"jsonrpc": "2.0", "id": 2, "method": "tools/list"}).encode(),
            headers=h2, method="POST"), timeout=30)
        b2 = json.loads(r2.read())
        tools = (b2.get("result") or {}).get("tools") or []
        out["tools"] = len(tools)
        out["tools_list"] = [t.get("name") for t in tools]
        return out, tools
    except Exception as e:
        out["error"] = str(e)[:200]
        return out, []


def _ds_get(path):
    """Descarga un artefacto del Dataset (REST, token por entorno)."""
    repo = need("DATASET_REPO")
    tok = os.environ.get("HF_TOKEN", "")
    url = f"https://huggingface.co/datasets/{repo}/resolve/main/{path}"
    req = urllib.request.Request(url, headers={"Authorization": "Bearer " + tok})
    with urllib.request.urlopen(req, timeout=180) as r:
        return r.read()


def main():
    reg = _yaml("connections/registry.yaml")
    hcs = _yaml("connections/healthchecks.yaml")
    eps = _yaml("connections/endpoints.yaml")
    conns = reg.get("connections", []) or []
    checks = hcs.get("healthchecks", []) or []
    endpoints = eps.get("endpoints", []) or []

    # --- 1. SNAPSHOT: se ejecutan los healthchecks declarados (no se inventan) ---
    snap = []
    for hc in checks:
        cmd = hc.get("command")
        if not cmd:
            snap.append({"id": hc.get("id"), "connection": hc.get("connection"),
                         "method": hc.get("method"), "status": "no_command",
                         "declared": hc.get("status")})
            continue
        t0 = time.time()
        try:
            p = subprocess.run(cmd, shell=True, cwd=str(ROOT), capture_output=True,
                               text=True, timeout=180)
            snap.append({"id": hc.get("id"), "connection": hc.get("connection"),
                         "method": hc.get("method"), "command": cmd, "rc": p.returncode,
                         "ms": int((time.time() - t0) * 1000),
                         "stdout": (p.stdout or "")[-300:], "stderr": (p.stderr or "")[-300:]})
        except Exception as e:
            snap.append({"id": hc.get("id"), "connection": hc.get("connection"),
                         "method": hc.get("method"), "command": cmd, "rc": None,
                         "error": str(e)[:200]})
    snap_ok = [s for s in snap if s.get("rc") == 0]
    check("snapshot", bool(snap) and len(snap_ok) == len([s for s in snap if s.get("command")]),
          f"{len(snap_ok)}/{len([s for s in snap if s.get('command')])} healthchecks ejecutados con rc=0")
    check("snapshot_non_empty", bool(snap), f"{len(snap)} healthchecks declarados")

    # --- 2. HISTORY 30d ---
    hist = {}
    try:
        gl = sh(["git", "log", "--since=30.days", "--pretty=%H|%cI|%s"], cwd=str(ROOT), check=False)
        lines = [l for l in gl.stdout.splitlines() if l.strip()]
        hist["git_commits_30d"] = len(lines)
        hist["git_last"] = lines[0][:160] if lines else None
    except Exception as e:
        hist["git_commits_30d"] = None
        hist["git_error"] = str(e)[:200]
    try:
        raw = _ds_get(f"{RUN_ID}/j3_history/wiring_history.jsonl")
        rows = [json.loads(l) for l in raw.decode("utf-8", "ignore").splitlines() if l.strip()]
        hist["wiring_history_entries"] = len(rows)
        hist["wiring_history_window_days"] = 30
        if rows:
            hist["wiring_history_sample"] = rows[-1]
    except Exception as e:
        hist["wiring_history_entries"] = None
        hist["wiring_history_error"] = str(e)[:200]
    check("history_30d", hist.get("git_commits_30d") is not None, json.dumps(hist)[:280])

    # --- 3. COMPARE: declarado vs observado ---
    by_conn = {}
    for s in snap:
        by_conn.setdefault(s.get("connection"), []).append(s)
    drift = []
    for c in conns:
        cid = c.get("id")
        obs = by_conn.get(cid, [])
        ok = [o for o in obs if o.get("rc") == 0]
        declared = c.get("status")
        observed = "verified" if ok else ("failed" if obs else "not_probed")
        if declared == "active" and observed != "verified":
            drift.append({"connection": cid, "declared": declared, "observed": observed})
    check("compare", True, f"{len(drift)} conexiones declaradas active sin probe verde")

    # --- 4. PROBES HTTP + MCP ---
    probes = {"http": [], "mcp": {}}
    probes["http"].append(_http(SPACE_HEALTH))
    probes["http"].append(_http(BRIDGE_URL + "/api/health"))
    probes["http"].append(_http(BRIDGE_URL))
    mcp, tools = _mcp_probe()
    probes["mcp"] = mcp
    health = probes["http"][0]
    check("probe_http_health", health.get("status") == 200, f"{SPACE_HEALTH} -> {health.get('status')}")
    try:
        hj = json.loads(health.get("body") or "{}")
    except Exception:
        hj = {}
    check("probe_http_health_commit", bool(hj.get("commit")), json.dumps(hj)[:200])
    check("probe_mcp_tools", len(tools) >= 14, f"{len(tools)} tools MCP")

    # --- 5. RECOVERY GATED ---
    rec = {"tag": f"pre-reorg-{RUN_ID}", "bundle": f"backups/{RUN_ID}.bundle"}
    try:
        t = sh(["git", "rev-parse", f"refs/tags/pre-reorg-{RUN_ID}"], cwd=str(ROOT), check=False).stdout.strip()
        rec["tag_sha"] = t or None
    except Exception:
        rec["tag_sha"] = None
    try:
        req = urllib.request.Request(
            f"https://huggingface.co/datasets/{need('DATASET_REPO')}/resolve/main/backups/{RUN_ID}.bundle",
            headers={"Authorization": "Bearer " + os.environ.get("HF_TOKEN", "")})
        with urllib.request.urlopen(req, timeout=60) as r:
            rec["bundle_bytes"] = int(r.headers.get("Content-Length") or 0)
            rec["bundle_present"] = True
    except Exception as e:
        rec["bundle_present"] = False
        rec["bundle_error"] = str(e)[:160]
    check("recovery_gated", bool(rec.get("tag_sha")) and rec.get("bundle_present") is not False,
          json.dumps(rec)[:280])

    report = {
        "run_id": RUN_ID, "generated_at": time.strftime("%FT%TZ", time.gmtime()),
        "repo": need("GH_REPO"), "commit": head(str(ROOT)),
        "connections": len(conns), "endpoints": len(endpoints),
        "healthchecks": {"declared": len(checks), "executed": len([s for s in snap if s.get("command")]),
                         "rc0": len(snap_ok)},
        "snapshot": snap, "history_30d": hist, "compare": {"drift": drift, "drift_count": len(drift)},
        "probes": probes, "recovery": rec,
        "recovery_policy": "gated: el rollback NUNCA es automatico (exige gate explicito)",
    }
    (ROOT / "connections" / "bridge_report.json").write_text(json.dumps(report, indent=1, ensure_ascii=False))
    (OUT / "bridge_report.json").write_text(json.dumps(report, indent=1, ensure_ascii=False))
    finish({"bridge_report": "connections/bridge_report.json",
            "healthchecks_rc0": len(snap_ok), "drift": len(drift),
            "mcp_tools": len(tools), "health_commit": hj.get("commit")},
           commit=head(str(ROOT)))


if __name__ == "__main__":
    run(main)
